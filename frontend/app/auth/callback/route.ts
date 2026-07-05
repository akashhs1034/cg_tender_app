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
  const tokenHash = url.searchParams.get('token_hash')
  const type = url.searchParams.get('type')
  const next = url.searchParams.get('next') ?? '/dashboard'
  // only allow same-site relative redirects
  const safeNext = next.startsWith('/') && !next.startsWith('//') ? next : '/dashboard'

  if (code || (tokenHash && type === 'recovery')) {
    try {
      const supabase = await createClient()
      const { error } = code
        ? await supabase.auth.exchangeCodeForSession(code)
        : await supabase.auth.verifyOtp({
            token_hash: tokenHash!,
            type: 'recovery',
          })
      if (!error) {
        return NextResponse.redirect(new URL(safeNext, url.origin))
      }
      console.error('[auth/callback] exchange failed:', error.message)
    } catch (e) {
      console.error('[auth/callback] error:', e)
    }
  }

  const errorMessage = 'This link is invalid or expired. Please request a new one.'
  const errorTarget = safeNext.startsWith('/reset-password') ? '/reset-password' : '/login'
  const errorUrl = new URL(errorTarget, url.origin)
  errorUrl.searchParams.set('error', errorMessage)
  return NextResponse.redirect(errorUrl)
}
