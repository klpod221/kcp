<template>
  <div class="space-y-5">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-lg bg-zinc-900/40 border border-zinc-800/80">
      <div>
        <h2 class="text-sm font-semibold text-zinc-100 flex items-center gap-2">
          <ShieldCheck class="w-4 h-4 text-zinc-400" />
          OAuth 2.0 Clients &amp; Active Sessions
        </h2>
        <p class="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
          Manage applications connected via the OAuth 2.0 protocol (such as Google Gemini Connected Apps) and monitor live refresh token sessions.
        </p>
      </div>
      <Button
        variant="primary"
        @click="showCreateModal = true"
        class="shrink-0"
      >
        <template #prefix>
          <Plus class="w-3.5 h-3.5" />
        </template>
        Add OAuth Client
      </Button>
    </div>

    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-hidden">
      <div class="px-4 py-3 border-b border-zinc-800/80 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            Registered Applications
          </h3>
          <Badge variant="neutral" size="sm">{{ clients.length }} clients</Badge>
        </div>
        <Button
          variant="secondary"
          size="sm"
          :loading="loading"
          @click="loadData"
        >
          <template #prefix>
            <RefreshCw class="w-3.5 h-3.5" />
          </template>
          Refresh
        </Button>
      </div>

      <div v-if="loading && !clients.length" class="p-8 text-center text-xs text-zinc-500 flex items-center justify-center gap-2">
        <Loader2 class="w-4 h-4 animate-spin text-zinc-400" />
        <span>Loading OAuth clients...</span>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-zinc-800/80 bg-zinc-950/50 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
              <th class="py-2.5 px-4">Application</th>
              <th class="py-2.5 px-4">Client ID</th>
              <th class="py-2.5 px-4">Redirect URIs</th>
              <th class="py-2.5 px-4">Active Sessions</th>
              <th class="py-2.5 px-4">Status</th>
              <th class="py-2.5 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60 text-xs">
            <tr
              v-for="c in clients"
              :key="c.id"
              class="hover:bg-zinc-900/60 transition-colors"
            >
              <td class="py-3 px-4 font-medium text-zinc-100 whitespace-nowrap">
                <div class="flex items-center gap-2">
                  <div class="w-6 h-6 rounded bg-zinc-800 border border-zinc-700 text-zinc-200 flex items-center justify-center font-mono font-semibold text-[11px]">
                    {{ c.client_name[0] }}
                  </div>
                  <div>
                    <div>{{ c.client_name }}</div>
                    <div class="text-[10px] text-zinc-500 font-normal">Created {{ formatDate(c.created_at) }}</div>
                  </div>
                </div>
              </td>
              <td class="py-3 px-4 font-mono text-[11px] text-zinc-300 whitespace-nowrap">
                <span class="px-2 py-0.5 rounded bg-zinc-950 border border-zinc-800">
                  {{ c.client_id }}
                </span>
              </td>
              <td class="py-3 px-4">
                <div class="flex flex-col gap-1 max-w-xs">
                  <span
                    v-for="uri in c.redirect_uris"
                    :key="uri"
                    class="truncate font-mono text-[10px] text-zinc-400"
                    :title="uri"
                  >
                    {{ uri }}
                  </span>
                </div>
              </td>
              <td class="py-3 px-4 font-mono text-[11px] whitespace-nowrap tabular-nums">
                <Badge :variant="c.active_sessions > 0 ? 'success' : 'neutral'" size="sm">
                  {{ c.active_sessions }} active
                </Badge>
              </td>
              <td class="py-3 px-4 whitespace-nowrap">
                <Badge :variant="c.is_active ? 'success' : 'danger'" size="sm">
                  {{ c.is_active ? 'active' : 'disabled' }}
                </Badge>
              </td>
              <td class="py-3 px-4 text-right whitespace-nowrap">
                <Button
                  v-if="c.client_id !== 'gemini_client'"
                  variant="danger"
                  size="sm"
                  @click="deleteClient(c.id, c.client_name)"
                >
                  <template #prefix>
                    <Trash2 class="w-3 h-3" />
                  </template>
                  Delete
                </Button>
                <span v-else class="text-[11px] font-mono text-zinc-500">Core Client</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-hidden">
      <div class="px-4 py-3 border-b border-zinc-800/80 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Key class="w-4 h-4 text-zinc-400" />
          <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            Active OAuth Sessions
          </h3>
          <Badge variant="neutral" size="sm">{{ activeSessions.length }} active</Badge>
        </div>
      </div>

      <div v-if="!activeSessions.length" class="p-8 text-center text-xs text-zinc-500">
        No active OAuth sessions recorded.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-zinc-800/80 bg-zinc-950/50 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
              <th class="py-2.5 px-4">Client</th>
              <th class="py-2.5 px-4">User</th>
              <th class="py-2.5 px-4">Family Token</th>
              <th class="py-2.5 px-4">Created</th>
              <th class="py-2.5 px-4">Expires</th>
              <th class="py-2.5 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60 text-xs">
            <tr v-for="s in activeSessions" :key="s.id" class="hover:bg-zinc-900/60 transition-colors">
              <td class="py-3 px-4 font-medium text-zinc-100 whitespace-nowrap">{{ s.client_name }}</td>
              <td class="py-3 px-4 text-zinc-300 font-mono text-[11px] whitespace-nowrap">{{ s.username }}</td>
              <td class="py-3 px-4 text-zinc-400 font-mono text-[11px] whitespace-nowrap">{{ s.family_id }}</td>
              <td class="py-3 px-4 text-zinc-400 font-mono text-[11px] tabular-nums whitespace-nowrap">{{ formatDate(s.created_at) }}</td>
              <td class="py-3 px-4 text-zinc-300 font-mono text-[11px] tabular-nums whitespace-nowrap">{{ formatDate(s.expires_at) }}</td>
              <td class="py-3 px-4 text-right whitespace-nowrap">
                <Button variant="danger" size="sm" @click="revokeSession(s.id)">
                  Revoke
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <Modal
      v-model="showCreateModal"
      title="Register New OAuth 2.0 Client"
      maxWidth="md"
    >
      <form @submit.prevent="handleCreateClient" class="space-y-4">
        <Input
          v-model="createForm.client_name"
          label="Application Name"
          placeholder="e.g. Nextcloud, Home Assistant, n8n Workflow"
          required
        />

        <Input
          v-model="createForm.client_id"
          label="Client ID (optional, leave blank to auto-generate)"
          placeholder="custom_client_id"
        />

        <Input
          v-model="createForm.client_secret"
          label="Client Secret (optional, leave blank to auto-generate)"
          placeholder="Secure random secret"
        />

        <div class="space-y-1.5">
          <label class="block text-xs font-medium text-zinc-300">Redirect URIs (one per line)</label>
          <textarea
            v-model="redirectUrisText"
            rows="3"
            class="w-full rounded-md bg-zinc-950 border border-zinc-800 px-3 py-2 text-xs text-zinc-100 font-mono focus:outline-none focus:border-zinc-500"
            placeholder="https://oauth.google.com/callback&#10;https://oauth.pstmn.io/v1/callback"
            required
          ></textarea>
        </div>

        <div class="pt-3 flex justify-end gap-2 border-t border-zinc-800">
          <Button variant="ghost" size="sm" @click="showCreateModal = false">Cancel</Button>
          <Button
            type="submit"
            variant="primary"
            size="sm"
            :loading="creating"
          >
            Register Client
          </Button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  ShieldCheck,
  Plus,
  RefreshCw,
  Trash2,
  Key,
  Loader2,
} from 'lucide-vue-next'
import { adminService } from '../../services/admin.service.js'
import { useToastStore } from '../../stores/toast.store.js'
import { formatDate } from '../../utils/format.js'
import Button from '../../components/ui/Button.vue'
import Badge from '../../components/ui/Badge.vue'
import Input from '../../components/ui/Input.vue'
import Modal from '../../components/ui/Modal.vue'

