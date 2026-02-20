<template>
  <div>
    <h2>设置</h2>

    <el-card style="margin-top: 20px">
      <template #header>API Keys</template>
      <p style="color: #606266; margin-top: 0">API Keys 用于 Plugin API 认证，供 AI 和 CLI 工具使用。</p>

      <el-button type="primary" size="small" @click="showDialog = true" style="margin-bottom: 16px">
        <el-icon><Plus /></el-icon> 创建 API Key
      </el-button>

      <el-table :data="keys" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="scopes" label="权限" width="150">
          <template #default="{ row }">
            <el-tag v-for="scope in row.scopes" :key="scope" size="small" style="margin-right: 4px">{{ scope }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button text type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Show newly created key -->
    <el-dialog v-model="showKeyResult" title="API Key 已创建" width="500px" :close-on-click-modal="false">
      <el-alert type="warning" :closable="false" style="margin-bottom: 16px">
        请立即复制此 API Key，关闭后将无法再次查看。
      </el-alert>
      <el-input :model-value="newKey" readonly>
        <template #append>
          <el-button @click="copyKey">复制</el-button>
        </template>
      </el-input>
    </el-dialog>

    <el-dialog v-model="showDialog" title="创建 API Key" width="400px">
      <el-form :model="form" label-position="top">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="my-api-key" />
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
import { getApiKeys, createApiKey, deleteApiKey } from '../api'

const keys = ref([])
const loading = ref(false)
const showDialog = ref(false)
const showKeyResult = ref(false)
const creating = ref(false)
const newKey = ref('')
const form = reactive({ name: '' })

async function loadKeys() {
  loading.value = true
  try {
    const res = await getApiKeys()
    keys.value = res.data
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!form.name) {
    ElMessage.warning('请填写名称')
    return
  }
  creating.value = true
  try {
    const res = await createApiKey(form)
    newKey.value = res.data.key
    showDialog.value = false
    showKeyResult.value = true
    form.name = ''
    loadKeys()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function handleDelete(id) {
  try {
    await deleteApiKey(id)
    ElMessage.success('已删除')
    loadKeys()
  } catch {
    ElMessage.error('删除失败')
  }
}

function copyKey() {
  navigator.clipboard.writeText(newKey.value)
  ElMessage.success('已复制')
}

onMounted(loadKeys)
</script>
