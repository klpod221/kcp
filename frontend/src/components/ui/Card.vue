<template>
  <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80" :class="paddingClass">
    <div
      v-if="$slots.header || title"
      class="pb-3 border-b border-zinc-800/80 flex items-center justify-between mb-4"
    >
      <slot name="header">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-300 flex items-center gap-2">
          {{ title }}
        </h3>
      </slot>
    </div>
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  padding: {
    type: String,
    default: 'normal',
    validator: v => ['none', 'sm', 'normal', 'lg'].includes(v),
  },
})

const paddingClass = computed(() => {
  switch (props.padding) {
    case 'none':
      return 'p-0'
    case 'sm':
      return 'p-3'
    case 'lg':
      return 'p-6'
    case 'normal':
    default:
      return 'p-4'
  }
})
</script>
