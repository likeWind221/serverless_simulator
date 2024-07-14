# 计算节点类
import pandas as pd
import random

class ComputeNode:
  def __init__(self, id, records, Controller):
    self.id = id # 计算节点id
    self.used_mem = 0 # 计算节点已用内存
    self.total_mem = 4096 * 1024 # 计算节点总内存,设置为4T,测试用，管够
    self.avail_mem = self.total_mem - self.used_mem # 计算节点可用内存
    self.records = records # 获取全局的记录表
    # 存储apps_status的哈希值
    self.apps_store = set()
    # 存储函数实例与app的对应关系
    self.functions_store = {}
    # 控制器
    self.controller = Controller

  # 加载应用实例到计算节点
  def load_app(self, HashApp):
    # 装载app实例
    self.apps_store.add(HashApp)
    # 新增functions_store字典值
    self.functions_store[HashApp] = set()
    # 重新计算内存使用情况
    self.used_mem += self.records.apps_status[HashApp].AverageAllocatedMb
    self.avail_mem = self.total_mem - self.used_mem
    self.records.used_mem += self.records.apps_status[HashApp].AverageAllocatedMb
    # 修改记录中的节点分配情况
    self.records.apps_status[HashApp].ComputeNodeId = self.id
    # 设定窗口
    self.controller.set_window(self.records.apps_status[HashApp])
      
  # 卸载应用实例
  def unload_app(self, HashApp, time):
    self.apps_store.remove(HashApp)
    self.used_mem -= self.records.apps_status[HashApp].AverageAllocatedMb
    self.avail_mem = self.total_mem - self.used_mem
    self.records.used_mem -= self.records.apps_status[HashApp].AverageAllocatedMb
    # 修改记录中的节点分配情况
    self.records.apps_status[HashApp].ComputeNodeId = -1
    self.records.apps_status[HashApp].ReleaseTime = time
    self.records.apps_status[HashApp].Preload = False
    # 卸载关于该app的所有函数实例
    functions_set = self.functions_store.get(HashApp, set())
    if len(functions_set) == 0:
      return
    for function in functions_set:
      self.records.functions_status[function.HashFunction].ReleaseTime = time
      self.records.functions_status[function.HashFunction].ComputeNodeId = -1
      self.functions_store[HashApp].remove(function)

  # 加入重载列表 
  def add_reload(self, app):
    # 计算优先级
    priority = app.ReleaseTime + app.PreWarmWindow
    # 创建df
    reload_df = pd.DataFrame({
      'Priority': [priority],
      'HashApp': [app.HashApp],
    })
    # 根据优先级，加入到列表中，最小堆
    pd.concat([self.records.reload_queue, reload_df],ignore_index=True)
    
  # 强制释放应用
  def force_unload_app(self,time):
    # 将set转为list
    apps_list = list(self.apps_store)
    # 随机抽取应用
    if not apps_list:
      return
    HashApp = random.choice(apps_list)
    # 卸载应用
    self.unload_app(HashApp,time)
    # 加入重载队列
    self.add_reload(self.records.apps_status[HashApp])

  # 添加调用
  def load_function(self,function,time):
    # 如果函数对应的app还未装载
    if function.HashApp not in  self.apps_store:
      # 装载app
      self.load_app(function.HashApp)
    # 如果app处于预加载状态，由于有函数实例运行了，预加载状态解除
    if self.records.apps_status[function.HashApp].Preload == True:
      self.records.apps_status[function.HashApp].Preload = False
    # 判断函数实例是否已经存在
    function_set = self.functions_store.get(function.HashApp, set())

    # 更新直方图信息
    self.controller.update_histogram(function,time)
    if function.HashFunction in [f.HashFunction for f in function_set]:
      # 已经存在，重置时间
      self.records.functions_status[function.HashFunction].ReleaseTime = time
    else:
      # 不存在，则添加
      self.functions_store[function.HashApp].add(function)
      # 修改记录中的节点分配情况
      self.records.functions_status[function.HashFunction].ComputeNodeId = self.id
    # 重置函数的执行状态
    self.records.functions_status[function.HashFunction].ExecuteDuration = 0

  # 释放某个函数实例
  def unload_function(self,HashFunction,time):
    # 释放函数实例
    self.records.functions_status[HashFunction].ReleaseTime = time
    self.records.functions_status[HashFunction].ComputeNodeId = -1

  def release_function(self,time):
    # 过期应用列表
    out_time_apps = list()
    # 正常卸载列表
    normal_unload_apps = list()
    # 遍历所有app，排除其中已经执行完毕的函数，并更新执行时间
    for HashApp in self.apps_store:
      # 更新预加载信息，查看是否过期
      app = self.records.apps_status[HashApp]
      idle_time = app.ReleaseTime + app.PreWarmWindow + app.KeepAliveWindow
      if idle_time < time and app.Preload == True:
        # 过期,直接释放app
        out_time_apps.append(HashApp)
        continue
      # 判断是否是预加载的
      # 如果不是
      if app.Preload == False:
        # 遍历该app的所有函数
        functions_set = self.functions_store.get(HashApp, set())
        function_to_release = list()
        for function in functions_set:
          function.ExecuteDuration += 60000 # 1分钟
          # 移除执行完毕的函数实例
          if function.ExecuteDuration >= function.Average:
            function_to_release.append(function)
        # 释放执行完毕的函数实例
        for function in function_to_release:
          self.unload_function(function.HashFunction,time)
          functions_set.remove(function)
        # 检查是否所有函数实例都执行完毕
        if len(functions_set) == 0:
          # 如果预热窗口为0，则不释放app，将app直接预加载
          if app.PreWarmWindow == 0:
            app.Preload = True
            app.ReleaseTime = time
            # 相当于马上重载，重载也需要设置窗口
            self.controller.set_window(app)
          else:
            normal_unload_apps.append(HashApp)
      else:
        # 如果是预加载的，计算内存浪费时间
        app.MemWasteTime += 1
        self.records.memWasteTime += 1
    # 释放过期app
    for HashApp in out_time_apps:
      self.unload_app(HashApp,time)
    # 正常释放app
    for HashApp in normal_unload_apps:
      self.unload_app(HashApp,time)
      self.add_reload(self.records.apps_status[HashApp])
          

        

    



      

    
