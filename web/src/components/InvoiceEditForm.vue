<script setup lang="ts">
import { reactive, ref } from 'vue'

import { api, ApiError } from '@/api/client'
import type { Invoice } from '@/api/types'

const props = defineProps<{ invoice: Invoice }>()
const emit = defineEmits<{ saved: [invoice: Invoice]; cancel: [] }>()

const form = reactive({
  issue_date: props.invoice.issue_date,
  due_date: props.invoice.due_date,
  notes: props.invoice.notes ?? '',
  taxes: props.invoice.taxes.map((t) => ({ name: t.name, rate: String(Number(t.rate)) })),
})
const error = ref('')
const busy = ref(false)

async function submit() {
  busy.value = true
  error.value = ''
  try {
    emit('saved', await api.patch<Invoice>(`/invoices/${props.invoice.id}`, form))
  } catch (e) {
    if (e instanceof ApiError) error.value = e.details[0]?.message ?? e.message
    else throw e
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="form" @submit.prevent="submit">
    <div class="row">
      <label>
        Issue date
        <input v-model="form.issue_date" type="date" required />
      </label>
      <label>
        Due date
        <input v-model="form.due_date" type="date" required />
      </label>
    </div>
    <fieldset class="taxes">
      <legend>Taxes</legend>
      <div v-for="(tax, i) in form.taxes" :key="i" class="tax-row">
        <input v-model="tax.name" aria-label="Tax name" maxlength="60" required />
        <input v-model="tax.rate" aria-label="Rate %" inputmode="decimal" required />
        <span>%</span>
        <button type="button" @click="form.taxes.splice(i, 1)">Remove</button>
      </div>
      <button
        type="button"
        :disabled="form.taxes.length >= 5"
        @click="form.taxes.push({ name: 'VAT', rate: '19' })"
      >
        Add tax
      </button>
    </fieldset>
    <label>
      Notes
      <textarea v-model="form.notes" rows="4" />
    </label>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="actions">
      <button type="button" @click="emit('cancel')">Cancel</button>
      <button class="primary" type="submit" :disabled="busy">Save</button>
    </div>
  </form>
</template>

<style scoped>
.taxes {
  border: 1px solid var(--border);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-start;
}

.tax-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.tax-row input:last-of-type {
  width: 5rem;
}
</style>
