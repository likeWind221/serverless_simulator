<template>
  <div clas="main-container">
    <div class="params-container">
      <span class="title">选择模拟器调度参数</span>
      <el-form :model="form" class="form-container" label-position="left" label-width="180px" ref="ruleFormRef"
        :rules="rules">
        <el-form-item label="数据集天数">
          <el-select v-model="form.dateTime" placeholder="请选择某一天的数据集" style="width: 320px">
            <el-option v-for="item in options" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="一天运行时间(分钟)">
          <el-input-number v-model="form.totalTime" :min="1" :max="1440" :step="1"
            value-on-clear="max"></el-input-number>
        </el-form-item>
        <el-form-item label="运行模式">
          <el-select v-model="form.mode" placeholder="Select" style="width: 320px">
            <el-option v-for="(item, index) in modeList" :key="index" :label="item" :value="index" />
          </el-select>
        </el-form-item>
        <el-form-item label="保活窗口基准大小(分钟)">
          <el-input-number v-model="form.keepAliveWindow" :min="0" :max="1440" :step="1"
            :value-on-clear="10"></el-input-number>
        </el-form-item>
        <el-form-item label="直方图预热窗口百分位(%)" prop="perwarm_percent">
          <el-input-number v-model="form.perwarm_percent" :min="0" :max="100" :step="1" :value-on-clear="5"
            :disabled="!setable"></el-input-number>
        </el-form-item>
        <el-form-item label="直方图保活窗口百分位(%)" prop="keepalive_percent">
          <el-input-number v-model="form.keepalive_percent" :min="0" :max="100" :step="1" :value-on-clear="99"
            :disabled="!setable"></el-input-number>
        </el-form-item>
      </el-form>
      <div class="btn-container">
        <el-button type="primary" @click="submit" :disabled="is_btn_disabled"
          :loading="run_btn_loading">运行模型</el-button>
        <el-button type="danger" @click="stop" :loading="stop_btn_loading" :disabled="!is_btn_disabled">停止</el-button>
        <el-button type="default" @click="reset" :loading="reset_btn_loading">重置</el-button>
      </div>
    </div>

    <div class="console-container">
      <div class="terminal-container">
        <div class="console-header">Terminal Print</div>
        <div class="console-body" ref="consoleBody" v-html="log_data">
        </div>
      </div>
      <div></div>
      <div class="progress">
        <Progress :value="progress"></Progress>
      </div>
      <div></div>
      <div class="panel-container">
        <el-descriptions title="数据跟踪" :column="1" border style="width: 100%;">
          <el-descriptions-item label="当前数据集">
            {{ date_select ? date_select : '数据集未选择' }}
          </el-descriptions-item>
          <el-descriptions-item label="当前运行模式">
            {{ mode_select ? mode_select : '运行模式未选择' }}
          </el-descriptions-item>
          <el-descriptions-item label="冷启动次数">
            {{ panel_data.coldStartTimes }}
          </el-descriptions-item>
          <el-descriptions-item label="调用次数">
            {{ panel_data.invocateTimes }}
          </el-descriptions-item>
          <el-descriptions-item label="内存浪费时间">
            {{ panel_data.memWasteTime }}
          </el-descriptions-item>
          <el-descriptions-item label="总内存大小">
            {{ total_mem_size }}
          </el-descriptions-item>
          <el-descriptions-item label="总内存使用">
            {{ total_mem_used }}
          </el-descriptions-item>
        </el-descriptions>
        <el-progress :percentage="mem_usage[0]" type="dashboard">
          <template #default="{ percentage }" color="var(--theme-color-primary)">
            <span class="percentage-value">{{ percentage }}%</span>
            <span class="percentage-label">总内存使用比例</span>
          </template>
        </el-progress>
      </div>

    </div>
  </div>
</template>

<script lang='ts' setup>
import { computed, onMounted, reactive, ref } from 'vue';
import Progress from '@/components/progress.vue'
import { execute_model, get_model_status, stop_model } from '@/api/dashboard';
import { ElMessage } from 'element-plus';
import 'element-plus/theme-chalk/el-message.css';
import type { FormInstance, FormRules } from 'element-plus'
import { useModel } from '@/stores/counter';

