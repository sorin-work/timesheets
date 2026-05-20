<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, getToken } from '@/api/client'
import type { Client, Invoice, Settings } from '@/api/types'
import InvoiceEditForm from '@/components/InvoiceEditForm.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { formatDate, formatMoney } from '@/lib/format'
import { useToasts } from '@/stores/toasts'

const toast = useToasts()

const route = useRoute()
const router = useRouter()
const id = Number(route.params.id)

const invoice = ref<Invoice | null>(null)
const client = ref<Client | null>(null)
const settings = ref<Settings | null>(null)
const error = ref('')
const busy = ref(false)
const editing = ref(false)

function onSaved(updated: Invoice) {
  invoice.value = updated
  editing.value = false
}
const paidOn = ref(new Date().toISOString().slice(0, 10))

const pdfUrl = computed(
  () => `/api/invoices/${id}/pdf?token=${encodeURIComponent(getToken() ?? '')}`,
)

async function act(action: 'send' | 'pay' | 'unpay' | 'revert') {
  busy.value = true
  error.value = ''
  try {
    const body = action === 'pay' ? { paid_on: paidOn.value } : undefined
    invoice.value = await api.post<Invoice>(`/invoices/${id}/${action}`, body)
    toast.success(`Invoice ${invoice.value.number} is now ${invoice.value.status}`)
  } catch (e) {
    toast.error((e as Error).message)
  } finally {
    busy.value = false
  }
}

async function remove() {
  if (!confirm('Delete this draft? Its time entries become unbilled again.')) return
  busy.value = true
  try {
    await api.delete(`/invoices/${id}`)
    toast.success('Draft deleted')
    await router.push('/invoices')
  } catch (e) {
    error.value = (e as Error).message
    busy.value = false
  }
}

function money(amount: string) {
  return formatMoney(amount, invoice.value!.currency)
}

onMounted(async () => {
  try {
    invoice.value = await api.get<Invoice>(`/invoices/${id}`)
    ;[client.value, settings.value] = await Promise.all([
      api.get<Client>(`/clients/${invoice.value.client_id}`),
      api.get<Settings>('/settings'),
    ])
  } catch (e) {
    error.value = (e as Error).message
  }
})
</script>

<template>
  <section>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <template v-if="invoice">
      <div class="page-header">
        <h1>
          Invoice {{ invoice.number }}
          <StatusBadge :status="invoice.status" />
        </h1>
        <RouterLink to="/invoices">All invoices</RouterLink>
      </div>

      <div class="toolbar">
        <a class="button" :href="pdfUrl" target="_blank" rel="noopener">Download PDF</a>
        <template v-if="invoice.status === 'draft'">
          <button class="primary" type="button" :disabled="busy" @click="act('send')">
            Mark as sent
          </button>
          <button type="button" :disabled="busy" @click="editing = true">Edit</button>
          <button class="danger" type="button" :disabled="busy" @click="remove">
            Delete draft
          </button>
        </template>
        <template v-else-if="invoice.status === 'sent' || invoice.status === 'overdue'">
          <label class="inline">
            Paid on
            <input v-model="paidOn" type="date" />
          </label>
          <button class="primary" type="button" :disabled="busy" @click="act('pay')">
            Mark as paid
          </button>
          <button type="button" :disabled="busy" @click="act('revert')">Back to draft</button>
        </template>
        <template v-else-if="invoice.status === 'paid'">
          <span class="muted">Paid on {{ formatDate(invoice.paid_at!) }}</span>
          <button type="button" :disabled="busy" @click="act('unpay')">Mark as unpaid</button>
        </template>
      </div>

      <article class="paper card">
        <div class="parties">
          <div>
            <div class="muted label">From</div>
            <strong>{{ settings?.business_name || settings?.name }}</strong>
            <div class="pre">{{ settings?.business_address }}</div>
            <div v-if="settings?.tax_id">Tax ID: {{ settings.tax_id }}</div>
          </div>
          <div>
            <div class="muted label">Bill to</div>
            <strong>{{ invoice.client_name }}</strong>
            <div class="pre">{{ client?.address }}</div>
            <div v-if="client?.email" class="muted">{{ client.email }}</div>
          </div>
          <dl class="dates">
            <dt>Issued</dt>
            <dd>{{ formatDate(invoice.issue_date) }}</dd>
            <dt>Due</dt>
            <dd>{{ formatDate(invoice.due_date) }}</dd>
            <template v-if="invoice.period_start && invoice.period_end">
              <dt>Period</dt>
              <dd>{{ formatDate(invoice.period_start) }} – {{ formatDate(invoice.period_end) }}</dd>
            </template>
          </dl>
        </div>

        <table class="lines">
          <thead>
            <tr>
              <th>Description</th>
              <th class="num">Hours</th>
              <th class="num">Rate</th>
              <th class="num">Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="line in invoice.lines" :key="line.id">
              <td>{{ line.description }}</td>
              <td class="num">{{ line.quantity }}</td>
              <td class="num">{{ money(line.unit_price) }}</td>
              <td class="num">{{ money(line.amount) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td colspan="3" class="num">Subtotal</td>
              <td class="num">{{ money(invoice.subtotal) }}</td>
            </tr>
            <tr v-for="tax in invoice.taxes" :key="tax.name">
              <td colspan="3" class="num">{{ tax.name }} ({{ Number(tax.rate) }}%)</td>
              <td class="num">{{ money(tax.amount) }}</td>
            </tr>
            <tr class="grand">
              <td colspan="3" class="num">Total</td>
              <td class="num">{{ money(invoice.total) }}</td>
            </tr>
          </tfoot>
        </table>

        <div v-if="invoice.notes" class="notes">{{ invoice.notes }}</div>
      </article>

      <ModalDialog v-if="editing" title="Edit draft" @close="editing = false">
        <InvoiceEditForm :invoice="invoice" @saved="onSaved" @cancel="editing = false" />
      </ModalDialog>
    </template>
    <p v-else class="muted">Loading…</p>
  </section>
</template>

<style scoped>
h1 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.paper {
  padding: 2rem;
  max-width: 52rem;
}

.parties {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.label {
  font-size: 0.75rem;
  text-transform: uppercase;
}

.pre {
  white-space: pre-line;
}

.dates {
  display: grid;
  grid-template-columns: auto auto;
  gap: 0.25rem 1rem;
  margin: 0;
}

.dates dt {
  color: var(--muted);
}

.dates dd {
  margin: 0;
  text-align: right;
}

.lines {
  width: 100%;
  border-collapse: collapse;
}

.lines th,
.lines td {
  padding: 0.5rem;
  border-bottom: 1px solid var(--border);
  text-align: left;
}

.lines tfoot td {
  border-bottom: none;
}

.grand td {
  font-weight: 700;
  border-top: 2px solid var(--text);
}

.notes {
  white-space: pre-line;
  margin-top: 2rem;
  color: var(--muted);
}

@media (max-width: 700px) {
  .parties {
    grid-template-columns: 1fr;
  }
}
</style>
