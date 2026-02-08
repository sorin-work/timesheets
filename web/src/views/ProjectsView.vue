<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { api } from '@/api/client'
import type { Client, Project } from '@/api/types'
import EmptyState from '@/components/EmptyState.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import ProjectForm from '@/components/ProjectForm.vue'
import { formatMoney } from '@/lib/format'
import { useProjects } from '@/stores/projects'

const { load: refreshPickers } = useProjects()

const projects = ref<Project[]>([])
const clients = ref<Client[]>([])
const loading = ref(true)
const error = ref('')
const editing = ref<Project | null>(null)
const creating = ref(false)
const showArchived = ref(false)

const byClient = computed(() => {
  const groups = new Map<string, Project[]>()
  for (const p of projects.value) {
    const list = groups.get(p.client_name) ?? []
    list.push(p)
    groups.set(p.client_name, list)
  }
  return [...groups.entries()]
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    ;[projects.value, clients.value] = await Promise.all([
      api.get<Project[]>('/projects', { include_archived: showArchived.value }),
      api.get<Client[]>('/clients'),
    ])
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

async function toggleArchived(project: Project) {
  const action = project.archived_at ? 'restore' : 'archive'
  try {
    await api.post(`/projects/${project.id}/${action}`)
    await load()
    refreshPickers(true)
  } catch (e) {
    error.value = (e as Error).message
  }
}

function closeForm() {
  editing.value = null
  creating.value = false
}

function onSaved() {
  closeForm()
  load()
  refreshPickers(true)
}

onMounted(load)
</script>

<template>
  <section>
    <div class="page-header">
      <h1>Projects</h1>
      <div class="header-actions">
        <label class="inline">
          <input v-model="showArchived" type="checkbox" @change="load" />
          Show archived
        </label>
        <button class="primary" type="button" :disabled="!clients.length" @click="creating = true">
          New project
        </button>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="loading" class="muted">Loading…</p>
    <EmptyState
      v-else-if="!clients.length"
      title="Add a client first"
      message="Projects belong to a client."
    >
      <RouterLink to="/clients">Go to clients</RouterLink>
    </EmptyState>
    <EmptyState
      v-else-if="!projects.length"
      title="No projects yet"
      message="Create a project to start tracking time."
    />
    <div v-else class="groups">
      <div v-for="[clientName, list] in byClient" :key="clientName">
        <h2>{{ clientName }}</h2>
        <table class="table">
          <tbody>
            <tr v-for="p in list" :key="p.id">
              <td>
                <span class="dot" :style="{ background: p.color }" />
                {{ p.name }}
                <span v-if="!p.billable" class="badge">non-billable</span>
                <span v-if="p.archived_at" class="badge">archived</span>
              </td>
              <td class="num">
                <template v-if="p.effective_rate">
                  {{ formatMoney(p.effective_rate, p.currency) }}/h
                  <span v-if="!p.hourly_rate" class="muted">(client)</span>
                </template>
                <span v-else class="muted">no rate</span>
              </td>
              <td class="row-actions">
                <button type="button" @click="editing = p">Edit</button>
                <button type="button" @click="toggleArchived(p)">
                  {{ p.archived_at ? 'Restore' : 'Archive' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ModalDialog
      v-if="creating || editing"
      :title="editing ? 'Edit project' : 'New project'"
      @close="closeForm"
    >
      <ProjectForm :project="editing" :clients="clients" @saved="onSaved" @cancel="closeForm" />
    </ModalDialog>
  </section>
</template>

<style scoped>
.groups {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

h2 {
  font-size: 1rem;
  margin: 0 0 0.5rem;
}

.dot {
  display: inline-block;
  width: 0.625rem;
  height: 0.625rem;
  border-radius: 999px;
  margin-right: 0.375rem;
}
</style>
