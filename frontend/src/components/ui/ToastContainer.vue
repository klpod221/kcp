<template>
  <div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
    <TransitionGroup
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform translate-y-2 opacity-0"
      enter-to-class="transform translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform translate-y-0 opacity-100"
      leave-to-class="transform translate-y-1 opacity-0"
    >
      <div
        v-for="toast in toastStore.toasts"
        :key="toast.id"
        class="pointer-events-auto px-3.5 py-3 rounded-lg shadow-2xl bg-zinc-900 border border-zinc-800 flex items-start gap-2.5 text-xs"
      >
        <CheckCircle v-if="toast.type === 'success'" class="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        <AlertTriangle v-else-if="toast.type === 'warning'" class="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <AlertCircle v-else-if="toast.type === 'error'" class="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
        <Info v-else class="w-4 h-4 text-zinc-300 shrink-0 mt-0.5" />

        <div class="flex-1 min-w-0">
          <div v-if="toast.title" class="font-semibold text-zinc-100 mb-0.5">{{ toast.title }}</div>
          <p class="text-zinc-400 leading-relaxed">{{ toast.message }}</p>
        </div>

        <button
          @click="toastStore.remove(toast.id)"
          class="text-zinc-500 hover:text-zinc-200 p-0.5 rounded transition shrink-0 cursor-pointer"
        >
          <X class="w-3.5 h-3.5" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { CheckCircle, AlertTriangle, AlertCircle, Info, X } from 'lucide-vue-next'
import { useToastStore } from '../../stores/toast.store.js'

const toastStore = useToastStore()
</script>
