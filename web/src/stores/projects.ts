import { computed, ref } from 'vue'

import { api } from '@/api/client'
import type { Project } from '@/api/types'

const projects = ref<Project[]>([])
let loaded: Promise<void> | null = null

/** Active projects for pickers, loaded once and shared between components. */
/** Forget the cached list, e.g. when the user signs out. */
export function resetProjects(): void {
  projects.value = []
  loaded = null
}

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

  /** [[client name, projects]] in list order, for <optgroup>s. */
  const grouped = computed(() => {
    const groups = new Map<string, Project[]>()
    for (const p of projects.value)
      groups.set(p.client_name, [...(groups.get(p.client_name) ?? []), p])
    return [...groups.entries()]
  })

  return { projects, byId, grouped, load }
}