const toast = useToastStore()

const clients = ref([])
const activeSessions = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const creating = ref(false)

const createForm = ref({
  client_name: '',
  client_id: '',
  client_secret: '',
})
const redirectUrisText = ref('')

async function loadData() {
  loading.value = true
  try {
    const data = await adminService.getClients()
    clients.value = data.clients || []
    activeSessions.value = data.active_sessions || []
  } catch (err) {
    toast.error(err.message || 'Failed to load OAuth data')
  } finally {
    loading.value = false
  }
}

async function handleCreateClient() {
  creating.value = true
  try {
    const uris = redirectUrisText.value
      .split('\n')
      .map(u => u.trim())
      .filter(Boolean)

    const payload = {
      client_name: createForm.value.client_name,
      client_id: createForm.value.client_id || undefined,
      client_secret: createForm.value.client_secret || undefined,
      redirect_uris: uris,
      allowed_scopes: 'mcp:read mcp:tools',
    }
    await adminService.createClient(payload)
    toast.success('OAuth client registered successfully')
    showCreateModal.value = false
    createForm.value = { client_name: '', client_id: '', client_secret: '' }
    redirectUrisText.value = ''
    await loadData()
  } catch (err) {
    toast.error(err.message || 'Failed to create client')
  } finally {
    creating.value = false
  }
}

async function deleteClient(id, name) {
  if (!confirm(`Delete OAuth client "${name}"?`)) return
  try {
    await adminService.deleteClient(id)
    toast.success(`Client "${name}" deleted`)
    await loadData()
  } catch (err) {
    toast.error(err.message || 'Failed to delete client')
  }
}

async function revokeSession(sessionId) {
  if (!confirm('Revoke this OAuth session?')) return
  try {
    await adminService.revokeSession(sessionId)
    toast.success('Session revoked successfully')
    await loadData()
  } catch (err) {
    toast.error(err.message || 'Failed to revoke session')
  }
}

onMounted(() => {
  loadData()
})
</script>
