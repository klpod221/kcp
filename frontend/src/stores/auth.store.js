import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '../services/auth.service.js'
import { useToastStore } from './toast.store.js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const serverInfo = ref(null)
  const isLoaded = ref(false)
  const isLoggingIn = ref(false)
  const loginError = ref('')

  const isAuthenticated = computed(() => !!user.value)
  const username = computed(() => user.value?.username || 'Guest')
  const isAdmin = computed(() => !!user.value?.is_admin)

  async function checkAuth() {
    try {
      const data = await authService.getMe()
      if (data.authenticated) {
        user.value = data.user
        serverInfo.value = data.server
      } else {
        user.value = null
      }
    } catch {
      user.value = null
    } finally {
      isLoaded.value = true
    }
    return isAuthenticated.value
  }

  async function login(usernameInput, passwordInput, returnTo = '/') {
    isLoggingIn.value = true
    loginError.value = ''
    const toast = useToastStore()

    try {
      const res = await authService.login(usernameInput, passwordInput, returnTo)
      user.value = res.user
      toast.success(`Welcome back, ${res.user.username}!`, 'Signed In')
      return res.return_to || '/'
    } catch (err) {
      loginError.value = err.message || 'Invalid username or password.'
      toast.error(loginError.value, 'Sign In Failed')
      throw err
    } finally {
      isLoggingIn.value = false
    }
  }

  async function logout() {
    try {
      await authService.logout()
    } catch {}
    user.value = null
  }

  return {
    user,
    serverInfo,
    isLoaded,
    isLoggingIn,
    loginError,
    isAuthenticated,
    username,
    isAdmin,
    checkAuth,
    login,
    logout,
  }
})

