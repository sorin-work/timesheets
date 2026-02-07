import { computed, ref } from 'vue'

import { api } from '@/api/client'
import type { Project } from '@/api/types'

const projects = ref<Project[]>([])
let loaded: Promise<void> | null = null

/** Active projects for pickers, loaded once and shared between components. */
export function useProjects() {
  function load(force = false): Promise<void> {
    if (!loaded || force) {
      loaded = api.get<Project[]>('/projects').then((list) => {
        projects.value = list
      })
    }
    return loaded
  }

  const byId = computed(() => new Map(projects.value.map((p) => [p.id, p])))

  return { projects, byId, load }
}
