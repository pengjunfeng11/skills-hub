<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h2 style="margin: 0">Skills</h2>
      <el-button type="primary" @click="$router.push('/skills/new')">
        <el-icon><Plus /></el-icon> 创建 Skill
      </el-button>
    </div>

    <el-card>
      <div style="display: flex; gap: 12px; margin-bottom: 16px">
        <el-input v-model="search" placeholder="搜索 Skills..." clearable style="max-width: 300px"
          @keyup.enter="loadSkills" @clear="loadSkills">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="visibility" placeholder="可见性" clearable @change="loadSkills" style="width: 120px">
          <el-option label="Public" value="public" />
          <el-option label="Team" value="team" />
          <el-option label="Private" value="private" />
        </el-select>
      </div>

      <el-table :data="skills" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="200">
          <template #default="{ row }">
            <router-link :to="`/skills/${row.name}`" style="color: #409eff; text-decoration: none; font-weight: 500">
              {{ row.display_name }}
            </router-link>
            <div style="color: #909399; font-size: 12px">{{ row.name }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="latest_version" label="版本" width="100" />
        <el-table-column prop="tags" label="标签" width="200">
          <template #default="{ row }">
            <el-tag v-for="tag in row.tags" :key="tag" size="small" style="margin-right: 4px">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="visibility" label="可见性" width="100">
          <template #default="{ row }">
            <el-tag :type="row.visibility === 'public' ? 'success' : row.visibility === 'team' ? 'warning' : 'info'" size="small">
              {{ row.visibility }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="$router.push(`/skills/${row.name}/edit`)">编辑</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row.name)">
              <template #reference>
                <el-button text type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        style="margin-top: 16px; justify-content: center"
        v-model:current-page="page"
        :page-size="20"
        :total="total"
        layout="prev, pager, next"
        @current-change="loadSkills"
      />
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getSkills, deleteSkill } from '../api'

const skills = ref([])
const total = ref(0)
const page = ref(1)
const search = ref('')
const visibility = ref('')
const loading = ref(false)

async function loadSkills() {
  loading.value = true
  try {
    const res = await getSkills({ page: page.value, size: 20, q: search.value || undefined, visibility: visibility.value || undefined })
    skills.value = res.data.items
    total.value = res.data.total
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function handleDelete(name) {
  try {
    await deleteSkill(name)
    ElMessage.success('已删除')
    loadSkills()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(loadSkills)
</script>
