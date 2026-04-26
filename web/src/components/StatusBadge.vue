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

<style>
:root[data-theme='dark'] .status.draft {
  background: #334155;
  color: #cbd5e1;
}

:root[data-theme='dark'] .status.sent {
  background: #1e3a8a;
  color: #bfdbfe;
}

:root[data-theme='dark'] .status.paid {
  background: #14532d;
  color: #bbf7d0;
}

:root[data-theme='dark'] .status.overdue {
  background: #7f1d1d;
  color: #fecaca;
}
</style>
