<template>
  <div class="space-y-5">
    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 grid grid-cols-2 md:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-zinc-800/80">
      <div class="p-4">
        <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">Total Containers</div>
        <div class="mt-1 text-2xl font-semibold text-zinc-100 font-mono tabular-nums">{{ summary.total || 0 }}</div>
        <div class="text-[11px] text-zinc-500 mt-0.5">Docker Engine (/var/run/docker.sock)</div>
      </div>

      <div class="p-4">
        <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">Running</div>
        <div class="mt-1 text-2xl font-semibold text-emerald-400 font-mono tabular-nums">{{ summary.running || 0 }}</div>
        <div class="text-[11px] text-zinc-500 mt-0.5">Active daemon processes</div>
      </div>

      <div class="p-4">
        <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">Stopped / Exited</div>
        <div
          class="mt-1 text-2xl font-semibold font-mono tabular-nums"
          :class="summary.stopped > 0 ? 'text-rose-400' : 'text-zinc-400'"
        >
          {{ summary.stopped || 0 }}
        </div>
        <div class="text-[11px] text-zinc-500 mt-0.5">Inactive containers</div>
      </div>

      <div class="p-4">
        <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">Healthcheck Passed</div>
        <div class="mt-1 text-2xl font-semibold text-zinc-100 font-mono tabular-nums">{{ summary.healthy || 0 }}</div>
        <div class="text-[11px] text-zinc-500 mt-0.5">Containers with healthy status</div>
      </div>
    </div>

    <div v-if="errorMsg" class="rounded-lg bg-rose-500/10 border border-rose-500/25 px-4 py-3 text-xs text-rose-400">
      {{ errorMsg }}
    </div>

    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-hidden">
      <div class="p-3 border-b border-zinc-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="inline-flex items-center rounded-md bg-zinc-950 p-0.5 border border-zinc-800">
          <button
            v-for="tab in filterTabs"
            :key="tab.value"
            @click="stateFilter = tab.value"
            class="px-3 py-1 rounded text-xs font-medium transition cursor-pointer tabular-nums"
            :class="stateFilter === tab.value
              ? 'bg-zinc-800 text-zinc-100'
              : 'text-zinc-400 hover:text-zinc-200'"
          >
            {{ tab.label }}
            <span class="ml-1 text-[11px] text-zinc-500 font-mono">{{ tab.count }}</span>
          </button>
        </div>

        <div class="flex items-center gap-2">
          <div class="w-full sm:w-64">
            <Input
              v-model="searchQuery"
              placeholder="Filter container, image, port..."
            >
              <template #prefix>
                <Search class="w-3.5 h-3.5 text-zinc-500" />
              </template>
            </Input>
          </div>
          <Button variant="secondary" :loading="isLoading" @click="fetchContainers">
            <template #prefix>
              <RefreshCw class="w-3.5 h-3.5" />
            </template>
            Refresh
          </Button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-zinc-800/80 bg-zinc-950/50 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
              <th class="py-2.5 px-4">Container</th>
              <th class="py-2.5 px-4">Image</th>
              <th class="py-2.5 px-4">State</th>
              <th class="py-2.5 px-4">Uptime / Status</th>
              <th class="py-2.5 px-4">Published Ports</th>
              <th class="py-2.5 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60 text-xs">
            <tr
              v-for="c in filteredContainers"
              :key="c.id"
              class="hover:bg-zinc-900/60 transition-colors"
            >
              <td class="py-3 px-4 whitespace-nowrap">
                <div class="flex items-center gap-2.5">
                  <span
                    class="w-2 h-2 rounded-full shrink-0"
                    :class="c.state === 'running' ? 'bg-emerald-400' : 'bg-rose-400'"
                  ></span>
                  <div>
                    <div class="font-medium text-zinc-100 flex items-center gap-2">
                      <span>{{ c.name }}</span>
                      <span v-if="c.is_protected" class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                        core
                      </span>
                    </div>
                    <div class="text-[11px] font-mono text-zinc-500">{{ c.short_id }}</div>
                  </div>
                </div>
              </td>

              <td class="py-3 px-4 font-mono text-[11px] text-zinc-400 max-w-[240px] truncate" :title="c.image">
                {{ c.image }}
              </td>

              <td class="py-3 px-4 whitespace-nowrap">
                <div class="flex items-center gap-1.5">
                  <Badge :variant="c.state === 'running' ? 'success' : 'danger'" size="sm">
                    {{ c.state }}
                  </Badge>
                  <Badge v-if="c.health === 'healthy'" variant="neutral" size="sm">
                    healthy
                  </Badge>
                </div>
              </td>

              <td class="py-3 px-4 font-mono text-[11px] text-zinc-300 whitespace-nowrap tabular-nums">
                {{ c.status || c.state }}
              </td>

              <td class="py-3 px-4">
                <div v-if="c.ports && c.ports.length" class="flex flex-wrap gap-1">
                  <span
                    v-for="port in c.ports"
                    :key="port"
                    class="px-1.5 py-0.5 rounded bg-zinc-950 border border-zinc-800 font-mono text-[11px] text-zinc-300 tabular-nums"
                  >
                    {{ port }}
                  </span>
                </div>
                <span v-else class="text-[11px] font-mono text-zinc-600">host / internal</span>
              </td>

              <td class="py-3 px-4 text-right whitespace-nowrap">
                <div class="inline-flex items-center gap-1.5">
                  <Button variant="ghost" size="sm" @click="openLogsModal(c)">
                    <template #prefix>
                      <FileText class="w-3.5 h-3.5" />
                    </template>
                    Logs
                  </Button>

                  <Button
                    v-if="c.state !== 'running'"
                    variant="secondary"
                    size="sm"
                    :loading="actionLoadingId === `${c.id}:start`"
                    @click="handleAction(c, 'start')"
                  >
                    <template #prefix>
                      <Play class="w-3.5 h-3.5 text-emerald-400" />
                    </template>
                    Start
                  </Button>

                  <Button
                    variant="secondary"
                    size="sm"
                    :loading="actionLoadingId === `${c.id}:restart`"
                    @click="handleAction(c, 'restart')"
                  >
                    <template #prefix>
                      <RotateCw class="w-3.5 h-3.5" />
                    </template>
                    Restart
                  </Button>

                  <Button
                    v-if="c.state === 'running' && !c.is_protected"
                    variant="danger"
                    size="sm"
                    :loading="actionLoadingId === `${c.id}:stop`"
                    @click="handleAction(c, 'stop')"
                  >
                    <template #prefix>
                      <Square class="w-3.5 h-3.5" />
                    </template>
                    Stop
                  </Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <Modal
      v-model="logsModalOpen"
      :title="`Container Logs — ${selectedContainer?.name || ''}`"
      maxWidth="4xl"
    >
      <div class="space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <span class="text-xs text-zinc-400">Tail:</span>
            <select
              v-model.number="logsTail"
              @change="fetchLogs"
              class="h-8 rounded-md bg-zinc-950 border border-zinc-800 px-2.5 text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
            >
              <option :value="100">100 lines</option>
              <option :value="200">200 lines</option>
              <option :value="500">500 lines</option>
            </select>
          </div>

          <div class="flex items-center gap-2">
            <div class="w-56">
              <Input
                v-model="logsSearch"
                placeholder="Filter log output..."
              />
            </div>
            <Button variant="secondary" :loading="isLoadingLogs" @click="fetchLogs">
              <template #prefix>
                <RefreshCw class="w-3.5 h-3.5" />
              </template>
              Reload
            </Button>
          </div>
        </div>

        <pre
          ref="logsContainer"
          class="w-full h-[440px] overflow-auto rounded-md bg-zinc-950 border border-zinc-800 p-4 text-[11px] font-mono text-zinc-300 leading-relaxed whitespace-pre-wrap"
        >{{ filteredLogsText || (isLoadingLogs ? 'Loading container logs...' : 'No log lines returned.') }}</pre>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import {
  Play,
  Square,
  RotateCw,
  Search,
  RefreshCw,
  FileText,
} from 'lucide-vue-next'
import { dockerService } from '../../services/docker.service.js'
import { useToastStore } from '../../stores/toast.store.js'
import Badge from '../../components/ui/Badge.vue'
import Button from '../../components/ui/Button.vue'
import Input from '../../components/ui/Input.vue'
import Modal from '../../components/ui/Modal.vue'

