<template>
  <div class="folder-upload">
    <div class="upload-area" @click="triggerInput" @dragover.prevent @drop.prevent="handleDrop">
      <input
        ref="fileInput"
        type="file"
        webkitdirectory
        directory
        multiple
        style="display: none"
        @change="handleFiles"
      />
      <el-icon :size="40" style="color: #909399; margin-bottom: 8px"><UploadFilled /></el-icon>
      <p style="margin: 0; color: #606266">点击选择文件夹，或拖拽文件夹到此处</p>
      <p style="margin: 4px 0 0; color: #909399; font-size: 12px">支持包含 SKILL.md 的文件夹</p>
    </div>

    <div v-if="fileList.length > 0" style="margin-top: 12px">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px">
        <span style="font-size: 14px; font-weight: 500">已选文件 ({{ fileList.length }})</span>
        <el-button text type="danger" size="small" @click="clearFiles">清除</el-button>
      </div>
      <el-tag
        v-if="hasSkillMd"
        type="success"
        size="small"
        style="margin-bottom: 8px"
      >
        已识别 SKILL.md
      </el-tag>
      <el-tag
        v-else
        type="warning"
        size="small"
        style="margin-bottom: 8px"
      >
        未找到 SKILL.md
      </el-tag>
      <div class="file-list">
        <div v-for="f in fileList" :key="f.path" class="file-item">
          <el-icon style="margin-right: 4px; flex-shrink: 0"><Document /></el-icon>
          <span class="file-path">{{ f.path }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { UploadFilled, Document } from '@element-plus/icons-vue'

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
  // Files without extension but known names
  if (['makefile', 'dockerfile', 'license', 'readme'].includes(lower)) return true
  const ext = lower.split('.').pop()
  return TEXT_EXTENSIONS.has(ext)
}

function isHidden(pathPart) {
  return pathPart.startsWith('.')
}

function stripRootDir(relativePath) {
  // webkitRelativePath looks like "rootDir/subdir/file.txt"
  // We strip the root directory prefix
  const parts = relativePath.split('/')
  return parts.slice(1).join('/')
}

async function handleFiles(event) {
  const files = event.target.files
  if (!files || files.length === 0) return
  await processFiles(Array.from(files))
}

async function handleDrop(event) {
  const items = event.dataTransfer?.items
  if (!items) return
  // Fallback: use files directly
  const files = event.dataTransfer.files
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

    // Skip empty paths
    if (!strippedPath) continue

    // Skip hidden files/directories
    const pathParts = strippedPath.split('/')
    if (pathParts.some(isHidden)) continue

    // Skip non-text files
    const fileName = pathParts[pathParts.length - 1]
    if (!isTextFile(fileName)) continue

    // Read file content
    try {
      const content = await readFileAsText(file)
      results.push({ path: strippedPath, content })

      // Identify SKILL.md (at root level of the folder)
      if (fileName.toUpperCase() === 'SKILL.MD' && pathParts.length === 1) {
        skillMdContent = content
        foundSkillMd = true
      }
    } catch {
      // Skip files that can't be read as text
      console.warn(`Skipped file: ${strippedPath}`)
    }
  }

  fileList.value = results
  hasSkillMd.value = foundSkillMd

  // Collect non-SKILL.md files
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

<style scoped>
.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.upload-area:hover {
  border-color: #409eff;
}

.file-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 4px 0;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 4px 12px;
  font-size: 13px;
  color: #606266;
}

.file-item:hover {
  background-color: #f5f7fa;
}

.file-path {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
