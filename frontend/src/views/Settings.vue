<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">设置</h1>

    <!-- Subscription info banner -->
    <div class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-2xl flex items-start gap-3">
      <span class="material-icons-round text-blue-500 text-[20px] mt-0.5">info</span>
      <div class="text-sm text-blue-700">
        <p class="font-medium">Plugin API 现已基于订阅过滤</p>
        <p class="mt-1 text-blue-600">前往 <router-link to="/skills" class="underline font-medium">Skills 页面</router-link> 管理您的 Skill 订阅。只有已订阅且启用的 Skill 才会通过 Plugin API 返回。</p>
      </div>
    </div>

    <!-- API Keys -->
    <div class="bg-white rounded-2xl border border-gray-200 shadow-card">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 class="text-base font-semibold text-gray-900">API Keys</h3>
          <p class="text-sm text-gray-500 mt-0.5">API Keys 用于 Plugin API 认证，供 AI 和 CLI 工具使用。</p>
        </div>
        <button
          @click="openCreateDialog"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary rounded-xl hover:bg-primary-dark transition-colors cursor-pointer"
        >
          <span class="material-icons-round text-[18px]">add</span>
          创建 API Key
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-16">
        <span class="material-icons-round text-primary text-4xl animate-spin">progress_activity</span>
      </div>

      <!-- Table -->
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-gray-500 border-b border-gray-100">
              <th class="px-6 py-3 font-medium">名称</th>
              <th class="px-6 py-3 font-medium">API Key</th>
              <th class="px-6 py-3 font-medium">绑定标签</th>
              <th class="px-6 py-3 font-medium">创建时间</th>
              <th class="px-6 py-3 font-medium text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in keys" :key="row.id" class="border-b border-gray-50 last:border-0 hover:bg-gray-50/50">
              <td class="px-6 py-3 font-medium text-gray-800">{{ row.name }}</td>
              <td class="px-6 py-3">
                <div class="flex items-center gap-1.5">
                  <template v-if="revealedKeys[row.id]">
                    <code class="text-xs bg-gray-50 border border-gray-200 rounded px-2 py-1 font-mono text-gray-700 select-all">{{ revealedKeys[row.id] }}</code>
                    <button @click="copyText(revealedKeys[row.id])" class="p-1 text-gray-400 hover:text-primary cursor-pointer" title="复制">
                      <span class="material-icons-round text-[16px]">content_copy</span>
                    </button>
                    <button @click="delete revealedKeys[row.id]" class="p-1 text-gray-400 hover:text-gray-600 cursor-pointer" title="隐藏">
                      <span class="material-icons-round text-[16px]">visibility_off</span>
                    </button>
                  </template>
                  <template v-else>
                    <span class="text-xs text-gray-400 font-mono">skh_••••••••</span>
                    <button @click="revealKey(row)" class="p-1 text-gray-400 hover:text-primary cursor-pointer" title="显示">
                      <span class="material-icons-round text-[16px]">visibility</span>
                    </button>
                  </template>
                </div>
              </td>
              <td class="px-6 py-3">
                <template v-if="row.allowed_tags && row.allowed_tags.length">
                  <span v-for="tag in row.allowed_tags" :key="tag" class="inline-flex px-2 py-0.5 bg-primary-light text-primary text-xs rounded-md mr-1">{{ tag }}</span>
                </template>
                <span v-else class="text-xs text-gray-400">未绑定</span>
              </td>
              <td class="px-6 py-3 text-gray-500">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</td>
              <td class="px-6 py-3 text-right">
                <div class="flex items-center justify-end gap-1">
                  <button @click="openEditDialog(row)" class="p-1.5 text-gray-400 hover:text-primary hover:bg-primary/5 rounded-lg transition-colors cursor-pointer" title="编辑">
                    <span class="material-icons-round text-[18px]">edit</span>
                  </button>
                  <button @click="confirmDeleteKey(row.id)" class="p-1.5 text-gray-400 hover:text-danger hover:bg-red-50 rounded-lg transition-colors cursor-pointer" title="删除">
                    <span class="material-icons-round text-[18px]">delete</span>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!keys.length">
              <td colspan="5" class="px-6 py-12 text-center text-gray-400">
                <span class="material-icons-round text-4xl mb-2">vpn_key_off</span>
                <p>暂无 API Key</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create Dialog -->
    <Modal v-model="showDialog" title="创建 API Key" max-width="460px">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">名称 <span class="text-danger">*</span></label>
          <input v-model="form.name" placeholder="my-api-key" class="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">绑定标签</label>
          <TagInput v-model="form.allowed_tags" placeholder="输入标签后回车添加" />
        </div>
      </div>
      <template #footer>
        <button @click="showDialog = false" class="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-xl hover:bg-gray-50 cursor-pointer">取消</button>
        <button @click="handleCreate" :disabled="creating" class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-xl hover:bg-primary-dark disabled:opacity-60 cursor-pointer">创建</button>
      </template>
    </Modal>

    <!-- Show newly created key -->
    <Modal v-model="showKeyResult" title="API Key 已创建" :close-on-backdrop="false">
      <div class="flex items-center gap-2">
        <input :value="newKey" readonly class="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl text-sm bg-gray-50 font-mono" />
        <button @click="copyText(newKey)" class="px-3 py-2.5 text-sm font-medium text-primary border border-gray-300 rounded-xl hover:bg-gray-50 cursor-pointer">复制</button>
      </div>
      <p class="text-xs text-gray-500 mt-2">请立即复制保存，关闭后无法再次查看完整 Key。</p>
    </Modal>

    <!-- Edit Dialog -->
    <Modal v-model="showEditDialog" title="编辑 API Key" max-width="460px">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">名称</label>
          <input v-model="editForm.name" class="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">绑定标签</label>
          <TagInput v-model="editForm.allowed_tags" placeholder="输入标签后回车添加" />
        </div>
      </div>
      <template #footer>
        <button @click="showEditDialog = false" class="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-xl hover:bg-gray-50 cursor-pointer">取消</button>
        <button @click="handleEdit" :disabled="editing" class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-xl hover:bg-primary-dark disabled:opacity-60 cursor-pointer">保存</button>
      </template>
    </Modal>

    <!-- Delete confirm modal -->
    <Modal v-model="showDeleteModal" title="确认删除" max-width="400px">
      <p class="text-gray-600">确定要删除这个 API Key 吗？</p>
      <template #footer>
        <button @click="showDeleteModal = false" class="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-xl hover:bg-gray-50 cursor-pointer">取消</button>
        <button @click="handleDelete" class="px-4 py-2 text-sm font-medium text-white bg-danger rounded-xl hover:bg-red-600 cursor-pointer">删除</button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useToast } from '../composables/useToast'
