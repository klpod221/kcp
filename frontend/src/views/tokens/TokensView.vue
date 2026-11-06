<template>
  <div class="space-y-5">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-lg bg-zinc-900/40 border border-zinc-800/80">
      <div>
        <h2 class="text-sm font-semibold text-zinc-100 flex items-center gap-2">
          <KeyRound class="w-4 h-4 text-zinc-400" />
          Personal Access Tokens (Static API Keys)
        </h2>
        <p class="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
          Generate static API tokens (<code class="text-zinc-200 font-mono">klpod_pat_...</code>) for long-term integration with Claude Desktop, Cursor, AI agents, or scripts without OAuth session expiration.
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
        Generate Token
      </Button>
    </div>

    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-hidden">
      <div class="px-4 py-3 border-b border-zinc-800/80 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            Active Tokens
          </h3>
          <Badge variant="neutral" size="sm">{{ tokens.length }} active</Badge>
        </div>
        <Button
          variant="secondary"
          size="sm"
          :loading="loading"
          @click="loadTokens"
        >
          <template #prefix>
            <RefreshCw class="w-3.5 h-3.5" />
          </template>
          Refresh
        </Button>
      </div>

      <div v-if="loading && !tokens.length" class="p-8 text-center text-xs text-zinc-500 flex items-center justify-center gap-2">
        <Loader2 class="w-4 h-4 animate-spin text-zinc-400" />
        <span>Loading access tokens...</span>
      </div>

      <div v-else-if="!tokens.length" class="p-8 text-center text-xs text-zinc-500">
        No active API tokens found. Generate one to authenticate MCP clients.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-zinc-800/80 bg-zinc-950/50 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
              <th class="py-2.5 px-4">Token Name</th>
              <th class="py-2.5 px-4">Token Key</th>
              <th class="py-2.5 px-4">Scopes</th>
              <th class="py-2.5 px-4">Last Used</th>
              <th class="py-2.5 px-4">Expires</th>
              <th class="py-2.5 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60 text-xs">
            <tr
              v-for="t in tokens"
              :key="t.id"
              class="hover:bg-zinc-900/60 transition-colors"
            >
              <td class="py-3 px-4 font-medium text-zinc-100 whitespace-nowrap">
                {{ t.name }}
              </td>
              <td class="py-3 px-4 font-mono text-[11px] text-zinc-300 whitespace-nowrap">
                <span class="px-2 py-0.5 rounded bg-zinc-950 border border-zinc-800">
                  {{ t.token_prefix }}••••••••
                </span>
              </td>
              <td class="py-3 px-4">
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="scope in t.scopes.split(' ')"
                    :key="scope"
                    class="px-1.5 py-0.5 rounded bg-zinc-950 text-zinc-300 border border-zinc-800 text-[10px] font-mono"
                  >
                    {{ scope }}
                  </span>
                </div>
              </td>
              <td class="py-3 px-4 text-zinc-400 font-mono text-[11px] whitespace-nowrap tabular-nums">
                {{ t.last_used_at ? formatDate(t.last_used_at) : 'Never' }}
              </td>
              <td class="py-3 px-4 font-mono text-[11px] whitespace-nowrap tabular-nums">
                <Badge :variant="t.expires_at ? 'warning' : 'neutral'" size="sm">
                  {{ t.expires_at ? formatDate(t.expires_at) : 'Never' }}
                </Badge>
              </td>
              <td class="py-3 px-4 text-right whitespace-nowrap">
                <Button
                  variant="danger"
                  size="sm"
                  :disabled="revokingId === t.id"
                  @click="revokeToken(t.id, t.name)"
                >
                  <template #prefix>
                    <Trash2 class="w-3 h-3" />
                  </template>
                  Revoke
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 p-5 space-y-3">
      <div class="flex items-center gap-2">
        <Sparkles class="w-4 h-4 text-zinc-400" />
        <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
          Fast Connect Integration Snippets
        </h3>
      </div>
      <p class="text-xs text-zinc-400">
        Copy the configuration block below into your MCP client to connect directly:
      </p>

      <div class="flex items-center gap-1.5 border-b border-zinc-800/80 pb-2 text-xs">
        <button
          v-for="tab in snippetTabs"
          :key="tab.id"
          @click="activeSnippetTab = tab.id"
          class="px-2.5 py-1 rounded-md transition cursor-pointer font-medium text-xs"
          :class="activeSnippetTab === tab.id ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-400 hover:text-zinc-200'"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="relative">
        <pre class="rounded-md bg-zinc-950 p-4 text-xs font-mono text-zinc-300 overflow-x-auto leading-relaxed border border-zinc-800">{{ currentSnippetCode }}</pre>
        <button
          @click="copySnippet"
          class="absolute top-3 right-3 px-2.5 py-1 rounded-md bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white transition cursor-pointer border border-zinc-800 flex items-center gap-1.5 text-xs font-mono"
        >
          <Copy class="w-3.5 h-3.5" />
          <span>{{ copied ? 'Copied' : 'Copy' }}</span>
        </button>
      </div>
    </div>

    <Modal
      v-model="showCreateModal"
      title="Generate Personal Access Token"
      maxWidth="md"
    >
      <template v-if="!createdRawToken">
        <form @submit.prevent="handleCreateToken" class="space-y-4">
          <Input
            v-model="createForm.name"
            label="Token Name / Description"
            placeholder="e.g. Claude Desktop, Cursor IDE, Home Assistant"
            required
            hint="Identifies which client or integration uses this token."
          />

          <div class="space-y-1.5">
            <label class="block text-xs font-medium text-zinc-300">Expiration</label>
            <select
              v-model.number="createForm.expires_in_days"
              class="w-full h-8 rounded-md bg-zinc-950 border border-zinc-800 px-2.5 text-xs text-zinc-200 focus:outline-none focus:border-zinc-500"
            >
              <option :value="0">Never expires (Recommended for private homelab)</option>
              <option :value="30">30 days</option>
              <option :value="90">90 days</option>
              <option :value="365">1 year (365 days)</option>
            </select>
          </div>

          <Input
            v-model="createForm.scopes"
            label="Scopes"
            disabled
            hint="Default grants full read and execution rights across all 78 MCP tools."
          />

          <div class="pt-3 flex justify-end gap-2 border-t border-zinc-800">
            <Button variant="ghost" size="sm" @click="closeCreateModal">Cancel</Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              :loading="creating"
            >
              Generate Token
            </Button>
          </div>
        </form>
      </template>

      <template v-else>
        <div class="space-y-4">
          <div class="p-3 rounded-md bg-emerald-500/10 border border-emerald-500/25 flex items-start gap-2.5">
            <CheckCircle2 class="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div class="text-xs text-emerald-300 leading-relaxed">
              <strong>Token generated successfully.</strong> Copy it now; for security, it will not be displayed again.
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="block text-xs font-medium text-zinc-300">Your Access Token</label>
            <div class="flex items-center gap-2">
              <input
                type="text"
                readonly
                :value="createdRawToken"
                class="flex-1 h-8 rounded-md bg-zinc-950 border border-zinc-800 px-3 font-mono text-xs text-zinc-100 select-all focus:outline-none"
              />
              <Button variant="primary" size="sm" @click="copyCreatedToken">
                <template #prefix>
                  <Copy class="w-3.5 h-3.5" />
                </template>
                Copy
              </Button>
            </div>
          </div>

          <div class="pt-3 flex justify-end border-t border-zinc-800">
            <Button variant="secondary" size="sm" @click="closeCreateModal">Done</Button>
          </div>
        </div>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  KeyRound,
  Plus,
  RefreshCw,
  Trash2,
  Sparkles,
  Copy,
  CheckCircle2,
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

