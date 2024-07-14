# 整体架构模型
import pandas as pd
import compute_node as cn
import time as os_time
import json
import os
import records

# 启用全局类型下推选项
pd.set_option('future.no_silent_downcasting', True)

class Model:
  def __init__(self,Records,DataSet,Controller):

    self.compute_nodes = list() # 计算节点列表

    # 创建用于记录计算节点情况的数据表
    self.node_mem_usage = pd.DataFrame(columns=range(0,11),index=range(1,1441))
    # 记录应用的各类状态：冷启动次数、调用次数、内存浪费时间、分配的计算节点id、预热窗口、保持窗口、到达时间、

    # 运行参数
    self.run_minutes = 1440 # 运行时长（分钟）

    # 装载数据集类和记录类
    self.dataset = DataSet
    self.records = Records
    
    # 控制器模式设定
    # 0-fixed keep alive, 1- hybrid histogram
    self.Controller = Controller

  # 添加计算节点 
  def add_compute_node(self, node_num):
    # 根据计算节点数量，创建计算节点列表
    for i in range(node_num):
      # 添加计算节点
      self.compute_nodes.append(cn.ComputeNode(i,self.records,self.Controller))
      # 初始化个节点内存的记录状态
      self.node_mem_usage[i]=self.node_mem_usage[i].fillna(0)

  # 保存运行结果
  def save_model_result(self):
    save_time = os_time.strftime("%Y-%m-%d_%H-%M-%S", os_time.localtime())
    # 创建保存的json信息
    result_dict = {
      "mode": self.Controller.mode,
      "time": save_time,
      "fixed_keepalive_time": self.Controller.fixed_keepalive_time,
      "prewarm_percent":self.Controller.prewarm_percent,
      "keepalive_percent":self.Controller.keepalive_percent,
      "coldStartCount": self.records.coldStartCount,
      "invocateCount": self.records.invocateCount,
      "model_run_time": round(self.records.model_run_time,2),
      "without_first": self.records.without_first_invocate(),
      "memWasteTime":self.records.memWasteTime
    }
    # 定义文件名
    dir = f"{self.Controller.mode}_{save_time}"
    # 定义路径
    dir_path = os.path.join(self.dataset.result_dir,dir)
    # 查找result路径是否存在,不存在就创建
    if not os.path.exists(self.dataset.result_dir):
      os.makedirs(self.dataset.result_dir)
    # 在result目录下创建对应的文件夹
    if not os.path.exists(dir_path):
      os.makedirs(dir_path)
    # 定义文件名
    result_path = os.path.join(dir_path, "result.json")
    apps_path = os.path.join(dir_path, "apps.json")
    # 保存json信息
    with open(result_path, 'w') as json_file:
      json.dump(result_dict, json_file)
    # 保存apps信息
    with open(apps_path, 'w') as json_file:
      json.dump(self.records.to_dict(), json_file)
    print(f"结果已保存至：{dir_path}")

  # 应用分配
  def distribute_app(self,app,time):
    # 找到最空闲的节点,即内存空间最大的节点
    node_id = 0
    for i in range(len(self.compute_nodes)):
      if self.compute_nodes[i].avail_mem > self.compute_nodes[node_id].avail_mem:
        node_id = i
    # 再次判断找到的节点空间是否够用
    while app.AverageAllocatedMb > self.compute_nodes[node_id].avail_mem:
      # 空间不够，让节点强制释放app
      self.compute_nodes[node_id].force_unload_app(time)
    # 释放完毕以后，分配给节点
    self.compute_nodes[node_id].load_app(app.HashApp)
    return node_id

  # 调用函数
  def functions_invocate(self,invocate,time):
    # 检查functions_status中是否存在该函数
    # 如果不存在，则创建新条目
    if self.records.functions_status.get(invocate["HashFunction"]) is None:
      # 创建新条目，添加到functions_status中
      function = records.function_status(invocate,time)
      self.records.functions_status[invocate["HashFunction"]] = function
    # 取出对应的函数实例条目
    function = self.records.functions_status[invocate["HashFunction"]]
    # 无论是否已经存在都要,修改function的ArrivalTime信息
    function.ArrivalTime = time

    # 查询该函数对应app是否已经存在
    if self.records.apps_status.get(invocate['HashApp']) is None:
      # 该app不存在，创建新条目
      AverageAllocatedMb = self.dataset.app_data[invocate['HashApp']]['AverageAllocatedMb']
      # 创建app实例
      app = records.app_status(invocate,time,AverageAllocatedMb)
      # 添加到apps_status中
      self.records.apps_status[invocate['HashApp']] = app
    # 取出app条目
    app = self.records.apps_status[invocate['HashApp']]

    # 判断该app是否已经分配节点
    if app.ComputeNodeId == -1:
      # 检查是否在重载队列中
      # 获取所有复合条件的重载应用
      reload_apps = [row.HashApp for row in self.records.reload_queue.itertuples() if row.HashApp == invocate['HashApp']]
      # 从队列中删除
      self.records.reload_queue[~self.records.reload_queue['HashApp'].isin(reload_apps)]
      # 未分配节点,分配节点 
      node_id =self.distribute_app(app,time)
      # 修改节点的ArrivalTime信息
      app = self.records.apps_status[invocate['HashApp']]
      app.ArrivalTime = time
      app.ComputeNodeId = node_id
      # 增加冷启动次数
      app.ColdStartCount += 1
      self.records.coldStartCount += 1
    else:
      # 已分配节点,找到对应节点
      node_id = self.records.apps_status[invocate['HashApp']].ComputeNodeId
    # 将function加入节点中
    self.compute_nodes[node_id].load_function(function,time)
    # 增加调用次数
    self.records.apps_status[invocate['HashApp']].InvocateCount += 1
    self.records.invocateCount += 1
    
    
  # 释放函数
  def functions_release(self,time):
    # 每个节点都进行释放
    for i in range(len(self.compute_nodes)):
      self.compute_nodes[i].release_function(time)

  # 重载函数
  def reload_apps(self, time):
    if len(self.records.reload_queue) == 0:
      return
    # 获取所有复合条件的重载应用
    reload_apps = [row.HashApp for row in self.records.reload_queue.itertuples() if row.priority <= time]
    # 从队列中删除
    self.records.reload_queue[~self.records.reload_queue['HashApp'].isin(reload_apps)]
    # 分配与装载节点
    for HashApp in reload_apps:
      app = self.records.apps_status[HashApp]
      node_id = self.distribute_app(app, time)
      app.ArrivalTime = time
      app.ComputeNodeId = node_id
      app.Preload = True
      self.compute_nodes[node_id].load_app(HashApp)


      
          
            
      


