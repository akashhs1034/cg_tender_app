import { createBrowserClient } from '@supabase/ssr'

/**
 * Browser-side Supabase client (singleton). Reads the public env vars and
 * stores the session in cookies so server components and middleware can see it.
 */
export function createClient() {
  // Placeholder fallbacks so the client never throws when env vars are absent;
  // requests simply fail and are handled gracefully by callers.
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co',
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-anon-key'
  )
}
