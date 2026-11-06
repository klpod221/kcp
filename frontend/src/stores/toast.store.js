import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])

  function show(message, type = 'info', title = '', duration = 4000) {
    const id = Date.now() + Math.random().toString(36).substring(2, 9)
    const toast = { id, message, type, title }
    toasts.value.push(toast)

    if (duration > 0) {
      setTimeout(() => {
        remove(id)
      }, duration)
    }
    return id
  }

  function success(message, title = 'Success') {
    return show(message, 'success', title)
  }

  function error(message, title = 'Error') {
    return show(message, 'error', title, 6000)
  }

  function info(message, title = 'Notice') {
    return show(message, 'info', title)
  }

  function remove(id) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  return {
    toasts,
    show,
    success,
    error,
    info,
    remove,
  }
})

