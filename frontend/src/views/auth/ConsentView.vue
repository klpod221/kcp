<template>
  <div class="w-full max-w-md relative">
    <div class="w-full rounded-lg bg-zinc-900/60 border border-zinc-800 p-6 shadow-2xl">
      <div class="flex flex-col items-center text-center mb-5">
        <div class="w-10 h-10 rounded-md bg-zinc-800 border border-zinc-700 text-zinc-100 flex items-center justify-center mb-3">
          <ShieldCheck class="w-5 h-5 text-emerald-400" />
        </div>
        <h1 class="text-base font-semibold text-zinc-100">Authorize Application</h1>
        <p class="text-xs text-zinc-400 mt-1">
          <span class="font-medium text-zinc-200">{{ clientName }}</span> is requesting access to your MCP server
        </p>
      </div>

      <div v-if="authStore.user" class="flex items-center justify-between px-3 py-2 rounded-md bg-zinc-950 border border-zinc-800 mb-4 text-xs">
        <div class="flex items-center gap-2">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
          <span class="text-zinc-500">Account:</span>
          <strong class="text-zinc-200 font-mono">{{ authStore.username }}</strong>
        </div>
        <button
          @click="changeAccount"
          class="text-zinc-400 hover:text-zinc-100 transition cursor-pointer text-[11px]"
        >
          Switch account
        </button>
      </div>

      <div class="rounded-md bg-zinc-950/60 border border-zinc-800 p-4 mb-4">
        <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500 mb-3">
          Requested Permissions (78 Homelab MCP Tools)
        </div>
        <div class="space-y-3">
          <div class="flex items-start gap-2.5">
            <Check class="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <div class="text-xs font-medium text-zinc-200">
                Read system status &amp; media (<code class="text-[11px] text-zinc-300 font-mono">mcp:read</code>)
              </div>
              <p class="text-[11px] text-zinc-400 mt-0.5 leading-relaxed">
                Inspect CPU, RAM, GPU, temperatures, Docker containers, Rclone Google Drive, library contents, and TriliumNext notes.
              </p>
            </div>
          </div>
          <div class="flex items-start gap-2.5">
            <Check class="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <div class="text-xs font-medium text-zinc-200">
                Execute management tools (<code class="text-[11px] text-zinc-300 font-mono">mcp:tools</code>)
              </div>
              <p class="text-[11px] text-zinc-400 mt-0.5 leading-relaxed">
                Submit media requests, control Radarr/Sonarr/Lidarr, manage qBittorrent downloads, Docker containers, and Rclone cache.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-md bg-zinc-950 border border-zinc-850 px-3 py-2 mb-5 text-[11px] text-zinc-400 break-all font-mono">
        <span class="text-zinc-500 font-sans">Callback URI:</span> {{ redirectUri }}
      </div>

      <div v-if="error" class="mb-4 rounded-md bg-rose-500/10 border border-rose-500/25 px-3 py-2 text-xs text-rose-400 flex items-center gap-2">
        <AlertCircle class="w-4 h-4 shrink-0" />
        <span>{{ error }}</span>
      </div>

      <div class="grid grid-cols-2 gap-2.5">
        <Button
          variant="secondary"
          :disabled="submitting"
          @click="submitConsent('deny')"
        >
          Deny
        </Button>
        <Button
          variant="primary"
          :loading="submitting"
          @click="submitConsent('allow')"
        >
          Allow Access
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ShieldCheck, Check, AlertCircle } from 'lucide-vue-next'
import { useAuthStore } from '../../stores/auth.store.js'
import Button from '../../components/ui/Button.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const submitting = ref(false)
const error = ref('')

const clientId = computed(() => route.query.client_id || '')
const clientName = computed(() => {
  if (clientId.value === 'gemini_client') return 'Google Gemini'
  return route.query.client_name || clientId.value || 'Client Application'
})
const redirectUri = computed(() => route.query.redirect_uri || '')
const state = computed(() => route.query.state || '')
const scope = computed(() => route.query.scope || 'mcp:read mcp:tools')
const codeChallenge = computed(() => route.query.code_challenge || '')
const codeChallengeMethod = computed(() => route.query.code_challenge_method || '')

function changeAccount() {
  authStore.logout()
  router.push({
    name: 'login',
    query: { return_to: route.fullPath },
  })
}

async function submitConsent(action) {
  submitting.value = true
  error.value = ''
  try {
    const payload = {
      client_id: clientId.value,
      redirect_uri: redirectUri.value,
      action,
      state: state.value || undefined,
      scope: scope.value || undefined,
      code_challenge: codeChallenge.value || undefined,
      code_challenge_method: codeChallengeMethod.value || undefined,
    }

    const resp = await fetch('/consent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    const data = await resp.json().catch(() => ({}))

    if (resp.ok && data.redirect_url) {
      window.location.href = data.redirect_url
      return
    }

    throw new Error(data.detail || 'Authorization request failed')
  } catch (err) {
    error.value = err.message || 'Authorization failed'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  if (!clientId.value || !redirectUri.value) {
    error.value = 'Invalid authorization request parameters.'
  }
})
</script>
