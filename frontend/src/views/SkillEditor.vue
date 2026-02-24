<template>
  <div>
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <span class="material-icons-round text-primary text-4xl animate-spin">progress_activity</span>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-4">
          <button @click="$router.back()" class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer">
            <span class="material-icons-round">arrow_back</span>
          </button>
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ isEdit ? '编辑 Skill' : '创建 Skill' }}</h1>
            <p v-if="isEdit" class="text-sm text-gray-500 mt-0.5">更新 '{{ form.name }}' 的配置</p>
            <p v-else class="text-sm text-gray-500 mt-0.5">创建一个新的 Skill 并发布初始版本</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span v-if="isEdit && latestVersion" class="text-xs font-medium px-2.5 py-1 bg-green-50 text-green-700 border border-green-200 rounded-lg">v{{ latestVersion }}</span>
          <button @click="$router.back()" class="px-4 py-2.5 text-sm font-medium text-gray-700 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer">
            取消
          </button>
          <button @click="handleSave" :disabled="saving" class="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-primary rounded-xl hover:bg-primary-dark disabled:opacity-60 transition-colors cursor-pointer shadow-lg shadow-blue-500/20">
            <span v-if="saving" class="material-icons-round text-[16px] animate-spin">progress_activity</span>
            <span v-else class="material-icons-round text-[16px]">save</span>
            {{ isEdit ? '保存更改' : '创建 Skill' }}
          </button>
        </div>
      </div>

      <!-- Main Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column -->
        <div class="space-y-6 lg:col-span-1">
          <!-- General Information -->
          <section class="bg-white rounded-2xl border border-gray-200 shadow-card">
            <div class="px-6 py-4 border-b border-gray-100">
              <h3 class="text-base font-semibold text-gray-900 flex items-center">
                <span class="bg-blue-50 text-blue-600 p-1.5 rounded-lg mr-3">
                  <span class="material-icons-round text-[16px]">info</span>
                </span>
                基本信息
              </h3>
            </div>
            <div class="p-6 space-y-5">
              <div>
                <label class="block text-sm font-medium text-gray-500 mb-1.5">名称 (kebab-case) <span v-if="!isEdit" class="text-red-500">*</span></label>
                <input
                  v-model="form.name"
                  :disabled="isEdit"
                  placeholder="my-skill-name"
                  class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-shadow disabled:text-gray-400 disabled:cursor-not-allowed"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-500 mb-1.5">显示名称 <span class="text-red-500">*</span></label>
                <input
                  v-model="form.display_name"
                  placeholder="My Skill Name"
                  class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-shadow"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-500 mb-1.5">描述</label>
                <textarea
                  v-model="form.description"
                  rows="3"
                  placeholder="Skill 的功能描述..."
                  class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-shadow resize-none"
                ></textarea>
              </div>
            </div>
          </section>

          <!-- Configuration -->
          <section class="bg-white rounded-2xl border border-gray-200 shadow-card">
            <div class="px-6 py-4 border-b border-gray-100">
              <h3 class="text-base font-semibold text-gray-900 flex items-center">
                <span class="bg-purple-50 text-purple-600 p-1.5 rounded-lg mr-3">
                  <span class="material-icons-round text-[16px]">tune</span>
                </span>
                配置
              </h3>
            </div>
            <div class="p-6 space-y-5">
              <!-- Visibility -->
              <div>
                <label class="block text-sm font-medium text-gray-500 mb-3">可见性</label>
                <div class="space-y-2">
                  <label
                    v-for="opt in visibilityOptions"
                    :key="opt.value"
                    class="flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition-colors"
                    :class="form.visibility === opt.value ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50 border border-transparent'"
                  >
                    <input type="radio" v-model="form.visibility" :value="opt.value" class="text-primary accent-[#1A73E8]" />
                    <div>
                      <span class="text-sm font-medium text-gray-700">{{ opt.label }}</span>
                      <p class="text-xs text-gray-400 mt-0.5">{{ opt.desc }}</p>
                    </div>
                  </label>
                </div>
              </div>

              <!-- Tags -->
              <div>
                <label class="block text-sm font-medium text-gray-500 mb-1.5">标签</label>
                <TagInput v-model="form.tags" placeholder="输入标签后回车添加" />
              </div>
            </div>
          </section>

          <!-- Folder Import (create mode) -->
          <section v-if="!isEdit" class="bg-white rounded-2xl border border-gray-200 shadow-card">
            <div class="px-6 py-4 border-b border-gray-100">
              <h3 class="text-base font-semibold text-gray-900 flex items-center">
                <span class="bg-teal-50 text-teal-600 p-1.5 rounded-lg mr-3">
                  <span class="material-icons-round text-[16px]">folder_open</span>
                </span>
                文件夹导入
              </h3>
            </div>
            <div class="p-6">
              <FolderUpload @parsed="handleFolderParsed" />
            </div>
          </section>
        </div>

        <!-- Right Column: Editor -->
        <div class="lg:col-span-2 flex flex-col">
          <section class="bg-white rounded-2xl border border-gray-200 shadow-card flex flex-col flex-1 min-h-[600px]">
            <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <div class="flex items-center">
                <h3 class="text-base font-semibold text-gray-900 flex items-center mr-6">
                  <span class="bg-orange-50 text-orange-600 p-1.5 rounded-lg mr-3">
                    <span class="material-icons-round text-[16px]">code</span>
                  </span>
                  SKILL.md 内容
                </h3>
                <div v-if="!isEdit" class="flex bg-gray-100 rounded-lg p-1">
                  <button
                    @click="editorTab = 'edit'"
                    class="px-3 py-1 text-xs font-medium rounded-md transition-colors cursor-pointer"
                    :class="editorTab === 'edit' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'"
                  >编辑</button>
                  <button
                    @click="editorTab = 'preview'"
                    class="px-3 py-1 text-xs font-medium rounded-md transition-colors cursor-pointer"
                    :class="editorTab === 'preview' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'"
                  >预览</button>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <div v-if="!isEdit" class="flex items-center gap-2 mr-3">
                  <label class="text-xs text-gray-500">版本号</label>
                  <input
                    v-model="initialVersion.version"
                    placeholder="0.1.0"
                    class="w-24 px-2.5 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-mono focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                  />
                </div>
                <button
                  v-if="initialVersion.content || isEdit"
                  @click="copyContent"
                  class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors cursor-pointer"
                  title="复制"
                >
                  <span class="material-icons-round text-[18px]">content_copy</span>
                </button>
              </div>
            </div>

            <!-- Editor area for create mode -->
            <div v-if="!isEdit" class="flex-1 flex flex-col overflow-hidden">
              <template v-if="editorTab === 'edit'">
                <MdEditor
                  v-model="initialVersion.content"
                  language="zh-CN"
                  class="flex-1"
                  style="height: 100%; border: none; border-radius: 0 0 1rem 1rem;"
                  :toolbars="editorToolbars"
                />
              </template>
              <template v-else>
                <div class="flex-1 p-6 overflow-y-auto">
                  <pre v-if="initialVersion.content" class="whitespace-pre-wrap break-words text-sm leading-relaxed text-gray-700 font-mono bg-gray-50 rounded-xl p-4 border border-gray-100 m-0">{{ initialVersion.content }}</pre>
                  <div v-else class="flex flex-col items-center justify-center h-full text-gray-400">
                    <span class="material-icons-round text-4xl mb-2">description</span>
                    <p class="text-sm">暂无内容</p>
                  </div>
                </div>
              </template>
            </div>

            <!-- Info for edit mode (no editor, just version info) -->
            <div v-else class="flex-1 flex flex-col items-center justify-center p-8 text-gray-400">
              <span class="material-icons-round text-5xl mb-3">edit_note</span>
              <p class="text-sm text-center">编辑模式下仅修改元信息</p>
              <p class="text-xs mt-1 text-center">如需修改 SKILL.md 内容，请前往详情页发布新版本</p>
              <button
                @click="$router.push(`/skills/${form.name}`)"
                class="mt-4 inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary border border-primary/30 rounded-xl hover:bg-primary/5 transition-colors cursor-pointer"
              >
                <span class="material-icons-round text-[16px]">open_in_new</span>
                前往详情页
              </button>
            </div>
          </section>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '../composables/useToast'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { createSkill, createVersion, getSkill, updateSkill, parseSkillMd } from '../api'
