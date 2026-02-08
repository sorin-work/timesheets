<script setup lang="ts">
const props = defineProps<{ page: number; pages: number; total: number }>()
const emit = defineEmits<{ change: [page: number] }>()

function go(page: number) {
  if (page >= 1 && page <= props.pages && page !== props.page) emit('change', page)
}
</script>

<template>
  <nav class="pagination" aria-label="Pagination">
    <span class="muted">{{ total }} {{ total === 1 ? 'entry' : 'entries' }}</span>
    <div class="controls">
      <button type="button" :disabled="page <= 1" @click="go(page - 1)">Previous</button>
      <span>Page {{ page }} of {{ pages }}</span>
      <button type="button" :disabled="page >= pages" @click="go(page + 1)">Next</button>
    </div>
  </nav>
</template>

<style scoped>
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
</style>
