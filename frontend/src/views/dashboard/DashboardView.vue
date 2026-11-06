<template>
  <div class="space-y-6">
    <!-- Server Hardware Telemetry Grid (4 Dedicated Hardware Tiles) -->
    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-zinc-800/80">
      <!-- 1. CPU & Load -->
      <div class="p-4 flex flex-col justify-between gap-3">
        <div>
          <div class="flex items-center justify-between text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            <span>Processor &amp; Load</span>
            <span class="font-mono text-zinc-400 tabular-nums">{{ cpuTemp ? `${cpuTemp}°C` : '—' }}</span>
          </div>
          <div class="mt-2 flex items-baseline justify-between">
            <div class="text-2xl font-semibold text-zinc-100 font-mono tabular-nums">
              {{ hw.cpu?.usage_percent ?? 0 }}%
            </div>
            <div class="text-xs font-mono text-zinc-400 tabular-nums">
              {{ hw.cpu?.avg_frequency_mhz ? `${hw.cpu.avg_frequency_mhz} MHz` : '' }}
            </div>
          </div>
          <div class="mt-2 w-full h-1.5 rounded-sm bg-zinc-800 overflow-hidden">
            <div
              class="h-full transition-all duration-500"
              :class="(hw.cpu?.usage_percent || 0) > 80 ? 'bg-rose-400' : ((hw.cpu?.usage_percent || 0) > 50 ? 'bg-amber-400' : 'bg-zinc-200')"
              :style="{ width: `${hw.cpu?.usage_percent || 0}%` }"
            ></div>
          </div>
        </div>
        <div class="text-[11px] text-zinc-500 font-mono flex items-center justify-between pt-1 border-t border-zinc-800/60 tabular-nums">
          <span class="truncate max-w-[160px]" :title="hw.cpu?.model">{{ hw.cpu?.model || 'Intel Core i5-8265U' }}</span>
          <span>Load {{ loadAvgText }}</span>
        </div>
      </div>

      <!-- 2. Memory & Swap -->
      <div class="p-4 flex flex-col justify-between gap-3">
        <div>
          <div class="flex items-center justify-between text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            <span>System Memory</span>
            <span class="font-mono text-zinc-400 tabular-nums">{{ hw.memory?.ram_used ?? '—' }} / {{ hw.memory?.ram_total ?? '—' }}</span>
          </div>
          <div class="mt-2 flex items-baseline justify-between">
            <div class="text-2xl font-semibold text-zinc-100 font-mono tabular-nums">
              {{ hw.memory?.ram_usage_percent ?? 0 }}%
            </div>
            <div class="text-xs font-mono text-zinc-400 tabular-nums">
              Avail: {{ hw.memory?.ram_available ?? '—' }}
            </div>
          </div>
          <div class="mt-2 w-full h-1.5 rounded-sm bg-zinc-800 overflow-hidden">
            <div
              class="h-full bg-zinc-200 transition-all duration-500"
              :style="{ width: `${hw.memory?.ram_usage_percent || 0}%` }"
            ></div>
          </div>
        </div>
        <div class="text-[11px] text-zinc-500 font-mono flex items-center justify-between pt-1 border-t border-zinc-800/60 tabular-nums">
          <span>Swap {{ hw.memory?.swap_used ?? '0 B' }}</span>
          <span>Up {{ hw.uptime_and_power?.uptime_formatted || '—' }}</span>
        </div>
      </div>

      <!-- 3. GPU (Pure Hardware) -->
      <div class="p-4 flex flex-col justify-between gap-3">
        <div>
          <div class="flex items-center justify-between text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            <span>Graphics (iGPU &amp; dGPU)</span>
            <span class="font-mono text-emerald-400 tabular-nums">
              {{ igpuInfo?.current_frequency_mhz ? `${igpuInfo.current_frequency_mhz} MHz` : 'Active' }}
            </span>
          </div>
          <div class="mt-2.5 space-y-2 text-xs">
            <div class="flex items-center justify-between">
              <span class="text-zinc-300 font-medium truncate max-w-[170px]" title="Intel UHD Graphics 620">Intel UHD 620</span>
              <span class="font-mono text-zinc-400 text-[11px]">VA-API / QSync</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-zinc-300 font-medium truncate max-w-[170px]" title="NVIDIA GeForce MX250">NVIDIA MX250</span>
              <span class="font-mono text-[11px]" :class="dgpuInfo?.power_state === 'active' ? 'text-emerald-400' : 'text-zinc-500'">
                {{ dgpuInfo?.power_state || 'suspended' }} · 2GB
              </span>
            </div>
          </div>
        </div>
        <div class="text-[11px] text-zinc-500 font-mono flex items-center justify-between pt-1 border-t border-zinc-800/60 tabular-nums">
          <span>Hardware Transcoding</span>
          <span>Power: {{ hw.uptime_and_power?.power_supply?.ac_mains_connected ? 'AC Online' : 'Battery' }}</span>
        </div>
      </div>

      <!-- 4. Storage & Cloud VFS -->
      <div class="p-4 flex flex-col justify-between gap-3">
        <div>
          <div class="flex items-center justify-between text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            <span>Storage &amp; Rclone VFS</span>
            <span class="font-mono text-zinc-400 tabular-nums">{{ hw.system_disk?.used ?? '—' }} / {{ hw.system_disk?.total ?? '—' }}</span>
          </div>
          <div class="mt-2 flex items-baseline justify-between">
            <div class="text-2xl font-semibold text-zinc-100 font-mono tabular-nums">
              {{ hw.system_disk?.usage_percent ?? 0 }}%
            </div>
            <div class="text-xs font-mono text-emerald-400 tabular-nums">
              GDrive: {{ rclone.cloud_storage_used || 'Mounted' }}
            </div>
          </div>
          <div class="mt-2 w-full h-1.5 rounded-sm bg-zinc-800 overflow-hidden">
            <div
              class="h-full bg-zinc-200 transition-all duration-500"
              :style="{ width: `${hw.system_disk?.usage_percent || 0}%` }"
            ></div>
          </div>
        </div>
        <div class="text-[11px] text-zinc-500 font-mono flex items-center justify-between pt-1 border-t border-zinc-800/60 tabular-nums">
          <span>Cache {{ rclone.vfs_cache?.used_human || '0 B' }}</span>
          <span>{{ rclone.vfs_cache?.files_cached ?? 0 }} files</span>
        </div>
      </div>
    </div>

    <!-- MCP & AI Gateway Summary Strip (Dedicated Management Strip) -->
    <div class="rounded-lg bg-zinc-900/30 border border-zinc-800/80 p-3.5 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <span class="text-xs font-semibold uppercase tracking-wider text-zinc-300 flex items-center gap-2">
          <BotMessageSquare class="w-3.5 h-3.5 text-zinc-400" />
          <span>MCP &amp; AI Gateway</span>
        </span>
        <Badge variant="success" size="sm">Online</Badge>
      </div>

      <div class="flex flex-wrap items-center gap-3 text-xs font-mono tabular-nums">
        <router-link
          to="/tools"
          class="px-2.5 py-1 rounded-md bg-zinc-950 border border-zinc-800 text-zinc-300 hover:text-white hover:border-zinc-700 transition flex items-center gap-1.5"
        >
          <Wrench class="w-3 h-3 text-zinc-500" />
          <span>Tools Catalog: <strong class="text-emerald-400 font-medium">{{ systemStore.serverInfo.total_tools || 78 }}</strong></span>
        </router-link>

        <router-link
          to="/chat"
          class="px-2.5 py-1 rounded-md bg-zinc-950 border border-zinc-800 text-zinc-300 hover:text-white hover:border-zinc-700 transition flex items-center gap-1.5"
        >
          <BotMessageSquare class="w-3 h-3 text-zinc-500" />
          <span>AI Workspace: <strong class="text-zinc-200 font-medium">Ready</strong></span>
        </router-link>

        <router-link
          to="/tokens"
          class="px-2.5 py-1 rounded-md bg-zinc-950 border border-zinc-800 text-zinc-300 hover:text-white hover:border-zinc-700 transition flex items-center gap-1.5"
        >
          <KeyRound class="w-3 h-3 text-zinc-500" />
          <span>PAT: <strong class="text-zinc-200 font-medium">{{ systemStore.serverInfo.active_api_tokens || 0 }}</strong></span>
        </router-link>

        <router-link
          to="/clients"
          class="px-2.5 py-1 rounded-md bg-zinc-950 border border-zinc-800 text-zinc-300 hover:text-white hover:border-zinc-700 transition flex items-center gap-1.5"
        >
          <ShieldCheck class="w-3 h-3 text-zinc-500" />
          <span>OAuth: <strong class="text-zinc-200 font-medium">{{ systemStore.serverInfo.active_oauth_clients || 0 }}</strong> clients / <strong class="text-zinc-200 font-medium">{{ systemStore.serverInfo.active_oauth_sessions || 0 }}</strong> sess</span>
        </router-link>
      </div>
    </div>

    <!-- Homelab Services Table -->
    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-hidden">
      <div class="px-4 py-3 border-b border-zinc-800/80 flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <h2 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            Homelab Services Status
          </h2>
          <Badge variant="neutral" size="sm">
            {{ onlineServicesCount }}/{{ totalServicesCount }} online
          </Badge>
        </div>

        <div class="flex items-center gap-2">
          <router-link
            to="/services"
            class="text-xs text-zinc-400 hover:text-zinc-100 px-2.5 py-1 rounded-md hover:bg-zinc-800/60 transition"
          >
            Manage Services &rarr;
          </router-link>
          <Button
            variant="secondary"
            size="sm"
            :loading="systemStore.loading"
            @click="systemStore.fetchOverview"
          >
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
              <th class="py-2.5 px-4">Service</th>
              <th class="py-2.5 px-4">Status</th>
              <th class="py-2.5 px-4">Latency</th>
              <th class="py-2.5 px-4">Live Telemetry Summary</th>
              <th class="py-2.5 px-4 text-right">Internal Endpoint</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60 text-xs">
            <tr
              v-for="(svc, key) in systemStore.services"
              :key="key"
              class="hover:bg-zinc-900/60 transition-colors"
            >
              <td class="py-3 px-4 font-medium text-zinc-100 whitespace-nowrap">
                <div class="flex items-center gap-2.5">
                  <span
                    class="w-2 h-2 rounded-full shrink-0"
                    :class="svc?.status === 'online' ? 'bg-emerald-400' : 'bg-rose-400'"
                  ></span>
                  <span>{{ serviceNames[key]?.name || key }}</span>
                  <span class="text-[11px] text-zinc-500 font-normal">{{ serviceNames[key]?.role || '' }}</span>
                </div>
              </td>
              <td class="py-3 px-4 whitespace-nowrap">
                <Badge :variant="svc?.status === 'online' ? 'success' : 'danger'" size="sm">
                  {{ svc?.status === 'online' ? 'ONLINE' : 'OFFLINE' }}
                </Badge>
              </td>
              <td class="py-3 px-4 font-mono text-zinc-400 whitespace-nowrap tabular-nums">
                {{ svc?.status === 'online' ? `${svc?.latency_ms ?? 0} ms` : '—' }}
              </td>
              <td class="py-3 px-4 text-zinc-300 font-mono text-[11px] tabular-nums">
                {{ formatServiceSummary(key, svc) }}
              </td>
              <td class="py-3 px-4 text-right font-mono text-[11px] text-zinc-500 whitespace-nowrap">
                {{ svc?.url || '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import {
  RefreshCw,
  BotMessageSquare,
  Wrench,
  KeyRound,
  ShieldCheck,
} from 'lucide-vue-next'
import { useSystemStore } from '../../stores/system.store.js'
import Badge from '../../components/ui/Badge.vue'
import Button from '../../components/ui/Button.vue'

const systemStore = useSystemStore()

const hw = computed(() => systemStore.hardware || {})
const rclone = computed(() => systemStore.rclone || {})

const cpuTemp = computed(() => hw.value.temperatures?.cpu_package_temp_c)
const loadAvgText = computed(() => {
  const la = hw.value.cpu?.load_average
  if (!la) return '—'
  return `${la['1m'] ?? '—'} / ${la['5m'] ?? '—'}`
})

const igpuInfo = computed(() => (hw.value.gpu?.gpus || [])[0] || null)
const dgpuInfo = computed(() => (hw.value.gpu?.gpus || [])[1] || null)

const totalServicesCount = computed(() => Object.keys(systemStore.services || {}).length)
const onlineServicesCount = computed(() =>
  Object.values(systemStore.services || {}).filter((s) => s?.status === 'online').length
)

const serviceNames = {
  radarr: { name: 'Radarr', role: 'Movies' },
  sonarr: { name: 'Sonarr', role: 'Series & Anime' },
  lidarr: { name: 'Lidarr', role: 'Music' },
  prowlarr: { name: 'Prowlarr', role: 'Indexers' },
  bazarr: { name: 'Bazarr', role: 'Subtitles' },
  jellyfin: { name: 'Jellyfin', role: 'Media Streaming' },
  jellyseerr: { name: 'Jellyseerr', role: 'Requests' },
  qbittorrent: { name: 'qBittorrent', role: 'BitTorrent' },
  triliumnext: { name: 'TriliumNext', role: 'Knowledge Base' },
  rclone_gdrive: { name: 'Rclone VFS', role: 'Google Drive' },
}

function formatServiceSummary(key, svc) {
  if (!svc || svc.status !== 'online') {
    return svc?.error ? `Error: ${svc.error}` : 'Unreachable'
  }
  switch (key) {
    case 'radarr':
      return `${svc.movies_count ?? 0} movies (${svc.monitored_movies ?? 0} monitored) · Queue: ${svc.download_queue_count ?? 0}`
    case 'sonarr':
      return `${svc.series_count ?? 0} series (${svc.episodes_count ?? 0} episodes) · Queue: ${svc.download_queue_count ?? 0}`
    case 'lidarr':
      return `${svc.artists_count ?? 0} artists · Queue: ${svc.download_queue_count ?? 0}`
    case 'prowlarr':
      return `${svc.enabled_indexers ?? 0}/${svc.total_indexers ?? 0} active indexers`
    case 'bazarr':
      return `Missing subs: ${svc.missing_movie_subtitles ?? 0} movies, ${svc.missing_episode_subtitles ?? 0} episodes`
    case 'jellyfin':
      return `v${svc.version || ''} · ${svc.currently_playing_count ?? 0} active streams`
    case 'jellyseerr':
      return `${svc.pending_requests ?? 0} pending requests (${svc.total_requests ?? 0} total)`
    case 'qbittorrent':
      return `${svc.active_torrents ?? 0} active · DL ${svc.download_speed_human ?? '0 B/s'} · UL ${svc.upload_speed_human ?? '0 B/s'}`
    case 'triliumnext':
      return `ETAPI v${svc.app_version || ''}`
    case 'rclone_gdrive':
      return `Cloud ${svc.cloud_storage_used || '—'} · Cache ${svc.vfs_cache?.used_human || '0 B'}`
    default:
      return 'Healthy'
  }
}

onMounted(() => {
  systemStore.startPolling(10000)
})

onUnmounted(() => {
  systemStore.stopPolling()
})
</script>
