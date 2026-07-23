import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { normalizeUserRole } from '@/lib/user-role'

export const dynamic = 'force-dynamic'

/** OAuth / email-link callback. */
export async function GET(request: Request) {
  const url = new URL(request.url)
  const code = url.searchParams.get('code')
  const tokenHash = url.searchParams.get('token_hash')
  const type = url.searchParams.get('type')
  const requestedNext = url.searchParams.get('next')
  const safeNext = requestedNext && requestedNext.startsWith('/') && !requestedNext.startsWith('//')
    ? requestedNext
    : null

  if (code || (tokenHash && type === 'recovery')) {
    try {
      const supabase = await createClient()
      const { error } = code
        ? await supabase.auth.exchangeCodeForSession(code)
        : await supabase.auth.verifyOtp({ token_hash: tokenHash!, type: 'recovery' })

      if (!error) {
        if (safeNext) return NextResponse.redirect(new URL(safeNext, url.origin))

        const { data } = await supabase.auth.getUser()
        const role = normalizeUserRole(data.user?.user_metadata?.role)
        return NextResponse.redirect(new URL(role ? '/dashboard' : '/select-role', url.origin))
      }
      console.error('[auth/callback] exchange failed:', error.message)
    } catch (error) {
      console.error('[auth/callback] error:', error)
    }
  }

  const errorMessage = 'This link is invalid or expired. Please request a new one.'
  const errorTarget = safeNext?.startsWith('/reset-password') ? '/reset-password' : '/login'
  const errorUrl = new URL(errorTarget, url.origin)
  errorUrl.searchParams.set('error', errorMessage)
  return NextResponse.redirect(errorUrl)
}
