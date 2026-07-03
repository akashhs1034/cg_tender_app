import { NextResponse } from 'next/server'
import { isCurrentUserAdmin } from '@/lib/admin'
import { createAdminClient } from '@/lib/supabase/admin'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

/**
 * POST /api/admin/cleanup
 * Body: { mode: 'archive' | 'purge' }
 *  - archive: mark tenders/jobs past their deadline as status='expired'
 *             (the public app already filters these out) — safe + reversible.
 *  - purge:   permanently DELETE rows past deadline. Irreversible.
 *
 * Guarded: caller must be signed in and their email listed in ADMIN_EMAILS
 * (comma-separated env var).
 */
export async function POST(req: Request) {
  if (!(await isCurrentUserAdmin())) {
    return NextResponse.json({ error: 'Admin access required' }, { status: 403 })
  }

  const admin = createAdminClient()
  if (!admin) {
    return NextResponse.json(
      { error: 'Server missing SUPABASE_SERVICE_ROLE_KEY' }, { status: 500 })
  }

  let mode = 'archive'
  try {
    const body = await req.json()
    if (body?.mode === 'purge') mode = 'purge'
  } catch { /* default archive */ }

  const today = new Date().toISOString().slice(0, 10)

  try {
    if (mode === 'purge') {
      const [t, j] = await Promise.all([
        admin.from('tenders').delete({ count: 'exact' }).lt('deadline', today),
        admin.from('jobs').delete({ count: 'exact' }).lt('deadline', today),
      ])
      if (t.error) throw t.error
      if (j.error) throw j.error
      return NextResponse.json({
        mode, tendersDeleted: t.count ?? 0, jobsDeleted: j.count ?? 0,
      })
    }

    const [t, j] = await Promise.all([
      admin.from('tenders')
        .update({ status: 'expired' }, { count: 'exact' })
        .lt('deadline', today)
        .or('status.is.null,status.neq.expired'),
      admin.from('jobs')
        .update({ status: 'expired' }, { count: 'exact' })
        .lt('deadline', today)
        .or('status.is.null,status.neq.expired'),
    ])
    if (t.error) throw t.error
    if (j.error) throw j.error
    return NextResponse.json({
      mode, tendersArchived: t.count ?? 0, jobsArchived: j.count ?? 0,
    })
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    return NextResponse.json({ error: msg }, { status: 500 })
  }
}
