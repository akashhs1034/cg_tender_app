import { supabase } from '@/lib/supabase'
import type { Tender, Job, State, TenderMode } from '@/lib/mock-data'

// ── Helpers ───────────────────────────────────────────────────────────────────
// The scraped data is messy: many nulls, mixed-language state names, free-text
// values. Every field below is normalized so the UI never has to defend itself.

function normState(raw: string | null | undefined): State {
  if (!raw) return 'Chhattisgarh'
  const v = raw.trim().toLowerCase()
  if (v.includes('uttar') || v === 'up' || v.includes('उत्तर')) return 'Uttar Pradesh'
  return 'Chhattisgarh'
}

function normMode(online: string | null, portal?: string | null): TenderMode {
  const p = (portal ?? '').toLowerCase()
  if (p.includes('newspaper')) return 'Newspaper'
  const v = (online ?? '').toLowerCase()
  if (v === 'offline') return 'Offline'
  return 'Online'
}

/** "2026-07-10" → "10 Jul 2026". Leaves already-formatted / unknown text as-is. */
function fmtDate(raw: string | null | undefined): string {
  if (!raw) return 'Not specified'
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(raw)
  if (!m) return raw
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const [, y, mo, d] = m
  return `${parseInt(d, 10)} ${months[parseInt(mo, 10) - 1]} ${y}`
}

function fmtValue(estimated: string | null, lakhs: number | string | null): string {
  if (estimated && estimated.trim()) return estimated.trim()
  const n = typeof lakhs === 'string' ? parseFloat(lakhs) : lakhs
  if (n && !Number.isNaN(n)) {
    return n >= 100 ? `₹${(n / 100).toFixed(2)} Cr` : `₹${n.toFixed(2)} L`
  }
  return 'Not specified'
}

/** Split a free-text blob into clean bullet points. */
function toList(...sources: (string | null | undefined)[]): string[] {
  const out: string[] = []
  for (const s of sources) {
    if (!s) continue
    s.split(/\r?\n|•|;|·/)
      .map((x) => x.trim())
      .filter((x) => x.length > 2)
      .forEach((x) => out.push(x))
  }
  return [...new Set(out)]
}

/** jsonb / text[] / string → string[] */
function jsonToList(raw: unknown): string[] {
  if (!raw) return []
  if (Array.isArray(raw)) return raw.map(String).filter(Boolean)
  if (typeof raw === 'string') {
    try {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed)) return parsed.map(String).filter(Boolean)
    } catch {
      return toList(raw)
    }
  }
  return []
}

function riskFromScore(score: number): Tender['riskLevel'] {
  if (score >= 80) return 'Low'
  if (score >= 60) return 'Medium'
  return 'High'
}

// ── Mappers (DB row → UI type) ─────────────────────────────────────────────────

/* eslint-disable @typescript-eslint/no-explicit-any */
function mapTender(r: any): Tender {
  const score = typeof r.ai_score === 'number' ? r.ai_score : 0
  const eligibility = toList(r.eligibility, r.experience_required, r.required_turnover, r.contractor_class)
  return {
    id: r.source_id,
    title: r.title ?? 'Untitled tender',
    nitNumber: r.tender_no ?? r.source_id ?? '—',
    department: r.department ?? r.organization ?? r.agency ?? 'Government Department',
    district: r.district ?? r.location ?? '—',
    state: normState(r.state),
    mode: normMode(r.online_or_offline, r.source_portal),
    category: r.category ?? r.sector ?? 'Miscellaneous Works',
    estimatedValue: fmtValue(r.estimated_value, r.value_lakhs),
    emd: r.emd ?? 'Not specified',
    deadline: fmtDate(r.deadline),
    source: r.source_name ?? r.source_portal ?? 'Government Portal',
    aiMatchScore: score,
    isRecommended: score >= 85,
    description: r.description ?? 'Full details are available on the source portal.',
    eligibility: eligibility.length ? eligibility : ['See tender document for eligibility criteria.'],
    documents: jsonToList(r.required_documents),
    riskLevel: riskFromScore(score),
    missingDocuments: [],
    bidReadiness: score,
    documentUrl: r.document_url ?? r.document_link ?? undefined,
    sourceUrl: r.source_url ?? undefined,
    publishedDate: r.published_date ? fmtDate(r.published_date) : undefined,
    organization: r.organization ?? undefined,
    location: r.location ?? undefined,
    sourceCount: typeof r.source_count === 'number' ? r.source_count : undefined,
    contractorClass: r.contractor_class ?? undefined,
    experience: r.experience ?? r.experience_required ?? undefined,
  }
}

