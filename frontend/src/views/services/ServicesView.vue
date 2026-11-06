<template>
  <div class="space-y-6">
    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-hidden">
      <div class="px-4 py-3 border-b border-zinc-800/80 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <h2 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            Service Endpoints Directory
          </h2>
          <Badge variant="neutral" size="sm">10 endpoints</Badge>
        </div>
        <Button variant="secondary" size="sm" :loading="isLoading" @click="fetchDetails">
          <template #prefix>
            <RefreshCw class="w-3.5 h-3.5" />
          </template>
          Refresh Telemetry
        </Button>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 divide-y sm:divide-y-0 sm:divide-x divide-zinc-800/60">
        <a
          v-for="link in serviceLinks"
          :key="link.name"
          :href="link.url"
          target="_blank"
          rel="noopener noreferrer"
          class="p-3.5 hover:bg-zinc-900/80 transition group flex flex-col justify-between gap-1.5 border-b border-zinc-800/60"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-zinc-100 group-hover:text-white">
              {{ link.name }}
            </span>
            <ExternalLink class="w-3 h-3 text-zinc-500 group-hover:text-zinc-200 transition" />
          </div>
          <div class="text-[11px] text-zinc-400 truncate">{{ link.desc }}</div>
          <div class="text-[10px] font-mono text-zinc-500 truncate">{{ link.badge }}</div>
        </a>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-hidden flex flex-col">
        <div class="px-4 py-3 border-b border-zinc-800/80 flex items-center justify-between">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            Jellyseerr Media Requests
          </h3>
          <Badge variant="neutral" size="sm">{{ jellyseerrRequests.length }} recent</Badge>
        </div>

        <div v-if="jellyseerrRequests.length === 0" class="p-8 text-center text-xs text-zinc-500">
          No media requests recorded on Jellyseerr.
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="border-b border-zinc-800/80 bg-zinc-950/50 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
                <th class="py-2 px-4">ID / Type</th>
                <th class="py-2 px-4">Requester</th>
                <th class="py-2 px-4">Status</th>
                <th class="py-2 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-zinc-800/60 text-xs">
              <tr
                v-for="req in jellyseerrRequests"
                :key="req.id"
                class="hover:bg-zinc-900/60 transition-colors"
              >
                <td class="py-2.5 px-4 font-mono whitespace-nowrap">
                  <span class="text-zinc-200 font-medium">#{{ req.id }}</span>
                  <span class="text-zinc-500 ml-1.5">{{ req.media_type?.toUpperCase() || 'MEDIA' }}</span>
                  <div class="text-[10px] text-zinc-500">TMDB {{ req.tmdb_id }}</div>
                </td>
                <td class="py-2.5 px-4 text-zinc-300">
                  <div>{{ req.requested_by || 'User' }}</div>
                  <div class="text-[11px] text-zinc-500 font-mono">{{ req.media_status }}</div>
                </td>
                <td class="py-2.5 px-4 whitespace-nowrap">
                  <Badge
                    :variant="req.request_status === 'PENDING' ? 'warning' : (req.request_status === 'APPROVED' ? 'success' : 'neutral')"
                    size="sm"
                  >
                    {{ req.request_status }}
                  </Badge>
                </td>
                <td class="py-2.5 px-4 text-right whitespace-nowrap">
                  <div v-if="req.request_status === 'PENDING'" class="inline-flex items-center gap-1">
                    <Button
                      variant="primary"
                      size="sm"
                      :loading="reqActionId === `${req.id}:approve`"
                      @click="handleRequestAction(req.id, 'approve')"
                    >
                      <Check class="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      :loading="reqActionId === `${req.id}:decline`"
                      @click="handleRequestAction(req.id, 'decline')"
                    >
                      <X class="w-3.5 h-3.5" />
                    </Button>
                  </div>
                  <span v-else class="text-[11px] font-mono text-zinc-600">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-hidden flex flex-col">
        <div class="px-4 py-3 border-b border-zinc-800/80 flex items-center justify-between">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            Jellyfin Active Sessions
          </h3>
          <Badge :variant="playingSessions.length > 0 ? 'success' : 'neutral'" size="sm">
            {{ playingSessions.length }} playing
          </Badge>
        </div>

        <div v-if="jellyfinSessions.length === 0" class="p-8 text-center text-xs text-zinc-500">
          No active client sessions on Jellyfin.
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="border-b border-zinc-800/80 bg-zinc-950/50 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
                <th class="py-2 px-4">User &amp; Device</th>
                <th class="py-2 px-4">Stream Info</th>
                <th class="py-2 px-4 text-right">State</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-zinc-800/60 text-xs">
              <tr
                v-for="s in jellyfinSessions"
                :key="s.sessionId"
                class="hover:bg-zinc-900/60 transition-colors"
              >
                <td class="py-2.5 px-4">
                  <div class="font-medium text-zinc-100">{{ s.userName || 'Guest' }}</div>
                  <div class="text-[11px] text-zinc-500">{{ s.client }} · {{ s.deviceName }}</div>
                </td>
                <td class="py-2.5 px-4">
                  <div v-if="s.nowPlaying" class="text-zinc-200 truncate max-w-[220px]">
                    {{ s.nowPlaying.name }}
                  </div>
                  <div v-else class="text-zinc-500 text-[11px]">Idle</div>
                </td>
                <td class="py-2.5 px-4 text-right whitespace-nowrap">
                  <Badge :variant="s.nowPlaying ? 'success' : 'neutral'" size="sm">
                    {{ s.nowPlaying ? (s.nowPlaying.isPaused ? 'PAUSED' : 'PLAYING') : 'IDLE' }}
                  </Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-hidden flex flex-col">
        <div class="px-4 py-3 border-b border-zinc-800/80 flex items-center justify-between">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            *arr Download Queues (Radarr / Sonarr / Lidarr)
          </h3>
          <Badge variant="neutral" size="sm">{{ combinedQueues.length }} queued</Badge>
        </div>

        <div v-if="combinedQueues.length === 0" class="p-8 text-center text-xs text-zinc-500">
          All *arr download queues are currently empty.
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="border-b border-zinc-800/80 bg-zinc-950/50 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
                <th class="py-2 px-4">Release Title</th>
                <th class="py-2 px-4">Source</th>
                <th class="py-2 px-4">ETA</th>
                <th class="py-2 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-zinc-800/60 text-xs">
              <tr
                v-for="(item, idx) in combinedQueues"
                :key="idx"
                class="hover:bg-zinc-900/60 transition-colors"
              >
                <td class="py-2.5 px-4 font-medium text-zinc-100 max-w-[260px] truncate" :title="item.title">
                  {{ item.title }}
                </td>
                <td class="py-2.5 px-4 text-zinc-400 font-mono text-[11px]">
                  {{ item.source }}
                </td>
                <td class="py-2.5 px-4 text-zinc-400 font-mono text-[11px] tabular-nums">
                  {{ item.timeleft || '—' }}
                </td>
                <td class="py-2.5 px-4 text-right">
                  <Badge variant="neutral" size="sm">{{ item.status || 'queued' }}</Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-hidden flex flex-col">
        <div class="px-4 py-3 border-b border-zinc-800/80 flex items-center justify-between">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            Prowlarr Indexers &amp; Bazarr Subtitles
          </h3>
          <Badge variant="success" size="sm">{{ prowlarrIndexers.length }} indexers</Badge>
        </div>

        <div class="p-4 space-y-4">
          <div class="grid grid-cols-2 divide-x divide-zinc-800/80 rounded-md bg-zinc-950/60 border border-zinc-800/80">
            <div class="p-3">
              <div class="text-[11px] text-zinc-500 uppercase tracking-wider">Missing Movie Subs</div>
              <div class="text-xl font-semibold text-zinc-100 font-mono mt-1 tabular-nums">
                {{ details.bazarr?.wanted_movies?.total ?? 0 }}
              </div>
            </div>
            <div class="p-3">
              <div class="text-[11px] text-zinc-500 uppercase tracking-wider">Missing Episode Subs</div>
              <div class="text-xl font-semibold text-zinc-100 font-mono mt-1 tabular-nums">
                {{ details.bazarr?.wanted_episodes?.total ?? 0 }}
              </div>
            </div>
          </div>

          <div class="space-y-2">
            <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">Configured Indexers</div>
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="idx in prowlarrIndexers"
                :key="idx.id"
                class="px-2 py-1 rounded bg-zinc-950 border text-[11px] font-mono flex items-center gap-1.5"
                :class="idx.enable
                  ? 'text-zinc-200 border-zinc-800'
                  : 'text-zinc-500 border-zinc-900'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="idx.enable ? 'bg-emerald-400' : 'bg-zinc-600'"></span>
                {{ idx.name }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  RefreshCw,
  ExternalLink,
  Check,
  X,
} from 'lucide-vue-next'
import { systemService } from '../../services/system.service.js'
import { useToastStore } from '../../stores/toast.store.js'
import Badge from '../../components/ui/Badge.vue'
import Button from '../../components/ui/Button.vue'

