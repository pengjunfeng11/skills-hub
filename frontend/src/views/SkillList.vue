<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Skills</h1>
      <button
        @click="$router.push('/skills/new')"
        class="inline-flex items-center gap-2 px-4 py-2.5 bg-primary text-white text-sm font-medium rounded-xl hover:bg-primary-dark transition-colors cursor-pointer"
      >
        <span class="material-icons-round text-[18px]">add</span>
        创建 Skill
      </button>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-2xl border border-gray-200 shadow-card">
      <div class="p-4 border-b border-gray-100 flex flex-wrap items-center gap-3">
        <div class="relative flex-1 max-w-sm">
          <span class="material-icons-round text-gray-400 text-[20px] absolute left-3 top-1/2 -translate-y-1/2">search</span>
          <input
            v-model="search"
            placeholder="搜索 Skills..."
            class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-xl text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
            @keyup.enter="resetAndLoad"
          />
        </div>
        <select
          v-model="visibility"
          @change="resetAndLoad"
          class="px-3 py-2 border border-gray-300 rounded-xl text-sm text-gray-700 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none bg-white cursor-pointer"
        >
          <option value="">全部可见性</option>
          <option value="public">Public</option>
          <option value="team">Team</option>
          <option value="private">Private</option>
        </select>
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
              <th class="px-6 py-3 font-medium">Skill</th>
              <th class="px-6 py-3 font-medium">标签</th>
              <th class="px-6 py-3 font-medium">状态</th>
              <th class="px-6 py-3 font-medium">可见性</th>
              <th class="px-6 py-3 font-medium text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in skills" :key="row.name" class="border-b border-gray-50 last:border-0 hover:bg-gray-50/50">
              <!-- Skill column: color icon + name + version -->
              <td class="px-6 py-3">
                <div class="flex items-center gap-3">
                  <div
                    class="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm shrink-0"
                    :style="{ backgroundColor: skillColor(row.name) }"
                  >
                    {{ row.name.charAt(0).toUpperCase() }}
                  </div>
                  <div>
                    <router-link :to="`/skills/${row.name}`" class="font-medium text-gray-900 hover:text-primary transition-colors">
                      {{ row.display_name }}
                    </router-link>
                    <div class="flex items-center gap-2 mt-0.5">
                      <span class="text-xs text-gray-400">{{ row.name }}</span>
                      <span v-if="row.latest_version" class="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">v{{ row.latest_version }}</span>
                      <span v-if="row.author_username" class="text-xs text-gray-500 before:content-['·'] before:mx-1">{{ row.author_username }}</span>
                    </div>
                  </div>
                </div>
              </td>
              <!-- Tags column -->
              <td class="px-6 py-3">
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="tag in (row.tags || []).slice(0, 3)"
                    :key="tag"
                    class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full"
                    :style="{ backgroundColor: tagColor(tag) + '18', color: tagColor(tag) }"
                  >{{ tag }}</span>
                  <span v-if="(row.tags || []).length > 3" class="text-xs text-gray-400">+{{ row.tags.length - 3 }}</span>
                  <span v-if="!row.tags || row.tags.length === 0" class="text-gray-300 text-xs">—</span>
                </div>
              </td>
              <!-- Status column: subscription toggle -->
              <td class="px-6 py-3">
                <button
                  @click.stop="toggleSubscription(row)"
                  class="inline-flex items-center gap-1.5 cursor-pointer group"
                  :title="row.subscription_enabled ? '已启用 (点击取消)' : '未启用 (点击订阅)'"
                >
                  <span
                    class="w-2.5 h-2.5 rounded-full transition-colors"
                    :class="row.subscription_enabled ? 'bg-green-500' : 'bg-gray-300 group-hover:bg-gray-400'"
                  ></span>
                  <span class="text-xs" :class="row.subscription_enabled ? 'text-green-600' : 'text-gray-400'">
                    {{ row.subscription_enabled ? '已启用' : '未启用' }}
                  </span>
                </button>
              </td>
              <!-- Visibility column -->
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
              <!-- Actions column: more_vert dropdown -->
              <td class="px-6 py-3 text-right">
                <div class="relative inline-block" ref="menuRefs">
                  <button
                    @click.stop="toggleMenu(row.name)"
                    class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
                  >
                    <span class="material-icons-round text-[20px]">more_vert</span>
                  </button>
                  <!-- Dropdown menu -->
                  <Teleport to="body">
                    <div
                      v-if="openMenu === row.name"
                      class="fixed inset-0 z-40"
                      @click="closeMenu"
                    ></div>
                  </Teleport>
                  <div
                    v-if="openMenu === row.name"
                    class="absolute right-0 top-full mt-1 w-40 bg-white rounded-xl border border-gray-200 shadow-lg z-50 py-1"
                  >
                    <button
                      @click="closeMenu(); $router.push(`/skills/${row.name}/edit`)"
                      class="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 cursor-pointer"
                    >
                      <span class="material-icons-round text-[16px] text-gray-400">edit</span>
                      编辑
                    </button>
                    <button
                      @click="closeMenu(); toggleSubscription(row)"
                      class="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 cursor-pointer"
                    >
                      <span class="material-icons-round text-[16px] text-gray-400">
                        {{ row.subscription_enabled ? 'notifications_off' : 'notifications_active' }}
                      </span>
                      {{ row.subscription_enabled ? '取消订阅' : '订阅' }}
                    </button>
                    <div class="border-t border-gray-100 my-1"></div>
                    <button
                      @click="closeMenu(); confirmDelete(row.name)"
                      class="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 cursor-pointer"
                    >
                      <span class="material-icons-round text-[16px]">delete</span>
                      删除
                    </button>
                  </div>
                </div>
              </td>
            </tr>
            <tr v-if="!skills.length">
              <td colspan="5" class="px-6 py-12 text-center text-gray-400">
                <span class="material-icons-round text-4xl mb-2">folder_off</span>
                <p>暂无 Skills</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination: page number navigation -->
      <div v-if="totalPages > 1" class="px-6 py-4 border-t border-gray-100 flex items-center justify-center gap-1">
        <button
          :disabled="page <= 1"
          @click="page = 1; loadSkills()"
          class="px-2 py-1.5 text-sm text-gray-500 hover:text-primary hover:bg-primary/5 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          title="首页"
        >&laquo;</button>
        <button
          :disabled="page <= 1"
          @click="page--; loadSkills()"
          class="px-2 py-1.5 text-sm text-gray-500 hover:text-primary hover:bg-primary/5 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >&lsaquo;</button>
        <button
          v-for="p in visiblePages"
          :key="p"
          @click="page = p; loadSkills()"
          :class="[
            'px-3 py-1.5 text-sm rounded-lg cursor-pointer transition-colors',
            p === page ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
          ]"
        >{{ p }}</button>
        <button
          :disabled="page >= totalPages"
          @click="page++; loadSkills()"
          class="px-2 py-1.5 text-sm text-gray-500 hover:text-primary hover:bg-primary/5 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >&rsaquo;</button>
        <button
          :disabled="page >= totalPages"
          @click="page = totalPages; loadSkills()"
          class="px-2 py-1.5 text-sm text-gray-500 hover:text-primary hover:bg-primary/5 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          title="末页"
        >&raquo;</button>
      </div>
    </div>

    <!-- Delete confirm modal -->
    <Modal v-model="showDeleteModal" title="确认删除" max-width="400px">
      <p class="text-gray-600">确定要删除这个 Skill 吗？此操作不可撤销。</p>
      <template #footer>
        <button @click="showDeleteModal = false" class="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-xl hover:bg-gray-50 cursor-pointer">取消</button>
        <button @click="handleDelete" class="px-4 py-2 text-sm font-medium text-white bg-danger rounded-xl hover:bg-red-600 cursor-pointer">删除</button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useToast } from '../composables/useToast'
