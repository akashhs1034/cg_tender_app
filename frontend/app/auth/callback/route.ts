import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export const dynamic = 'force-dynamic'

/**
 * OAuth / email-link callback. Supabase redirects here with ?code=…;
 * exchange it for a session cookie, then continue to ?next= (or /dashboard).
 * Used by Google sign-in and password-recovery links.
 */
export async function GET(request: Request) {
  const url = new URL(request.url)
  const code = url.searchParams.get('code')
  const next = url.searchParams.get('next') ?? '/dashboard'
  // only allow same-site relative redirects
  const safeNext = next.startsWith('/') && !next.startsWith('//') ? next : '/dashboard'

  if (code) {
    try {
      const supabase = await createClient()
      const { error } = await supabase.auth.exchangeCodeForSession(code)
      if (!error) {
        return NextResponse.redirect(new URL(safeNext, url.origin))
      }
      console.error('[auth/callback] exchange failed:', error.message)
    } catch (e) {
      console.error('[auth/callback] error:', e)
    }
  }
  return NextResponse.redirect(
    new URL(`/login?error=${encodeURIComponent('Sign-in link was invalid or expired. Please try again.')}`, url.origin))
}
