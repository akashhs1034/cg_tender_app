import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

/**
 * Server-side Supabase client bound to the current request's cookies, so
 * server components / route handlers can read the authenticated session.
 */
export async function createClient() {
  const cookieStore = await cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL ?? '',
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? '',
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // Called from a Server Component — safe to ignore; middleware
            // refreshes the session cookie on the next request.
          }
        },
      },
    }
  )
}

/** Returns the current authenticated user (or null) on the server. */
export async function getCurrentUser() {
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL) return null
  try {
    const supabase = await createClient()
    const { data } = await supabase.auth.getUser()
    return data.user
  } catch {
    return null
  }
}
