<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">团队管理</h1>
      <button
        @click="showCreateDialog = true"
        class="inline-flex items-center gap-2 px-4 py-2.5 bg-primary text-white text-sm font-medium rounded-xl hover:bg-primary-dark transition-colors cursor-pointer"
      >
        <span class="material-icons-round text-[18px]">add</span>
        创建团队
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <span class="material-icons-round text-primary text-4xl animate-spin">progress_activity</span>
    </div>

    <template v-else>
      <!-- My Teams -->
      <div v-if="myTeams.length" class="mb-8">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">我的团队</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="team in myTeams"
            :key="team.id"
            class="bg-white rounded-2xl border border-gray-200 shadow-card p-5 hover:shadow-md transition-shadow"
          >
            <div class="flex items-start justify-between mb-3">
              <div>
                <h3 class="font-semibold text-gray-900">{{ team.name }}</h3>
                <span class="text-xs text-gray-400 font-mono">{{ team.slug }}</span>
              </div>
              <span
                class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium"
                :class="team.my_role === 'admin' ? 'bg-primary-light text-primary' : 'bg-gray-100 text-gray-600'"
              >{{ team.my_role }}</span>
            </div>
            <p v-if="team.description" class="text-sm text-gray-500 mb-4 line-clamp-2">{{ team.description }}</p>
            <div class="flex items-center justify-between">
              <button
                @click="viewTeamDetail(team.slug)"
                class="text-sm text-primary hover:underline cursor-pointer"
              >查看详情</button>
              <button
                @click="handleLeave(team.slug)"
                class="text-sm text-gray-400 hover:text-red-500 cursor-pointer transition-colors"
              >退出</button>
            </div>
          </div>
        </div>
      </div>

      <!-- All Teams -->
      <div>
        <h2 class="text-lg font-semibold text-gray-800 mb-4">所有团队</h2>
        <div class="bg-white rounded-2xl border border-gray-200 shadow-card">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-gray-500 border-b border-gray-100">
                  <th class="px-6 py-3 font-medium">团队名称</th>
                  <th class="px-6 py-3 font-medium">描述</th>
                  <th class="px-6 py-3 font-medium">创建时间</th>
                  <th class="px-6 py-3 font-medium text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in allTeams" :key="row.id" class="border-b border-gray-50 last:border-0 hover:bg-gray-50/50">
                  <td class="px-6 py-3">
                    <div>
                      <span class="font-medium text-gray-800">{{ row.name }}</span>
                      <div class="text-xs text-gray-400 font-mono mt-0.5">{{ row.slug }}</div>
                    </div>
                  </td>
                  <td class="px-6 py-3 text-gray-600 max-w-[250px] truncate">{{ row.description || '—' }}</td>
                  <td class="px-6 py-3 text-gray-500">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</td>
                  <td class="px-6 py-3 text-right">
                    <button
                      v-if="!isMyTeam(row.id)"
                      @click="handleJoin(row.slug)"
                      class="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-primary border border-primary/30 rounded-lg hover:bg-primary/5 cursor-pointer transition-colors"
                    >
                      <span class="material-icons-round text-[16px]">group_add</span>
                      加入
                    </button>
                    <span v-else class="text-xs text-gray-400">已加入</span>
                  </td>
                </tr>
                <tr v-if="!allTeams.length">
                  <td colspan="4" class="px-6 py-12 text-center text-gray-400">
                    <span class="material-icons-round text-4xl mb-2">groups</span>
                    <p>暂无团队</p>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>

    <!-- Create team modal -->
    <Modal v-model="showCreateDialog" title="创建团队">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">团队名称 <span class="text-danger">*</span></label>
          <input v-model="form.name" placeholder="我的团队" class="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">标识 (slug) <span class="text-danger">*</span></label>
          <input v-model="form.slug" placeholder="my-team" class="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">描述</label>
          <textarea v-model="form.description" rows="2" class="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all resize-none"></textarea>
        </div>
      </div>
      <template #footer>
        <button @click="showCreateDialog = false" class="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-xl hover:bg-gray-50 cursor-pointer">取消</button>
        <button @click="handleCreate" :disabled="creating" class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-xl hover:bg-primary-dark disabled:opacity-60 cursor-pointer">创建</button>
      </template>
    </Modal>

    <!-- Team detail modal -->
    <Modal v-model="showDetailModal" :title="detailTeam?.name || '团队详情'" max-width="600px">
      <div v-if="detailLoading" class="flex items-center justify-center py-8">
        <span class="material-icons-round text-primary text-3xl animate-spin">progress_activity</span>
      </div>
      <template v-else-if="detailTeam">
        <p v-if="detailTeam.description" class="text-sm text-gray-500 mb-4">{{ detailTeam.description }}</p>
        <h4 class="text-sm font-semibold text-gray-700 mb-3">成员 ({{ detailTeam.members?.length || 0 }})</h4>
        <div class="space-y-2 max-h-[300px] overflow-y-auto">
          <div
            v-for="member in detailTeam.members"
            :key="member.id"
            class="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg"
          >
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-medium">
                {{ member.username.charAt(0).toUpperCase() }}
              </div>
              <div>
                <span class="text-sm font-medium text-gray-800">{{ member.username }}</span>
                <span
                  class="ml-2 inline-flex px-1.5 py-0.5 rounded text-xs font-medium"
                  :class="member.role === 'admin' ? 'bg-primary-light text-primary' : 'bg-gray-200 text-gray-500'"
                >{{ member.role }}</span>
              </div>
            </div>
            <button
              v-if="detailTeam.my_role === 'admin' && member.user_id !== currentUserId"
              @click="handleRemoveMember(detailTeam.slug, member.user_id)"
              class="text-xs text-gray-400 hover:text-red-500 cursor-pointer transition-colors"
            >移除</button>
          </div>
        </div>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useToast } from '../composables/useToast'
