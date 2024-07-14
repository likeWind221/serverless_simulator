<template>
  <div ref="chart" class="chart"></div>
</template>

<script lang='ts' setup>
import * as echarts from "echarts";
var myChart: any;

const props = defineProps<{
  data: any[]
  type: string
}>()

window.addEventListener('resize', function () {
  myChart.resize();
});

const createChart = () => {
  // 取出props.data中的属性，构成数组
  const values = props.data.map(item => item.value);
  const memWasteTime = props.data.map(item => item.memWaste);
  const names = props.data.map(item => item.name);
  if (props.type === 'first') {
    // 绘制图表
    myChart.setOption({
      tooltip: {},
      xAxis: {
        data: names
      },
      yAxis: {
        name: '冷启动占比',
        type: 'value',
        axisLabel: {
          formatter: function (value: any) {
            return value + '%';
          }
        }
      },
      series: [
        {
          name: '冷启动占比(排除首次)',
          type: 'bar',
          data: values
        }
      ]
    });
  } else {
    // 绘制图表
    myChart.setOption({
      tooltip: {},
      xAxis: {
        data: names
      },
      yAxis: {
        name: '内存浪费时间',
        type: 'value',
        axisLabel: {
          formatter: function (value: any) {
            return value / 10000 + '万';
          }
        }
      },
      series: [
        {
          name: '内存浪费时间',
          type: 'bar',
          data: memWasteTime
        }
      ]
    });
  }
}

watch(() => props.type, () => {
  console.log(props.type)
  createChart()
})
watch(() => props.data.length, () => {
  console.log(props.data)
  createChart()
})

const chart = ref(null);
const initChart = () => {
  // 基于准备好的dom，初始化echarts实例
  myChart = echarts.init(chart.value);
  createChart();
}

onMounted(() => {
  initChart();
});
</script>

<style lang='scss' scoped>
.chart {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
}
</style>
