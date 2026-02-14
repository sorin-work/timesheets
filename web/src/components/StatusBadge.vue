<script setup lang="ts">
import type { InvoiceStatus } from '@/api/types'

defineProps<{ status: InvoiceStatus }>()
</script>

<template>
  <span class="status" :class="status">{{ status }}</span>
</template>

<style scoped>
.status {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
  padding: 0.125rem 0.625rem;
  border-radius: 999px;
}

.draft {
  background: #e2e8f0;
  color: #475569;
}

.sent {
  background: #dbeafe;
  color: #1d4ed8;
}

.paid {
  background: #dcfce7;
  color: #166534;
}

.overdue {
  background: #fee2e2;
  color: #b91c1c;
}
</style>