import { getSkills, deleteSkill, subscribeSkill, unsubscribeSkill } from '../api'
import Modal from '../components/Modal.vue'

const toast = useToast()
const skills = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const search = ref('')
const visibility = ref('')
const loading = ref(false)
const showDeleteModal = ref(false)
const deletingName = ref('')
const openMenu = ref(null)

const totalPages = computed(() => Math.ceil(total.value / pageSize))
const visiblePages = computed(() => {
  const pages = []
  const start = Math.max(1, page.value - 2)
  const end = Math.min(totalPages.value, page.value + 2)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

function skillColor(name) {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316', '#eab308', '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6']
  return colors[Math.abs(hash) % colors.length]
}

function tagColor(tag) {
  let hash = 0
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316', '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6', '#a855f7']
  return colors[Math.abs(hash) % colors.length]
}

async function loadSkills() {
  loading.value = true
  try {
    const res = await getSkills({ page: page.value, size: pageSize, q: search.value || undefined, visibility: visibility.value || undefined })
    skills.value = res.data.items
    total.value = res.data.total
  } catch {
    toast.error('加载失败')
  } finally {
    loading.value = false
  }
}

function resetAndLoad() {
  page.value = 1
  loadSkills()
}

function confirmDelete(name) {
  deletingName.value = name
  showDeleteModal.value = true
}

async function handleDelete() {
  try {
    await deleteSkill(deletingName.value)
    toast.success('已删除')
    showDeleteModal.value = false
    loadSkills()
  } catch {
    toast.error('删除失败')
  }
}

async function toggleSubscription(row) {
  try {
    if (row.subscription_enabled) {
      await unsubscribeSkill(row.name)
      row.is_subscribed = true
      row.subscription_enabled = false
      toast.success('已取消订阅')
    } else {
      await subscribeSkill(row.name)
      row.is_subscribed = true
      row.subscription_enabled = true
      toast.success('已订阅')
    }
  } catch {
    toast.error('操作失败')
  }
}

function toggleMenu(name) {
  openMenu.value = openMenu.value === name ? null : name
}

function closeMenu() {
  openMenu.value = null
}

onMounted(() => {
  loadSkills()
})
</script>
