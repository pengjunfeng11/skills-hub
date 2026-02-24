import { ref } from 'vue'

const toasts = ref([])
let nextId = 0

export function useToast() {
  function show(message, type = 'info', duration = 3000) {
    const id = nextId++
    toasts.value.push({ id, message, type })
    if (duration > 0) {
      setTimeout(() => remove(id), duration)
    }
    return id
  }

  function remove(id) {
    const idx = toasts.value.findIndex(t => t.id === id)
    if (idx !== -1) toasts.value.splice(idx, 1)
  }

  function success(msg, duration) { return show(msg, 'success', duration) }
  function error(msg, duration) { return show(msg, 'error', duration) }
  function warning(msg, duration) { return show(msg, 'warning', duration) }
  function info(msg, duration) { return show(msg, 'info', duration) }

  return { toasts, show, remove, success, error, warning, info }
}
