<script setup lang="ts">
import { reactive, ref } from 'vue'

import { api, ApiError } from '@/api/client'
import type { Invoice } from '@/api/types'
import TaxLinesEditor from '@/components/TaxLinesEditor.vue'

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
    <TaxLinesEditor v-model="form.taxes" />
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

<style scoped></style>