const toast = useToastStore()

const isLoading = ref(false)
const errorMsg = ref('')
const containers = ref([])
const summary = ref({ total: 0, running: 0, stopped: 0, healthy: 0 })
const stateFilter = ref('all')
const searchQuery = ref('')
const actionLoadingId = ref('')

const logsModalOpen = ref(false)
const selectedContainer = ref(null)
const logsText = ref('')
const logsTail = ref(200)
const logsSearch = ref('')
const isLoadingLogs = ref(false)
const logsContainer = ref(null)

const filterTabs = computed(() => [
  { label: 'All', value: 'all', count: summary.value.total || 0 },
  { label: 'Running', value: 'running', count: summary.value.running || 0 },
  { label: 'Stopped', value: 'stopped', count: summary.value.stopped || 0 },
])

const filteredContainers = computed(() => {
  return containers.value.filter((c) => {
    if (stateFilter.value === 'running' && c.state !== 'running') return false
    if (stateFilter.value === 'stopped' && c.state === 'running') return false
    if (!searchQuery.value.trim()) return true
    const q = searchQuery.value.toLowerCase()
    const portsStr = (c.ports || []).join(' ').toLowerCase()
    return (
      c.name.toLowerCase().includes(q) ||
      c.image.toLowerCase().includes(q) ||
      portsStr.includes(q)
    )
  })
})

