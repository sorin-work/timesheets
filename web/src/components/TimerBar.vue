<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch, watchEffect } from 'vue'
import { useRoute } from 'vue-router'

import { formatClock } from '@/lib/format'
import { pageTitle } from '@/lib/title'
import { useProjects } from '@/stores/projects'
import { useTimer } from '@/stores/timer'

const timer = useTimer()
const { projects, grouped, load } = useProjects()

const projectId = ref<number | null>(null)
const description = ref('')
const busy = ref(false)
const error = ref('')

watch(
  () => timer.state.running,
  (running) => {
    if (running) {
      projectId.value = running.project_id
      description.value = running.description
    }
  },
)

async function run(action: () => Promise<void>) {
  busy.value = true
  error.value = ''
  try {
    await action()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}

function toggle() {
  if (timer.state.running) {
    run(async () => {
      await timer.stop()
      description.value = ''
    })
  } else if (projectId.value) {
    const id = projectId.value
    rememberProject(id)
    run(() => timer.start(id, description.value))
  }
}

const LAST_PROJECT = 'timesheets.lastProject'

function rememberProject(id: number) {
  try {
    localStorage.setItem(LAST_PROJECT, String(id))
  } catch {
    // private mode: nothing to remember
  }
}

function lastProject(): number | null {
  try {
    const id = Number(localStorage.getItem(LAST_PROJECT))
    return projects.value.some((p) => p.id === id) ? id : null
  } catch {
    return null
  }
}

function saveDescription() {
  const running = timer.state.running
  if (running && running.description !== description.value) {
    run(() => timer.update({ description: description.value }))
  }
}

function changeProject() {
  if (timer.state.running && projectId.value) {
    const id = projectId.value
    run(() => timer.update({ project_id: id }))
  }
}

// Show the running time in the browser tab, so it is visible from other tabs.
// The page title comes from the current route, not from when the timer started.
const route = useRoute()
watchEffect(() => {
  const running = timer.state.running
  if (running) {
    document.title = `▶ ${formatClock(timer.elapsed.value)} · ${running.project_name}`
  } else if (document.title.startsWith('▶')) {
    document.title = pageTitle(route)
  }
})

const descriptionInput = ref<HTMLInputElement | null>(null)

function onShortcut(event: KeyboardEvent) {
  if (!event.altKey || event.ctrlKey || event.metaKey) return
  if (event.code === 'KeyS') {
    event.preventDefault()
    toggle()
  } else if (event.code === 'KeyN') {
    event.preventDefault()
    descriptionInput.value?.focus()
  }
}

onMounted(() => {
  document.addEventListener('keydown', onShortcut)
  load().then(() => {
    if (!timer.state.running && projectId.value === null) projectId.value = lastProject()
  })
  timer.refresh().catch(() => {})
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onShortcut)
  if (document.title.startsWith('▶')) document.title = pageTitle(route)
})
</script>

<template>
  <form class="timer" @submit.prevent="toggle">
    <input
      ref="descriptionInput"
      v-model="description"
      class="description"
      title="Alt+N to focus, Alt+S to start or stop"
      placeholder="What are you working on?"
      maxlength="500"
      @blur="saveDescription"
    />
    <select v-model.number="projectId" required aria-label="Project" @change="changeProject">
      <option :value="null" disabled>Project…</option>
      <optgroup v-for="[clientName, list] in grouped" :key="clientName" :label="clientName">
        <option v-for="p in list" :key="p.id" :value="p.id">{{ p.name }}</option>
      </optgroup>
    </select>
    <span class="clock" :class="{ live: timer.state.running }">
      {{ formatClock(timer.elapsed.value) }}
    </span>
    <button
      type="submit"
      :class="timer.state.running ? 'stop' : 'primary'"
      :disabled="busy || (!timer.state.running && !projectId)"
    >
      {{ timer.state.running ? 'Stop' : 'Start' }}
    </button>
    <span v-if="error" class="error">{{ error }}</span>
  </form>
</template>

<style scoped>
.timer {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  flex-wrap: wrap;
}

.description {
  flex: 1;
  min-width: 12rem;
}

select {
  max-width: 16rem;
}

.clock {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  min-width: 5rem;
  text-align: right;
  color: var(--muted);
}

.clock.live {
  color: var(--text);
}

.stop {
  background: var(--danger);
  border-color: var(--danger);
  color: white;
}
</style>
