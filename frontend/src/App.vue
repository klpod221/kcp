<template>
  <div v-if="isAuthRoute" class="h-screen w-screen bg-zinc-950 text-zinc-100 flex items-center justify-center p-4 overflow-y-auto">
    <router-view />
    <ToastContainer />
  </div>

  <div v-else class="h-screen w-screen bg-zinc-950 text-zinc-100 flex antialiased overflow-hidden">
    <Sidebar />

    <div class="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
      <HeaderBar :title="currentTitle" />

      <main class="flex-1 overflow-y-auto p-6 bg-zinc-950 min-h-0">
        <div class="max-w-[1600px] mx-auto">
          <router-view />
        </div>
      </main>
    </div>

    <ToastContainer />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth.store.js'
import { useSystemStore } from './stores/system.store.js'
import Sidebar from './components/layout/Sidebar.vue'
import HeaderBar from './components/layout/HeaderBar.vue'
import ToastContainer from './components/ui/ToastContainer.vue'

const route = useRoute()
const authStore = useAuthStore()
const systemStore = useSystemStore()

const isAuthRoute = computed(() => !!route.meta.isAuth)
const currentTitle = computed(() => route.meta.title || 'Overview')

onMounted(async () => {
  await authStore.checkAuth()
  if (authStore.isAuthenticated) {
    systemStore.fetchOverview()
  }
})
</script>
