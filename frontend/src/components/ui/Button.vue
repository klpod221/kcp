<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    class="inline-flex items-center justify-center font-medium transition-colors cursor-pointer disabled:opacity-45 disabled:cursor-not-allowed select-none"
    :class="[variantClasses, sizeClasses, roundedClasses]"
  >
    <Loader2 v-if="loading" class="animate-spin shrink-0" :class="iconSizeClass" />
    <slot name="prefix" v-else-if="$slots.prefix" />
    <span
      v-if="hasDefaultSlot"
      :class="{
        'ml-1.5': (loading || $slots.prefix) && hasDefaultSlot,
        'mr-1.5': $slots.suffix && hasDefaultSlot,
      }"
    >
      <slot />
    </span>
    <slot name="suffix" />
  </button>
</template>

<script setup>
import { computed, useSlots } from 'vue'
import { Loader2 } from 'lucide-vue-next'

const slots = useSlots()

const props = defineProps({
  type: { type: String, default: 'button' },
  variant: {
    type: String,
    default: 'primary',
    validator: v => ['primary', 'secondary', 'danger', 'ghost', 'emerald'].includes(v),
  },
  size: {
    type: String,
    default: 'md',
    validator: v => ['sm', 'md', 'lg'].includes(v),
  },
  rounded: { type: String, default: 'md' },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const hasDefaultSlot = computed(() => {
  if (!slots.default) return false
  const nodes = slots.default()
  return nodes.some(node => {
    if (typeof node.children === 'string') return node.children.trim().length > 0
    return true
  })
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-zinc-100 hover:bg-white text-zinc-950 border border-zinc-200 shadow-xs'
    case 'emerald':
      return 'bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30'
    case 'secondary':
      return 'bg-zinc-900 hover:bg-zinc-800/90 text-zinc-200 border border-zinc-800 hover:border-zinc-700'
    case 'danger':
      return 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/25'
    case 'ghost':
      return 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60 border border-transparent'
    default:
      return ''
  }
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-7 px-2.5 text-xs'
    case 'lg':
      return 'h-10 px-4 text-sm'
    case 'md':
    default:
      return 'h-8 px-3 text-xs'
  }
})

const iconSizeClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'w-3.5 h-3.5'
    case 'lg':
      return 'w-4 h-4'
    default:
      return 'w-3.5 h-3.5'
  }
})

const roundedClasses = computed(() => {
  switch (props.rounded) {
    case 'sm':
      return 'rounded-sm'
    case 'lg':
      return 'rounded-lg'
    case 'full':
      return 'rounded-full'
    case 'md':
    default:
      return 'rounded-md'
  }
})
</script>
