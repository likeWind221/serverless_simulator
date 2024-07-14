# 数据集加载与处理
import sys
import pandas as pd
import os

# 定义数据集类
class Dataset:
  def __init__(self,day_index=1):
    # 当前工作目录
    self.current_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    # 数据集目录
    self.data_dir = os.path.join(self.current_dir, 'data')
    # 结果目录
    self.result_dir = os.path.join(self.current_dir,'result')
    # 设定天数索引
    self.day_index = day_index

    # 初始化表格数据
    self.app_data = {}
    self.function_data = pd.DataFrame()

  # 加载数据集
  def load_data(self,mode='default'):

    if mode == 'default':
      # 读取应用内存数据集、读取函数调取数据集、读取函数执行时间数据集
      df_memory = pd.read_csv(os.path.join(self.data_dir, f'app_memory_percentiles.anon.d{self.day_index:02d}.csv'))
      df_memory = df_memory.drop(columns=df_memory.columns[0])
      df_duration = pd.read_csv(os.path.join(self.data_dir, f'function_durations_percentiles.anon.d{self.day_index:02d}.csv'))
      df_invocations = pd.read_csv(os.path.join(self.data_dir, f'invocations_per_function_md.anon.d{self.day_index:02d}.csv'))
      # 去重 清洗 数据集
      # df_memory去重,清洗
      df_memory = df_memory.drop_duplicates(subset=['HashApp'])
      df_memory = df_memory[["HashApp","SampleCount","AverageAllocatedMb"]]
      
      # df_duration去重,清洗
      df_duration = df_duration.drop_duplicates(subset=['HashFunction'])
      df_duration = df_duration[["HashApp","HashFunction","Count", "Average", "percentile_Average_1","percentile_Average_99"]]

      # df_invocations去重,清洗
      df_invocations = df_invocations.drop_duplicates(subset=['HashFunction'])
      df_invocations = df_invocations.drop(columns=['HashOwner'])

      # app_invocation合并df_invocations与df_duration
      df_functions = pd.merge(df_duration, df_invocations, on=["HashApp","HashFunction"])
      df_functions = pd.merge(df_functions, df_memory,on="HashApp")

      # 进一步筛选df_functions
      df_functions['invocation_sum'] = df_functions[[str(i) for i in range(1,1441)]].sum(axis=1)
      self.function_data = df_functions[df_functions['invocation_sum']<=300]  

      # 保存数据集
      df_memory.to_csv(os.path.join(self.data_dir,'df_memory.csv'),index=False)
      df_functions.to_csv(os.path.join(self.data_dir,'df_functions.csv'),index=False)
      # 保存至类变量
      df_memory.set_index('HashApp',inplace=True)
      self.app_data = df_memory.to_dict(orient='index')

      
    elif mode == 'fast':
      if os.path.exists(os.path.join(self.data_dir,'df_memory.csv')) and os.path.exists(os.path.join(self.data_dir,'df_functions.csv')):
        self.app_data = pd.read_csv(os.path.join(self.data_dir,'df_memory.csv'))
        self.function_data = pd.read_csv(os.path.join(self.data_dir,'df_functions.csv'))
      else:
        print("保存数据集不存在,需要重新加载")
        self.load_data(mode='default')








  