<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h2 style="margin: 0">团队管理</h2>
      <el-button type="primary" @click="showDialog = true">创建团队</el-button>
    </div>

    <el-card>
      <el-table :data="teams" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="团队名称" />
        <el-table-column prop="slug" label="标识" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showDialog" title="创建团队" width="500px">
      <el-form :model="form" label-position="top">
        <el-form-item label="团队名称" required>
          <el-input v-model="form.name" placeholder="我的团队" />
        </el-form-item>
        <el-form-item label="标识 (slug)" required>
          <el-input v-model="form.slug" placeholder="my-team" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getTeams, createTeam } from '../api'

const teams = ref([])
const loading = ref(false)
const showDialog = ref(false)
const creating = ref(false)
const form = reactive({ name: '', slug: '', description: '' })

async function loadTeams() {
  loading.value = true
  try {
    const res = await getTeams()
    teams.value = res.data
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!form.name || !form.slug) {
    ElMessage.warning('请填写必填字段')
    return
  }
  creating.value = true
  try {
    await createTeam(form)
    ElMessage.success('创建成功')
    showDialog.value = false
    Object.assign(form, { name: '', slug: '', description: '' })
    loadTeams()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

onMounted(loadTeams)
</script>