import { getApiKeys, getApiKeyDetail, createApiKey, updateApiKey, deleteApiKey } from '../api'
import Modal from '../components/Modal.vue'
import TagInput from '../components/TagInput.vue'

const toast = useToast()
const keys = ref([])
const loading = ref(false)
const showDialog = ref(false)
const showKeyResult = ref(false)
const creating = ref(false)
const newKey = ref('')
const form = reactive({ name: '', allowed_tags: [] })

const revealedKeys = reactive({})

const showEditDialog = ref(false)
const editing = ref(false)
const editingKeyId = ref(null)
const editForm = reactive({ name: '', allowed_tags: [] })

const showDeleteModal = ref(false)
const deletingKeyId = ref(null)

async function loadKeys() {
  loading.value = true
  try {
    const res = await getApiKeys()
    keys.value = res.data
  } catch {
    toast.error('加载失败')
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
    toast.warning('请填写名称')
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
    toast.error(err.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function revealKey(row) {
  try {
    const res = await getApiKeyDetail(row.id)
    if (res.data.key) {
      revealedKeys[row.id] = res.data.key
    } else {
      toast.warning('此 Key 无法查看原始值')
    }
  } catch {
    toast.error('获取 Key 失败')
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
    toast.success('已更新')
    showEditDialog.value = false
    loadKeys()
  } catch (err) {
    toast.error(err.response?.data?.detail || '更新失败')
  } finally {
    editing.value = false
  }
}

function confirmDeleteKey(id) {
  deletingKeyId.value = id
  showDeleteModal.value = true
}

async function handleDelete() {
  try {
    await deleteApiKey(deletingKeyId.value)
    toast.success('已删除')
    showDeleteModal.value = false
    loadKeys()
  } catch {
    toast.error('删除失败')
  }
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    toast.success('已复制')
  } catch {
    toast.error('复制失败，请手动复制')
  }
}

onMounted(loadKeys)
</script>
