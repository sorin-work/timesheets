import type { Entry } from '@/api/types'

import { isoDate } from './format'

export interface DayGroup {
  day: string
  entries: Entry[]
  total: number
}

/** Group a newest-first list of entries by the local calendar day they started on. */
export function groupByDay(entries: Entry[]): DayGroup[] {
  const groups: DayGroup[] = []
  for (const entry of entries) {
    const day = isoDate(new Date(entry.started_at))
    let group = groups.at(-1)
    if (!group || group.day !== day) {
      group = { day, entries: [], total: 0 }
      groups.push(group)
    }
    group.entries.push(entry)
    group.total += entry.duration_seconds
  }
  return groups
}
