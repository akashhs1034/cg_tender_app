import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseKey) {
  // Surfaced clearly in server logs so a missing .env is obvious rather than
  // failing later with a cryptic fetch error.
  console.warn(
    '[supabase] Missing NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY — ' +
      'data fetching will fail. Copy .env.example to .env.local and fill it in.'
  )
}

/**
 * Shared Supabase client. Uses the public (anon/publishable) key, so it is safe
 * for both server components and the browser — all access is gated by RLS.
 *
 * Falls back to a harmless placeholder URL/key when env vars are absent so the
 * client never throws at import time (which would break the build). Queries then
 * fail at request time and are caught by the data layer, degrading to empty
 * results instead of crashing.
 */
export const supabase = createClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseKey || 'placeholder-anon-key',
  { auth: { persistSession: false } }
)