const tokens = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const creating = ref(false)
const revokingId = ref(null)
const createdRawToken = ref('')
const copied = ref(false)

const createForm = ref({
  name: '',
  expires_in_days: 0,
  scopes: 'mcp:read mcp:tools',
})

const activeSnippetTab = ref('claude')
const snippetTabs = [
  { id: 'claude', label: 'Claude Desktop' },
  { id: 'cursor', label: 'Cursor IDE' },
  { id: 'curl', label: 'cURL JSON-RPC' },
]

const sampleToken = computed(() => {
  if (createdRawToken.value) return createdRawToken.value
  if (tokens.value.length > 0) return `${tokens.value[0].token_prefix}••••••••`
  return 'klpod_pat_YOUR_TOKEN_HERE'
})

const currentSnippetCode = computed(() => {
  const token = sampleToken.value
  switch (activeSnippetTab.value) {
    case 'claude':
      return JSON.stringify({
        mcpServers: {
          "klpod221-homelab": {
            url: "https://kcp.klpod221.com/mcp",
            headers: {
              Authorization: `Bearer ${token}`
            }
          }
        }
      }, null, 2)
    case 'cursor':
      return JSON.stringify({
        "mcpServers": {
          "klpod221": {
            "type": "sse",
            "url": "https://kcp.klpod221.com/mcp",
            "headers": {
              "Authorization": `Bearer ${token}`
            }
          }
        }
      }, null, 2)
    case 'curl':
      return `curl -X POST https://kcp.klpod221.com/mcp \\
  -H "Authorization: Bearer ${token}" \\
  -H "Content-Type: application/json" \\
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'`
    default:
      return ''
  }
})

async function loadTokens() {
  loading.value = true
  try {
    const data = await adminService.getTokens()
    tokens.value = data.tokens || []
  } catch (err) {
    toast.error(err.message || 'Failed to load tokens')
  } finally {
    loading.value = false
  }
}

async function handleCreateToken() {
  creating.value = true
  try {
    const payload = {
      name: createForm.value.name,
      expires_in_days: createForm.value.expires_in_days === 0 ? null : createForm.value.expires_in_days,
      scopes: createForm.value.scopes,
    }
    const res = await adminService.createToken(payload)
    createdRawToken.value = res.token
    toast.success('Token generated successfully')
    await loadTokens()
  } catch (err) {
    toast.error(err.message || 'Failed to create token')
  } finally {
    creating.value = false
  }
}

async function revokeToken(tokenId, tokenName) {
  if (!confirm(`Revoke token "${tokenName}"? Active clients using this key will immediately lose access.`)) {
    return
  }
  revokingId.value = tokenId
  try {
    await adminService.revokeToken(tokenId)
    toast.success(`Token "${tokenName}" revoked`)
    await loadTokens()
  } catch (err) {
    toast.error(err.message || 'Failed to revoke token')
  } finally {
    revokingId.value = null
  }
}

function closeCreateModal() {
  showCreateModal.value = false
  createdRawToken.value = ''
  createForm.value = {
    name: '',
    expires_in_days: 0,
    scopes: 'mcp:read mcp:tools',
  }
}

function copyCreatedToken() {
  if (!createdRawToken.value) return
  navigator.clipboard.writeText(createdRawToken.value)
  toast.success('Token copied to clipboard')
}

function copySnippet() {
  navigator.clipboard.writeText(currentSnippetCode.value)
  copied.value = true
  toast.success('Configuration snippet copied')
  setTimeout(() => { copied.value = false }, 2000)
}

onMounted(() => {
  loadTokens()
})
</script>
