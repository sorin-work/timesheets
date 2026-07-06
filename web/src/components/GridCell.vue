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

/** Left/right only leave the cell when the caret is already at that end of the text. */
function atEdge(event: KeyboardEvent, edge: 'start' | 'end'): boolean {
  const input = event.target as HTMLInputElement
  const position = edge === 'start' ? 0 : input.value.length
  return input.selectionStart === position && input.selectionEnd === position
}

function move(event: KeyboardEvent, dx: number, dy: number) {
  const input = event.target as HTMLInputElement
  const cell = input.closest('td')
  const row = cell?.parentElement
  if (!cell || !row) return
  let target: Element | null | undefined
  if (dy !== 0) {
    const sibling = dy < 0 ? row.previousElementSibling : row.nextElementSibling
    target = sibling?.children[[...row.children].indexOf(cell)]
  } else {
    target = dx < 0 ? cell.previousElementSibling : cell.nextElementSibling
  }
  const next = target?.querySelector<HTMLInputElement>('input.cell')
  if (next) {
    event.preventDefault()
    next.focus()
  }
}

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
    @keydown.up.prevent="move($event, 0, -1)"
    @keydown.down.prevent="move($event, 0, 1)"
    @keydown.left="atEdge($event, 'start') && move($event, -1, 0)"
    @keydown.right="atEdge($event, 'end') && move($event, 1, 0)"
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