function mapJob(r: any): Job {
  const score = typeof r.ai_score === 'number' ? r.ai_score : 0
  const eligibility = toList(r.qualification, r.age_limit, r.reservation_info)
  return {
    id: r.source_id,
    title: r.title ?? 'Untitled job',
    advNumber: r.advertisement_no ?? r.source_id ?? '—',
    department: r.department ?? 'Government Department',
    district: r.district ?? '—',
    state: normState(r.state),
    mode: normMode(r.online_or_offline, r.source_portal),
    category: r.category ?? r.field ?? 'Miscellaneous',
    qualification: r.qualification ?? 'See official notification',
    vacancies: typeof r.vacancies === 'number' ? r.vacancies : 0,
    salary: r.salary ?? 'As per government norms',
    deadline: fmtDate(r.deadline ?? r.application_end_date),
    matchScore: score,
    isRecommended: score >= 85,
    description: r.description ?? 'Full details are available on the official notification.',
    eligibility: eligibility.length ? eligibility : ['See official notification for eligibility.'],
    ageLimit: r.age_limit ?? 'As per norms',
    examDate: r.exam_date ? fmtDate(r.exam_date) : undefined,
    selectionProcess: toList(r.selection_process),
    applyUrl: r.apply_url ?? r.apply_link ?? undefined,
    documentUrl: r.document_url ?? undefined,
    publishedDate: r.published_date ? fmtDate(r.published_date) : (r.post_date ? fmtDate(r.post_date) : undefined),
    applicationFee: r.application_fee ?? undefined,
    reservationInfo: r.reservation_info ?? undefined,
  }
}
/* eslint-enable @typescript-eslint/no-explicit-any */

// ── Public data API ─────────────────────────────────────────────────────────────
// Order by ai_score (best matches first), nulls last. We cap listings so the
// client stays snappy while still surfacing the most relevant opportunities.

const LIST_LIMIT = 300

export async function getTenders(): Promise<Tender[]> {
  const { data, error } = await supabase
    .from('tenders')
    .select('*')
    .or('status.is.null,status.neq.expired')
    .order('ai_score', { ascending: false, nullsFirst: false })
    .limit(LIST_LIMIT)
  if (error) {
    console.error('[data] getTenders failed:', error.message)
    return []
  }
  return (data ?? []).map(mapTender)
}

export async function getTenderById(id: string): Promise<Tender | null> {
  const { data, error } = await supabase.from('tenders').select('*').eq('source_id', id).maybeSingle()
  if (error) {
    console.error('[data] getTenderById failed:', error.message)
    return null
  }
  return data ? mapTender(data) : null
}

export async function getJobs(): Promise<Job[]> {
  const { data, error } = await supabase
    .from('jobs')
    .select('*')
    .order('ai_score', { ascending: false, nullsFirst: false })
    .limit(LIST_LIMIT)
  if (error) {
    console.error('[data] getJobs failed:', error.message)
    return []
  }
  return (data ?? []).map(mapJob)
}

export async function getJobById(id: string): Promise<Job | null> {
  const { data, error } = await supabase.from('jobs').select('*').eq('source_id', id).maybeSingle()
  if (error) {
    console.error('[data] getJobById failed:', error.message)
    return null
  }
  return data ? mapJob(data) : null
}

