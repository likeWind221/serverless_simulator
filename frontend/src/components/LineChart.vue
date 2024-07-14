<template>
  <div ref="chart" class="chart"></div>
</template>

<script lang='ts' setup>
import * as echarts from "echarts";
var myChart: any;
const chart = ref(null);

const props = defineProps<{
  data: any[]
}>()

window.addEventListener('resize', function () {
  myChart.resize();
});

const createChart = () => {
  // 取出props.data中的属性，构成数组
  const data = props.data.map(item => item.value)
  const labels = props.data.map(item => item.percentile)
  myChart.setOption({
    xAxis: {
      type: 'category',
      name: '应用百分位(分位点)',
      nameLocation: 'middle',
      data: labels,
      nameTextStyle: { lineHeight: 28 }
    },
    yAxis: {
      name: '冷启动次数(不计首次)',
      nameLocation: 'middle',
      nameTextStyle: { lineHeight: 28 },
      type: 'value'
    },
    series: [
      {
        data: data,
        type: 'line'
      }
    ]
  })
}

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
