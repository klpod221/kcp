import { api } from './api.js'

export const aiService = {
  async getConfig() {
    return api.get('/api/admin/ai-config')
  },

  async saveConfig(payload) {
    return api.put('/api/admin/ai-config', payload)
  },

  async testConnection() {
    return api.post('/api/admin/ai-config/test')
  },

  async chatCompletion(messages, toolCategories = null) {
    return api.post('/api/admin/chat', {
      messages,
      tool_categories: toolCategories,
    })
  },
}

