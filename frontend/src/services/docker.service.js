import { api } from './api.js'

export const dockerService = {
  async getContainers(allContainers = true) {
    return api.get(`/api/admin/docker/containers?all_containers=${allContainers}`)
  },

  async containerAction(containerId, action) {
    return api.post(`/api/admin/docker/containers/${encodeURIComponent(containerId)}/${action}`)
  },

  async getContainerLogs(containerId, tail = 200) {
    return api.get(`/api/admin/docker/containers/${encodeURIComponent(containerId)}/logs?tail=${tail}`)
  },
}

