import { api } from './api.js'

export const adminService = {
  async getOverview() {
    return api.get('/api/admin/overview')
  },

  async getTokens() {
    return api.get('/api/admin/tokens')
  },

  async createToken(payload) {
    return api.post('/api/admin/tokens', payload)
  },

  async revokeToken(tokenId) {
    return api.delete(`/api/admin/tokens/${tokenId}`)
  },

  async getClients() {
    return api.get('/api/admin/clients')
  },

  async createClient(payload) {
    return api.post('/api/admin/clients', payload)
  },

  async updateClient(clientId, payload) {
    return api.put(`/api/admin/clients/${clientId}`, payload)
  },

  async deleteClient(clientId) {
    return api.delete(`/api/admin/clients/${clientId}`)
  },

  async revokeSession(sessionId) {
    return api.delete(`/api/admin/sessions/${sessionId}`)
  },

  async updateProfile(payload) {
    return api.put('/api/admin/profile', payload)
  },

  async getUsers() {
    return api.get('/api/admin/users')
  },

  async createUser(payload) {
    return api.post('/api/admin/users', payload)
  },

  async updateUser(userId, payload) {
    return api.put(`/api/admin/users/${userId}`, payload)
  },

  async deleteUser(userId) {
    return api.delete(`/api/admin/users/${userId}`)
  },
}

