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
import { getSkills, getApiKeys } from '../api'

const stats = reactive({ totalSkills: 0, publishedSkills: 0, apiKeys: 0 })
const recentSkills = ref([])
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
  } catch {}
  finally {
    loading.value = false
  }
})
</script>