const useModelStore = useModel()
const ruleFormRef = ref<FormInstance>()
const modeList = ref(['Fixed-KeepAlive模式', '单直方图模式', '时间序列结合模式'])
const is_btn_disabled = ref(false)
const run_btn_loading = ref(false)
const stop_btn_loading = ref(false)
const reset_btn_loading = ref(false)
const date_select = ref('')
const mode_select = ref('')
const log_data = ref<string>()
const progress = ref(0)
const consoleBody = ref<InstanceType<typeof HTMLDivElement> | null>(null)

const setable = computed(() => {
  if (form.mode === 0) {
    form.perwarm_percent = 5
    form.keepalive_percent = 99
    return false
  } else {
    return true
  }
})

const options = ref<any>([])
for (let i = 1; i <= 14; i++) {
  options.value.push({
    label: `第${i}天`,
    value: i
  })
}

// 计算节点内存统计，目前只支持1个节点
const compute_node = ref<any[]>([{
  id: 1,
  total_mem: 4096 * 1024,
  used_mem: 0,
}])

// 仪表盘数据
const panel_data = reactive({
  coldStartTimes: 0,
  invocateTimes: 0,
  memWasteTime: 0,
  used_mem: 0,
})

// 计算内存比例
const total_mem_size = ref('')
const total_mem_used = ref('')
const mem_usage = computed(() => {
  let mem_usage_list = [0]
  let total_mem = 0
  let total_used_mem = 0
  compute_node.value.forEach(item => {
    total_mem += item.total_mem
    total_used_mem += item.used_mem
    mem_usage_list.push(item.used_mem / item.total_mem * 100)
  })
  mem_usage_list[0] = Math.round(total_used_mem / total_mem * 100)

  if (total_mem > 1024) {
    total_mem = total_mem / 1024
    total_mem_size.value = `${total_mem.toFixed(2)}GB`
  } else {
    total_mem_size.value = `${total_mem}MB`
  }
  if (total_used_mem > 1024) {
    total_used_mem = total_used_mem / 1024
    total_mem_used.value = `${total_used_mem.toFixed(2)}GB`
  } else {
    total_mem_used.value = `${total_used_mem}MB`
  }
  return mem_usage_list
})

const form = reactive({
  // 数据集天数
  dateTime: 1,
  // 模拟器运行总时间，分钟计数
  totalTime: 1440,
  // 运行模式
  mode: 0,
  // fixed-keep-alive参数
  keepAliveWindow: 10,
  // 直方图预热窗口百分位
  perwarm_percent: 5,
  // 直方图保活窗口百分位
  keepalive_percent: 99
})

const submit = async () => {
  ruleFormRef.value?.validate(async (valid: boolean) => {
    if (valid) {
      // 重置状态信息
      useModelStore.run()
      mode_select.value = modeList.value[form.mode]
      date_select.value = `第${form.dateTime}天`
      ElMessage.success('模拟器开始运行')
      log_data.value = ''
      panel_data.coldStartTimes = 0
      panel_data.invocateTimes = 0
      panel_data.memWasteTime = 0
      const params: any = {
        dateTime: form.dateTime,
        totalTime: form.totalTime,
        mode: form.mode,
        keepAliveWindow: form.keepAliveWindow,
        prewarm_percent: form.perwarm_percent,
        keepalive_percent: form.keepalive_percent
      }
      const res = await execute_model(params)
      is_btn_disabled.value = true
      run_btn_loading.value = !run_btn_loading.value
      //轮询 创建定时器
      const timer = window.setInterval(() => {
        setTimeout(async () => {
          const res: any = await get_model_status() //调用接口的方法
          const data = res.data //获取接口返回的数据
          // type 0的数据必然在数组第一个
          if (data.length > 0) {
            if (data[0].type === 0) {
              log_data.value += '<h1>' + data[0].message + '<h1>'
            } else {
              data.forEach((item: any, index: number) => {
                if (item.type === 1) {
                  log_data.value += '<h1>迭代至第' + item.minutes + '分钟<h1>'
                  panel_data.coldStartTimes = item.coldStartTimes
                  panel_data.invocateTimes = item.invocateTimes
                  panel_data.memWasteTime = item.memWasteTime
                  compute_node.value[0].used_mem = item.used_mem
                }
                if (index === data.length - 1) {
                  progress.value = item.progress
                }
              })
            }
            // type 2的数据必然是最后一个,关闭计时器
            if (data[data.length - 1].type === 2) {
              clearInterval(timer)
              log_data.value += '<h1>冷启动次数：' + data[data.length - 1].coldStartTimes + '<h1>'
              log_data.value += '<h1>不算首次启动的冷启动次数：' + data[data.length - 1].without_first + '<h1>'
              log_data.value += '<h1>调用次数：' + data[data.length - 1].invocateTimes + '<h1>'
              log_data.value += '<h1>模拟器运行时间：' + data[data.length - 1].actualRunTime + '<h1>'
              log_data.value += '<h1>模拟器运行结束<h1>'
              log_data.value += '<h1>模型结果已保存<h1>'
              is_btn_disabled.value = false
              run_btn_loading.value = !run_btn_loading.value
              stop_btn_loading.value = false
              reset_btn_loading.value = false
              useModelStore.stop()
              ElMessage.success('模拟器运行结束')
              // 在定时器结束后再进行一次滚动条滚动
              setTimeout(() => {
                consoleBody.value?.scrollTo({
                  top: consoleBody.value.scrollHeight,
                  behavior: 'smooth'
                });
              }, 0);
            }
            consoleBody.value?.scrollTo({
              top: consoleBody.value.scrollHeight,
              behavior: 'smooth'
            })
          }
        }, 0)
      }, 1000);
    } else {
      ElMessage.error('请检查输入参数')
      return
    }
  })

}

