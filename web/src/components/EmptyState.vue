<script setup lang="ts">
defineProps<{ title: string; message?: string }>()
</script>

<template>
  <div class="empty card">
    <strong>{{ title }}</strong>
    <p v-if="message" class="muted">{{ message }}</p>
    <slot />
  </div>
</template>

<style scoped>
.empty {
  text-align: center;
  padding: 2.5rem 1rem;
}

.empty p {
  margin: 0.25rem 0 1rem;
}
</style>
