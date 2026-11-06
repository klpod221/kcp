import { api } from './api.js'

export const systemService = {
  async getTransfers() {
    return api.get('/api/admin/transfers')
  },

  async torrentAction(hashes, action, deleteFiles = false) {
    return api.post('/api/admin/transfers/torrent-action', {
      hashes,
      action,
      delete_files: deleteFiles,
    })
  },

  async refreshRclone(dirPath = null, recursive = true) {
    return api.post('/api/admin/transfers/rclone-refresh', {
      dir_path: dirPath,
      recursive,
    })
  },

  async getServicesDetails() {
    return api.get('/api/admin/services/details')
  },

  async handleJellyseerrRequest(requestId, action) {
    return api.post(`/api/admin/services/jellyseerr/${requestId}/${action}`)
  },
}

