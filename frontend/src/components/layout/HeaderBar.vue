<template>
  <header class="h-14 px-6 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md flex items-center justify-between shrink-0 sticky top-0 z-20">
    <div class="flex items-center gap-2 text-xs">
      <span class="text-zinc-500 font-medium">{{ sectionName }}</span>
      <span class="text-zinc-700">/</span>
      <h1 class="font-semibold text-zinc-100 tracking-tight">
        <slot name="title">{{ title }}</slot>
      </h1>
    </div>

    <div class="flex items-center gap-4">
      <div
        v-if="systemStore.overview?.host"
        class="hidden md:flex items-center divide-x divide-zinc-800/80 border border-zinc-800/80 rounded-md bg-zinc-900/40 text-[11px] font-mono tabular-nums"
      >
        <div class="px-2.5 py-1 flex items-center gap-1.5">
          <span class="text-zinc-500">CPU</span>
          <span :class="cpuColorClass">{{ systemStore.cpuPercent }}%</span>
        </div>
        <div class="px-2.5 py-1 flex items-center gap-1.5">
          <span class="text-zinc-500">MEM</span>
          <span class="text-zinc-200">{{ systemStore.ramPercent }}%</span>
        </div>
        <div v-if="systemStore.cpuTemp" class="px-2.5 py-1 flex items-center gap-1.5">
          <span class="text-zinc-500">TEMP</span>
          <span :class="systemStore.cpuTemp > 75 ? 'text-amber-400' : 'text-zinc-200'">{{ systemStore.cpuTemp }}°C</span>
        </div>
        <div class="px-2.5 py-1 flex items-center gap-1.5">
          <span class="text-zinc-500">UP</span>
          <span class="text-zinc-300">{{ systemStore.overview.host.uptime_human || '—' }}</span>
        </div>
      </div>

      <a
        href="https://github.com/klpod221/kcp"
        target="_blank"
        rel="noopener noreferrer"
        class="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-900/60 border border-zinc-800 text-[11px] font-mono text-zinc-400 hover:text-zinc-100 hover:border-zinc-700 transition"
        title="View klpod221/kcp on GitHub"
      >
        <svg class="w-3.5 h-3.5 text-zinc-400 fill-current" viewBox="0 0 24 24" aria-hidden="true">
          <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"></path>
        </svg>
        <span>klpod221/kcp</span>
      </a>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useSystemStore } from '../../stores/system.store.js'

defineProps({
  title: { type: String, default: '' },
})

const route = useRoute()
const systemStore = useSystemStore()

const sectionName = computed(() => {
  const mcpPaths = ['/chat', '/tools', '/tokens', '/clients']
  const accountPaths = ['/profile', '/users']
  if (mcpPaths.includes(route.path)) return 'MCP & AI Gateway'
  if (accountPaths.includes(route.path)) return 'Account & System'
  return 'Infrastructure'
})

const cpuColorClass = computed(() => {
  if (systemStore.cpuPercent > 80) return 'text-rose-400'
  if (systemStore.cpuPercent > 50) return 'text-amber-400'
  return 'text-zinc-200'
})
</script>
