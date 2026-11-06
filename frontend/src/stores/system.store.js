import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { adminService } from '../services/admin.service.js'

export const useSystemStore = defineStore('system', () => {
  const overviewData = ref(null)
  const loading = ref(false)
  let timer = null

  const serverInfo = computed(() => overviewData.value?.server_info || {})
  const hardware = computed(() => overviewData.value?.stack?.server_hardware || {})
  const rclone = computed(() => overviewData.value?.stack?.rclone_gdrive || {})

  const services = computed(() => {
    const stack = overviewData.value?.stack || {}
    const keys = [
      'radarr',
      'sonarr',
      'lidarr',
      'prowlarr',
      'bazarr',
      'jellyfin',
      'jellyseerr',
      'qbittorrent',
      'triliumnext',
      'rclone_gdrive',
    ]
    const res = {}
    for (const k of keys) {
      if (stack[k]) res[k] = stack[k]
    }
    return res
  })

  async function fetchOverview() {
    loading.value = true
    try {
      const data = await adminService.getOverview()
      overviewData.value = data
    } catch (err) {
      console.error('Failed to fetch system overview:', err)
    } finally {
      loading.value = false
    }
  }

  function startPolling(intervalMs = 10000) {
    fetchOverview()
    if (!timer) {
      timer = setInterval(fetchOverview, intervalMs)
    }
  }

  function stopPolling() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  return {
    overviewData,
    loading,
    serverInfo,
    hardware,
    rclone,
    services,
    fetchOverview,
    startPolling,
    stopPolling,
  }
})

