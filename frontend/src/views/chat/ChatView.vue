<template>
  <div class="h-[calc(100vh-7rem)] flex flex-col space-y-3">
    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 px-4 py-2.5 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-md bg-zinc-900 border border-zinc-800 text-zinc-100 flex items-center justify-center">
          <BotMessageSquare class="w-4 h-4" />
        </div>
        <div>
          <div class="text-xs font-semibold text-zinc-100 flex items-center gap-2">
            Homelab AI Agent Workspace
            <span class="font-mono text-[10px] px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
              {{ aiConfig?.model || 'Model not configured' }}
            </span>
          </div>
          <div class="text-[11px] text-zinc-500 flex items-center gap-1.5 mt-0.5">
            <span class="w-1.5 h-1.5 rounded-full" :class="aiStatus === 'online' ? 'bg-emerald-400' : 'bg-amber-400'"></span>
            <span class="font-mono">{{ aiConfig?.base_url || 'AI Server offline' }}</span>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          @click="showSettingsModal = true"
        >
          <template #prefix>
            <Settings class="w-3.5 h-3.5" />
          </template>
          Connection Settings
        </Button>
      </div>
    </div>

    <div ref="chatContainer" class="flex-1 rounded-lg bg-zinc-900/30 border border-zinc-800/80 overflow-y-auto p-4 space-y-4 min-h-0">
      <div v-if="!messages.length" class="h-full flex flex-col items-center justify-center text-center p-6 space-y-4 max-w-lg mx-auto">
        <div class="w-12 h-12 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 flex items-center justify-center">
          <Sparkles class="w-6 h-6" />
        </div>
        <div>
          <h3 class="text-sm font-semibold text-zinc-100">Homelab AI Assistant Ready</h3>
          <p class="text-xs text-zinc-400 mt-1 leading-relaxed">
            Connected to <strong>78 MCP Tools</strong> on this host. Ask to inspect hardware, check media status, query downloads, or inspect notes.
          </p>
        </div>

        <div class="w-full grid grid-cols-1 gap-1.5 pt-2 text-left">
          <button
            v-for="hint in promptHints"
            :key="hint"
            @click="useHint(hint)"
            class="p-2.5 rounded-md bg-zinc-900/80 hover:bg-zinc-850 border border-zinc-800 text-xs text-zinc-300 hover:text-white transition cursor-pointer flex items-center justify-between"
          >
            <span class="truncate pr-2">"{{ hint }}"</span>
            <ArrowRight class="w-3.5 h-3.5 text-zinc-500 shrink-0" />
          </button>
        </div>
      </div>

      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        class="flex gap-2.5"
        :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <div
          v-if="msg.role === 'assistant'"
          class="w-7 h-7 rounded-md bg-zinc-900 border border-zinc-800 text-zinc-300 flex items-center justify-center shrink-0 mt-0.5"
        >
          <BotMessageSquare class="w-3.5 h-3.5" />
        </div>

        <div class="space-y-2 max-w-2xl">
          <div v-if="msg.tool_executions && msg.tool_executions.length" class="space-y-1">
            <div
              v-for="(t, tIdx) in msg.tool_executions"
              :key="tIdx"
              class="px-2.5 py-1.5 rounded-md bg-zinc-950 border border-zinc-800 text-[11px] font-mono text-zinc-300 flex items-center justify-between"
            >
              <div class="flex items-center gap-1.5 text-zinc-400">
                <Wrench class="w-3 h-3 text-zinc-500" />
                <span>Called tool: <strong class="text-zinc-200">{{ t.tool }}</strong></span>
              </div>
              <Badge :variant="t.status === 'ok' ? 'success' : 'danger'" size="sm">
                {{ t.duration_ms }}ms
              </Badge>
            </div>
          </div>

          <div
            class="p-3 rounded-lg text-xs leading-relaxed"
            :class="msg.role === 'user'
              ? 'bg-zinc-100 text-zinc-950 font-medium'
              : 'bg-zinc-900/80 text-zinc-200 border border-zinc-800 whitespace-pre-wrap font-sans'"
          >
            {{ msg.content }}
          </div>
        </div>

        <div
          v-if="msg.role === 'user'"
          class="w-7 h-7 rounded-md bg-zinc-800 border border-zinc-700 text-zinc-200 flex items-center justify-center font-mono font-semibold text-xs shrink-0 mt-0.5"
        >
          U
        </div>
      </div>

      <div v-if="thinking" class="flex gap-2.5 items-center text-xs text-zinc-400 py-1">
        <div class="w-7 h-7 rounded-md bg-zinc-900 border border-zinc-800 text-zinc-400 flex items-center justify-center shrink-0">
          <Loader2 class="w-3.5 h-3.5 animate-spin" />
        </div>
        <span class="animate-pulse">Executing MCP tools &amp; generating response...</span>
      </div>
    </div>

    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 p-2 shrink-0">
      <form @submit.prevent="sendMessage" class="flex items-center gap-2">
        <input
          v-model="inputQuery"
          type="text"
          placeholder="Ask AI assistant (e.g. 'Inspect server hardware and torrent downloads')..."
          :disabled="thinking"
          class="flex-1 bg-transparent px-3 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none"
        />
        <Button
          type="submit"
          variant="primary"
          size="sm"
          :disabled="!inputQuery.trim() || thinking"
        >
          <template #prefix>
            <Send class="w-3 h-3" />
          </template>
          Send
        </Button>
      </form>
    </div>

    <Modal
      v-model="showSettingsModal"
      title="AI Server Connection Settings"
      maxWidth="md"
    >
      <form id="aiConfigForm" @submit.prevent="saveAiConfig" class="space-y-3.5">
        <Input
          v-model="configForm.base_url"
          label="AI Server Base URL"
          placeholder="e.g. http://host.docker.internal:11434/v1"
          required
          hint="Supports Ollama, vLLM, LM Studio, OpenRouter, or OpenAI."
        />

        <Input
          v-model="configForm.model"
          label="Model Name"
          placeholder="e.g. qwen2.5:14b, llama3.3:70b, gpt-4o-mini"
          required
        />

        <Input
          v-model="configForm.api_key"
          type="password"
          label="API Key (optional)"
          placeholder="Leave empty for local Ollama"
        />
      </form>

      <template #footer>
        <div class="flex items-center justify-between w-full">
          <Button
            variant="secondary"
            size="sm"
            :loading="testing"
            @click="testAiConnection"
          >
            Test Connection
          </Button>

          <div class="flex gap-2">
            <Button variant="ghost" size="sm" @click="showSettingsModal = false">Cancel</Button>
            <Button
              type="submit"
              form="aiConfigForm"
              variant="primary"
              size="sm"
              :loading="saving"
            >
              Save Settings
            </Button>
          </div>
        </div>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import {
  BotMessageSquare,
  Sparkles,
  Settings,
  ArrowRight,
  Send,
  Wrench,
  Loader2,
} from 'lucide-vue-next'
import { aiService } from '../../services/ai.service.js'
import { useToastStore } from '../../stores/toast.store.js'
import Button from '../../components/ui/Button.vue'
import Input from '../../components/ui/Input.vue'
import Modal from '../../components/ui/Modal.vue'
import Badge from '../../components/ui/Badge.vue'

