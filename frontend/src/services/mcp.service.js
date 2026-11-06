import { api } from './api.js'

export const mcpService = {
  async listTools() {
    return api.get('/api/admin/tools')
  },

  async getTools() {
    return api.get('/api/admin/tools')
  },

  async callTool(toolName, args = {}) {
    return api.post(`/api/admin/tools/${toolName}/call`, {
      arguments: args,
    })
  },
}