export interface DashboardStats {
  activeTenders: number
  activeJobs: number
  offlineNewspaper: number
  corrigendums: number
  closingSoon: number
  newToday: number
  cgCount: number
  upCount: number
}

async function count(
  table: string,
  build?: (q: any) => any // eslint-disable-line @typescript-eslint/no-explicit-any
): Promise<number> {
  let q = supabase.from(table).select('*', { count: 'exact', head: true })
  if (build) q = build(q)
  const { count: c, error } = await q
  if (error) {
    console.error(`[data] count(${table}) failed:`, error.message)
    return 0
  }
  return c ?? 0
}

/** Fetches every value of one or more columns across a table, paginating past
 *  PostgREST's 1000-row cap so aggregates are accurate, not sampled. */
async function fetchAllRows<T = Record<string, unknown>>(
  table: string,
  columns: string
): Promise<T[]> {
  const PAGE = 1000
  const all: T[] = []
  for (let from = 0; ; from += PAGE) {
    const { data, error } = await supabase
      .from(table)
      .select(columns)
      .range(from, from + PAGE - 1)
    if (error) {
      console.error(`[data] fetchAllRows(${table}) failed:`, error.message)
      break
    }
    const rows = (data ?? []) as T[]
    all.push(...rows)
    if (rows.length < PAGE) break
  }
  return all
}

export interface CategorySlice {
  label: string
  count: number
  pct: number
}

export interface Analytics {
  totalTenders: number
  totalJobs: number
  totalOpportunities: number
  expiringSoon: number
  corrigendums: number
  avgScore: number
  totalVacancies: number
  cgCount: number
  upCount: number
  tenderCategories: CategorySlice[]
  jobCategories: CategorySlice[]
  modes: { online: number; offline: number; newspaper: number }
  sources: CategorySlice[]
}

function topSlices(counts: Map<string, number>, total: number, limit = 6): CategorySlice[] {
  const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1])
  const top = sorted.slice(0, limit)
  const rest = sorted.slice(limit).reduce((acc, [, c]) => acc + c, 0)
  const slices = top.map(([label, count]) => ({
    label,
    count,
    pct: total ? Math.round((count / total) * 100) : 0,
  }))
  if (rest > 0) slices.push({ label: 'Other', count: rest, pct: total ? Math.round((rest / total) * 100) : 0 })
  return slices
}

