<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs"
        @click.self="handleBackdropClick"
      >
        <div
          class="w-full rounded-lg bg-zinc-950 border border-zinc-800 shadow-2xl overflow-hidden flex flex-col"
          :class="maxWidthClass"
        >
          <div class="px-5 py-3.5 border-b border-zinc-800/80 flex items-center justify-between bg-zinc-900/40">
            <h3 class="text-xs font-semibold text-zinc-100 flex items-center gap-2">
              <slot name="title">{{ title }}</slot>
            </h3>
            <button
              v-if="closable"
              @click="$emit('update:modelValue', false)"
              class="text-zinc-500 hover:text-zinc-200 transition p-1 rounded-md hover:bg-zinc-800/80 cursor-pointer"
            >
              <X class="w-4 h-4" />
            </button>
          </div>

          <div class="p-5 space-y-4 max-h-[75vh] overflow-y-auto">
            <slot />
          </div>

          <div
            v-if="$slots.footer"
            class="px-5 py-3 bg-zinc-900/30 border-t border-zinc-800/80 flex items-center justify-end gap-2"
          >
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { X } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  maxWidth: {
    type: String,
    default: 'md',
    validator: v => ['sm', 'md', 'lg', 'xl', '2xl', '4xl'].includes(v),
  },
  closable: { type: Boolean, default: true },
  closeOnBackdrop: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue'])

const maxWidthClass = computed(() => {
  switch (props.maxWidth) {
    case 'sm':
      return 'max-w-sm'
    case 'lg':
      return 'max-w-lg'
    case 'xl':
      return 'max-w-xl'
    case '2xl':
      return 'max-w-2xl'
    case '4xl':
      return 'max-w-4xl'
    case 'md':
    default:
      return 'max-w-md'
  }
})

function handleBackdropClick() {
  if (props.closeOnBackdrop && props.closable) {
    emit('update:modelValue', false)
  }
}
</script>
