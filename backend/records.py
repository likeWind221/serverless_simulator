import pandas as pd

class app_status:
  def __init__(self, invocate, time, AverageAllocatedMb):
    self.HashApp = invocate['HashApp']
    self.AverageAllocatedMb = AverageAllocatedMb
    self.ColdStartCount = 0
    self.InvocateCount = 0
    self.MemWasteTime = 0
    self.ComputeNodeId = -1
    self.PreWarmWindow = 0
    self.KeepAliveWindow = 10
    self.ArrivalTime = time
    self.ReleaseTime = -1
    self.Preload = False
    self.histogram = histogram()

  def to_dict(self):
    return {
      "HashApp": self.HashApp,
      "AverageAllocatedMb": self.AverageAllocatedMb,
      "ColdStartCount": self.ColdStartCount,
      "InvocateCount": self.InvocateCount,
      "MemWasteTime": self.MemWasteTime,
      "ComputeNodeId": self.ComputeNodeId,
      "PreWarmWindow": self.PreWarmWindow,
      "KeepAliveWindow": self.KeepAliveWindow,
    }

class function_status:
  def __init__(self, invocate, time):
    self.HashApp = invocate['HashApp']
    self.HashFunction = invocate['HashFunction']
    self.Average = invocate['Average']
    self.ExecuteDuration = 0
    self.ComputeNodeId = -1
    self.ArrivalTime = time
    self.ReleaseTime = -1

  def get(self):
    # 获取优先级最小的hash_app和优先级值
    if self._queue:
      priority, app = self._queue[0]
      return priority, app.HashApp
    else:
      return None, None
    
  def empty(self):
    return len(self._queue) == 0

# 直方图，及其他数据
class histogram:
  def __init__(self):
    self.distribution = None # 直方图分布情况
    self.OOB_times = 0 # 越界次数
    self.history = list() # 历史数据
    self.num = 0 # 直方图有效数据个数

class Records:
  def __init__(self):
    # 记录应用状态：应用hash、冷启动次数、函数调用次数、内存溢出时间、节点id、预热窗口、保持窗口、到达时间、释放时间
    self.apps_status = {}
    # 记录函数调用情况：函数hash、应用hash、执行时间、节点id、最后使用时间
    self.functions_status = {}
    # 重载队列
    self.reload_queue = pd.DataFrame(columns=['Priority','HashApp'])

    # 其他参数
    self.coldStartCount = 0 # 冷启动次数
    self.invocateCount = 0 # 调用次数
    self.memWasteTime = 0 # 内存浪费
    self.model_run_time = 0 # 模型运行实际时间
    self.used_mem = 0 # 已用内存

  # 清空数据
  def clear(self):
    self.apps_status.clear()
    self.functions_status.clear()
    self.coldStartCount = 0
    self.invocateCount = 0
    self.model_run_time = 0

  # 统计调用状态
  def count_status(self):
    for app in self.apps_status.values():
      self.coldStartCount += app.ColdStartCount
      self.invocateCount += app.InvocateCount

  # 转换字典，方便存json

  def to_dict(self):
    sorted_apps_status = dict(sorted(self.apps_status.items(), key=lambda item: item[1].ColdStartCount))
    # 打印排序后的结果
    return {str(index): v.to_dict() for index, (k, v) in enumerate(sorted_apps_status.items())}

  
  # 计算不算首次启动的冷启动次数
  def without_first_invocate(self):
    return self.coldStartCount - len(self.apps_status)

