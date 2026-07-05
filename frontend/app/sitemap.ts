import type { MetadataRoute } from 'next'
import { supabase } from '@/lib/supabase'

export const revalidate = 3600 // regenerate hourly

const BASE = 'https://opporta.vercel.app'

/**
 * Sitemap: static surfaces + the most relevant live tender/job detail pages
 * (capped so the file stays small and fast; Google discovers the rest by
 * crawling the paginated listings).
 */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date()
  const entries: MetadataRoute.Sitemap = [
    { url: `${BASE}/`, lastModified: now, changeFrequency: 'daily', priority: 1 },
    { url: `${BASE}/tenders`, lastModified: now, changeFrequency: 'hourly', priority: 0.9 },
    { url: `${BASE}/jobs`, lastModified: now, changeFrequency: 'hourly', priority: 0.9 },
    { url: `${BASE}/exam-planner`, lastModified: now, changeFrequency: 'daily', priority: 0.7 },
    { url: `${BASE}/bid-documents`, lastModified: now, changeFrequency: 'weekly', priority: 0.5 },
    { url: `${BASE}/analytics`, lastModified: now, changeFrequency: 'daily', priority: 0.5 },
    { url: `${BASE}/dashboard`, lastModified: now, changeFrequency: 'daily', priority: 0.6 },
  ]

  try {
    const [tenders, jobs] = await Promise.all([
      supabase.from('tenders').select('source_id,last_seen_at')
        .or('status.is.null,status.neq.expired')
        .order('ai_score', { ascending: false, nullsFirst: false }).limit(500),
      supabase.from('jobs').select('source_id,last_seen_at')
        .or('status.is.null,status.neq.expired')
        .order('ai_score', { ascending: false, nullsFirst: false }).limit(200),
    ])
    for (const r of tenders.data ?? []) {
      entries.push({
        url: `${BASE}/tenders/${r.source_id}`,
        lastModified: r.last_seen_at ? new Date(r.last_seen_at) : now,
        changeFrequency: 'daily',
        priority: 0.6,
      })
    }
    for (const r of jobs.data ?? []) {
      entries.push({
        url: `${BASE}/jobs/${r.source_id}`,
        lastModified: r.last_seen_at ? new Date(r.last_seen_at) : now,
        changeFrequency: 'daily',
        priority: 0.6,
      })
    }
  } catch {
    // DB unreachable — static entries alone are still a valid sitemap.
  }
  return entries
}
