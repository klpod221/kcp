<template>
  <span
    class="inline-flex items-center gap-1.5 font-medium rounded-md select-none tabular-nums"
    :class="[variantClasses, sizeClasses]"
  >
    <span v-if="dot" class="w-1.5 h-1.5 rounded-full shrink-0" :class="dotColorClass"></span>
    <slot />
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'neutral',
  },
  size: {
    type: String,
    default: 'md',
    validator: v => ['sm', 'md'].includes(v),
  },
  dot: { type: Boolean, default: false },
})

const normalizedVariant = computed(() => {
  switch (props.variant) {
    case 'emerald':
    case 'success':
      return 'success'
    case 'rose':
    case 'danger':
    case 'error':
      return 'danger'
    case 'amber':
    case 'warning':
      return 'warning'
    case 'indigo':
    case 'info':
      return 'info'
    case 'slate':
    case 'zinc':
    case 'neutral':
    default:
      return 'neutral'
  }
})

const variantClasses = computed(() => {
  switch (normalizedVariant.value) {
    case 'success':
      return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
    case 'danger':
      return 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
    case 'warning':
      return 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
    case 'info':
      return 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
    case 'neutral':
    default:
      return 'bg-zinc-900 text-zinc-300 border border-zinc-800'
  }
})

const dotColorClass = computed(() => {
  switch (normalizedVariant.value) {
    case 'success':
      return 'bg-emerald-400'
    case 'danger':
      return 'bg-rose-400'
    case 'warning':
      return 'bg-amber-400'
    case 'info':
      return 'bg-sky-400'
    case 'neutral':
    default:
      return 'bg-zinc-500'
  }
})

const sizeClasses = computed(() => {
  return props.size === 'sm' ? 'px-1.5 py-0.5 text-[11px] leading-none' : 'px-2 py-0.5 text-xs'
})
</script>
