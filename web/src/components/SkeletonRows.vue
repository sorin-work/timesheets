<script setup lang="ts">
withDefaults(defineProps<{ rows?: number }>(), { rows: 5 })
</script>

<template>
  <div class="skeleton card" aria-busy="true" aria-label="Loading">
    <div v-for="i in rows" :key="i" class="line" :style="{ width: `${90 - ((i * 17) % 35)}%` }" />
  </div>
</template>

<style scoped>
.skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.line {
  height: 0.875rem;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--subtle), var(--border), var(--subtle));
  background-size: 200% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}

@keyframes shimmer {
  from {
    background-position: 200% 0;
  }

  to {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .line {
    animation: none;
  }
}
</style>
