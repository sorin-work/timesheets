<script setup lang="ts">
import { reactive, ref } from 'vue'

import { api, ApiError } from '@/api/client'
import type { Invoice } from '@/api/types'

const props = defineProps<{ invoiceId: number }>()
const emit = defineEmits<{ added: [invoice: Invoice] }>()

const form = reactive({ description: '', quantity: '1', unit_price: '' })
const error = ref('')
const busy = ref(false)

async function submit() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    const invoice = await api.post<Invoice>(`/invoices/${props.invoiceId}/lines`, {
      ...form,
      unit_price: form.unit_price.replace(',', '.'),
      quantity: form.quantity.replace(',', '.'),
    })
    Object.assign(form, { description: '', quantity: '1', unit_price: '' })
    emit('added', invoice)
  } catch (e) {
    error.value = e instanceof ApiError ? (e.details[0]?.message ?? e.message) : 'Failed'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="add-line" @submit.prevent="submit">
    <input
      v-model="form.description"
      placeholder="Expense, fee or discount"
      required
      maxlength="500"
    />
    <input v-model="form.quantity" aria-label="Quantity" inputmode="decimal" required />
    <input
      v-model="form.unit_price"
      aria-label="Unit price"
      placeholder="Price"
      inputmode="decimal"
      required
    />
    <button type="submit" :disabled="busy">Add line</button>
    <small v-if="error" class="error">{{ error }}</small>
  </form>
</template>

<style scoped>
.add-line {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 0.75rem;
}

.add-line input:first-child {
  flex: 1;
  min-width: 12rem;
}

.add-line input:not(:first-child) {
  width: 6rem;
}

.error {
  width: 100%;
}
</style>
