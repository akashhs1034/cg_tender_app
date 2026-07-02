import { createClient } from '@supabase/supabase-js'

/**
 * Server-only admin client using the service-role key. Bypasses RLS — use ONLY
 * in trusted server code (API routes) for writes the anon key can't do, e.g.
 * caching AI results back onto the public tenders/jobs tables.
 *
 * Returns null when the service key is not configured, so callers degrade
 * gracefully (generate without caching) instead of crashing.
 */
export function createAdminClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!url || !serviceKey) return null
  return createClient(url, serviceKey, { auth: { persistSession: false } })
}
