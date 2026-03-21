import { vi } from 'vitest'
import { createMemoryHistory, createRouter, type RouteRecordRaw } from 'vue-router'

type Handler = (url: string, init: RequestInit) => { status?: number; body?: unknown }

/** Replace fetch with a router of [method path] -> response handlers. Returns the mock. */
export function mockApi(routes: Record<string, Handler | object>) {
  const mock = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = String(input)
    const method = (init.method ?? 'GET').toUpperCase()
    const path = url.split('?')[0]
    const route = routes[`${method} ${path}`]
    if (!route)
      return new Response(JSON.stringify({ error: { message: 'not mocked' } }), { status: 404 })
    const result = typeof route === 'function' ? (route as Handler)(url, init) : { body: route }
    const status = result.status ?? 200
    return new Response(status === 204 ? null : JSON.stringify(result.body ?? null), {
      status,
      headers: { 'Content-Type': 'application/json' },
    })
  })
  vi.stubGlobal('fetch', mock)
  return mock
}

export function testRouter(routes: RouteRecordRaw[] = []) {
  const Empty = { template: '<div />' }
  return createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: Empty }, ...routes, { path: '/:p(.*)*', component: Empty }],
  })
}

export function flush() {
  return new Promise((resolve) => setTimeout(resolve, 0))
}
