<template>
  <div class="h-[calc(100vh-7rem)] flex flex-col space-y-3">
    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 p-3 space-y-2.5 shrink-0">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="relative w-full sm:w-96">
          <Input
            v-model="searchQuery"
            placeholder="Search tools by name or description..."
          >
            <template #prefix>
              <Search class="w-3.5 h-3.5 text-zinc-500" />
            </template>
          </Input>
        </div>
        <div class="text-xs text-zinc-400 flex items-center gap-2">
          <span>Found: <strong class="text-zinc-100 font-mono tabular-nums">{{ filteredTools.length }}</strong> / {{ totalTools }} tools</span>
          <Button
            variant="secondary"
            size="sm"
            :loading="loading"
            @click="loadTools"
          >
            <template #prefix>
              <RefreshCw class="w-3.5 h-3.5" />
            </template>
          </Button>
        </div>
      </div>

      <div class="flex items-center gap-1.5 overflow-x-auto pb-0.5 text-xs">
        <button
          @click="selectedCategory = ''"
          class="px-2.5 py-1 rounded-md shrink-0 transition cursor-pointer font-medium text-xs tabular-nums"
          :class="!selectedCategory ? 'bg-zinc-800 text-zinc-100' : 'bg-zinc-950 text-zinc-400 hover:text-zinc-200 border border-zinc-850'"
        >
          All ({{ totalTools }})
        </button>
        <button
          v-for="cat in categories"
          :key="cat.name"
          @click="selectedCategory = cat.name"
          class="px-2.5 py-1 rounded-md shrink-0 transition cursor-pointer font-medium text-xs tabular-nums"
          :class="selectedCategory === cat.name ? 'bg-zinc-800 text-zinc-100' : 'bg-zinc-950 text-zinc-400 hover:text-zinc-200 border border-zinc-850'"
        >
          {{ cat.name }} ({{ cat.count }})
        </button>
      </div>
    </div>

    <div class="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 min-h-0">
      <div class="lg:col-span-5 rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-y-auto divide-y divide-zinc-800/60 p-1.5 space-y-1">
        <button
          v-for="t in filteredTools"
          :key="t.name"
          @click="selectTool(t)"
          class="w-full text-left p-2.5 rounded-md transition cursor-pointer flex flex-col gap-1"
          :class="selectedTool?.name === t.name ? 'bg-zinc-800/90 text-zinc-100' : 'hover:bg-zinc-900/60 text-zinc-400'"
        >
          <div class="flex items-center justify-between gap-2">
            <span class="font-mono font-medium text-xs text-zinc-200 truncate">{{ t.name }}</span>
            <Badge variant="neutral" size="sm">{{ t.category }}</Badge>
          </div>
          <p class="text-[11px] text-zinc-400 line-clamp-2 leading-relaxed">
            {{ t.description || 'No description provided.' }}
          </p>
        </button>
      </div>

      <div class="lg:col-span-7 flex flex-col gap-3 overflow-y-auto">
        <template v-if="selectedTool">
          <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 p-4 space-y-3.5">
            <div class="flex items-start justify-between gap-3 border-b border-zinc-800/80 pb-3">
              <div>
                <h3 class="font-mono text-sm font-semibold text-zinc-100 flex items-center gap-2">
                  <Wrench class="w-3.5 h-3.5 text-zinc-400" />
                  {{ selectedTool.name }}
                </h3>
                <p class="text-xs text-zinc-400 mt-1 leading-relaxed">
                  {{ selectedTool.description }}
                </p>
              </div>
              <Badge variant="neutral" size="sm">{{ selectedTool.category }}</Badge>
            </div>

            <div class="space-y-2">
              <div class="flex items-center justify-between text-xs font-medium text-zinc-300">
                <span>Arguments (JSON)</span>
                <span class="text-[10px] text-zinc-500 font-mono">raw input</span>
              </div>

              <textarea
                v-model="argumentsJson"
                rows="6"
                class="w-full rounded-md bg-zinc-950 border border-zinc-800 p-3 font-mono text-xs text-zinc-200 focus:outline-none focus:border-zinc-500 leading-relaxed"
                placeholder="{}"
              ></textarea>
            </div>

            <div class="flex items-center justify-between pt-1">
              <Button
                variant="ghost"
                size="sm"
                @click="resetArguments"
              >
                Reset Default
              </Button>

              <Button
                variant="primary"
                size="sm"
                :loading="calling"
                @click="executeTool"
              >
                <template #prefix>
                  <Play class="w-3.5 h-3.5" />
                </template>
                Execute Tool
              </Button>
            </div>
          </div>

          <div v-if="callResult" class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 p-4 space-y-2.5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Response</span>
                <Badge :variant="callResult.status === 'ok' ? 'success' : 'danger'" size="sm">
                  {{ callResult.status === 'ok' ? 'SUCCESS' : 'ERROR' }}
                </Badge>
              </div>
              <div class="text-[11px] font-mono text-zinc-400 tabular-nums">
                Duration: <strong class="text-zinc-200">{{ callResult.duration_ms }} ms</strong>
              </div>
            </div>

            <pre class="w-full rounded-md bg-zinc-950 border border-zinc-800 p-3 font-mono text-xs text-zinc-300 overflow-x-auto max-h-96 leading-relaxed whitespace-pre-wrap">{{ formattedResult }}</pre>
          </div>
        </template>

        <div v-else class="h-full rounded-lg bg-zinc-900/20 border border-dashed border-zinc-800 flex flex-col items-center justify-center text-center p-8 text-zinc-500">
          <Wrench class="w-8 h-8 mb-2 opacity-30 text-zinc-400" />
          <h4 class="text-xs font-medium text-zinc-300">Select a tool to test</h4>
          <p class="text-[11px] max-w-xs mt-1">
            Choose any tool from the catalog to inspect arguments and run live executions.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Search,
  RefreshCw,
  Wrench,
  Play,
} from 'lucide-vue-next'
import { mcpService } from '../../services/mcp.service.js'
import { useToastStore } from '../../stores/toast.store.js'
import Button from '../../components/ui/Button.vue'
import Badge from '../../components/ui/Badge.vue'
import Input from '../../components/ui/Input.vue'

