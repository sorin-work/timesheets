<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import { api, ApiError } from '@/api/client'
import type { Rounding, Settings } from '@/api/types'
import PasswordForm from '@/components/PasswordForm.vue'
import { useToasts } from '@/stores/toasts'

const toast = useToasts()
import { CURRENCIES } from '@/lib/currencies'

const loaded = ref(false)
const saved = ref(false)
const error = ref('')
const errors = ref<Record<string, string>>({})
const busy = ref(false)

const form = reactive({
  name: '',
  email: '',
  timezone: 'UTC',
  rounding: 'none' as Rounding,
  currency: 'EUR',
  business_name: '',
  business_address: '',
  tax_id: '',
  invoice_prefix: 'INV-',
  payment_terms_days: 14,
})

const timezones: string[] =
  typeof Intl.supportedValuesOf === 'function' ? Intl.supportedValuesOf('timeZone') : ['UTC']
if (!timezones.includes('UTC')) timezones.unshift('UTC')

const ROUNDING: { value: Rounding; label: string }[] = [
  { value: 'none', label: 'No rounding' },
  { value: '6', label: 'Round up to 6 minutes (0.1 h)' },
  { value: '15', label: 'Round up to 15 minutes' },
]

function fill(settings: Settings) {
  Object.assign(form, {
    ...settings,
    business_name: settings.business_name ?? '',
    business_address: settings.business_address ?? '',
    tax_id: settings.tax_id ?? '',
  })
}

async function save() {
  busy.value = true
  saved.value = false
  error.value = ''
  errors.value = {}
  try {
    const { email: _email, ...changes } = form
    fill(await api.patch<Settings>('/settings', changes))
    saved.value = true
    toast.success('Settings saved')
  } catch (e) {
    if (e instanceof ApiError) {
      error.value = e.message
      errors.value = e.fieldErrors()
    } else throw e
  } finally {
    busy.value = false
  }
}

onMounted(async () => {
  fill(await api.get<Settings>('/settings'))
  loaded.value = true
})
</script>

<template>
  <section class="settings">
    <div class="page-header">
      <h1>Settings</h1>
    </div>
    <form v-if="loaded" class="form" @submit.prevent="save">
      <fieldset class="card form">
        <legend>Profile</legend>
        <label>
          Name
          <input v-model="form.name" required maxlength="120" />
        </label>
        <label>
          Email
          <input :value="form.email" disabled />
        </label>
      </fieldset>

      <fieldset class="card form">
        <legend>Time tracking</legend>
        <label>
          Time zone
          <select v-model="form.timezone">
            <option v-for="tz in timezones" :key="tz" :value="tz">{{ tz }}</option>
          </select>
          <small class="muted">Used to decide which day an entry belongs to.</small>
        </label>
        <label>
          Rounding when invoicing
          <select v-model="form.rounding">
            <option v-for="r in ROUNDING" :key="r.value" :value="r.value">{{ r.label }}</option>
          </select>
          <small class="muted">Applied to each entry; your tracked time is not changed.</small>
        </label>
      </fieldset>

      <fieldset class="card form">
        <legend>Invoices</legend>
        <label>
          Business name
          <input v-model="form.business_name" maxlength="200" :placeholder="form.name" />
        </label>
        <label>
          Address
          <textarea v-model="form.business_address" rows="3" />
        </label>
        <div class="row">
          <label>
            Tax / VAT ID
            <input v-model="form.tax_id" maxlength="64" />
          </label>
          <label>
            Default currency
            <select v-model="form.currency">
              <option v-for="c in CURRENCIES" :key="c" :value="c">{{ c }}</option>
            </select>
          </label>
        </div>
        <div class="row">
          <label>
            Number prefix
            <input v-model="form.invoice_prefix" maxlength="16" />
            <small v-if="errors.invoice_prefix" class="error">Letters, digits, - _ / only</small>
          </label>
          <label>
            Payment terms (days)
            <input v-model.number="form.payment_terms_days" type="number" min="0" max="365" />
          </label>
        </div>
      </fieldset>

      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <div class="actions">
        <span v-if="saved" class="saved">Saved</span>
        <button class="primary" type="submit" :disabled="busy">Save settings</button>
      </div>
    </form>

    <PasswordForm class="password" />
  </section>
</template>

<style scoped>
.settings {
  max-width: 40rem;
}

fieldset {
  border: 1px solid var(--border);
}

legend {
  font-weight: 600;
  padding: 0 0.25rem;
}

.password {
  margin-top: 1.5rem;
}

.saved {
  color: var(--success);
  align-self: center;
}
</style>
