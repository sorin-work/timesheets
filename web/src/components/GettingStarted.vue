<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { api } from '@/api/client'
import type { Client, Page, Entry, Project, Settings } from '@/api/types'

const steps = ref<{ label: string; to: string; done: boolean }[]>([])
const loaded = ref(false)

const remaining = computed(() => steps.value.filter((s) => !s.done).length)

onMounted(async () => {
  try {
    const [settings, clients, projects, entries] = await Promise.all([
      api.get<Settings>('/settings'),
      api.get<Client[]>('/clients'),
      api.get<Project[]>('/projects'),
      api.get<Page<Entry>>('/entries', { page_size: 1 }),
    ])
    steps.value = [
      { label: 'Add your business details', to: '/settings', done: !!settings.business_name },
      { label: 'Add a client with an hourly rate', to: '/clients', done: clients.length > 0 },
      { label: 'Create a project', to: '/projects', done: projects.length > 0 },
      { label: 'Track some time', to: '/entries', done: entries.total > 0 },
    ]
  } finally {
    loaded.value = true
  }
})
</script>

<template>
  <div v-if="loaded && remaining" class="card getting-started">
    <h2>Getting started</h2>
    <ol>
      <li v-for="step in steps" :key="step.label" :class="{ done: step.done }">
        <RouterLink v-if="!step.done" :to="step.to">{{ step.label }}</RouterLink>
        <span v-else>{{ step.label }}</span>
      </li>
    </ol>
  </div>
</template>

<style scoped>
.getting-started {
  margin-bottom: 1.5rem;
}

h2 {
  font-size: 1rem;
  margin: 0 0 0.5rem;
}

ol {
  margin: 0;
  padding-left: 1.25rem;
}

li.done {
  color: var(--muted);
  text-decoration: line-through;
}
</style>
