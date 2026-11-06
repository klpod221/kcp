<template>
  <div class="w-full max-w-sm relative">
    <div class="w-full rounded-lg bg-zinc-900/60 border border-zinc-800 p-6 shadow-2xl">
      <div class="flex flex-col items-center text-center mb-6">
        <div class="w-10 h-10 rounded-md bg-zinc-100 text-zinc-950 flex items-center justify-center font-bold text-sm tracking-tight mb-3">
          KCP
        </div>
        <div class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-zinc-950 border border-zinc-850 text-[11px] text-zinc-400 font-mono mb-1">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
          <span>klpod221 Kontrol Panel</span>
        </div>
        <h1 class="text-lg font-semibold text-zinc-100">Sign In</h1>
        <p class="text-xs text-zinc-400 mt-1">
          {{ appSubtitle }}
        </p>
      </div>

      <div v-if="error" class="mb-4 rounded-md bg-rose-500/10 border border-rose-500/25 px-3 py-2 text-xs text-rose-400 flex items-center gap-2">
        <AlertCircle class="w-4 h-4 text-rose-400 shrink-0" />
        <span>{{ error }}</span>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <Input
          v-model="username"
          label="Username"
          placeholder="admin username"
          required
          autocomplete="username"
        >
          <template #prefix>
            <User class="w-3.5 h-3.5 text-zinc-500" />
          </template>
        </Input>

        <Input
          v-model="password"
          label="Password"
          :type="showPassword ? 'text' : 'password'"
          placeholder="••••••••••••"
          required
          autocomplete="current-password"
        >
          <template #prefix>
            <Key class="w-3.5 h-3.5 text-zinc-500" />
          </template>
          <template #suffix>
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="text-zinc-500 hover:text-zinc-200 transition cursor-pointer"
            >
              <EyeOff v-if="showPassword" class="w-3.5 h-3.5" />
              <Eye v-else class="w-3.5 h-3.5" />
            </button>
          </template>
        </Input>

        <Button
          type="submit"
          variant="primary"
          :loading="authStore.isLoggingIn"
          class="w-full mt-2"
        >
          Sign In
          <template #suffix>
            <ArrowRight class="w-3.5 h-3.5" />
          </template>
        </Button>
      </form>

      <div class="mt-6 pt-4 border-t border-zinc-800/80 flex items-center justify-between text-[11px] text-zinc-500 font-mono">
        <span>KCP</span>
        <span>klpod221-server</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { User, Key, Eye, EyeOff, ArrowRight, AlertCircle } from 'lucide-vue-next'
import { useAuthStore } from '../../stores/auth.store.js'
import Input from '../../components/ui/Input.vue'
import Button from '../../components/ui/Button.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const error = ref(route.query.error || '')

const returnTo = computed(() => route.query.return_to || '/')

const appSubtitle = computed(() => {
  if (returnTo.value && returnTo.value.includes('authorize')) {
    return 'Authorize external application connection via OAuth 2.0'
  }
  return 'Unified administrative portal for klpod221 server'
})

async function handleSubmit() {
  error.value = ''
  try {
    const target = await authStore.login(username.value, password.value, returnTo.value)
    if (target.startsWith('http://') || target.startsWith('https://')) {
      window.location.href = target
    } else {
      router.push(target)
    }
  } catch (err) {
    error.value = err.message || 'Invalid credentials'
  }
}
</script>