const filteredLogsText = computed(() => {
  if (!logsSearch.value.trim()) return logsText.value
  const q = logsSearch.value.toLowerCase()
  return logsText.value
    .split('\n')
    .filter((line) => line.toLowerCase().includes(q))
    .join('\n')
})

async function fetchContainers() {
  isLoading.value = true
  errorMsg.value = ''
  try {
    const res = await dockerService.getContainers(true)
    containers.value = res.containers || []
    summary.value = res.summary || { total: 0, running: 0, stopped: 0, healthy: 0 }
    if (res.available === false && res.error) {
      errorMsg.value = res.error
    }
  } catch (err) {
    errorMsg.value = err.message || 'Failed to load Docker containers.'
  } finally {
    isLoading.value = false
  }
}

async function handleAction(container, action) {
  actionLoadingId.value = `${container.id}:${action}`
  try {
    await dockerService.containerAction(container.name, action)
    toast.success(`Action '${action}' executed on ${container.name}`)
    await fetchContainers()
  } catch (err) {
    toast.error(err.message || `Error executing ${action} on ${container.name}`)
  } finally {
    actionLoadingId.value = ''
  }
}

async function openLogsModal(container) {
  selectedContainer.value = container
  logsModalOpen.value = true
  logsSearch.value = ''
  await fetchLogs()
}

async function fetchLogs() {
  if (!selectedContainer.value) return
  isLoadingLogs.value = true
  try {
    const res = await dockerService.getContainerLogs(selectedContainer.value.name, logsTail.value)
    logsText.value = res.logs || ''
    await nextTick()
    if (logsContainer.value) {
      logsContainer.value.scrollTop = logsContainer.value.scrollHeight
    }
  } catch (err) {
    logsText.value = `Error loading logs: ${err.message}`
  } finally {
    isLoadingLogs.value = false
  }
}

onMounted(() => {
  fetchContainers()
})
</script>