import FolderUpload from '../components/FolderUpload.vue'
import TagInput from '../components/TagInput.vue'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const isEdit = computed(() => route.name === 'SkillEdit')
const saving = ref(false)
const loading = ref(false)
const importedFiles = ref({})
const editorTab = ref('edit')
const latestVersion = ref('')

const visibilityOptions = [
  { value: 'public', label: 'Public', desc: '所有人可见' },
  { value: 'team', label: 'Team', desc: '仅团队成员可见' },
  { value: 'private', label: 'Private', desc: '仅自己可见' },
]

const editorToolbars = [
  'bold', 'underline', 'italic', 'strikeThrough', '-',
  'title', 'sub', 'sup', 'quote', 'unorderedList', 'orderedList', '-',
  'codeRow', 'code', 'link', 'table', '-',
  'revoke', 'next', '=',
  'preview', 'fullscreen',
]

const form = reactive({
  name: '',
  display_name: '',
  description: '',
  visibility: 'public',
  tags: [],
})

const initialVersion = reactive({
  version: '0.1.0',
  content: '',
})

onMounted(async () => {
  if (isEdit.value) {
    loading.value = true
    try {
      const res = await getSkill(route.params.name)
      Object.assign(form, {
        name: res.data.name,
        display_name: res.data.display_name,
        description: res.data.description || '',
        visibility: res.data.visibility,
        tags: res.data.tags || [],
      })
      latestVersion.value = res.data.latest_version || ''
    } catch {
      toast.error('加载失败')
    } finally {
      loading.value = false
    }
  }
})

