<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

import ModalDialog from '@/components/ModalDialog.vue'

const open = ref(false)

const SHORTCUTS = [
  ['Alt + S', 'Start or stop the timer'],
  ['Alt + N', 'Type what you are working on'],
  ['↑ ↓ ← →', 'Move between timesheet cells'],
  ['Enter', 'Save a timesheet cell'],
  ['Esc', 'Undo a cell edit or close a dialog'],
  ['?', 'Show this help'],
]

function onKey(event: KeyboardEvent) {
  const target = event.target as HTMLElement | null
  const typing = target?.closest('input, textarea, select, [contenteditable]')
  if (event.key === '?' && !typing) {
    event.preventDefault()
    open.value = true
  }
}

onMounted(() => document.addEventListener('keydown', onKey))
onBeforeUnmount(() => document.removeEventListener('keydown', onKey))
</script>

<template>
  <ModalDialog v-if="open" title="Keyboard shortcuts" @close="open = false">
    <dl class="shortcuts">
      <template v-for="[keys, action] in SHORTCUTS" :key="keys">
        <dt>
          <kbd>{{ keys }}</kbd>
        </dt>
        <dd>{{ action }}</dd>
      </template>
    </dl>
  </ModalDialog>
</template>

<style scoped>
.shortcuts {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.5rem 1rem;
  margin: 0;
}

dd {
  margin: 0;
}

kbd {
  font-family: inherit;
  font-size: 0.8125rem;
  padding: 0.125rem 0.375rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--subtle);
}
</style>
