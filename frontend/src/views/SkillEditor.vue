<template>
  <div>
    <el-page-header @back="$router.back()">
      <template #content>
        <span style="font-size: 20px; font-weight: 600">{{ isEdit ? '编辑 Skill' : '创建 Skill' }}</span>
      </template>
    </el-page-header>

    <!-- Folder Import (create mode only) -->
    <el-card v-if="!isEdit" style="margin-top: 20px">
      <template #header>从文件夹导入</template>
      <FolderUpload @parsed="handleFolderParsed" />
    </el-card>

    <el-card style="margin-top: 20px">
      <el-form :model="form" label-position="top" style="max-width: 600px">
        <el-form-item label="名称 (kebab-case)" :required="!isEdit">
          <el-input v-model="form.name" :disabled="isEdit" placeholder="my-skill-name" />
        </el-form-item>
        <el-form-item label="显示名称" required>
          <el-input v-model="form.display_name" placeholder="My Skill Name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="Skill 的功能描述..." />
        </el-form-item>
        <el-form-item label="可见性">
          <el-radio-group v-model="form.visibility">
            <el-radio value="public">Public</el-radio>
            <el-radio value="team">Team</el-radio>
            <el-radio value="private">Private</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="form.tags" multiple filterable allow-create placeholder="输入标签后回车" style="width: 100%" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">
            {{ isEdit ? '保存' : '创建' }}
          </el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Initial version for new skill -->
    <el-card v-if="!isEdit" style="margin-top: 20px">
      <template #header>初始版本（可选）</template>
      <el-form label-position="top" style="max-width: 100%">
        <el-form-item label="版本号">
          <el-input v-model="initialVersion.version" placeholder="0.1.0" style="max-width: 200px" />
        </el-form-item>
        <el-form-item label="SKILL.md 内容">
          <MdEditor v-model="initialVersion.content" language="zh-CN" style="height: 400px" />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { createSkill, createVersion, getSkill, updateSkill, parseSkillMd } from '../api'
import FolderUpload from '../components/FolderUpload.vue'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => route.name === 'SkillEdit')
const saving = ref(false)
const importedFiles = ref({})

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
    try {
      const res = await getSkill(route.params.name)
      Object.assign(form, {
        name: res.data.name,
        display_name: res.data.display_name,
        description: res.data.description || '',
        visibility: res.data.visibility,
        tags: res.data.tags || [],
      })
    } catch {
      ElMessage.error('加载失败')
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
      if (parsed.body) {
        initialVersion.content = skillMdContent
      }

      ElMessage.success('已从 SKILL.md 导入信息')
    } catch {
      // Even if parsing fails, still use the raw content
      initialVersion.content = skillMdContent
      ElMessage.warning('SKILL.md 解析失败，已导入原始内容')
    }
  }
}

async function handleSave() {
  if (!form.display_name) {
    ElMessage.warning('请填写显示名称')
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
      ElMessage.success('保存成功')
      router.push(`/skills/${form.name}`)
    } else {
      if (!form.name) {
        ElMessage.warning('请填写名称')
        saving.value = false
        return
      }
      await createSkill(form)

      // Create initial version if provided
      if (initialVersion.version && initialVersion.content) {
        const versionData = {
          version: initialVersion.version,
          content: initialVersion.content,
        }

        // Include imported files if any
        if (Object.keys(importedFiles.value).length > 0) {
          versionData.files = importedFiles.value
        }

        await createVersion(form.name, versionData)
      }

      ElMessage.success('创建成功')
      router.push(`/skills/${form.name}`)
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}
</script>
