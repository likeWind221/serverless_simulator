# fastapi
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket,Request,WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
# type
import json
import queue
# system
import sys
import time
import os
import threading
from datetime import datetime
# mylib
import dataset as ds
import model as md
import records
import controller as cn

root_path = os.getcwd()
sys.path.append(root_path)

app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 实际上应根据需求设置允许的来源
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 辅助类
class result:
  def __init__(self):
    self.day_index = [1]
    self.mode = 0
    self.cold_start_times = 0
    self.total_invocate_times = 0
    self.mem_waste_time = 0
    self.total_mem = 0
    self.used_mem = 0
  def clear(self):
    self.day_index = [1]
    self.mode = 0
    self.cold_start_times = 0
    self.total_invocate_times = 0
    self.total_mem = 0
    self.mem_waste_time = 0
    self.used_mem = 0
  def set_init(self,day_index,mode,total_mem):
    self.day_index = day_index
    self.mode = mode
    self.total_mem = total_mem
    self.cold_start_times = 0
    self.total_invocate_times = 0
    self.mem_waste_time = 0
    self.used_mem = 0
  def set_change(self,cold_start_times,total_invocate_times,mem_waste_time=0,used_mem=0):
    self.cold_start_times = cold_start_times
    self.total_invocate_times = total_invocate_times
    self.mem_waste_time = mem_waste_time
    self.used_mem = used_mem

class ModelInput(BaseModel):
  dateTime: int
  totalTime: int
  mode: int
  keepAliveWindow: int
  prewarm_percent: int
  keepalive_percent: int

class AppStatus(BaseModel):
  name: str

# 全局变量
message_queue = queue.Queue()
model_thread = None
stop_event = threading.Event()
progress = 0
result_obj = result()

# 工具函数
def extract_timestamp(filename):
    # 假设文件名格式为 fixed_keepalive_YYYY-MM-DD_HH-MM-SS
    parts = filename.split('_')
    timestamp_str = '_'.join(parts[2:])  # 提取时间戳部分
    return datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')

def sort_files_by_timestamp(files):
    return sorted(files, key=extract_timestamp, reverse=True)

# 接口
@app.post("/api/run_model")
async def start(input: ModelInput):
  global model_thread
  global stop_event
  global progress
  progress = 0
  # 检查是否有正在运行的任务
  if model_thread and model_thread.is_alive():
    return {"message": "Model is running"}
  stop_event.clear()
  model_thread = threading.Thread(target=run_model, args=(input.dateTime, input.totalTime, input.mode, input.keepAliveWindow,input.prewarm_percent,input.keepalive_percent))
  model_thread.start()
  return {"message": "Model is running"}


@app.post("/api/stop_model")
async def stop_model():
  global stop_event
  global model_thread
  if model_thread and model_thread.is_alive():
    stop_event.set()
    return {"message": "Model is stopping"}
  else:
    return {"message": "Model is not running"}
  
@app.get('/api/status')
async def get_status():
  send_list = []
  while not message_queue.empty():
    send_list.append(message_queue.get())
  return send_list

@app.get('/api/result')
async def get_result():
  # 获取当前文件路径
  current_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
  # 查找result文件夹
  result_dir = os.path.join(current_dir,'result')
  # 判断result文件夹是否存在
  if not os.path.exists(result_dir):
    return {"message": "Result not found"}
  # 获取result文件夹下所有的文件夹
  result_dirs = os.listdir(result_dir)
  # 对文件列表进行排序
  sorted_dirs = sort_files_by_timestamp(result_dirs)
  # 建立结果list
  result_list = []
  # 遍历文件夹
  for child_dir in sorted_dirs:
    # 获取当前文件夹名称
    result_name = os.path.basename(child_dir)
    # 读取文件夹下的result.json文件
    result_file = os.path.join(result_dir,child_dir,'result.json')
    # 读取文件夹下的apps.json文件
    apps_file = os.path.join(result_dir,child_dir,'apps.json')
    # json读取
    with open(result_file, 'r') as f:
      result_data = json.load(f)
    # 组装json
    result_json = {
      "name": result_name,
      "data": result_data,
    }
    # 加入结果list
    result_list.append(result_json)
  return result_list

