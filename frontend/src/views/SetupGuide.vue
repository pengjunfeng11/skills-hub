<template>
  <div>
    <h2>集成指南</h2>
    <p style="color: #606266">配置 Claude Code 与 Skills Hub 的集成（Hook + MCP Server）</p>

    <el-steps :active="activeStep" finish-status="success" style="margin: 24px 0">
      <el-step title="获取 API Key" />
      <el-step title="一键配置" />
      <el-step title="手动配置" />
      <el-step title="验证" />
    </el-steps>

    <!-- Step 1: API Key -->
    <el-card v-show="activeStep >= 0" style="margin-bottom: 16px">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>Step 1 - 获取 API Key</span>
          <el-button text type="primary" @click="activeStep = 1" v-if="activeStep === 0">下一步</el-button>
        </div>
      </template>
      <p style="margin-top: 0">前往 <router-link to="/settings">设置页面</router-link> 创建一个 API Key，用于 Claude Code 访问 Skills Hub。</p>
      <el-alert type="info" :closable="false">
        创建后请立即复制保存 API Key，关闭弹窗后将无法再次查看。
      </el-alert>
    </el-card>

    <!-- Step 2: 一键配置 -->
    <el-card v-show="activeStep >= 1" style="margin-bottom: 16px">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>Step 2 - 一键配置（推荐）</span>
          <el-button text type="primary" @click="activeStep = 2" v-if="activeStep === 1">下一步</el-button>
        </div>
      </template>
      <p style="margin-top: 0">在 Skills Hub 项目根目录下执行配置脚本：</p>
      <div class="code-block">
        <code>bash setup-claude.sh</code>
        <el-button text size="small" @click="copy('bash setup-claude.sh')">
          <el-icon><CopyDocument /></el-icon>
        </el-button>
      </div>
      <p>脚本会交互式引导你完成 Hook、MCP Server 和环境变量的配置。</p>
    </el-card>

    <!-- Step 3: 手动配置 -->
    <el-card v-show="activeStep >= 2" style="margin-bottom: 16px">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>Step 3 - 手动配置（可选）</span>
          <el-button text type="primary" @click="activeStep = 3" v-if="activeStep === 2">下一步</el-button>
        </div>
      </template>
      <p style="margin-top: 0">如果你更喜欢手动配置，可以按以下步骤操作：</p>

      <el-tabs>
        <el-tab-pane label="Hook 脚本">
          <p>创建 <code>~/.claude/hooks/fetch-skills.sh</code>：</p>
          <div class="code-block">
            <pre>{{ hookScript }}</pre>
            <el-button text size="small" @click="copy(hookScript)">
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </div>

          <p>在 <code>~/.claude/settings.json</code> 中添加 Hook 配置：</p>
          <div class="code-block">
            <pre>{{ hookConfig }}</pre>
            <el-button text size="small" @click="copy(hookConfig)">
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </div>
        </el-tab-pane>

        <el-tab-pane label="MCP Server">
          <p>在 <code>~/.claude.json</code> 中添加 MCP Server 配置：</p>
          <div class="code-block">
            <pre>{{ mcpConfig }}</pre>
            <el-button text size="small" @click="copy(mcpConfig)">
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </div>
        </el-tab-pane>

        <el-tab-pane label="环境变量">
          <p>在 <code>~/.bashrc</code> 或 <code>~/.zshrc</code> 中添加：</p>
          <div class="code-block">
            <pre>{{ envConfig }}</pre>
            <el-button text size="small" @click="copy(envConfig)">
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </div>
          <p>添加后执行 <code>source ~/.bashrc</code> 使其生效。</p>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- Step 4: 验证 -->
    <el-card v-show="activeStep >= 3">
      <template #header>Step 4 - 验证配置</template>
      <p style="margin-top: 0">执行以下命令验证 API 连接是否正常：</p>
      <div class="code-block">
        <pre>{{ verifyCommand }}</pre>
        <el-button text size="small" @click="copy(verifyCommand)">
          <el-icon><CopyDocument /></el-icon>
        </el-button>
      </div>
      <p>如果返回 JSON 数据（Skills 列表），说明配置成功。</p>
      <el-alert type="success" :closable="false">
        配置完成后，重启 Claude Code 即可使用 Skills Hub 集成。
      </el-alert>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const activeStep = ref(0)

const backendUrl = computed(() => {
  const loc = window.location
  // 推断后端地址：同 host，端口 8000
  return `${loc.protocol}//${loc.hostname}:8000`
})

const hookScript = computed(() =>
`#!/usr/bin/env bash
SKILLS_HUB_URL="\${SKILLS_HUB_URL:-${backendUrl.value}}"
SKILLS_HUB_API_KEY="\${SKILLS_HUB_API_KEY:-}"

if [[ -z "$SKILLS_HUB_API_KEY" ]]; then exit 0; fi

INPUT=$(cat)
USER_MSG=$(echo "$INPUT" | jq -r '.messages[-1].content // empty' 2>/dev/null)
if [[ -z "$USER_MSG" ]]; then exit 0; fi

RESPONSE=$(curl -s --max-time 5 \\
  -H "Authorization: Bearer $SKILLS_HUB_API_KEY" \\
  -H "Content-Type: application/json" \\
  "\${SKILLS_HUB_URL}/plugin/match" \\
  -d "{\\"query\\": \\"$USER_MSG\\"}" 2>/dev/null)

SKILL=$(echo "$RESPONSE" | jq -r '.skill // empty' 2>/dev/null)
if [[ -n "$SKILL" ]]; then
  jq -n --arg s "$SKILL" '{"instructions": $s}'
else
  echo '{}'
fi`)

const hookConfig = computed(() =>
  JSON.stringify({
    hooks: {
      UserPromptSubmit: [{
        command: "bash ~/.claude/hooks/fetch-skills.sh",
        timeout: 10000
      }]
    }
  }, null, 2))

const mcpConfig = computed(() =>
  JSON.stringify({
    mcpServers: {
      "skills-hub": {
        type: "sse",
        url: `${backendUrl.value}/mcp`,
        headers: {
          Authorization: "Bearer <YOUR_API_KEY>"
        }
      }
    }
  }, null, 2))

const envConfig = computed(() =>
`# Skills Hub
export SKILLS_HUB_URL="${backendUrl.value}"
export SKILLS_HUB_API_KEY="<YOUR_API_KEY>"`)

const verifyCommand = computed(() =>
`curl -s -H "Authorization: Bearer \$SKILLS_HUB_API_KEY" \\
  "${backendUrl.value}/plugin/skills"`)

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}
</script>

<style scoped>
.code-block {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px 16px;
  margin: 8px 0 16px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
}

.code-block pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  flex: 1;
}

.code-block code {
  flex: 1;
}
</style>
