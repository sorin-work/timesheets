<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'

defineProps<{ title: string }>()
const emit = defineEmits<{ close: [] }>()

function onKey(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close')
}

onMounted(() => document.addEventListener('keydown', onKey))
onBeforeUnmount(() => document.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="backdrop" @mousedown.self="emit('close')">
    <div class="dialog card" role="dialog" aria-modal="true" :aria-label="title">
      <header>
        <h2>{{ title }}</h2>
        <button type="button" class="close" aria-label="Close" @click="emit('close')">×</button>
      </header>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  background: rgb(15 23 42 / 0.45);
  display: grid;
  place-items: center;
  padding: 1rem;
  z-index: 50;
}

.dialog {
  width: 100%;
  max-width: 32rem;
  max-height: calc(100vh - 2rem);
  overflow: auto;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

h2 {
  margin: 0;
  font-size: 1.125rem;
}

.close {
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  padding: 0 0.25rem;
  background: none;
}
</style>
