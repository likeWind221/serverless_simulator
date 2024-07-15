<template>
  <div class="main-container">
    <div class="records-container">
      <div class="title">结果列表</div>
      <div class="records-list" v-loading="loading">
        <div shadow="hover" class="record-card" v-for="(item, index) in resultList">
          <div class="item-title">记录-{{ index + 1 }}</div>
          <div class="item" v-for="(child_item, index) in item.data">
            <span class="label">{{ listLabel[index] ? listLabel[index] : index }}:</span>
            <span class="content">{{ child_item }}</span>
          </div>
          <div class="btn-group">
            <el-button type="primary" size="small" v-if="!choseStatusMulti[index]"
              @click="addMultiChart(item, index)">加入对比分析</el-button>
            <el-button type="warning" size="small" v-else @click="removeMultiChart(index)">取消对比选择</el-button>
            <el-button type="default" size="small" v-if="!choseStatusSingle[index]"
              @click="showSingleChart(item, index)" :disabled="enableSingle">单独分析</el-button>
            <el-button type="info" size="small" v-else @click="cancelSingleChart(item, index)">取消分析</el-button>
            <el-button type="danger" size="small" :disabled="!enableDel[index]"
              @click="removeRecord(item)">删除</el-button>
          </div>
        </div>
        <el-empty description="暂时没有数据" class="empty-container" v-if="isData" />
      </div>
    </div>
    <div class="analysis-container">
      <div class="multi-chart" v-if="multi_chart_data.length > 0">
        <div class="chart-title">
          <el-tabs v-model="activeName" class="tabs">
            <el-tab-pane label="冷启动占比" name="first"></el-tab-pane>
            <el-tab-pane label="内存浪费时间" name="second"></el-tab-pane>
          </el-tabs>
        </div>
        <BarChart :data="multi_chart_data" :type="activeName"></BarChart>
      </div>
      <el-empty v-else description="请选择对比记录" class="empty-container" />
      <div></div>
      <div v-if="single_chart_data.length > 0" class="single-chart">
        <LineChart :data="single_chart_data"></LineChart>
      </div>
      <el-empty v-else description="请选择单独分析记录" class="empty-container" :v-loading="loading_chart" />
    </div>
  </div>
</template>

<script lang='ts' setup>
import { getResult, getAppStatus, deleteResult } from '@/api/result';
import BarChart from '@/components/BarChart.vue';
import LineChart from '@/components/LineChart.vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import 'element-plus/theme-chalk/el-message.css';
import 'element-plus/theme-chalk/el-message-box.css';
import { en } from 'element-plus/es/locales.mjs';

const activeName = ref('first')
const isData = ref(true)
const loading = ref(false)
const loading_chart = ref(false)
const resultList = ref<any[]>([])
const choseStatusMulti = ref<any[]>([])
const choseStatusSingle = ref<any[]>([])
const enableSingle = ref(false)
const enableDel = ref<any[]>([])
const listLabel: any = {
  'mode': '模式',
  'time': '日期',
  'fixed_keepalive_time': '保活基准时长',
  'prewarm_percent': '预热窗口百分位',
  'keepalive_percent': '保活窗口百分位',
  'coldStartCount': '冷启动次数',
  'invocateCount': '总调用次数',
  'model_run_time': '模型运行时间(秒)',
  'without_first': '冷启动次数(不计首次)',
  'memWasteTime': '内存浪费总时间(分钟)',
}

const fetchList = async () => {
  loading.value = true
  const result: any = await getResult()
  console.log(result)
  loading.value = false
  if (result.data.length === 0) {
    isData.value = true
    resultList.value = []
    return
  }
  if (result.data.length > 0) {
    isData.value = false
    resultList.value = result.data
    console.log(resultList.value)
    choseStatusMulti.value = resultList.value.map(() => false)
    choseStatusSingle.value = resultList.value.map(() => false)
    enableDel.value = resultList.value.map(() => true)
    console.log(choseStatusMulti.value)
  }
}

const single_chart_data = ref<any[]>([])
const multi_chart_data = ref<any[]>([])

