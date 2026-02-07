import { computed, reactive, readonly } from 'vue'

import { api } from '@/api/client'
import type { Entry } from '@/api/types'

const state = reactive<{ running: Entry | null; now: number; version: number }>({
  running: null,
  now: Date.now(),
  version: 0,
})

let ticker: ReturnType<typeof setInterval> | null = null

function tick() {
  state.now = Date.now()
}

function setRunning(entry: Entry | null) {
  state.running = entry
  if (entry && !ticker) ticker = setInterval(tick, 1000)
  if (!entry && ticker) {
    clearInterval(ticker)
    ticker = null
  }
  tick()
}

async function refresh() {
  setRunning(await api.get<Entry | null>('/timer'))
}

async function start(projectId: number, description: string) {
  setRunning(await api.post<Entry>('/timer/start', { project_id: projectId, description }))
  state.version++
}

async function stop() {
  await api.post<Entry>('/timer/stop')
  setRunning(null)
  state.version++
}

async function update(changes: { description?: string; project_id?: number }) {
  setRunning(await api.patch<Entry>('/timer', changes))
}

const elapsed = computed(() =>
  state.running ? Math.max(0, (state.now - Date.parse(state.running.started_at)) / 1000) : 0,
)

export function useTimer() {
  return { state: readonly(state), elapsed, refresh, start, stop, update }
}