export async function getAnalytics(): Promise<Analytics> {
  /* eslint-disable @typescript-eslint/no-explicit-any */
  const todayMs = Date.now()
  const weekMs = 7 * 24 * 60 * 60 * 1000

  const [
    totalTenders,
    totalJobs,
    corrigendums,
    cgCount,
    upCount,
    tenderRows,
    jobRows,
  ] = await Promise.all([
    count('tenders', (q) => q.or('status.is.null,status.neq.expired')),
    count('jobs'),
    count('corrigendums'),
    count('tenders', (q) => q.eq('state', 'Chhattisgarh')),
    count('tenders', (q) => q.eq('state', 'Uttar Pradesh')),
    fetchAllRows<any>('tenders', 'category,online_or_offline,source_portal,ai_score,deadline'),
    fetchAllRows<any>('jobs', 'category,vacancies,ai_score'),
  ])

  const tenderCats = new Map<string, number>()
  const sourceCounts = new Map<string, number>()
  const modes = { online: 0, offline: 0, newspaper: 0 }
  let scoreSum = 0
  let scoreN = 0
  let expiringSoon = 0

  for (const r of tenderRows) {
    const cat = (r.category as string) || 'Uncategorized'
    tenderCats.set(cat, (tenderCats.get(cat) ?? 0) + 1)
    const portal = (r.source_portal as string) || 'Other'
    sourceCounts.set(portal, (sourceCounts.get(portal) ?? 0) + 1)
    const m = normMode(r.online_or_offline, r.source_portal)
    if (m === 'Offline') modes.offline++
    else if (m === 'Newspaper') modes.newspaper++
    else modes.online++
    if (typeof r.ai_score === 'number') {
      scoreSum += r.ai_score
      scoreN++
    }
    if (typeof r.deadline === 'string') {
      const t = Date.parse(r.deadline)
      if (!Number.isNaN(t) && t >= todayMs && t <= todayMs + weekMs) expiringSoon++
    }
  }

  const jobCats = new Map<string, number>()
  let totalVacancies = 0
  for (const r of jobRows) {
    const cat = (r.category as string) || 'Uncategorized'
    jobCats.set(cat, (jobCats.get(cat) ?? 0) + 1)
    if (typeof r.vacancies === 'number') totalVacancies += r.vacancies
    if (typeof r.ai_score === 'number') {
      scoreSum += r.ai_score
      scoreN++
    }
  }
  /* eslint-enable @typescript-eslint/no-explicit-any */

  return {
    totalTenders,
    totalJobs,
    totalOpportunities: totalTenders + totalJobs,
    expiringSoon,
    corrigendums,
    avgScore: scoreN ? Math.round(scoreSum / scoreN) : 0,
    totalVacancies,
    cgCount,
    upCount,
    tenderCategories: topSlices(tenderCats, tenderRows.length),
    jobCategories: topSlices(jobCats, jobRows.length),
    modes,
    sources: topSlices(sourceCounts, tenderRows.length),
  }
}

export interface DiscoveredSource {
  id: number
  url: string
  title: string
  domain: string
  state: string
  sourceType: string
  category: string
  confidenceScore: number
  status: string
  reason: string
  requiresCaptcha: boolean
}

export async function getDiscoveredSources(): Promise<DiscoveredSource[]> {
  const { data, error } = await supabase
    .from('discovered_sources')
    .select('id,url,title,domain,state,source_type,category,confidence_score,status,reason,requires_captcha')
    .order('confidence_score', { ascending: false, nullsFirst: false })
    .limit(500)
  if (error) {
    console.error('[data] getDiscoveredSources failed:', error.message)
    return []
  }
  /* eslint-disable @typescript-eslint/no-explicit-any */
  return (data ?? []).map((r: any) => ({
    id: r.id,
    url: r.url,
    title: r.title ?? r.domain ?? r.url,
    domain: r.domain ?? '',
    state: r.state ?? '—',
    sourceType: r.source_type ?? 'unknown',
    category: r.category ?? 'unknown',
    confidenceScore: typeof r.confidence_score === 'number' ? r.confidence_score : 0,
    status: r.status ?? 'pending_review',
    reason: r.reason ?? '',
    requiresCaptcha: !!r.requires_captcha,
  }))
  /* eslint-enable @typescript-eslint/no-explicit-any */
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const todayIso = new Date().toISOString().slice(0, 10)
  const [
    activeTenders,
    activeJobs,
    offlineNewspaper,
    corrigendums,
    closingSoon,
    newToday,
    cgTenders,
    upTenders,
  ] = await Promise.all([
    count('tenders', (q) => q.or('status.is.null,status.neq.expired')),
    count('jobs'),
    count('offline_tenders'),
    count('corrigendums'),
    count('tenders', (q) => q.eq('status', 'closing_soon')),
    count('tenders', (q) => q.gte('first_seen_at', `${todayIso}T00:00:00Z`)),
    count('tenders', (q) => q.eq('state', 'Chhattisgarh')),
    count('tenders', (q) => q.eq('state', 'Uttar Pradesh')),
  ])
  return {
    activeTenders,
    activeJobs,
    offlineNewspaper,
    corrigendums,
    closingSoon,
    newToday,
    cgCount: cgTenders,
    upCount: upTenders,
  }
}
