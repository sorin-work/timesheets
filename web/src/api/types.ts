export type Money = string

export interface User {
  id: number
  email: string
  name: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export type Rounding = 'none' | '6' | '15'

export interface Settings {
  name: string
  email: string
  timezone: string
  rounding: Rounding
  currency: string
  business_name: string | null
  business_address: string | null
  tax_id: string | null
  invoice_prefix: string
  payment_terms_days: number
}

export interface Client {
  id: number
  name: string
  email: string | null
  address: string | null
  currency: string
  hourly_rate: Money | null
  notes: string | null
  archived_at: string | null
  created_at: string
}

export interface Project {
  id: number
  client_id: number
  client_name: string
  name: string
  hourly_rate: Money | null
  effective_rate: Money | null
  currency: string
  billable: boolean
  color: string
  archived_at: string | null
  created_at: string
}

export interface Entry {
  id: number
  project_id: number
  project_name: string
  client_id: number
  client_name: string
  started_at: string
  ended_at: string | null
  duration_seconds: number
  running: boolean
  description: string
  billable: boolean
  source: 'manual' | 'timer' | 'grid'
  invoice_id: number | null
  hourly_rate: Money | null
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface TimesheetRow {
  project_id: number
  project_name: string
  client_name: string
  color: string
  seconds: number[]
  total: number
}

export interface Timesheet {
  week_start: string
  days: string[]
  rows: TimesheetRow[]
  totals: number[]
  total: number
}

export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue'

export interface InvoiceSummary {
  id: number
  number: string
  client_id: number
  client_name: string
  status: InvoiceStatus
  issue_date: string
  due_date: string
  currency: string
  subtotal: Money
  tax_total: Money
  total: Money
}

export interface InvoiceLine {
  id: number
  project_id: number | null
  description: string
  quantity: string
  unit_price: Money
  amount: Money
}

export interface InvoiceTax {
  name: string
  rate: string
  amount: Money
}

export interface Invoice extends InvoiceSummary {
  period_start: string | null
  period_end: string | null
  notes: string | null
  sent_at: string | null
  paid_at: string | null
  lines: InvoiceLine[]
  taxes: InvoiceTax[]
  entry_count: number
}

export interface Amount {
  currency: string
  amount: Money
}

export interface TimeReportRow {
  key: string
  label: string
  tracked_seconds: number
  billable_seconds: number
  unbilled_seconds: number
  amounts: Amount[]
}

export interface TimeReport {
  group_by: 'client' | 'project' | 'month'
  rows: TimeReportRow[]
  tracked_seconds: number
  billable_seconds: number
  amounts: Amount[]
}

export interface RevenueReport {
  year: number
  months: { month: string; invoiced: Amount[]; paid: Amount[] }[]
  invoiced: Amount[]
  paid: Amount[]
}

export interface UnbilledProject {
  project_id: number
  project_name: string
  hourly_rate: Money | null
  entries: number
  seconds: number
  billable_seconds: number
}

export interface UnbilledSummary {
  client_id: number
  currency: string
  projects: UnbilledProject[]
}
