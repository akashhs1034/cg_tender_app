import { createBrowserClient } from '@supabase/ssr'

/**
 * Browser-side Supabase client (singleton). Reads the public env vars and
 * stores the session in cookies so server components and middleware can see it.
 */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL ?? '',
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? ''
  )
}