const toast = useToastStore()

const isLoading = ref(false)
const reqActionId = ref('')
const details = ref({
  jellyfin: { sessions: [] },
  jellyseerr: { results: [], total: 0 },
  queues: { radarr: {}, sonarr: {}, lidarr: {} },
  prowlarr: { indexers: [] },
  bazarr: { wanted_movies: {}, wanted_episodes: {} },
  trilium: {},
})

const serviceLinks = [
  { name: 'Jellyfin', desc: 'Movies & Music Streaming', url: 'https://media.klpod221.com', badge: 'media.klpod221.com (:8096)' },
  { name: 'Jellyseerr', desc: 'Media Discovery & Requests', url: 'https://request.klpod221.com', badge: 'request.klpod221.com (:5055)' },
  { name: 'TriliumNext', desc: 'Personal Knowledge Base', url: 'https://notes.klpod221.com', badge: 'notes.klpod221.com' },
  { name: 'Radarr', desc: 'Movie Collection Manager', url: 'http://klpod221-server:7878', badge: 'klpod221-server:7878' },
  { name: 'Sonarr', desc: 'TV Series & Anime Manager', url: 'http://klpod221-server:8989', badge: 'klpod221-server:8989' },
  { name: 'Lidarr', desc: 'Lossless Music Manager', url: 'http://klpod221-server:8686', badge: 'klpod221-server:8686' },
  { name: 'Prowlarr', desc: 'Torrent Indexers Manager', url: 'http://klpod221-server:9696', badge: 'klpod221-server:9696' },
  { name: 'Bazarr', desc: 'Automated Subtitle Downloader', url: 'http://klpod221-server:6767', badge: 'klpod221-server:6767' },
  { name: 'qBittorrent', desc: 'Torrent Download Client', url: 'http://klpod221-server:8080', badge: 'klpod221-server:8080' },
  { name: 'Komepage', desc: 'Personal Dashboard & Portal', url: 'https://portal.klpod221.com', badge: 'portal.klpod221.com' },
]

