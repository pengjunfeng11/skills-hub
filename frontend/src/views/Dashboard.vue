<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">概览</h1>
    </div>

    <!-- Loading overlay -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <span class="material-icons-round text-primary text-4xl animate-spin">progress_activity</span>
    </div>

    <template v-else>
      <!-- Stats Cards -->
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <div v-for="stat in statCards" :key="stat.label" class="bg-white rounded-2xl border border-gray-200 shadow-card p-5 relative overflow-hidden">
          <div class="absolute -top-4 -right-4 w-16 h-16 rounded-full opacity-10" :class="stat.bgColor"></div>
          <p class="text-sm text-gray-500 mb-1">{{ stat.label }}</p>
          <p class="text-2xl font-bold text-gray-900">{{ stat.value }}</p>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <!-- Popular Skills -->
        <div class="bg-white rounded-2xl border border-gray-200 shadow-card">
          <div class="px-6 py-4 border-b border-gray-100">
            <h3 class="text-base font-semibold text-gray-900">热门 Skills（Top 10）</h3>
          </div>
          <div class="p-6">
            <table v-if="popularSkills.length" class="w-full text-sm">
              <thead>
                <tr class="text-left text-gray-500 border-b border-gray-100">
                  <th class="pb-3 font-medium">名称</th>
                  <th class="pb-3 font-medium text-right">调用次数</th>
                  <th class="pb-3 font-medium text-right">占比</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in popularSkills" :key="s.skill_name" class="border-b border-gray-50 last:border-0">
                  <td class="py-3 font-medium text-gray-800">{{ s.skill_name }}</td>
                  <td class="py-3 text-right text-gray-600">{{ s.call_count }}</td>
                  <td class="py-3 text-right">
                    <div class="flex items-center justify-end gap-2">
                      <div class="w-20 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div class="h-full bg-primary rounded-full" :style="{ width: s.percentage + '%' }"></div>
                      </div>
                      <span class="text-xs text-gray-500 w-10 text-right">{{ s.percentage }}%</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-else class="text-center py-8 text-gray-400">
              <span class="material-icons-round text-4xl mb-2">bar_chart</span>
              <p>暂无调用数据</p>
            </div>
          </div>
        </div>

        <!-- Trend Chart -->
        <div class="bg-white rounded-2xl border border-gray-200 shadow-card">
          <div class="px-6 py-4 border-b border-gray-100">
            <h3 class="text-base font-semibold text-gray-900">调用趋势（30 天）</h3>
          </div>
          <div class="p-6">
            <v-chart v-if="trendOption" :option="trendOption" style="height: 300px" autoresize />
            <div v-else class="text-center py-8 text-gray-400">
              <span class="material-icons-round text-4xl mb-2">show_chart</span>
              <p>暂无趋势数据</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Skills -->
      <div class="bg-white rounded-2xl border border-gray-200 shadow-card">
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="text-base font-semibold text-gray-900">最近更新的 Skills</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-gray-500 border-b border-gray-100">
                <th class="px-6 py-3 font-medium">名称</th>
                <th class="px-6 py-3 font-medium">版本</th>
                <th class="px-6 py-3 font-medium">可见性</th>
                <th class="px-6 py-3 font-medium">更新时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in recentSkills" :key="row.name" class="border-b border-gray-50 last:border-0 hover:bg-gray-50/50">
                <td class="px-6 py-3">
                  <router-link :to="`/skills/${row.name}`" class="font-medium text-primary hover:underline">
                    {{ row.display_name }}
                  </router-link>
                </td>
                <td class="px-6 py-3 text-gray-600">{{ row.latest_version }}</td>
                <td class="px-6 py-3">
                  <span
                    class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                    :class="{
                      'bg-green-50 text-green-700': row.visibility === 'public',
                      'bg-amber-50 text-amber-700': row.visibility === 'team',
                      'bg-gray-100 text-gray-600': row.visibility === 'private',
                    }"
                  >{{ row.visibility }}</span>
                </td>
                <td class="px-6 py-3 text-gray-500">{{ new Date(row.updated_at).toLocaleString('zh-CN') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, computed } from 'vue'
import VChart from 'vue-echarts'
import 'echarts'
import { getSkills, getApiKeys, getStatsOverview, getStatsPopular, getStatsTrend } from '../api'

const stats = reactive({ totalSkills: 0, publishedSkills: 0, apiKeys: 0 })
const usageStats = reactive({ totalCalls: 0, todayCalls: 0, weekCalls: 0 })
const recentSkills = ref([])
const popularSkills = ref([])
const trendOption = ref(null)
const loading = ref(false)

const statCards = computed(() => [
  { label: 'Skills 总数', value: stats.totalSkills, bgColor: 'bg-primary' },
  { label: '已发布', value: stats.publishedSkills, bgColor: 'bg-green-500' },
  { label: 'API Keys', value: stats.apiKeys, bgColor: 'bg-purple-500' },
  { label: '总 API 调用', value: usageStats.totalCalls, bgColor: 'bg-primary' },
  { label: '今日调用', value: usageStats.todayCalls, bgColor: 'bg-amber-500' },
  { label: '7 日调用', value: usageStats.weekCalls, bgColor: 'bg-cyan-500' },
])

onMounted(async () => {
  loading.value = true
  try {
    const [skillsRes, keysRes] = await Promise.all([
      getSkills({ page: 1, size: 10 }),
      getApiKeys(),
    ])
    stats.totalSkills = skillsRes.data.total
    stats.publishedSkills = skillsRes.data.items.filter(s => s.is_published).length
    stats.apiKeys = keysRes.data.length
    recentSkills.value = skillsRes.data.items.slice(0, 5)

    const [overviewRes, popularRes, trendRes] = await Promise.all([
      getStatsOverview(),
      getStatsPopular({ days: 30, limit: 10 }),
      getStatsTrend({ days: 30 }),
    ])

    usageStats.totalCalls = overviewRes.data.total_calls
    usageStats.todayCalls = overviewRes.data.today_calls
    usageStats.weekCalls = overviewRes.data.week_calls
    popularSkills.value = popularRes.data

    if (trendRes.data.length) {
      trendOption.value = {
        tooltip: { trigger: 'axis' },
        grid: { left: 40, right: 20, top: 20, bottom: 30 },
        xAxis: {
          type: 'category',
          data: trendRes.data.map(d => d.date),
          axisLabel: { formatter: (val) => val.slice(5) },
        },
        yAxis: { type: 'value', minInterval: 1 },
        series: [{
          data: trendRes.data.map(d => d.call_count),
          type: 'line',
          smooth: true,
          areaStyle: { opacity: 0.15 },
          itemStyle: { color: '#1877F2' },
        }],
      }
    }
  } catch (e) {
    console.error('Dashboard load error:', e)
  } finally {
    loading.value = false
  }
})
</script>
