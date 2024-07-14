import numpy as np
import pmdarima as pm

# 控制器模式：固定时间keepAlive，直方图单独处理，直方图混合模式
mode = ['fixed_keepalive', 'hybrid_histogram','arima_join']

# 控制器类
class Controller:
  def __init__(self,mode_select,records,fixed_keepalive_time=10,prewarm_percent=5,keepalive_percent=99):
    # 初始化参数
    self.mode = mode[mode_select] # 模式选择
    self.prewarm_percent = prewarm_percent/100 # 预热时间百分比
    self.keepalive_percent = keepalive_percent/100 # 保持活跃时间百分比

    # 模式1-config
    self.fixed_keepalive_time = fixed_keepalive_time # 固定时间keepAlive，单位分钟
  
    # 模式2-config
    self.histogram_range = 240 # 直方图记录范围，30分钟,论文中是240分钟
    self.CV_threshold = 2 # 直方图CV阈值,超过阈值代表直方图有效

    # 模式3-config,在模式2基础上增加arima模型
    self.OOB_threshold = 3 # 越界次数阈值，超过阈值要采用时间序列分析
    self.history_max_length = 10 # 历史记录最大长度
    
    # 记录类
    self.records = records
  
  # 判断是否越界
  def judge_out_bounds(self,app):
    OOB_times = app.histogram.OOB_times
    return OOB_times>self.OOB_threshold
  
  # 时间序列分析
  def set_window_by_arima(self,app):
    history = app.histogram.history

    # 检查数据是否恒定
    if all(x == history[0] for x in history) and len(history) > 1:
      self.set_window_by_FixedKeepAlive(app)
      return

    # 这里用arima分析时间序列
    arima = pm.auto_arima(history)
    # 找出下一个预测值
    next_idle_time = arima.predict(1)
    # 计算pre_warm_window和keep_alive_window
    pre_warm_window, keep_alive_window = next_idle_time * 0.85, next_idle_time * 0.15 * 2
    app.PreWarmWindow = pre_warm_window
    app.KeepAliveWindow = keep_alive_window

  # 判断直方图有效性
  def judge_histogram(self,app):
    # 找到对应的分布
    distribution = app.histogram.distribution
    # 计算总和，总数
    sum = 0
    num = 0
    for i in range(len(distribution)):
      if distribution[i]!=0:
        num += distribution[i]
        sum += distribution[i]*i
    # 计算均值
    if num==0:
      return False
    mean = sum/num
    if mean<1e-6:
      return False
    # 计算平方和
    square_sum = 0
    for i in range(len(distribution)):
      if distribution[i]!=0:
        square_sum += (i-mean)**2*distribution[i]
    # 计算标准差
    std = np.sqrt(square_sum/num)
    # 计算CV
    CV = std/mean
    app.histogram.num = num
    # 判断是否有效,需要有足够的样本数
    return CV>self.CV_threshold

    
  # 根据直方图设定窗口大小
  def set_window_by_distribution(self,app):
    # 找到对应的分布
    distribution = app.histogram.distribution
    num = app.histogram.num
    if num<3:
      # 样本数不足，采用固定时间keepAlive
      self.set_window_by_FixedKeepAlive(app)
      return
    # 计算百分位点
    pre_warm_perc = round(num*self.prewarm_percent)
    keep_alive_perc = round(num*self.keepalive_percent)
    # 计算pre_warm_window
    low = 0
    for i in range(len(distribution)):
      if distribution[i]!=0:
        low += distribution[i]
        if low>=pre_warm_perc:
          PreWarmWindow = i
          break
    # 计算keep_alive_window
    high = num
    KeepAliveWindow = 240
    for i in range(len(distribution)-1,0,-1):
      if distribution[i]!=0:
        high -= distribution[i]
        if high<=keep_alive_perc:
          KeepAliveWindow = i + 1
          break
    if PreWarmWindow < 8:
      PreWarmWindow = 0
    app.PreWarmWindow = PreWarmWindow
    app.KeepAliveWindow = round(1.15*(KeepAliveWindow-PreWarmWindow) )

  # 更新直方图状态
  def update_histogram(self,function,time):
    # 找到对应的app项的直方图类
    histogram = self.records.apps_status[function.HashApp].histogram
    # 直方图分布是否存在
    if histogram.distribution is None:
      # 直方图不存在，则初始化
      histogram.distribution = np.zeros(self.histogram_range)
    # 计算idle_time
    idle_time = time - function.ReleaseTime
    # 如果idle_time超出范围
    if idle_time>=self.histogram_range:
      histogram.OOB_times += 1
    else:
      # 更新直方图分布信息
      histogram.distribution[idle_time] += 1
    # 更新history列表
    histogram.history.append(idle_time)
    if(len(histogram.history)>self.history_max_length):
      histogram.history.pop(0)
    return


  def set_window_by_FixedKeepAlive(self,app):
    # app为app_status的某一项
    app.PreWarmWindow = 0
    app.KeepAliveWindow = 10

  # 设置窗口大小总入口,针对某一app项
  def set_window(self,app):
    # 判断模式
    if self.mode == 'fixed_keepalive':
      # 固定时间keepAlive
      self.set_window_by_FixedKeepAlive(app)
    elif self.mode == 'hybrid_histogram':
      # 单直方图模式
      # 判断分布是否存在，用于第一次的判断
      if app.histogram.distribution is None:
        # 直方图不存在，直接采用标准分析
        self.set_window_by_FixedKeepAlive(app)
        return
      if self.judge_histogram(app):
        # 直方图有效，采用直方图分析
        self.set_window_by_distribution(app)
      else:
        # 直方图无效，采用标准分析
        self.set_window_by_FixedKeepAlive(app)
    else:
      # 混合模式,加入时间序列分析
      # 判断分布是否存在，用于第一次的判断
      if app.histogram.distribution is None:
        # 直方图不存在，直接采用标准分析
        self.set_window_by_FixedKeepAlive(app)
        return
      # 判断直方图越界性
      if self.judge_out_bounds(app):
        # 直方图越界，则采用arima分析
        # self.set_window_by_arima(app)
        self.set_window_by_FixedKeepAlive(app)
      elif self.judge_histogram(app):
        # 直方图有效，采用直方图分析
        self.set_window_by_distribution(app)
      else:
        # 直方图无效，采用标准分析
        self.set_window_by_FixedKeepAlive(app)


  




