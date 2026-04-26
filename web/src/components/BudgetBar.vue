<script setup lang="ts">
import { computed } from 'vue'

import { formatDuration } from '@/lib/format'

const props = defineProps<{ usedSeconds: number; budgetHours: string }>()

const budgetSeconds = computed(() => Number(props.budgetHours) * 3600)
const percent = computed(() => Math.round((props.usedSeconds / budgetSeconds.value) * 100))
const level = computed(() => (percent.value >= 100 ? 'over' : percent.value >= 80 ? 'near' : 'ok'))
</script>

<template>
  <div class="budget" :class="level" :title="`${percent}% of ${budgetHours} h`">
    <div class="track">
      <div class="fill" :style="{ width: `${Math.min(100, percent)}%` }" />
    </div>
    <small>{{ formatDuration(usedSeconds) }} / {{ Number(budgetHours) }} h</small>
  </div>
</template>

<style scoped>
.budget {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 10rem;
}

.track {
  flex: 1;
  height: 0.375rem;
  background: var(--subtle);
  border-radius: 999px;
  overflow: hidden;
}

.fill {
  height: 100%;
  background: var(--success);
}

.near .fill {
  background: var(--warning);
}

.over .fill {
  background: var(--danger);
}

.over small {
  color: var(--danger);
}
</style>
