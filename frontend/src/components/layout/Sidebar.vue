<template>
  <aside class="w-60 h-full bg-zinc-950 border-r border-zinc-800/80 flex flex-col shrink-0 select-none overflow-hidden">
    <div class="h-14 px-4 border-b border-zinc-800/80 flex items-center justify-between">
      <router-link to="/" class="flex items-center gap-2.5 min-w-0">
        <div class="w-7 h-7 rounded-md bg-zinc-100 text-zinc-950 flex items-center justify-center font-bold text-xs tracking-tighter shrink-0">
          KCP
        </div>
        <div class="min-w-0">
          <div class="text-xs font-semibold text-zinc-100 tracking-tight truncate">klpod221</div>
          <div class="text-[11px] text-zinc-500 truncate leading-none mt-0.5">Kontrol Panel</div>
        </div>
      </router-link>
    </div>

    <nav class="flex-1 px-2.5 py-4 space-y-5 overflow-y-auto">
      <div v-for="section in navSections" :key="section.title" class="space-y-0.5">
        <div class="px-2.5 pb-1.5 text-[10px] font-medium uppercase tracking-widest text-zinc-500">
          {{ section.title }}
        </div>
        <router-link
          v-for="item in section.items"
          :key="item.path"
          :to="item.path"
          class="relative flex items-center gap-2.5 px-2.5 py-2 rounded-md text-xs transition-colors group"
          :class="route.path === item.path
            ? 'bg-zinc-900 text-zinc-100 font-medium'
            : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50'"
        >
          <span
            v-if="route.path === item.path"
            class="absolute left-0 top-1.5 bottom-1.5 w-0.5 bg-zinc-100 rounded-r"
          ></span>
          <component
            :is="item.icon"
            class="w-4 h-4 shrink-0 transition-colors"
            :class="route.path === item.path ? 'text-zinc-100' : 'text-zinc-500 group-hover:text-zinc-300'"
          />
          <span class="truncate">{{ item.label }}</span>
          <span
            v-if="item.badge"
            class="ml-auto text-[10px] font-mono px-1.5 py-0.2 rounded border tabular-nums"
            :class="route.path === item.path
              ? 'bg-zinc-800 text-zinc-200 border-zinc-700'
              : 'bg-zinc-900/80 text-zinc-500 border-zinc-800'"
          >
            {{ item.badge }}
          </span>
        </router-link>
      </div>
    </nav>

    <div class="p-2.5 border-t border-zinc-800/80">
      <div class="px-2.5 py-2 rounded-md bg-zinc-900/40 border border-zinc-800/80 flex items-center justify-between">
        <router-link to="/profile" class="flex items-center gap-2.5 min-w-0 hover:opacity-80 transition">
          <div class="w-6 h-6 rounded bg-zinc-800 text-zinc-200 border border-zinc-700 flex items-center justify-center font-mono font-semibold text-[11px] uppercase shrink-0">
            {{ (authStore.username || 'K')[0] }}
          </div>
          <div class="min-w-0">
            <div class="text-xs font-medium text-zinc-200 truncate leading-tight">{{ authStore.username || 'klpod221' }}</div>
            <div class="text-[10px] text-zinc-500 truncate flex items-center gap-1 mt-0.5">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              {{ authStore.isAdmin ? 'Administrator' : 'Standard User' }}
            </div>
          </div>
        </router-link>
        <button
          @click="handleLogout"
          title="Sign out"
          class="p-1.5 rounded-md text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition cursor-pointer"
        >
          <LogOut class="w-3.5 h-3.5" />
        </button>
      </div>
      <a
        href="https://klpod221.com"
        target="_blank"
        rel="noopener noreferrer"
        class="text-[11px] text-zinc-500 hover:text-zinc-300 transition text-center block pt-2.5 pb-0.5 tracking-tight font-sans"
      >
        Made with ❤️ by klpod221
      </a>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  LayoutDashboard,
  Box,
  Activity,
  Globe,
  BotMessageSquare,
  Wrench,
  KeyRound,
  ShieldCheck,
  User,
  Users,
  LogOut,
} from 'lucide-vue-next'
import { useAuthStore } from '../../stores/auth.store.js'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navSections = computed(() => {
  const sections = [
    {
      title: 'Infrastructure',
      items: [
        { path: '/', label: 'Overview', icon: LayoutDashboard },
        { path: '/docker', label: 'Containers', icon: Box, badge: '16' },
        { path: '/transfers', label: 'Transfers & I/O', icon: Activity },
        { path: '/services', label: 'Homelab Services', icon: Globe },
      ],
    },
    {
      title: 'MCP & AI Gateway',
      items: [
        { path: '/chat', label: 'AI Workspace', icon: BotMessageSquare },
        { path: '/tools', label: 'Tools Catalog', icon: Wrench, badge: '78' },
        { path: '/tokens', label: 'API Tokens', icon: KeyRound },
        { path: '/clients', label: 'OAuth Clients', icon: ShieldCheck },
      ],
    },
    {
      title: 'Account & System',
      items: [
        { path: '/profile', label: 'Profile & Security', icon: User },
      ],
    },
  ]

  if (authStore.isAdmin) {
    sections[2].items.push({ path: '/users', label: 'User Accounts', icon: Users })
  }

  return sections
})

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>
