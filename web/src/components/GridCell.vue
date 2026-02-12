<script setup lang="ts">
import { ref, watch } from 'vue'

import { formatDuration, parseDuration } from '@/lib/format'

const props = defineProps<{ seconds: number; disabled?: boolean; label: string }>()
const emit = defineEmits<{ change: [minutes: number] }>()

const text = ref('')
const invalid = ref(false)

function reset() {
  text.value = props.seconds ? formatDuration(props.seconds) : ''
  invalid.value = false
}

watch(() => props.seconds, reset, { immediate: true })

function commit() {
  const minutes = parseDuration(text.value)
  if (minutes === null || minutes > 24 * 60) {
    invalid.value = true
    return
  }
  invalid.value = false
  if (minutes * 60 !== Math.floor(props.seconds / 60) * 60) emit('change', minutes)
  else reset()
}
</script>

<template>
  <input
    v-model="text"
    class="cell"
    :class="{ invalid }"
    :disabled="disabled"
    :aria-label="label"
    inputmode="decimal"
    placeholder="–"
    @focus="($event.target as HTMLInputElement).select()"
    @keydown.enter.prevent="($event.target as HTMLInputElement).blur()"
    @keydown.esc="reset"
    @blur="commit"
  />
</template>

<style scoped>
.cell {
  width: 4.5rem;
  text-align: right;
  font-variant-numeric: tabular-nums;
  border-color: transparent;
  background: transparent;
  padding: 0.375rem 0.5rem;
}

.cell:hover:not(:disabled),
.cell:focus {
  border-color: var(--border);
  background: var(--surface);
}

.cell.invalid {
  border-color: var(--danger);
}
</style>