import { useAuthStore } from '../stores/auth'
import { getTeams, getTeam, getMyTeams, createTeam, joinTeam, leaveTeam, removeTeamMember } from '../api'
import Modal from '../components/Modal.vue'

const toast = useToast()
const authStore = useAuthStore()
const currentUserId = computed(() => authStore.user?.id)

const allTeams = ref([])
const myTeams = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const form = reactive({ name: '', slug: '', description: '' })

const showDetailModal = ref(false)
const detailTeam = ref(null)
const detailLoading = ref(false)

function isMyTeam(teamId) {
  return myTeams.value.some(t => t.id === teamId)
}

async function loadData() {
  loading.value = true
  try {
    const [teamsRes, myRes] = await Promise.all([getTeams(), getMyTeams()])
    allTeams.value = teamsRes.data
    myTeams.value = myRes.data
  } catch {
    toast.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!form.name || !form.slug) {
    toast.warning('请填写团队名称和标识')
    return
  }
  creating.value = true
  try {
    await createTeam(form)
    toast.success('创建成功')
    showCreateDialog.value = false
    form.name = ''
    form.slug = ''
    form.description = ''
    loadData()
  } catch (err) {
    toast.error(err.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function handleJoin(slug) {
  try {
    await joinTeam(slug)
    toast.success('加入成功')
    loadData()
  } catch (err) {
    toast.error(err.response?.data?.detail || '加入失败')
  }
}

async function handleLeave(slug) {
  try {
    await leaveTeam(slug)
    toast.success('已退出团队')
    loadData()
  } catch (err) {
    toast.error(err.response?.data?.detail || '退出失败')
  }
}

async function viewTeamDetail(slug) {
  showDetailModal.value = true
  detailLoading.value = true
  try {
    const res = await getTeam(slug)
    detailTeam.value = res.data
  } catch {
    toast.error('加载团队详情失败')
    showDetailModal.value = false
  } finally {
    detailLoading.value = false
  }
}

async function handleRemoveMember(slug, userId) {
  try {
    await removeTeamMember(slug, userId)
    toast.success('已移除成员')
    // Reload detail
    viewTeamDetail(slug)
    loadData()
  } catch (err) {
    toast.error(err.response?.data?.detail || '移除失败')
  }
}

onMounted(loadData)
</script>