const jellyseerrRequests = computed(() => details.value.jellyseerr?.results || [])
const jellyfinSessions = computed(() => details.value.jellyfin?.sessions || [])
const playingSessions = computed(() => jellyfinSessions.value.filter((s) => s.nowPlaying))
const prowlarrIndexers = computed(() => details.value.prowlarr?.indexers || [])

const combinedQueues = computed(() => {
  const r = (details.value.queues?.radarr?.records || []).map((x) => ({ ...x, source: 'Radarr' }))
  const s = (details.value.queues?.sonarr?.records || []).map((x) => ({ ...x, source: 'Sonarr' }))
  const l = (details.value.queues?.lidarr?.records || []).map((x) => ({ ...x, source: 'Lidarr' }))
  return [...r, ...s, ...l]
})

async function fetchDetails() {
  isLoading.value = true
  try {
    details.value = await systemService.getServicesDetails()
  } catch (err) {
    toast.error(err.message || 'Failed to fetch service details.')
  } finally {
    isLoading.value = false
  }
}

async function handleRequestAction(requestId, action) {
  reqActionId.value = `${requestId}:${action}`
  try {
    await systemService.handleJellyseerrRequest(requestId, action)
    toast.success(`Request #${requestId} ${action === 'approve' ? 'approved' : 'declined'}`)
    await fetchDetails()
  } catch (err) {
    toast.error(err.message || 'Failed to process Jellyseerr request')
  } finally {
    reqActionId.value = ''
  }
}

onMounted(() => {
  fetchDetails()
})
</script>
