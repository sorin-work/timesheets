<script setup lang="ts">
import { reactive, ref } from 'vue'

import { api, ApiError } from '@/api/client'
import type { Client } from '@/api/types'
import { CURRENCIES } from '@/lib/currencies'

const props = defineProps<{ client?: Client | null }>()
const emit = defineEmits<{ saved: [client: Client]; cancel: [] }>()

const form = reactive({
  name: props.client?.name ?? '',
  email: props.client?.email ?? '',
  address: props.client?.address ?? '',
  currency: props.client?.currency ?? 'EUR',
  hourly_rate: props.client?.hourly_rate ?? '',
  notes: props.client?.notes ?? '',
})
const errors = ref<Record<string, string>>({})
const error = ref('')
const busy = ref(false)

async function submit() {
  busy.value = true
  errors.value = {}
  error.value = ''
  const payload = {
    ...form,
    email: form.email.trim() || null,
    hourly_rate: String(form.hourly_rate).trim() || null,
  }
  try {
    const saved = props.client
      ? await api.patch<Client>(`/clients/${props.client.id}`, payload)
      : await api.post<Client>('/clients', payload)
    emit('saved', saved)
  } catch (e) {
    if (e instanceof ApiError) {
      errors.value = e.fieldErrors()
      error.value = e.message
    } else throw e
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="form" @submit.prevent="submit">
    <label>
      Name
      <input v-model="form.name" required maxlength="200" />
      <small v-if="errors.name" class="error">{{ errors.name }}</small>
    </label>
    <div class="row">
      <label>
        Hourly rate
        <input v-model="form.hourly_rate" inputmode="decimal" placeholder="e.g. 85.00" />
        <small v-if="errors.hourly_rate" class="error">{{ errors.hourly_rate }}</small>
      </label>
      <label>
        Currency
        <select v-model="form.currency">
          <option v-for="c in CURRENCIES" :key="c" :value="c">{{ c }}</option>
        </select>
      </label>
    </div>
    <label>
      Billing email
      <input v-model="form.email" type="email" />
      <small v-if="errors.email" class="error">{{ errors.email }}</small>
    </label>
    <label>
      Address
      <textarea v-model="form.address" rows="3" />
    </label>
    <label>
      Notes
      <textarea v-model="form.notes" rows="2" />
    </label>
    <p v-if="error && !Object.keys(errors).length" class="error">{{ error }}</p>
    <div class="actions">
      <button type="button" @click="emit('cancel')">Cancel</button>
      <button class="primary" type="submit" :disabled="busy">
        {{ client ? 'Save changes' : 'Add client' }}
      </button>
    </div>
  </form>
</template>
