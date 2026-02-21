<template>
  <div v-loading="loading">
    <h2>概览</h2>
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic title="Skills 总数" :value="stats.totalSkills" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic title="已发布" :value="stats.publishedSkills" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic title="API Keys" :value="stats.apiKeys" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic title="总 API 调用" :value="usageStats.totalCalls" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic title="今日调用" :value="usageStats.todayCalls" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic title="7 日调用" :value="usageStats.weekCalls" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>热门 Skills（Top 10）</template>
          <el-table :data="popularSkills" style="width: 100%" size="small">
            <el-table-column prop="skill_name" label="名称" />
            <el-table-column prop="call_count" label="调用次数" width="100" />
            <el-table-column label="占比" width="200">
              <template #default="{ row }">
                <el-progress :percentage="row.percentage" :stroke-width="14" :show-text="true" />
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!popularSkills.length" description="暂无调用数据" :image-size="60" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>调用趋势（30 天）</template>
          <v-chart v-if="trendOption" :option="trendOption" style="height: 300px" autoresize />
          <el-empty v-else description="暂无趋势数据" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px">
      <template #header>最近更新的 Skills</template>
      <el-table :data="recentSkills" style="width: 100%">
        <el-table-column prop="name" label="名称">
          <template #default="{ row }">
            <router-link :to="`/skills/${row.name}`" style="color: #409eff; text-decoration: none">
              {{ row.display_name }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="latest_version" label="版本" width="120" />
        <el-table-column prop="visibility" label="可见性" width="120">
          <template #default="{ row }">
            <el-tag :type="row.visibility === 'public' ? 'success' : row.visibility === 'team' ? 'warning' : 'info'" size="small">
              {{ row.visibility }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.updated_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { getSkills, getApiKeys, getStatsOverview, getStatsPopular, getStatsTrend } from '../api'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const stats = reactive({ totalSkills: 0, publishedSkills: 0, apiKeys: 0 })
const usageStats = reactive({ totalCalls: 0, todayCalls: 0, weekCalls: 0 })
const recentSkills = ref([])
const popularSkills = ref([])
const trendOption = ref(null)
const loading = ref(false)

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

    // Load usage stats in parallel
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
          axisLabel: {
            formatter: (val) => val.slice(5), // MM-DD
          },
        },
        yAxis: { type: 'value', minInterval: 1 },
        series: [{
          data: trendRes.data.map(d => d.call_count),
          type: 'line',
          smooth: true,
          areaStyle: { opacity: 0.15 },
          itemStyle: { color: '#409eff' },
        }],
      }
    }
  } catch {}
  finally {
    loading.value = false
  }
})
</script>
