<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { api } from '@/api/client'
import type { Client } from '@/api/types'
import ClientForm from '@/components/ClientForm.vue'
import EmptyState from '@/components/EmptyState.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import SkeletonRows from '@/components/SkeletonRows.vue'
import { formatMoney } from '@/lib/format'
import { useToasts } from '@/stores/toasts'

const toast = useToasts()

const clients = ref<Client[]>([])
const loading = ref(true)
const error = ref('')
const editing = ref<Client | null>(null)
const creating = ref(false)
const showArchived = ref(false)
const search = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    clients.value = await api.get<Client[]>('/clients', {
      include_archived: showArchived.value,
      q: search.value.trim(),
    })
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

function onSaved(client: Client) {
  toast.success(editing.value ? `Saved ${client.name}` : `Added ${client.name}`)
  closeForm()
  load()
}

async function toggleArchived(client: Client) {
  const action = client.archived_at ? 'restore' : 'archive'
  if (action === 'archive' && !confirm(`Archive ${client.name}? Their history is kept.`)) return
  try {
    await api.post(`/clients/${client.id}/${action}`)
    toast.success(action === 'archive' ? `Archived ${client.name}` : `Restored ${client.name}`)
    await load()
  } catch (e) {
    toast.error((e as Error).message)
  }
}

let debounce: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  clearTimeout(debounce)
  debounce = setTimeout(load, 250)
})

onMounted(load)
</script>

<template>
  <section>
    <div class="page-header">
      <h1>Clients</h1>
      <div class="header-actions">
        <input v-model="search" type="search" placeholder="Search clients" aria-label="Search" />
        <label class="inline">
          <input v-model="showArchived" type="checkbox" @change="load" />
          Show archived
        </label>
        <button class="primary" type="button" @click="creating = true">New client</button>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <SkeletonRows v-else-if="loading" />
    <EmptyState
      v-else-if="!clients.length && search.trim()"
      :title="`No clients match “${search.trim()}”`"
    />
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
          <th class="hide-sm">Email</th>
          <th class="num">Rate</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in clients" :key="c.id" :class="{ archived: c.archived_at }">
          <td>
            <RouterLink :to="`/clients/${c.id}`">{{ c.name }}</RouterLink>
            <span v-if="c.archived_at" class="badge">archived</span>
          </td>
          <td class="muted hide-sm">{{ c.email ?? '—' }}</td>
          <td class="num">
            {{ c.hourly_rate ? `${formatMoney(c.hourly_rate, c.currency)}/h` : '—' }}
          </td>
          <td class="row-actions">
            <button type="button" @click="editing = c">Edit</button>
            <button type="button" @click="toggleArchived(c)">
              {{ c.archived_at ? 'Restore' : 'Archive' }}
            </button>
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

<style scoped>
.archived td {
  color: var(--muted);
}
</style>
