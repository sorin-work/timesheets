<script setup lang="ts">
import { useToasts } from '@/stores/toasts'

const { toasts, dismiss } = useToasts()
</script>

<template>
  <div class="toasts" aria-live="polite">
    <TransitionGroup name="toast">
      <div v-for="t in toasts" :key="t.id" class="toast" :class="t.kind" role="status">
        <span>{{ t.message }}</span>
        <button type="button" aria-label="Dismiss" @click="dismiss(t.id)">×</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toasts {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 100;
  max-width: 22rem;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  border-radius: var(--radius);
  background: #1f2937;
  color: white;
  box-shadow: 0 6px 20px rgb(0 0 0 / 0.15);
}

.toast.success {
  background: #166534;
}

.toast.error {
  background: #b91c1c;
}

.toast span {
  flex: 1;
}

.toast button {
  border: none;
  background: none;
  color: inherit;
  padding: 0;
  font-size: 1.125rem;
  line-height: 1;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(0.5rem);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s;
}
</style>