const toast = useToastStore()
const aiConfig = ref(null)
const aiStatus = ref('offline')
const messages = ref([])
const inputQuery = ref('')
const thinking = ref(false)
const showSettingsModal = ref(false)
const saving = ref(false)
const testing = ref(false)
const chatContainer = ref(null)

const configForm = ref({
  base_url: 'http://host.docker.internal:11434/v1',
  model: 'qwen2.5:14b',
  api_key: '',
  system_prompt: '',
  enable_tools: true,
  max_tool_rounds: 5,
})

const promptHints = [
  'Inspect server hardware metrics and all 10 homelab services',
  'Is Dandadan anime series monitored and available on Sonarr or Jellyfin?',
  'Check Rclone Google Drive storage space and VFS cache status',
  'List all active torrent downloads on qBittorrent',
]

function useHint(hint) {
  inputQuery.value = hint
  sendMessage()
}

async function loadAiConfig() {
  try {
    const data = await aiService.getConfig()
    aiConfig.value = data
    configForm.value = { ...data }
    testAiConnection()
  } catch (err) {
    console.error('Failed to load AI config:', err)
  }
}

async function saveAiConfig() {
  saving.value = true
  try {
    await aiService.saveConfig(configForm.value)
    showSettingsModal.value = false
    toast.success('AI Server configuration saved!')
    await loadAiConfig()
  } catch (err) {
    toast.error(err.message || 'Failed to save AI config')
  } finally {
    saving.value = false
  }
}

async function testAiConnection() {
  testing.value = true
  try {
    const res = await aiService.testConnection()
    aiStatus.value = res.status === 'online' ? 'online' : 'offline'
    if (res.status === 'online') {
      toast.success(`AI Server connection successful (${res.latency_ms}ms)`)
    } else {
      toast.error(res.error || 'AI Server did not respond')
    }
  } catch (e) {
    aiStatus.value = 'offline'
    toast.error(e.message || 'AI Server test error')
  } finally {
    testing.value = false
  }
}

async function sendMessage() {
  const q = inputQuery.value.trim()
  if (!q || thinking.value) return

  messages.value.push({ role: 'user', content: q })
  inputQuery.value = ''
  thinking.value = true
  scrollToBottom()

  try {
    const res = await aiService.chatCompletion(
      messages.value.map(m => ({ role: m.role, content: m.content }))
    )
    messages.value.push({
      role: 'assistant',
      content: res.reply || 'No response received from AI.',
      tool_executions: res.tool_executions || [],
    })
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: `AI Server connection error: ${err.message}`,
    })
  } finally {
    thinking.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

onMounted(() => {
  loadAiConfig()
})
</script>
