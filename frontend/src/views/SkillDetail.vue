<template>
  <div>
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <span class="material-icons-round text-primary text-4xl animate-spin">progress_activity</span>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <button @click="$router.push('/skills')" class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer">
            <span class="material-icons-round text-[20px]">arrow_back</span>
          </button>
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ skill?.display_name }}</h1>
            <span class="text-sm text-gray-500">{{ skill?.name }}</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="toggleSubscription"
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-xl border transition-colors cursor-pointer"
            :class="skill?.subscription_enabled
              ? 'text-green-700 border-green-300 bg-green-50 hover:bg-green-100'
              : 'text-gray-500 border-gray-300 hover:bg-gray-50'"
          >
            <span class="material-icons-round text-[18px]">
              {{ skill?.subscription_enabled ? 'notifications_active' : 'notifications_none' }}
            </span>
            {{ skill?.subscription_enabled ? '已订阅' : '订阅' }}
          </button>
          <button
            @click="$router.push(`/skills/${skill?.name}/edit`)"
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer"
          >
            <span class="material-icons-round text-[18px]">edit</span>
            编辑
          </button>
          <button
            @click="showVersionDialog = true"
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary rounded-xl hover:bg-primary-dark transition-colors cursor-pointer"
          >
            <span class="material-icons-round text-[18px]">publish</span>
            发布新版本
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left: Content Preview -->
        <div class="lg:col-span-2 space-y-6">
          <div class="bg-white rounded-2xl border border-gray-200 shadow-card">
            <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-base font-semibold text-gray-900">内容预览</h3>
              <div class="flex items-center gap-2">
                <button
                  v-if="activeTab !== 'skill-md' && currentFiles[activeTab]"
                  @click="downloadAttachment(activeTab, currentFiles[activeTab])"
                  class="inline-flex items-center gap-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 cursor-pointer"
                >
                  <span class="material-icons-round text-[16px]">download</span>
                  下载当前文件
                </button>
                <select
                  v-model="selectedVersion"
                  @change="loadVersion"
                  class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white cursor-pointer focus:border-primary outline-none"
                >
                  <option v-for="v in versions" :key="v.version" :value="v.version">{{ v.version }}</option>
                </select>
              </div>
            </div>

            <!-- Tabs -->
            <div v-if="currentContent || Object.keys(currentFiles).length">
              <div class="flex border-b border-gray-100 px-6 gap-1 overflow-x-auto">
                <button
                  @click="activeTab = 'skill-md'"
                  :class="[
                    'px-3 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap cursor-pointer',
                    activeTab === 'skill-md' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'
                  ]"
                >SKILL.md</button>
                <button
                  v-for="(_, path) in currentFiles"
                  :key="path"
                  @click="activeTab = path"
                  :class="[
                    'px-3 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap cursor-pointer',
                    activeTab === path ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'
                  ]"
                >{{ path }}</button>
              </div>
              <div class="p-6">
                <pre v-if="activeTab === 'skill-md'" class="whitespace-pre-wrap break-words text-sm leading-relaxed text-gray-700 font-mono bg-gray-50 rounded-xl p-4 border border-gray-100 overflow-y-auto m-0">{{ currentContent }}</pre>
                <pre v-else class="whitespace-pre-wrap break-words text-sm leading-relaxed text-gray-700 font-mono bg-gray-50 rounded-xl p-4 border border-gray-100 overflow-y-auto m-0">{{ currentFiles[activeTab] }}</pre>
              </div>
            </div>
            <div v-else class="p-12 text-center text-gray-400">
              <span class="material-icons-round text-4xl mb-2">description</span>
              <p>暂无版本</p>
            </div>
          </div>

          <!-- Files list -->
          <div v-if="Object.keys(currentFiles).length" class="bg-white rounded-2xl border border-gray-200 shadow-card">
            <div class="px-6 py-4 border-b border-gray-100">
              <h3 class="text-base font-semibold text-gray-900">附属文件 ({{ Object.keys(currentFiles).length }})</h3>
            </div>
            <div class="divide-y divide-gray-50">
              <div
                v-for="(content, path) in currentFiles"
                :key="path"
                @click="activeTab = path"
                class="flex items-center px-6 py-3 cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <span class="material-icons-round text-gray-400 text-[18px] mr-3">description</span>
                <span class="text-sm font-medium text-primary">{{ path }}</span>
                <span class="ml-auto text-xs text-gray-400 mr-3">{{ content.length }} 字符</span>
                <button
                  @click.stop="downloadAttachment(path, content)"
                  class="inline-flex items-center gap-1 px-2.5 py-1 border border-gray-300 rounded-md text-xs text-gray-700 hover:bg-gray-50 cursor-pointer"
                >
                  <span class="material-icons-round text-[14px]">download</span>
                  下载
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Info + Version History -->
        <div class="space-y-6">
          <!-- Info -->
          <div class="bg-white rounded-2xl border border-gray-200 shadow-card">
            <div class="px-6 py-4 border-b border-gray-100">
              <h3 class="text-base font-semibold text-gray-900">信息</h3>
            </div>
            <div class="px-6 py-4 space-y-3 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-500">可见性</span>
                <span
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                  :class="{
                    'bg-green-50 text-green-700': skill?.visibility === 'public',
                    'bg-amber-50 text-amber-700': skill?.visibility === 'team',
                    'bg-gray-100 text-gray-600': skill?.visibility === 'private',
                  }"
                >{{ skill?.visibility }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">创建者</span>
                <span class="text-gray-800 font-medium">{{ skill?.author_username || '—' }}</span>
              </div>
              <div class="flex justify-between items-start">
                <span class="text-gray-500">标签</span>
                <div class="flex flex-wrap gap-1 justify-end">
                  <span v-for="tag in skill?.tags" :key="tag" class="inline-flex px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-md">{{ tag }}</span>
                  <span v-if="!skill?.tags?.length" class="text-gray-400">无</span>
                </div>
              </div>
              <div class="flex justify-between"><span class="text-gray-500">最新版本</span><span class="text-gray-800 font-medium">{{ skill?.latest_version || '未发布' }}</span></div>
              <div class="flex justify-between"><span class="text-gray-500">文件数</span><span class="text-gray-800">{{ Object.keys(currentFiles).length }}</span></div>
              <div class="flex justify-between"><span class="text-gray-500">创建时间</span><span class="text-gray-800">{{ formatDate(skill?.created_at) }}</span></div>
              <div class="flex justify-between"><span class="text-gray-500">更新时间</span><span class="text-gray-800">{{ formatDate(skill?.updated_at) }}</span></div>
            </div>
          </div>

          <!-- Version History -->
          <div class="bg-white rounded-2xl border border-gray-200 shadow-card">
            <div class="px-6 py-4 border-b border-gray-100">
              <h3 class="text-base font-semibold text-gray-900">版本历史</h3>
            </div>
            <div v-if="versions.length" class="px-6 py-4">
              <div v-for="(v, i) in versions" :key="v.version" class="flex gap-3">
                <div class="flex flex-col items-center">
                  <div class="w-2.5 h-2.5 rounded-full bg-primary mt-1.5 shrink-0"></div>
                  <div v-if="i < versions.length - 1" class="w-px flex-1 bg-gray-200 my-1"></div>
                </div>
                <div class="pb-4">
                  <button @click="selectedVersion = v.version; loadVersion()" class="text-sm font-semibold text-primary hover:underline cursor-pointer bg-transparent border-none p-0">
                    v{{ v.version }}
                  </button>
                  <p v-if="v.changelog" class="text-xs text-gray-500 mt-0.5">{{ v.changelog }}</p>
                  <p class="text-xs text-gray-400 mt-0.5">{{ formatDate(v.created_at) }}</p>
                </div>
              </div>
            </div>
            <div v-else class="p-8 text-center text-gray-400">
              <span class="material-icons-round text-3xl mb-2">history</span>
              <p class="text-sm">暂无版本</p>
            </div>
          </div>

          <!-- Edit History -->
          <div class="bg-white rounded-2xl border border-gray-200 shadow-card">
            <div class="px-6 py-4 border-b border-gray-100">
              <h3 class="text-base font-semibold text-gray-900">编辑记录</h3>
            </div>
            <div v-if="editLogs.length" class="px-6 py-4">
              <div v-for="(log, i) in editLogs" :key="log.id" class="flex gap-3">
                <div class="flex flex-col items-center">
                  <div class="w-2.5 h-2.5 rounded-full bg-gray-400 mt-1.5 shrink-0"></div>
                  <div v-if="i < editLogs.length - 1" class="w-px flex-1 bg-gray-200 my-1"></div>
                </div>
                <div class="pb-4 min-w-0">
                  <p class="text-sm font-semibold text-gray-800">{{ logActionLabel(log.action) }}</p>
                  <p class="text-xs text-gray-500 mt-0.5">
                    {{ log.actor_username || '未知用户' }} · {{ formatDate(log.created_at) }}
                  </p>
                  <p v-if="log.target_path" class="text-xs text-gray-500 mt-0.5">文件: {{ log.target_path }}</p>
                  <p v-if="log.from_version || log.to_version" class="text-xs text-gray-500 mt-0.5">
                    版本: {{ log.from_version || '∅' }} → {{ log.to_version || '∅' }}
                  </p>
                  <div v-if="logDetailLines(log).length" class="mt-2 space-y-1">
                    <p
                      v-for="(line, idx) in logDetailLines(log)"
                      :key="`${log.id}-${idx}`"
                      class="text-xs text-gray-600 break-words"
                    >
                      {{ line }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="p-8 text-center text-gray-400">
              <span class="material-icons-round text-3xl mb-2">edit_note</span>
              <p class="text-sm">暂无编辑记录</p>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- New Version Modal -->
    <Modal v-model="showVersionDialog" title="发布新版本" max-width="700px">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">从文件夹导入</label>
          <FolderUpload @parsed="handleVersionFolderParsed" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">版本号 (semver)</label>
          <input v-model="versionForm.version" placeholder="1.0.0" class="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">变更说明</label>
          <textarea v-model="versionForm.changelog" rows="2" placeholder="本次更新内容..." class="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all resize-none"></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">SKILL.md 内容</label>
          <MdEditor v-model="versionForm.content" language="zh-CN" style="height: 400px" />
        </div>
      </div>
      <template #footer>
        <button @click="showVersionDialog = false" class="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-xl hover:bg-gray-50 cursor-pointer">取消</button>
        <button @click="publishVersion" :disabled="publishing" class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-xl hover:bg-primary-dark disabled:opacity-60 cursor-pointer">
          <span v-if="publishing" class="material-icons-round text-[16px] animate-spin align-middle mr-1">progress_activity</span>
          发布
        </button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from '../composables/useToast'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { getSkill, getVersions, getVersion, createVersion, subscribeSkill, unsubscribeSkill, getSkillEditLogs } from '../api'
import Modal from '../components/Modal.vue'
import FolderUpload from '../components/FolderUpload.vue'

const route = useRoute()
const toast = useToast()
const skillName = computed(() => route.params.name)

const loading = ref(false)
const skill = ref(null)
const versions = ref([])
const editLogs = ref([])
const selectedVersion = ref('')
const currentContent = ref('')
const currentFiles = ref({})
const activeTab = ref('skill-md')
const showVersionDialog = ref(false)
const publishing = ref(false)
const versionFiles = ref({})

const versionForm = ref({
  version: '',
  content: '',
  changelog: '',
})

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN')
}

function logActionLabel(action) {
  const labels = {
    skill_created: '创建 Skill',
    skill_updated: '更新 Skill 信息',
    version_published: '发布版本',
    skill_md_updated: '更新 SKILL.md',
    file_added: '新增文件',
    file_modified: '修改文件',
    file_deleted: '删除文件',
  }
  return labels[action] || action
}

function parseLogDetail(detail) {
  if (!detail) return null
  if (typeof detail === 'object') return detail
  try {
    return JSON.parse(detail)
  } catch {
    return { _raw: String(detail) }
  }
}

function formatDetailValue(value) {
  if (value === null || value === undefined || value === '') return '空'
  if (Array.isArray(value)) return value.length ? value.join(', ') : '空'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function logDetailLines(log) {
  const detail = parseLogDetail(log.detail)
  if (!detail) return []

  const fieldLabelMap = {
    display_name: '显示名称',
    description: '描述',
    visibility: '可见性',
    tags: '标签',
    category_id: '分类',
    team_id: '团队',
    team_ids: '可见团队',
  }

  if (log.action === 'skill_updated' && detail.changes && typeof detail.changes === 'object') {
    return Object.entries(detail.changes).map(([field, change]) => {
      const label = fieldLabelMap[field] || field
      return `${label}: ${formatDetailValue(change?.old)} -> ${formatDetailValue(change?.new)}`
    })
  }

  if (log.action === 'skill_created') {
    const lines = []
    if (detail.display_name) lines.push(`显示名称: ${detail.display_name}`)
    if (detail.visibility) lines.push(`可见性: ${detail.visibility}`)
    if (detail.team_ids !== undefined) lines.push(`可见团队: ${formatDetailValue(detail.team_ids)}`)
    if (detail.tags !== undefined) lines.push(`标签: ${formatDetailValue(detail.tags)}`)
    return lines
  }

  if (log.action === 'version_published') {
    const lines = []
    if (detail.changelog) lines.push(`变更说明: ${detail.changelog}`)
    if (detail.summary) {
      lines.push(`文件变更: +${detail.summary.files_added || 0} / ~${detail.summary.files_modified || 0} / -${detail.summary.files_deleted || 0}`)
      if (detail.summary.added_paths?.length) lines.push(`新增文件: ${detail.summary.added_paths.join(', ')}`)
      if (detail.summary.modified_paths?.length) lines.push(`修改文件: ${detail.summary.modified_paths.join(', ')}`)
      if (detail.summary.deleted_paths?.length) lines.push(`删除文件: ${detail.summary.deleted_paths.join(', ')}`)
      if (detail.summary.skill_md_changed) lines.push('SKILL.md: 已更新')
    }
    return lines
  }

  if (log.action === 'skill_md_updated') {
    return [`内容长度: ${detail.old_length || 0} -> ${detail.new_length || 0}`]
  }

  if (log.action === 'file_added') {
    return [`文件长度: 0 -> ${detail.new_length || 0}`]
  }

  if (log.action === 'file_modified') {
    return [`文件长度: ${detail.old_length || 0} -> ${detail.new_length || 0}`]
  }

  if (log.action === 'file_deleted') {
    return [`文件长度: ${detail.old_length || 0} -> 0`]
  }

  if (detail._raw) return [detail._raw]
  return [JSON.stringify(detail)]
}

function attachmentDownloadName(path) {
  if (!path) return 'attachment.txt'
  return path.replace(/[\\/]/g, '__')
}

function downloadAttachment(path, content) {
  try {
    const blob = new Blob([content ?? ''], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = attachmentDownloadName(path)
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch {
    toast.error('下载失败')
  }
}

async function toggleSubscription() {
  if (!skill.value) return
  try {
    if (skill.value.subscription_enabled) {
      await unsubscribeSkill(skillName.value)
      skill.value.is_subscribed = true
      skill.value.subscription_enabled = false
      toast.success('已取消订阅')
    } else {
      await subscribeSkill(skillName.value)
      skill.value.is_subscribed = true
      skill.value.subscription_enabled = true
      toast.success('已订阅')
    }
  } catch {
    toast.error('操作失败')
  }
}

async function loadSkill() {
  loading.value = true
  try {
    const [skillRes, versionsRes, logsRes] = await Promise.all([
      getSkill(skillName.value),
      getVersions(skillName.value),
      getSkillEditLogs(skillName.value, { limit: 100 }),
    ])
    skill.value = skillRes.data
    versions.value = versionsRes.data
    editLogs.value = logsRes.data || []

    if (versions.value.length > 0) {
      selectedVersion.value = versions.value[0].version
      await loadVersion()
    }
  } catch {
    toast.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function loadVersion() {
  if (!selectedVersion.value) return
  try {
    const res = await getVersion(skillName.value, selectedVersion.value)
    currentContent.value = res.data.content
    currentFiles.value = res.data.files || {}
    activeTab.value = 'skill-md'
  } catch {
    toast.error('加载版本失败')
  }
}

function handleVersionFolderParsed({ skillMdContent, files }) {
  versionFiles.value = files || {}
  if (skillMdContent) {
    versionForm.value.content = skillMdContent
    toast.success('已从文件夹导入内容')
  }
}

async function publishVersion() {
  if (!versionForm.value.version || !versionForm.value.content) {
    toast.warning('请填写版本号和内容')
    return
  }
  publishing.value = true
  try {
    const data = { ...versionForm.value }
    if (Object.keys(versionFiles.value).length > 0) {
      data.files = versionFiles.value
    }
    await createVersion(skillName.value, data)
    toast.success('发布成功')
    showVersionDialog.value = false
    versionForm.value = { version: '', content: '', changelog: '' }
    versionFiles.value = {}
    loadSkill()
  } catch (err) {
    toast.error(err.response?.data?.detail || '发布失败')
  } finally {
    publishing.value = false
  }
}

onMounted(loadSkill)

watch(skillName, (newName, oldName) => {
  if (newName && newName !== oldName) loadSkill()
})
</script>
