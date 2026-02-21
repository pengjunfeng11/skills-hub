<template>
  <div>
    <h2>设置</h2>

    <el-card style="margin-top: 20px">
      <template #header>API Keys</template>
      <p style="color: #606266; margin-top: 0">API Keys 用于 Plugin API 认证，供 AI 和 CLI 工具使用。</p>

      <el-button type="primary" size="small" @click="openCreateDialog" style="margin-bottom: 16px">
        <el-icon><Plus /></el-icon> 创建 API Key
      </el-button>

      <el-table :data="keys" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="名称" />
        <el-table-column label="绑定标签" min-width="200">
          <template #default="{ row }">
            <template v-if="row.allowed_tags && row.allowed_tags.length">
              <el-tag v-for="tag in row.allowed_tags" :key="tag" size="small" style="margin-right: 4px">{{ tag }}</el-tag>
            </template>
            <span v-else style="color: #909399; font-size: 12px">未绑定（不返回任何 Skill）</span>
          </template>
        </el-table-column>
        <el-table-column prop="scopes" label="权限" width="120">
          <template #default="{ row }">
            <el-tag v-for="scope in row.scopes" :key="scope" size="small" type="info" style="margin-right: 4px">{{ scope }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="handleViewKey(row)">查看 Key</el-button>
            <el-button text type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button text type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- View Key Dialog -->
    <el-dialog v-model="showKeyView" title="查看 API Key" width="500px">
      <div v-if="viewKeyLoading" v-loading="true" style="height: 60px"></div>
      <template v-else>
        <el-input v-if="viewKeyValue" :model-value="viewKeyValue" readonly>
          <template #append>
            <el-button @click="copyText(viewKeyValue)">复制</el-button>
          </template>
        </el-input>
        <el-alert v-else type="info" :closable="false">
          此 Key 创建于功能上线前，无法查看原始值。
        </el-alert>
      </template>
    </el-dialog>

    <!-- Create Dialog -->
    <el-dialog v-model="showDialog" title="创建 API Key" width="460px">
      <el-form :model="form" label-position="top">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="my-api-key" />
        </el-form-item>
        <el-form-item label="绑定标签">
          <el-select
            v-model="form.allowed_tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入标签后回车添加"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- Show newly created key -->
    <el-dialog v-model="showKeyResult" title="API Key 已创建" width="500px" :close-on-click-modal="false">
      <el-input :model-value="newKey" readonly>
        <template #append>
          <el-button @click="copyText(newKey)">复制</el-button>
        </template>
      </el-input>
    </el-dialog>

    <!-- Edit Dialog -->
    <el-dialog v-model="showEditDialog" title="编辑 API Key" width="460px">
      <el-form :model="editForm" label-position="top">
        <el-form-item label="名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="绑定标签">
          <el-select
            v-model="editForm.allowed_tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入标签后回车添加"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="editing" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getApiKeys, getApiKeyDetail, createApiKey, updateApiKey, deleteApiKey } from '../api'

const keys = ref([])
const loading = ref(false)
const showDialog = ref(false)
const showKeyResult = ref(false)
const creating = ref(false)
const newKey = ref('')
const form = reactive({ name: '', allowed_tags: [] })

// View key
const showKeyView = ref(false)
const viewKeyValue = ref(null)
const viewKeyLoading = ref(false)

// Edit
const showEditDialog = ref(false)
const editing = ref(false)
const editingKeyId = ref(null)
const editForm = reactive({ name: '', allowed_tags: [] })

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

function openCreateDialog() {
  form.name = ''
  form.allowed_tags = []
  showDialog.value = true
}

async function handleCreate() {
  if (!form.name) {
    ElMessage.warning('请填写名称')
    return
  }
  creating.value = true
  try {
    const res = await createApiKey({ name: form.name, allowed_tags: form.allowed_tags })
    newKey.value = res.data.key
    showDialog.value = false
    showKeyResult.value = true
    loadKeys()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function handleViewKey(row) {
  showKeyView.value = true
  viewKeyLoading.value = true
  viewKeyValue.value = null
  try {
    const res = await getApiKeyDetail(row.id)
    viewKeyValue.value = res.data.key
  } catch {
    ElMessage.error('获取 Key 失败')
    showKeyView.value = false
  } finally {
    viewKeyLoading.value = false
  }
}

function openEditDialog(row) {
  editingKeyId.value = row.id
  editForm.name = row.name
  editForm.allowed_tags = [...(row.allowed_tags || [])]
  showEditDialog.value = true
}

async function handleEdit() {
  editing.value = true
  try {
    await updateApiKey(editingKeyId.value, {
      name: editForm.name,
      allowed_tags: editForm.allowed_tags,
    })
    ElMessage.success('已更新')
    showEditDialog.value = false
    loadKeys()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '更新失败')
  } finally {
    editing.value = false
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

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

onMounted(loadKeys)
</script>
