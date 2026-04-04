import { reactive, readonly } from 'vue'

export interface Toast {
  id: number
  kind: 'success' | 'error' | 'info'
  message: string
}

const toasts = reactive<Toast[]>([])
let nextId = 1

function dismiss(id: number) {
  const index = toasts.findIndex((t) => t.id === id)
  if (index >= 0) toasts.splice(index, 1)
}

function push(kind: Toast['kind'], message: string, timeout = 4000) {
  const id = nextId++
  toasts.push({ id, kind, message })
  if (timeout > 0) setTimeout(() => dismiss(id), timeout)
  return id
}

export function useToasts() {
  return {
    toasts: readonly(toasts),
    dismiss,
    success: (message: string) => push('success', message),
    error: (message: string) => push('error', message, 7000),
    info: (message: string) => push('info', message),
  }
}
