import { describe, expect, it } from 'vitest'

import type { Entry } from '@/api/types'

import { groupByDay } from '../entries'

function entry(id: number, start: Date, seconds = 3600): Entry {
  return {
    id,
    project_id: 1,
    project_name: 'P',
    client_id: 1,
    client_name: 'C',
    started_at: start.toISOString(),
    ended_at: new Date(start.getTime() + seconds * 1000).toISOString(),
    duration_seconds: seconds,
    running: false,
    description: '',
    billable: true,
    source: 'manual',
    invoice_id: null,
    hourly_rate: null,
  }
}

describe('groupByDay', () => {
  it('groups consecutive entries of the same day and sums them', () => {
    const groups = groupByDay([
      entry(3, new Date(2026, 3, 21, 14, 0), 1800),
      entry(2, new Date(2026, 3, 21, 9, 0)),
      entry(1, new Date(2026, 3, 20, 9, 0)),
    ])
    expect(groups.map((g) => [g.day, g.entries.length, g.total])).toEqual([
      ['2026-04-21', 2, 5400],
      ['2026-04-20', 1, 3600],
    ])
  })

  it('uses the local day, not the UTC date', () => {
    // Tests run in Pacific/Auckland: both entries are on 20 April in UTC.
    const late = new Date(2026, 3, 20, 23, 30)
    const early = new Date(2026, 3, 21, 0, 30)
    const groups = groupByDay([entry(2, early), entry(1, late)])
    expect(groups.map((g) => g.day)).toEqual(['2026-04-21', '2026-04-20'])
  })
})
