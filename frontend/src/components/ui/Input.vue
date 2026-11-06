<template>
  <div class="space-y-1.5 w-full">
    <label v-if="label" :for="id" class="block text-xs font-medium text-zinc-300">
      {{ label }}
      <span v-if="required" class="text-rose-400">*</span>
    </label>

    <div class="relative">
      <div v-if="$slots.prefix" class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">
        <slot name="prefix" />
      </div>

      <input
        :id="id"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :required="required"
        :disabled="disabled"
        :autocomplete="autocomplete"
        @input="$emit('update:modelValue', $event.target.value)"
        class="w-full rounded-md bg-zinc-950 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500/30 transition disabled:opacity-50"
        :class="[
          $slots.prefix ? 'pl-9' : 'pl-3',
          $slots.suffix ? 'pr-9' : 'pr-3',
          size === 'lg' ? 'h-10' : 'h-8',
          error ? 'border-rose-500/80 focus:border-rose-500 focus:ring-rose-500/20' : '',
        ]"
      />

      <div v-if="$slots.suffix" class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500">
        <slot name="suffix" />
      </div>
    </div>

    <p v-if="error" class="text-[11px] text-rose-400">{{ error }}</p>
    <p v-else-if="hint" class="text-[11px] text-zinc-500">{{ hint }}</p>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: [String, Number], default: '' },
  id: { type: String, default: () => `input-${Math.random().toString(36).substring(2, 9)}` },
  label: { type: String, default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  error: { type: String, default: '' },
  hint: { type: String, default: '' },
  required: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  autocomplete: { type: String, default: 'off' },
  size: { type: String, default: 'md' },
})

defineEmits(['update:modelValue'])
</script>
