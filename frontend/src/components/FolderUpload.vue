<template>
  <div>
    <div
      class="border-2 border-dashed border-gray-300 rounded-2xl p-6 text-center cursor-pointer transition-colors hover:border-primary flex flex-col items-center"
      @click="triggerInput"
      @dragover.prevent
      @drop.prevent="handleDrop"
    >
      <input
        ref="fileInput"
        type="file"
        webkitdirectory
        directory
        multiple
        class="hidden"
        @change="handleFiles"
      />
      <span class="material-icons-round text-[40px] text-gray-400 mb-2">cloud_upload</span>
      <p class="text-sm text-gray-600 m-0">点击选择文件夹，或拖拽文件夹到此处</p>
      <p class="text-xs text-gray-400 mt-1 m-0">支持包含 SKILL.md 的文件夹</p>
    </div>

    <div v-if="fileList.length > 0" class="mt-3">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700">已选文件 ({{ fileList.length }})</span>
        <button @click="clearFiles" class="text-xs text-danger hover:underline cursor-pointer bg-transparent border-none">清除</button>
      </div>

      <span
        v-if="hasSkillMd"
        class="inline-flex items-center gap-1 px-2 py-0.5 bg-green-50 text-green-700 text-xs font-medium rounded-md mb-2"
      >
        <span class="material-icons-round text-[14px]">check_circle</span>
        已识别 SKILL.md
      </span>
      <span
        v-else
        class="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-50 text-amber-700 text-xs font-medium rounded-md mb-2"
      >
        <span class="material-icons-round text-[14px]">warning</span>
        未找到 SKILL.md
      </span>

      <div class="border border-gray-200 rounded-xl max-h-[200px] overflow-y-auto">
        <div v-for="f in fileList" :key="f.path" class="flex items-center px-3 py-2 text-xs text-gray-600 hover:bg-gray-50">
          <span class="material-icons-round text-gray-400 text-[16px] mr-2 shrink-0">description</span>
          <span class="truncate">{{ f.path }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['parsed'])

const fileInput = ref(null)
const fileList = ref([])
const hasSkillMd = ref(false)

const TEXT_EXTENSIONS = new Set([
  'md', 'txt', 'yaml', 'yml', 'json', 'js', 'ts', 'py', 'sh', 'bash',
  'css', 'html', 'xml', 'toml', 'ini', 'cfg', 'conf', 'env', 'csv',
  'jsx', 'tsx', 'vue', 'svelte', 'rb', 'go', 'rs', 'java', 'c', 'cpp',
  'h', 'hpp', 'sql', 'graphql', 'proto', 'makefile', 'dockerfile',
])

function triggerInput() {
  fileInput.value?.click()
}

function isTextFile(name) {
  const lower = name.toLowerCase()
  if (['makefile', 'dockerfile', 'license', 'readme'].includes(lower)) return true
  const ext = lower.split('.').pop()
  return TEXT_EXTENSIONS.has(ext)
}

function isHidden(pathPart) {
  return pathPart.startsWith('.')
}

function stripRootDir(relativePath) {
  const parts = relativePath.split('/')
  return parts.slice(1).join('/')
}

async function handleFiles(event) {
  const files = event.target.files
  if (!files || files.length === 0) return
  await processFiles(Array.from(files))
}

async function handleDrop(event) {
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    await processFiles(Array.from(files))
  }
}

async function processFiles(files) {
  const results = []
  let skillMdContent = ''
  let foundSkillMd = false

  for (const file of files) {
    const relativePath = file.webkitRelativePath || file.name
    const strippedPath = stripRootDir(relativePath)

    if (!strippedPath) continue

    const pathParts = strippedPath.split('/')
    if (pathParts.some(isHidden)) continue

    const fileName = pathParts[pathParts.length - 1]
    if (!isTextFile(fileName)) continue

    try {
      const content = await readFileAsText(file)
      results.push({ path: strippedPath, content })

      if (fileName.toUpperCase() === 'SKILL.MD' && pathParts.length === 1) {
        skillMdContent = content
        foundSkillMd = true
      }
    } catch {
      console.warn(`Skipped file: ${strippedPath}`)
    }
  }

  fileList.value = results
  hasSkillMd.value = foundSkillMd

  const otherFiles = {}
  for (const f of results) {
    const fileName = f.path.split('/').pop()
    if (fileName.toUpperCase() !== 'SKILL.MD' || f.path.includes('/')) {
      otherFiles[f.path] = f.content
    }
  }

  emit('parsed', {
    skillMdContent,
    files: otherFiles,
  })
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error)
    reader.readAsText(file)
  })
}

function clearFiles() {
  fileList.value = []
  hasSkillMd.value = false
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  emit('parsed', { skillMdContent: '', files: {} })
}
</script>
