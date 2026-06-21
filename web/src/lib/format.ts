/** Formatting and parsing helpers shared by the views. */

/** 5400 -> "1:30" (hours:minutes). Seconds are dropped, not rounded. */
export function formatDuration(seconds: number): string {
  const sign = seconds < 0 ? '-' : ''
  const total = Math.floor(Math.abs(seconds) / 60)
  const hours = Math.floor(total / 60)
  const minutes = total % 60
  return `${sign}${hours}:${String(minutes).padStart(2, '0')}`
}

/** 5400 -> "1:30:00", used for the running timer. */
export function formatClock(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  return [h, m, sec].map((n, i) => (i === 0 ? String(n) : String(n).padStart(2, '0'))).join(':')
}

/** 5400 -> "1.50" */
export function formatHours(seconds: number): string {
  return (seconds / 3600).toFixed(2)
}

/**
 * Parse what people type into a duration field, in minutes.
 * Accepts "1:30", "1.5", "1,5", "90m", "1h", "1h 30m" and plain minutes like "45".
 */
export function parseDuration(input: string): number | null {
  const text = input.trim().toLowerCase()
  if (!text) return 0
  let match = /^(\d+):([0-5]?\d)$/.exec(text)
  if (match) return Number(match[1]) * 60 + Number(match[2])
  // "1h", "90m", "1h 15m" and "1h30" (minutes after hours need no unit)
  match = /^(?:(\d+(?:[.,]\d+)?)\s*h)?\s*(?:(\d+)\s*(m(?:in)?)?)?$/.exec(text)
  if (match && (match[1] || match[3])) {
    if (match[1] && match[2] && Number(match[2]) >= 60) return null
    const hours = match[1] ? Number(match[1].replace(',', '.')) : 0
    return Math.round(hours * 60) + (match[2] ? Number(match[2]) : 0)
  }
  match = /^\d+[.,]\d+$/.exec(text)
  if (match) return Math.round(Number(text.replace(',', '.')) * 60)
  if (/^\d+$/.test(text)) {
    const n = Number(text)
    // Small bare numbers are hours ("2"), larger ones minutes ("45").
    return n <= 12 ? n * 60 : n
  }
  return null
}

export function formatMoney(amount: string | number, currency: string): string {
  const value = typeof amount === 'string' ? Number(amount) : amount
  return new Intl.NumberFormat('en-GB', { style: 'currency', currency }).format(value)
}

/** Local calendar date as YYYY-MM-DD. */
export function isoDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function formatDate(value: string): string {
  const date = value.length === 10 ? new Date(`${value}T00:00:00`) : new Date(value)
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function formatTime(value: string): string {
  return new Date(value).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}