const toast = useToastStore()

const tools = ref([])
const totalTools = ref(0)
const categories = ref([])
const loading = ref(false)
const searchQuery = ref('')
const selectedCategory = ref('')

const selectedTool = ref(null)
const argumentsJson = ref('{}')
const calling = ref(false)
const callResult = ref(null)

const filteredTools = computed(() => {
  return tools.value.filter(t => {
    if (selectedCategory.value && t.category !== selectedCategory.value) {
      return false
    }
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      return (
        t.name.toLowerCase().includes(q) ||
        (t.description || '').toLowerCase().includes(q)
      )
    }
    return true
  })
})

const formattedResult = computed(() => {
  if (!callResult.value) return ''
  if (typeof callResult.value.result === 'object') {
    return JSON.stringify(callResult.value.result, null, 2)
  }
  return callResult.value.raw_text || String(callResult.value.result)
})

async function loadTools() {
  loading.value = true
  try {
    const data = await mcpService.getTools()
    tools.value = data.tools || []
    totalTools.value = data.total || 0
    categories.value = data.categories || []
    if (tools.value.length && !selectedTool.value) {
      selectTool(tools.value[0])
    }
  } catch (err) {
    toast.error(err.message || 'Failed to load tools')
  } finally {
    loading.value = false
  }
}

function selectTool(t) {
  selectedTool.value = t
  callResult.value = null
  resetArguments()
}

function resetArguments() {
  if (!selectedTool.value) return
  const schema = selectedTool.value.input_schema || {}
  const props = schema.properties || {}
  const defaults = {}

  for (const [key, prop] of Object.entries(props)) {
    if (prop.default !== undefined) {
      defaults[key] = prop.default
    } else if (prop.type === 'string') {
      defaults[key] = ''
    } else if (prop.type === 'integer' || prop.type === 'number') {
      defaults[key] = 0
    } else if (prop.type === 'boolean') {
      defaults[key] = false
    } else if (prop.type === 'array') {
      defaults[key] = []
    } else {
      defaults[key] = null
    }
  }
  argumentsJson.value = JSON.stringify(defaults, null, 2)
}

async function executeTool() {
  if (!selectedTool.value) return
  calling.value = true
  callResult.value = null

  let args = {}
  try {
    args = JSON.parse(argumentsJson.value || '{}')
  } catch (err) {
    toast.error('Invalid JSON arguments: ' + err.message)
    calling.value = false
    return
  }

  try {
    const res = await mcpService.callTool(selectedTool.value.name, args)
    callResult.value = res
    if (res.status === 'ok') {
      toast.success(`Executed ${selectedTool.value.name}`)
    } else {
      toast.error('Tool execution returned an error')
    }
  } catch (err) {
    toast.error(err.message || 'Execution error')
    callResult.value = {
      status: 'error',
      duration_ms: 0,
      result: { error: err.message },
      raw_text: err.message,
    }
  } finally {
    calling.value = false
  }
}

onMounted(() => {
  loadTools()
})
</script>