async function handleFolderParsed({ skillMdContent, files }) {
  importedFiles.value = files || {}
  if (skillMdContent) {
    try {
      const res = await parseSkillMd(skillMdContent)
      const parsed = res.data
      if (parsed.name) form.name = parsed.name
      if (parsed.display_name) form.display_name = parsed.display_name
      if (parsed.description) form.description = parsed.description
      if (parsed.tags && parsed.tags.length > 0) form.tags = parsed.tags
      if (parsed.version) initialVersion.version = parsed.version
      if (parsed.body) initialVersion.content = skillMdContent
      toast.success('已从 SKILL.md 导入信息')
    } catch {
      initialVersion.content = skillMdContent
      toast.warning('SKILL.md 解析失败，已导入原始内容')
    }
  }
}

async function handleSave() {
  if (!form.display_name) {
    toast.warning('请填写显示名称')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await updateSkill(form.name, {
        display_name: form.display_name,
        description: form.description,
        visibility: form.visibility,
        tags: form.tags,
      })
      toast.success('保存成功')
      router.push(`/skills/${form.name}`)
    } else {
      if (!form.name) {
        toast.warning('请填写名称')
        saving.value = false
        return
      }
      await createSkill(form)
      if (initialVersion.version && initialVersion.content) {
        const versionData = {
          version: initialVersion.version,
          content: initialVersion.content,
        }
        if (Object.keys(importedFiles.value).length > 0) {
          versionData.files = importedFiles.value
        }
        await createVersion(form.name, versionData)
      }
      toast.success('创建成功')
      router.push(`/skills/${form.name}`)
    }
  } catch (err) {
    toast.error(err.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

async function copyContent() {
  const text = isEdit.value ? '' : initialVersion.content
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    toast.success('已复制')
  } catch {
    toast.error('复制失败')
  }
}
</script>
