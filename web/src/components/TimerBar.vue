<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { formatClock } from '@/lib/format'
import { useProjects } from '@/stores/projects'
import { useTimer } from '@/stores/timer'

const timer = useTimer()
const { projects, load } = useProjects()

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
    run(() => timer.start(id, description.value))
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

onMounted(() => {
  load()
  timer.refresh().catch(() => {})
})
</script>

<template>
  <form class="timer" @submit.prevent="toggle">
    <input
      v-model="description"
      class="description"
      placeholder="What are you working on?"
      maxlength="500"
      @blur="saveDescription"
    />
    <select v-model.number="projectId" required aria-label="Project" @change="changeProject">
      <option :value="null" disabled>Project…</option>
      <option v-for="p in projects" :key="p.id" :value="p.id">
        {{ p.client_name }} · {{ p.name }}
      </option>
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
