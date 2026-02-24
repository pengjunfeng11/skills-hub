<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-2">集成指南</h1>
    <p class="text-gray-500 mb-6">配置 Claude Code 与 Skills Hub 的集成（Hook + MCP Server）</p>

    <!-- Steps indicator -->
    <div class="flex items-center gap-0 mb-8">
      <template v-for="(step, i) in steps" :key="i">
        <div
          @click="activeStep = i"
          class="flex items-center gap-2 cursor-pointer"
        >
          <div
            :class="[
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors',
              i <= activeStep ? 'bg-primary text-white' : 'bg-gray-200 text-gray-500'
            ]"
          >{{ i + 1 }}</div>
          <span :class="['text-sm font-medium', i <= activeStep ? 'text-gray-900' : 'text-gray-400']">{{ step }}</span>
        </div>
        <div v-if="i < steps.length - 1" :class="['flex-1 h-px mx-3', i < activeStep ? 'bg-primary' : 'bg-gray-200']"></div>
      </template>
    </div>

    <!-- Step 1: API Key -->
    <div v-show="activeStep >= 0" class="bg-white rounded-2xl border border-gray-200 shadow-card mb-4">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <span class="font-semibold text-gray-900">Step 1 - 获取 API Key</span>
        <button v-if="activeStep === 0" @click="activeStep = 1" class="text-sm text-primary font-medium hover:underline cursor-pointer bg-transparent border-none">下一步</button>
      </div>
      <div class="p-6">
        <p class="text-sm text-gray-600 mt-0">前往 <router-link to="/settings" class="text-primary font-medium">设置页面</router-link> 创建一个 API Key，用于 Claude Code 访问 Skills Hub。</p>
        <div class="mt-3 p-3 bg-blue-50 text-blue-700 text-sm rounded-xl flex items-start gap-2">
          <span class="material-icons-round text-[18px] mt-0.5">info</span>
          创建后请立即复制保存 API Key，关闭弹窗后将无法再次查看。
        </div>
      </div>
    </div>

    <!-- Step 2 -->
    <div v-show="activeStep >= 1" class="bg-white rounded-2xl border border-gray-200 shadow-card mb-4">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <span class="font-semibold text-gray-900">Step 2 - 一键配置（推荐）</span>
        <button v-if="activeStep === 1" @click="activeStep = 2" class="text-sm text-primary font-medium hover:underline cursor-pointer bg-transparent border-none">下一步</button>
      </div>
      <div class="p-6">
        <p class="text-sm text-gray-600 mt-0">在 Skills Hub 项目根目录下执行配置脚本：</p>
        <div class="mt-3 flex items-center justify-between bg-gray-900 text-gray-100 rounded-xl px-4 py-3 font-mono text-sm">
          <code>bash setup-claude.sh</code>
          <button @click="copy('bash setup-claude.sh')" class="text-gray-400 hover:text-white cursor-pointer bg-transparent border-none ml-3">
            <span class="material-icons-round text-[18px]">content_copy</span>
          </button>
        </div>
        <p class="text-sm text-gray-500 mt-3">脚本会交互式引导你完成 Hook、MCP Server 和环境变量的配置。</p>
      </div>
    </div>

    <!-- Step 3 -->
    <div v-show="activeStep >= 2" class="bg-white rounded-2xl border border-gray-200 shadow-card mb-4">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <span class="font-semibold text-gray-900">Step 3 - 手动配置（可选）</span>
        <button v-if="activeStep === 2" @click="activeStep = 3" class="text-sm text-primary font-medium hover:underline cursor-pointer bg-transparent border-none">下一步</button>
      </div>
      <div class="p-6">
        <p class="text-sm text-gray-600 mt-0 mb-4">如果你更喜欢手动配置，可以按以下步骤操作：</p>

        <!-- Sub-tabs -->
        <div class="flex border-b border-gray-200 gap-1 mb-4">
          <button
            v-for="tab in ['Hook 脚本', 'MCP Server', '环境变量']"
            :key="tab"
            @click="configTab = tab"
            :class="[
              'px-3 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer',
              configTab === tab ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'
            ]"
          >{{ tab }}</button>
        </div>

        <!-- Hook -->
        <div v-show="configTab === 'Hook 脚本'">
          <p class="text-sm text-gray-600 mb-2">创建 <code class="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">~/.claude/hooks/fetch-skills.sh</code>：</p>
          <div class="relative bg-gray-900 text-gray-100 rounded-xl px-4 py-3 font-mono text-xs leading-relaxed overflow-x-auto mb-4">
            <button @click="copy(hookScript)" class="absolute top-2 right-2 text-gray-400 hover:text-white cursor-pointer bg-transparent border-none">
              <span class="material-icons-round text-[16px]">content_copy</span>
            </button>
            <pre class="m-0 whitespace-pre-wrap">{{ hookScript }}</pre>
          </div>
          <p class="text-sm text-gray-600 mb-2">在 <code class="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">~/.claude/settings.json</code> 中添加：</p>
          <div class="relative bg-gray-900 text-gray-100 rounded-xl px-4 py-3 font-mono text-xs leading-relaxed overflow-x-auto">
            <button @click="copy(hookConfig)" class="absolute top-2 right-2 text-gray-400 hover:text-white cursor-pointer bg-transparent border-none">
              <span class="material-icons-round text-[16px]">content_copy</span>
            </button>
            <pre class="m-0 whitespace-pre-wrap">{{ hookConfig }}</pre>
          </div>
        </div>

        <!-- MCP -->
        <div v-show="configTab === 'MCP Server'">
          <p class="text-sm text-gray-600 mb-2">在 <code class="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">~/.claude.json</code> 中添加：</p>
          <div class="relative bg-gray-900 text-gray-100 rounded-xl px-4 py-3 font-mono text-xs leading-relaxed overflow-x-auto">
            <button @click="copy(mcpConfig)" class="absolute top-2 right-2 text-gray-400 hover:text-white cursor-pointer bg-transparent border-none">
              <span class="material-icons-round text-[16px]">content_copy</span>
            </button>
            <pre class="m-0 whitespace-pre-wrap">{{ mcpConfig }}</pre>
          </div>
        </div>

        <!-- Env -->
        <div v-show="configTab === '环境变量'">
          <p class="text-sm text-gray-600 mb-2">在 <code class="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">~/.bashrc</code> 或 <code class="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">~/.zshrc</code> 中添加：</p>
          <div class="relative bg-gray-900 text-gray-100 rounded-xl px-4 py-3 font-mono text-xs leading-relaxed overflow-x-auto">
            <button @click="copy(envConfig)" class="absolute top-2 right-2 text-gray-400 hover:text-white cursor-pointer bg-transparent border-none">
              <span class="material-icons-round text-[16px]">content_copy</span>
            </button>
            <pre class="m-0 whitespace-pre-wrap">{{ envConfig }}</pre>
          </div>
          <p class="text-sm text-gray-500 mt-3">添加后执行 <code class="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">source ~/.bashrc</code> 使其生效。</p>
        </div>
      </div>
    </div>

    <!-- Step 4 -->
    <div v-show="activeStep >= 3" class="bg-white rounded-2xl border border-gray-200 shadow-card">
      <div class="px-6 py-4 border-b border-gray-100">
        <span class="font-semibold text-gray-900">Step 4 - 验证配置</span>
      </div>
      <div class="p-6">
        <p class="text-sm text-gray-600 mt-0">执行以下命令验证 API 连接是否正常：</p>
        <div class="mt-3 relative bg-gray-900 text-gray-100 rounded-xl px-4 py-3 font-mono text-xs leading-relaxed overflow-x-auto">
          <button @click="copy(verifyCommand)" class="absolute top-2 right-2 text-gray-400 hover:text-white cursor-pointer bg-transparent border-none">
            <span class="material-icons-round text-[16px]">content_copy</span>
          </button>
          <pre class="m-0 whitespace-pre-wrap">{{ verifyCommand }}</pre>
        </div>
        <p class="text-sm text-gray-500 mt-3">如果返回 JSON 数据（Skills 列表），说明配置成功。</p>
        <div class="mt-3 p-3 bg-green-50 text-green-700 text-sm rounded-xl flex items-start gap-2">
          <span class="material-icons-round text-[18px] mt-0.5">check_circle</span>
          配置完成后，重启 Claude Code 即可使用 Skills Hub 集成。
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useToast } from '../composables/useToast'

const toast = useToast()
const activeStep = ref(0)
const configTab = ref('Hook 脚本')

const steps = ['获取 API Key', '一键配置', '手动配置', '验证']

const backendUrl = computed(() => {
  const loc = window.location
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
    toast.success('已复制')
  } catch {
    toast.error('复制失败，请手动复制')
  }
}
</script>