// 加入对比分析
const addMultiChart = (item: any, index: number) => {
  enableDel.value[index] = false
  choseStatusMulti.value[index] = true
  const chart_data = {
    index: index,
    value: (item.data.without_first / item.data.invocateCount * 100).toFixed(2),
    name: '记录' + (index + 1),
    memWaste: item.data.memWasteTime
  }
  multi_chart_data.value.push(chart_data)
}
// 删除对比分析
const removeMultiChart = (index: number) => {
  choseStatusMulti.value[index] = false
  if (choseStatusMulti.value[index] === false && choseStatusSingle.value[index] === false) {
    enableDel.value[index] = true
  }
  multi_chart_data.value.forEach((item, i, arr) => {
    if (item.index === index) {
      arr.splice(i, 1)
    }
  })
}
// 单独分析
const showSingleChart = async (item: any, index: number) => {
  loading_chart.value = true
  enableDel.value[index] = false
  choseStatusSingle.value[index] = true
  const data = {
    name: item.name
  }
  const result: any = await getAppStatus(data)
  // 将 result 转换为数组
  const resultArray = Object.values(result)
  if (resultArray.length === 0) {
    ElMessage.error('该记录没有数据')
    choseStatusSingle.value[index] = false
    return
  }
  // 计算百分位点
  const percentile = [0.01, 0.25, 0.5, 0.75, 0.99]
  const percentileData = percentile.map(item => {
    const index = Math.floor(item * resultArray.length)
    return resultArray[index]
  })
  // 取出数据
  single_chart_data.value = percentileData.map((item: any, index: number) => {
    return {
      percentile: percentile[index],
      value: item.ColdStartCount - 1,
    }
  })
  loading_chart.value = false
  enableSingle.value = true
}
const cancelSingleChart = (item: any, index: number) => {
  choseStatusSingle.value[index] = false
  single_chart_data.value = []
  if (choseStatusMulti.value[index] === false && choseStatusSingle.value[index] === false) {
    enableDel.value[index] = true
  }
  enableSingle.value = false
}
// 删除记录
const removeRecord = async (item: any) => {
  ElMessageBox.confirm('确认删除该记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
  }).then(async () => {
    const data = {
      name: item.name
    }
    const result: any = await deleteResult(data)
    ElMessage.success('删除成功')
    await fetchList()
    multi_chart_data.value = []
    single_chart_data.value = []
    enableSingle.value = false
  }).catch(() => {
    ElMessage.info('删除取消')
    console.log('cancel')
  })
}


onMounted(() => {
  fetchList()
})

onUnmounted(() => {

});
</script>

<style lang='scss' scoped>
.main-container {
  display: flex;
  flex-direction: column;
}

.records-container {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  background-color: white;
  padding: 24px;
  border-radius: 4px;
  min-width: 900px;

  .title {
    color: var(--color-text);
    font-weight: bold;
  }
}

.records-list {
  display: flex;
  overflow-x: auto;
  align-items: center;
  margin-top: 12px;
  padding: 10px;

  .record-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    min-width: 300px;
    height: 340px;
    border: 1px solid var(--color-border);
    border-radius: 4px;
    margin-right: 12px;
    transition: all 0.3s ease-in-out;

    .item-title {
      font-size: var(--font-size-rank-1);
      color: var(--color-text);
      font-weight: bold;
    }

    .item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
      font-size: var(--font-size-rank-2);
      color: var(--color-text);

      .label {
        font-weight: 600;
      }

      .content {
        font-weight: normal;
      }
    }

    .btn-group {
      width: 100%;
      display: flex;
      justify-content: flex-end;
      align-items: center;
    }
  }

  .record-card:hover {
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    scale: 1.05;
  }


  .record-card:last-child {
    margin-right: 0;
  }

  .empty-container {
    width: 100%;
    height: 300px;
  }
}

.analysis-container {
  display: grid;
  grid-template-columns: 1fr 20px 400px;
  height: 400px;
  margin-top: 20px;
  margin-bottom: 12px;


  .multi-chart {
    display: grid;
    grid-template-rows: 40px 1fr;
    background-color: white;
    border-radius: 4px;
    padding-top: 20px;
    padding-left: 20px;
    padding-right: 20px;
  }

  .single-chart {
    background-color: white;
    border-radius: 4px;
  }

  .empty-container {
    background-color: white;
    border-radius: 4px;
  }
}

p {
  color: var(--color-text)
}
</style>