<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api } from '@/api/client'
import type { Client } from '@/api/types'
import ClientForm from '@/components/ClientForm.vue'
import EmptyState from '@/components/EmptyState.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import { formatMoney } from '@/lib/format'

const clients = ref<Client[]>([])
const loading = ref(true)
const error = ref('')
const editing = ref<Client | null>(null)
const creating = ref(false)

async function load() {
  loading.value = true
  error.value = ''
  try {
    clients.value = await api.get<Client[]>('/clients')
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

function closeForm() {
  editing.value = null
  creating.value = false
}

function onSaved() {
  closeForm()
  load()
}

onMounted(load)
</script>

<template>
  <section>
    <div class="page-header">
      <h1>Clients</h1>
      <button class="primary" type="button" @click="creating = true">New client</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="loading" class="muted">Loading…</p>
    <EmptyState
      v-else-if="!clients.length"
      title="No clients yet"
      message="Add the people and companies you work for, with their hourly rate."
    >
      <button class="primary" type="button" @click="creating = true">Add your first client</button>
    </EmptyState>
    <table v-else class="table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Email</th>
          <th class="num">Rate</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in clients" :key="c.id">
          <td>{{ c.name }}</td>
          <td class="muted">{{ c.email ?? '—' }}</td>
          <td class="num">
            {{ c.hourly_rate ? `${formatMoney(c.hourly_rate, c.currency)}/h` : '—' }}
          </td>
          <td class="row-actions">
            <button type="button" @click="editing = c">Edit</button>
          </td>
        </tr>
      </tbody>
    </table>

    <ModalDialog
      v-if="creating || editing"
      :title="editing ? 'Edit client' : 'New client'"
      @close="closeForm"
    >
      <ClientForm :client="editing" @saved="onSaved" @cancel="closeForm" />
    </ModalDialog>
  </section>
</template>
