import { afterEach, describe, expect, it, vi } from 'vitest'

import { mockApi } from '@/__tests__/helpers'

import { useAuth } from '../auth'
import { useProjects } from '../projects'

afterEach(() => vi.unstubAllGlobals())

describe('auth store', () => {
  it('forgets cached projects when signing out', async () => {
    mockApi({ 'GET /api/projects': [{ id: 1, name: 'Old account project' }] })
    const projects = useProjects()
    await projects.load()
    expect(projects.projects.value).toHaveLength(1)

    useAuth().logout()
    expect(projects.projects.value).toEqual([])

    mockApi({ 'GET /api/projects': [{ id: 2, name: 'New account project' }] })
    await projects.load()
    expect(projects.projects.value.map((p) => p.id)).toEqual([2])
  })
})
