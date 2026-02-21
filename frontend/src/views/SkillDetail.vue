<template>
  <div v-loading="loading">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <div>
        <el-page-header @back="$router.push('/skills')">
          <template #content>
            <span style="font-size: 20px; font-weight: 600">{{ skill?.display_name }}</span>
            <el-tag style="margin-left: 12px" size="small">{{ skill?.name }}</el-tag>
          </template>
        </el-page-header>
      </div>
      <div>
        <el-button @click="$router.push(`/skills/${skill?.name}/edit`)">编辑</el-button>
        <el-button type="primary" @click="showVersionDialog = true">发布新版本</el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>内容预览</span>
              <el-select v-model="selectedVersion" placeholder="选择版本" style="width: 150px" @change="loadVersion">
                <el-option v-for="v in versions" :key="v.version" :label="v.version" :value="v.version" />
              </el-select>
            </div>
          </template>

          <!-- Tab: SKILL.md + 附属文件 -->
          <el-tabs v-if="currentContent || Object.keys(currentFiles).length" v-model="activeTab">
            <el-tab-pane label="SKILL.md" name="skill-md">
              <div class="markdown-body" v-html="renderedContent"></div>
            </el-tab-pane>
            <el-tab-pane
              v-for="(content, path) in currentFiles"
              :key="path"
              :label="path"
              :name="path"
            >
              <pre class="file-content">{{ content }}</pre>
            </el-tab-pane>
          </el-tabs>

          <el-empty v-else description="暂无版本" />
        </el-card>

        <!-- 文件列表卡片 -->
        <el-card v-if="Object.keys(currentFiles).length" style="margin-top: 20px">
          <template #header>
            <span>附属文件 ({{ Object.keys(currentFiles).length }})</span>
          </template>
          <div
            v-for="(content, path) in currentFiles"
            :key="path"
            class="file-entry"
            @click="activeTab = path"
          >
            <el-icon style="margin-right: 6px"><Document /></el-icon>
            <span>{{ path }}</span>
            <span style="margin-left: auto; color: #909399; font-size: 12px">
              {{ content.length }} 字符
            </span>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card style="margin-bottom: 20px">
          <template #header>信息</template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="可见性">
              <el-tag :type="skill?.visibility === 'public' ? 'success' : 'info'" size="small">
                {{ skill?.visibility }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="标签">
              <el-tag v-for="tag in skill?.tags" :key="tag" size="small" style="margin-right: 4px">{{ tag }}</el-tag>
              <span v-if="!skill?.tags?.length" style="color: #909399">无</span>
            </el-descriptions-item>
            <el-descriptions-item label="最新版本">{{ skill?.latest_version || '未发布' }}</el-descriptions-item>
            <el-descriptions-item label="文件数">{{ Object.keys(currentFiles).length }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDate(skill?.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ formatDate(skill?.updated_at) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card>
          <template #header>版本历史</template>
          <el-timeline>
            <el-timeline-item
              v-for="v in versions"
              :key="v.version"
              :timestamp="formatDate(v.created_at)"
              placement="top"
            >
              <span style="font-weight: 500; cursor: pointer; color: #409eff" @click="selectedVersion = v.version; loadVersion()">
                v{{ v.version }}
              </span>
              <p v-if="v.changelog" style="margin: 4px 0 0; color: #606266; font-size: 13px">{{ v.changelog }}</p>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-if="!versions.length" description="暂无版本" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <!-- New Version Dialog -->
    <el-dialog v-model="showVersionDialog" title="发布新版本" width="700px">
      <el-form :model="versionForm" label-position="top">
        <el-form-item label="从文件夹导入">
          <FolderUpload @parsed="handleVersionFolderParsed" />
        </el-form-item>
        <el-form-item label="版本号 (semver)">
          <el-input v-model="versionForm.version" placeholder="1.0.0" />
        </el-form-item>
        <el-form-item label="变更说明">
          <el-input v-model="versionForm.changelog" type="textarea" :rows="2" placeholder="本次更新内容..." />
        </el-form-item>
        <el-form-item label="SKILL.md 内容">
          <MdEditor v-model="versionForm.content" language="zh-CN" style="height: 400px" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showVersionDialog = false">取消</el-button>
        <el-button type="primary" :loading="publishing" @click="publishVersion">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { getSkill, getVersions, getVersion, createVersion } from '../api'
import FolderUpload from '../components/FolderUpload.vue'

const route = useRoute()
const skillName = route.params.name

const loading = ref(false)
const skill = ref(null)
const versions = ref([])
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

const renderedContent = computed(() => {
  return `<pre style="white-space: pre-wrap; word-wrap: break-word; font-family: inherit;">${escapeHtml(currentContent.value)}</pre>`
})

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN')
}

async function loadSkill() {
  loading.value = true
  try {
    const [skillRes, versionsRes] = await Promise.all([
      getSkill(skillName),
      getVersions(skillName),
    ])
    skill.value = skillRes.data
    versions.value = versionsRes.data

    if (versions.value.length > 0) {
      selectedVersion.value = versions.value[0].version
      // Load full version detail (with files) for the latest version
      await loadVersion()
    }
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function loadVersion() {
  if (!selectedVersion.value) return
  try {
    const res = await getVersion(skillName, selectedVersion.value)
    currentContent.value = res.data.content
    currentFiles.value = res.data.files || {}
    activeTab.value = 'skill-md'
  } catch {
    ElMessage.error('加载版本失败')
  }
}

function handleVersionFolderParsed({ skillMdContent, files }) {
  versionFiles.value = files || {}

  if (skillMdContent) {
    versionForm.value.content = skillMdContent
    ElMessage.success('已从文件夹导入内容')
  }
}

async function publishVersion() {
  if (!versionForm.value.version || !versionForm.value.content) {
    ElMessage.warning('请填写版本号和内容')
    return
  }
  publishing.value = true
  try {
    const data = { ...versionForm.value }

    // Include imported files if any
    if (Object.keys(versionFiles.value).length > 0) {
      data.files = versionFiles.value
    }

    await createVersion(skillName, data)
    ElMessage.success('发布成功')
    showVersionDialog.value = false
    versionForm.value = { version: '', content: '', changelog: '' }
    versionFiles.value = {}
    loadSkill()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '发布失败')
  } finally {
    publishing.value = false
  }
}

onMounted(loadSkill)
</script>

<style scoped>
.file-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 13px;
  line-height: 1.6;
  padding: 12px;
  background: #fafafa;
  border-radius: 4px;
  border: 1px solid #ebeef5;
  margin: 0;
  max-height: 600px;
  overflow-y: auto;
}

.file-entry {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
  color: #409eff;
  transition: background 0.2s;
}

.file-entry:hover {
  background: #f5f7fa;
}

.file-entry + .file-entry {
  border-top: 1px solid #ebeef5;
}
</style>
