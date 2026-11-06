<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2 text-xs">
        <span
          class="w-2 h-2 rounded-full"
          :class="livePolling ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-600'"
        ></span>
        <span class="text-zinc-300 font-medium">
          {{ livePolling ? 'Real-time I/O stream active (2s interval)' : 'Real-time stream paused' }}
        </span>
      </div>

      <div class="flex items-center gap-2">
        <Button
          :variant="livePolling ? 'primary' : 'secondary'"
          size="sm"
          @click="toggleLivePolling"
        >
          <template #prefix>
            <Activity class="w-3.5 h-3.5" />
          </template>
          {{ livePolling ? 'Live Stream: ON' : 'Live Stream: OFF' }}
        </Button>

        <Button
          variant="secondary"
          size="sm"
          :loading="isRefreshingVfs"
          @click="handleRefreshVfs"
        >
          <template #prefix>
            <Cloud class="w-3.5 h-3.5" />
          </template>
          Sync Rclone VFS
        </Button>

        <Button variant="secondary" size="sm" :loading="isLoading" @click="fetchTransfers">
          <template #prefix>
            <RefreshCw class="w-3.5 h-3.5" />
          </template>
          Refresh
        </Button>
      </div>
    </div>

    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-zinc-800/80">
      <div class="p-4 flex flex-col justify-between gap-2">
        <div class="flex items-center justify-between text-[11px] font-medium uppercase tracking-wider text-zinc-500">
          <span>Root Disk (/)</span>
          <span class="font-mono text-zinc-400 tabular-nums">{{ sysDisk.usage_percent || 0 }}%</span>
        </div>
        <div class="text-xl font-semibold text-zinc-100 font-mono tabular-nums">
          {{ sysDisk.free || '—' }} free
        </div>
        <div class="w-full h-1.5 rounded-sm bg-zinc-800 overflow-hidden">
          <div
            class="h-full bg-zinc-200 transition-all duration-300"
            :style="{ width: `${sysDisk.usage_percent || 0}%` }"
          ></div>
        </div>
        <div class="text-[11px] text-zinc-500 font-mono tabular-nums">
          Used {{ sysDisk.used || '—' }} of {{ sysDisk.total || '—' }}
        </div>
      </div>

      <div class="p-4 flex flex-col justify-between gap-2">
        <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
          Block Device I/O
        </div>
        <div class="space-y-1.5 font-mono text-xs tabular-nums">
          <div class="flex items-center justify-between">
            <span class="text-zinc-400">Disk Read</span>
            <span class="text-zinc-100 font-medium">{{ sysIo.disk_read_speed || '0 B/s' }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-zinc-400">Disk Write</span>
            <span class="text-zinc-100 font-medium">{{ sysIo.disk_write_speed || '0 B/s' }}</span>
          </div>
        </div>
        <div class="text-[11px] text-zinc-500 font-mono">Host NVMe / SATA throughput</div>
      </div>

      <div class="p-4 flex flex-col justify-between gap-2">
        <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
          Network Interface
        </div>
        <div class="space-y-1.5 font-mono text-xs tabular-nums">
          <div class="flex items-center justify-between">
            <span class="text-zinc-400">Ingress (RX)</span>
            <span class="text-emerald-400 font-medium">{{ sysIo.net_rx_speed || '0 B/s' }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-zinc-400">Egress (TX)</span>
            <span class="text-zinc-200 font-medium">{{ sysIo.net_tx_speed || '0 B/s' }}</span>
          </div>
        </div>
        <div class="text-[11px] text-zinc-500 font-mono">Host network interface</div>
      </div>

      <div class="p-4 flex flex-col justify-between gap-2">
        <div class="flex items-center justify-between text-[11px] font-medium uppercase tracking-wider text-zinc-500">
          <span>Rclone VFS Cache</span>
          <span class="font-mono text-zinc-400 tabular-nums">{{ rclone.speed || '0 B/s' }}</span>
        </div>
        <div class="text-xl font-semibold text-zinc-100 font-mono tabular-nums">
          {{ rclone.vfs_cache?.bytes_used || '0 B' }}
        </div>
        <div class="text-[11px] text-zinc-500 font-mono flex items-center justify-between pt-1 border-t border-zinc-800/60 tabular-nums">
          <span>Files: {{ rclone.vfs_cache?.files_in_cache ?? 0 }}</span>
          <span>Upload Queue: {{ rclone.vfs_cache?.uploads_queued ?? 0 }}</span>
        </div>
      </div>
    </div>

    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-hidden">
      <div class="px-4 py-3 border-b border-zinc-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-center gap-2.5">
          <h2 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            qBittorrent Transfers
          </h2>
          <Badge :variant="qb.online ? 'success' : 'danger'" size="sm">
            {{ qb.online ? 'ONLINE' : 'OFFLINE' }}
          </Badge>
        </div>

        <div class="flex flex-wrap items-center gap-3 text-xs font-mono tabular-nums">
          <span class="px-2 py-1 rounded bg-zinc-950 border border-zinc-800 text-emerald-400">
            DL {{ qb.dl_speed || '0 B/s' }}
          </span>
          <span class="px-2 py-1 rounded bg-zinc-950 border border-zinc-800 text-zinc-300">
            UL {{ qb.ul_speed || '0 B/s' }}
          </span>
          <div class="inline-flex rounded-md bg-zinc-950 p-0.5 border border-zinc-800 font-sans">
            <button
              @click="qbTab = 'active'"
              class="px-2.5 py-1 rounded text-[11px] font-medium transition cursor-pointer"
              :class="qbTab === 'active' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-400 hover:text-zinc-200'"
            >
              Active ({{ qb.active_count || 0 }})
            </button>
            <button
              @click="qbTab = 'all'"
              class="px-2.5 py-1 rounded text-[11px] font-medium transition cursor-pointer"
              :class="qbTab === 'all' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-400 hover:text-zinc-200'"
            >
              All ({{ qb.total_count || 0 }})
            </button>
          </div>
        </div>
      </div>

      <div v-if="!qb.online" class="p-6 text-xs text-rose-400">
        Cannot connect to qBittorrent: {{ qb.error }}
      </div>

      <div v-else-if="displayedTorrents.length === 0" class="p-8 text-center text-xs text-zinc-500">
        No torrents matching the current filter.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-zinc-800/80 bg-zinc-950/50 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
              <th class="py-2.5 px-4">Torrent Name</th>
              <th class="py-2.5 px-4">Progress</th>
              <th class="py-2.5 px-4">Size</th>
              <th class="py-2.5 px-4">DL / UL</th>
              <th class="py-2.5 px-4">ETA</th>
              <th class="py-2.5 px-4">State</th>
              <th class="py-2.5 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60 text-xs">
            <tr
              v-for="t in displayedTorrents"
              :key="t.hash"
              class="hover:bg-zinc-900/60 transition-colors"
            >
              <td class="py-3 px-4 font-medium text-zinc-100 max-w-[320px] truncate" :title="t.name">
                {{ t.name }}
              </td>
              <td class="py-3 px-4 w-44">
                <div class="flex items-center gap-2.5 font-mono tabular-nums">
                  <div class="flex-1 h-1.5 rounded-sm bg-zinc-800 overflow-hidden">
                    <div
                      class="h-full bg-zinc-200 transition-all duration-300"
                      :style="{ width: `${t.progress_percent || 0}%` }"
                    ></div>
                  </div>
                  <span class="text-[11px] text-zinc-300 w-10 text-right">{{ t.progress_percent }}%</span>
                </div>
              </td>
              <td class="py-3 px-4 font-mono text-[11px] text-zinc-400 whitespace-nowrap tabular-nums">
                {{ t.completed }} / {{ t.total_size }}
              </td>
              <td class="py-3 px-4 font-mono text-[11px] whitespace-nowrap tabular-nums">
                <span class="text-emerald-400">{{ t.dlspeed }}</span>
                <span class="text-zinc-600 mx-1">/</span>
                <span class="text-zinc-400">{{ t.upspeed }}</span>
              </td>
              <td class="py-3 px-4 font-mono text-[11px] text-zinc-400 whitespace-nowrap tabular-nums">
                {{ t.eta }}
              </td>
              <td class="py-3 px-4 whitespace-nowrap">
                <Badge variant="neutral" size="sm">{{ t.state }}</Badge>
              </td>
              <td class="py-3 px-4 text-right whitespace-nowrap">
                <Button
                  v-if="t.state.toLowerCase().includes('paused') || t.state.toLowerCase().includes('stopped')"
                  variant="secondary"
                  size="sm"
                  @click="handleTorrentAction(t.hash, 'resume')"
                >
                  <template #prefix>
                    <Play class="w-3 h-3 text-emerald-400" />
                  </template>
                  Resume
                </Button>
                <Button
                  v-else
                  variant="secondary"
                  size="sm"
                  @click="handleTorrentAction(t.hash, 'pause')"
                >
                  <template #prefix>
                    <Pause class="w-3 h-3 text-amber-400" />
                  </template>
                  Pause
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-hidden">
      <div class="px-4 py-3 border-b border-zinc-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-center gap-2.5">
          <h2 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            Rclone Google Drive Active Transfers
          </h2>
          <Badge :variant="rclone.online ? 'success' : 'danger'" size="sm">
            {{ rclone.online ? 'ONLINE' : 'OFFLINE' }}
          </Badge>
        </div>

        <div class="flex items-center gap-2 text-xs font-mono tabular-nums">
          <span class="px-2 py-1 rounded bg-zinc-950 border border-zinc-800 text-zinc-300">
            Throughput: {{ rclone.speed || '0 B/s' }}
          </span>
          <span class="px-2 py-1 rounded bg-zinc-950 border border-zinc-800 text-zinc-400">
            Active: {{ rclone.active_count || 0 }}
          </span>
        </div>
      </div>

      <div v-if="!rclone.online" class="p-6 text-xs text-rose-400">
        Cannot connect to Rclone RC: {{ rclone.error }}
      </div>

      <div v-else-if="(rclone.transfers || []).length === 0" class="p-8 text-center text-xs text-zinc-500">
        No active cloud transfers on Google Drive VFS mount.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-zinc-800/80 bg-zinc-950/50 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
              <th class="py-2.5 px-4">File Name</th>
              <th class="py-2.5 px-4">Progress</th>
              <th class="py-2.5 px-4">Transferred</th>
              <th class="py-2.5 px-4">Speed</th>
              <th class="py-2.5 px-4 text-right">ETA</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60 text-xs">
            <tr
              v-for="item in rclone.transfers"
              :key="item.full_path"
              class="hover:bg-zinc-900/60 transition-colors"
            >
              <td class="py-3 px-4 font-medium text-zinc-100 max-w-[360px] truncate" :title="item.full_path">
                {{ item.name }}
              </td>
              <td class="py-3 px-4 w-44">
                <div class="flex items-center gap-2.5 font-mono tabular-nums">
                  <div class="flex-1 h-1.5 rounded-sm bg-zinc-800 overflow-hidden">
                    <div
                      class="h-full bg-zinc-200 transition-all duration-300"
                      :style="{ width: `${item.percentage || 0}%` }"
                    ></div>
                  </div>
                  <span class="text-[11px] text-zinc-300 w-10 text-right">{{ item.percentage }}%</span>
                </div>
              </td>
              <td class="py-3 px-4 font-mono text-[11px] text-zinc-400 whitespace-nowrap tabular-nums">
                {{ item.bytes_done }} / {{ item.size }}
              </td>
              <td class="py-3 px-4 font-mono text-[11px] text-emerald-400 whitespace-nowrap tabular-nums">
                {{ item.speed }}
              </td>
              <td class="py-3 px-4 text-right font-mono text-[11px] text-zinc-400 whitespace-nowrap tabular-nums">
                {{ item.eta }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  Activity,
  RefreshCw,
  Cloud,
  Play,
  Pause,
} from 'lucide-vue-next'
import { systemService } from '../../services/system.service.js'
import { useToastStore } from '../../stores/toast.store.js'
import Badge from '../../components/ui/Badge.vue'
import Button from '../../components/ui/Button.vue'

const toast = useToastStore()

const isLoading = ref(false)
const isRefreshingVfs = ref(false)
const livePolling = ref(true)
const qbTab = ref('active')
const transferData = ref({
  system: { disk: {}, io: {} },
  qbittorrent: { online: true, active_torrents: [], all_torrents: [] },
  rclone: { online: true, transfers: [], vfs_cache: {} },
})

let timerId = null

const sysDisk = computed(() => transferData.value.system?.disk || {})
const sysIo = computed(() => transferData.value.system?.io || {})
const qb = computed(() => transferData.value.qbittorrent || {})
const rclone = computed(() => transferData.value.rclone || {})

const displayedTorrents = computed(() => {
  if (qbTab.value === 'active') {
    return qb.value.active_torrents || []
  }
  return qb.value.all_torrents || []
})

async function fetchTransfers() {
  if (isLoading.value) return
  isLoading.value = true
  try {
    const res = await systemService.getTransfers()
    transferData.value = res
  } catch (err) {
    // Keep existing telemetry if a poll fails transiently
  } finally {
    isLoading.value = false
  }
}

function startPolling() {
  stopPolling()
  timerId = setInterval(() => {
    if (livePolling.value) {
      fetchTransfers()
    }
  }, 2000)
}

function stopPolling() {
  if (timerId) {
    clearInterval(timerId)
    timerId = null
  }
}

function toggleLivePolling() {
  livePolling.value = !livePolling.value
  if (livePolling.value) {
    fetchTransfers()
  }
}

async function handleTorrentAction(hash, action) {
  try {
    await systemService.torrentAction([hash], action)
    toast.success(`Torrent action '${action}' executed`)
    await fetchTransfers()
  } catch (err) {
    toast.error(err.message || 'Failed to execute torrent action')
  }
}

async function handleRefreshVfs() {
  isRefreshingVfs.value = true
  try {
    await systemService.refreshRclone(null, true)
    toast.success('Rclone VFS cache refreshed')
    await fetchTransfers()
  } catch (err) {
    toast.error(err.message || 'Failed to refresh Rclone VFS cache')
  } finally {
    isRefreshingVfs.value = false
  }
}

onMounted(() => {
  fetchTransfers()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>
