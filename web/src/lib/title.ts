import type { RouteLocationNormalizedLoaded } from 'vue-router'

/** The browser tab title for a page, e.g. "Invoices · Timesheets". */
export function pageTitle(route: Pick<RouteLocationNormalizedLoaded, 'meta'>): string {
  const title = route.meta.title as string | undefined
  return title ? `${title} · Timesheets` : 'Timesheets'
}
