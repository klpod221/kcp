import { api } from './api.js'

export const authService = {
  async getMe() {
    return api.get('/api/admin/me')
  },

  async login(username, password, returnTo = '/') {
    return api.post('/login', {
      username,
      password,
      return_to: returnTo,
    })
  },

  async logout() {
    return api.post('/api/admin/logout')
  },

  async submitConsent(payload) {
    return api.post('/consent', payload)
  },
}