@app.post('/api/app_status')
async def get_app_status(input_data: AppStatus):
  # 获取当前文件路径
  current_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
  # 查找result文件夹
  result_dir = os.path.join(current_dir,'result')
  # 判断result文件夹是否存在
  if not os.path.exists(result_dir):
    return {"message": "Result not found"}
  # 获取result文件夹下所有的文件夹
  result_dirs = os.listdir(result_dir)
  # 遍历文件夹
  for child_dir in result_dirs:
    # 获取当前文件夹名称
    result_name = os.path.basename(child_dir)
    if result_name == input_data.name:
      # 读取文件夹下的apps.json文件
      apps_file = os.path.join(result_dir,child_dir,'apps.json')
      # 读取apps.json文件
      with open(apps_file, 'r') as f:
        apps_data = json.load(f)
      return apps_data
  return {"message": "App not found"}

@app.delete('/api/delete_result')
async def delete_result(input_data: AppStatus):
  # 获取当前文件路径
  current_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
  # 查找result文件夹
  result_dir = os.path.join(current_dir,'result')
  # 判断result文件夹是否存在
  if not os.path.exists(result_dir):
    return {"message": "Result not found"}
  # 获取result文件夹下所有的文件夹
  result_dirs = os.listdir(result_dir)
  # 遍历文件夹
  for child_dir in result_dirs:
    # 获取当前文件夹名称
    result_name = os.path.basename(child_dir)
    if result_name == input_data.name:
      # 删除文件夹
      import shutil
      shutil.rmtree(os.path.join(result_dir,child_dir))
      return {"message": "Delete success"}
  return {"message": "App not found"}

def run_model(date_time: int, total_time: int, mode: int, keep_alive_window: int,prewarm_percent: int,keepalive_percent: int):
  global stop_event
  global result_obj
  global progress
  global message_queue
  # 准备工作
  # 实例化结果类
  result_obj.clear()
  # 实例化记录类
  Records = records.Records()
  # 实例化数据集类
  DataSet = ds.Dataset(date_time)
  # 实例化控制器类
  Controller = cn.Controller(mode,Records,keep_alive_window,prewarm_percent,keepalive_percent)
  # 加载数据集
  message_queue.put({"type": 0, "message": "加载数据集中..."})
  DataSet.load_data(mode='default')
  message_queue.put({"type": 0, "message": "加载数据集完毕"})
  # 设定节点参数，实例化模型类
  node_num = 1
  model = md.Model(Records,DataSet,Controller) 
  model.add_compute_node(node_num)
  # 设定运行参数
  model.run_minutes = total_time
  
  # 开始运行
  start_time = time.time()
  count_time = 0
  # 时间轴,从数据集中读取启动的函数及其应用
  for i in range(1,model.run_minutes+1):
    count_time += 1
    if stop_event.is_set():
      break
    # 函数重载
    model.reload_apps(i)
    # 获取需要处理的函数调用
    current_invocate = DataSet.function_data[DataSet.function_data[str(i)]!=0]
    current_invocate = current_invocate[["HashApp","HashFunction","Average"]]
    # 调用函数部分
    current_invocate.apply(lambda row: model.functions_invocate(row, i), axis=1)
    # 释放函数部分
    model.functions_release(i)

    # 发送状态信息到ws服务器
    result_obj.set_change(Records.coldStartCount,Records.invocateCount,Records.memWasteTime,Records.used_mem)
    if (i == model.run_minutes):
      progress = 100
    else:
      progress = i/model.run_minutes*100
    message = { "type": 1,
                "run_period": count_time,
                "progress": round(progress),
                "coldStartTimes": result_obj.cold_start_times,
                "invocateTimes": result_obj.total_invocate_times,
                "memWasteTime": result_obj.mem_waste_time,
                "used_mem": result_obj.used_mem,
                "total_mem": result_obj.total_mem,
                "mode": result_obj.mode,
                "minutes": count_time}
    message_queue.put(message)

  end_time = time.time()
  Records.model_run_time = end_time - start_time
  model.save_model_result()
  message_queue.put({"type": 2, "progress": 100,"coldStartTimes":Records.coldStartCount,"invocateTimes":Records.invocateCount,"actualRunTime":round(Records.model_run_time,2),"without_first":Records.without_first_invocate()})
  

if __name__ == "__main__":
  import uvicorn
  uvicorn.run("main:app", host="localhost", port=8000,reload=False)