const stop = async () => {
  stop_btn_loading.value = true
  const res = await stop_model()
  ElMessage.info('停止中...')
}

// 重置参数
const reset = async () => {
  form.dateTime = 1
  form.totalTime = 1440
  form.mode = 0
  form.keepAliveWindow = 10
  form.perwarm_percent = 5
  form.keepalive_percent = 99
  ruleFormRef.value?.resetFields()
  ElMessage.success('参数已重置')
}

// 表单验证
const rules = reactive<FormRules<typeof form>>({
  totalTime: [{ required: true, message: '请输入运行总时间', trigger: 'blur' }],
  perwarm_percent: [{
    validator: (rule: any, value: any, callback: any) => {
      if (value > form.keepalive_percent) {
        callback(new Error('预热窗口百分位不能大于保活窗口百分位'))
      } else {
        callback()
      }
    }, trigger: 'blur'
  }],
  keepalive_percent: [{
    validator: (rule: any, value: any, callback: any) => {
      if (value < form.perwarm_percent) {
        callback(new Error('预热窗口百分位不能大于保活窗口百分位'))
      } else {
        callback()
      }
    }, trigger: 'blur'
  }]
})
</script>

<style lang='scss' scoped>
.params-container {
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

.params-label {
  font-size: var(--font-size-rank-2);
  color: var(--color-text);
}

.form-container {
  margin-top: 24px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  column-gap: 20px;
  row-gap: 0px;
}

.btn-container {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: right;
}

.console-container {
  margin-top: 12px;
  margin-bottom: 12px;
  display: grid;
  height: 480px;
  width: 100%;
  grid-template-columns: 1fr 20px 40px 20px 320px;
  min-width: 1000px;

  .panel-container {
    background-color: white;
    display: flex;
    flex-direction: column;
    padding: 20px 20px 0px 20px;
    align-items: center;
    justify-content: space-between;
  }
}

.percentage-value {
  display: block;
  margin-top: 10px;
  font-size: 28px;
}

.percentage-label {
  display: block;
  margin-top: 10px;
  font-size: 12px;
}

.terminal-container {
  display: flex;
  flex-direction: column;
  --header-height: 32px;

  .console-header {

    display: flex;
    align-items: center;
    padding: 0 12px;
    height: var(--header-height);
    background-color: rgb(84, 84, 84);
    border-top-right-radius: 4px;
    border-top-left-radius: 4px;
    color: white;
    font-size: var(--font-size-rank-2);
  }

  .console-body {
    height: calc(480px - var(--header-height));
    overflow-y: auto;
    padding: 12px;
    background-color: var(--vt-c-black);
    border-bottom-right-radius: 4px;
    border-bottom-left-radius: 4px;
  }


}

.console-body::-webkit-scrollbar {
  background-color: var(--vt-c-black);
}

.console-body::-webkit-scrollbar-thumb {
  background-color: rgb(84, 84, 84);
}
</style>
