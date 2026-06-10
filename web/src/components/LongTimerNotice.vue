<script setup lang="ts">
import { computed, ref } from 'vue'

import { formatTime } from '@/lib/format'
import { useTimer } from '@/stores/timer'
import { useToasts } from '@/stores/toasts'

/** Shown when the timer has been running suspiciously long, e.g. overnight. */
const LIMIT_SECONDS = 10 * 3600

const timer = useTimer()
const toast = useToasts()
const endTime = ref('')

const visible = computed(() => timer.state.running && timer.elapsed.value > LIMIT_SECONDS)

async function stopAt() {
  const running = timer.state.running
  if (!running || !endTime.value) return
  const start = new Date(running.started_at)
  const [h, m] = endTime.value.split(':').map(Number)
  const end = new Date(start)
  end.setHours(h!, m!, 0, 0)
  if (end <= start) end.setDate(end.getDate() + 1)
  try {
    await timer.stop(end)
    toast.success(`Stopped at ${formatTime(end.toISOString())}`)
  } catch (e) {
    toast.error((e as Error).message)
  }
}
</script>

<template>
  <div v-if="visible" class="notice" role="alert">
    <span>
      The timer has been running since
      {{ formatTime(timer.state.running!.started_at) }}. Forgot to stop it?
    </span>
    <form @submit.prevent="stopAt">
      <label class="inline">
        Stopped at
        <input v-model="endTime" type="time" required />
      </label>
      <button type="submit">Stop there</button>
    </form>
  </div>
</template>

<style scoped>
.notice {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.5rem 2rem;
  background: #fef3c7;
  color: #78350f;
  border-bottom: 1px solid #fde68a;
}

form {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
</style>
