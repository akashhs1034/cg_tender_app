import { NextResponse } from 'next/server'
import { getCurrentUser } from '@/lib/supabase/server'
import { createAdminClient } from '@/lib/supabase/admin'
import { paymentsEnabled, PLANS } from '@/lib/payments'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

/**
 * POST /api/payments/create-order  { planId }
 * Creates a Razorpay order server-side and records a 'created' payment row.
 * Returns { orderId, amount, currency, keyId } for the client checkout.
 *
 * Disabled (503) until RAZORPAY_KEY_ID/SECRET are set and
 * NEXT_PUBLIC_PAYMENTS_ENABLED=true — so the app ships free by default.
 */
export async function POST(req: Request) {
  if (!paymentsEnabled()) {
    return NextResponse.json({ error: 'Payments are not enabled' }, { status: 503 })
  }
  const user = await getCurrentUser()
  if (!user?.email) {
    return NextResponse.json({ error: 'Sign in required' }, { status: 401 })
  }

  let planId = ''
  try { planId = (await req.json())?.planId ?? '' } catch { /* noop */ }
  const plan = PLANS.find((p) => p.id === planId)
  if (!plan) return NextResponse.json({ error: 'Unknown plan' }, { status: 400 })

  const keyId = process.env.RAZORPAY_KEY_ID!
  const keySecret = process.env.RAZORPAY_KEY_SECRET!
  const auth = Buffer.from(`${keyId}:${keySecret}`).toString('base64')

  try {
    const res = await fetch('https://api.razorpay.com/v1/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Basic ${auth}` },
      body: JSON.stringify({
        amount: plan.amount,
        currency: 'INR',
        notes: { plan: plan.id, email: user.email },
      }),
    })
    const order = await res.json()
    if (!res.ok) {
      return NextResponse.json({ error: order?.error?.description || 'Order failed' }, { status: 502 })
    }

    const admin = createAdminClient()
    if (admin) {
      await admin.from('payments').insert({
        user_id: user.id,
        email: user.email,
        plan: plan.id,
        amount: plan.amount,
        currency: 'INR',
        razorpay_order_id: order.id,
        status: 'created',
      })
    }

    return NextResponse.json({
      orderId: order.id, amount: plan.amount, currency: 'INR', keyId,
    })
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    return NextResponse.json({ error: msg }, { status: 500 })
  }
}
