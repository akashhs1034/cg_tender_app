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
 */
export const supabase = createClient(supabaseUrl ?? '', supabaseKey ?? '', {
  auth: { persistSession: false },
})
