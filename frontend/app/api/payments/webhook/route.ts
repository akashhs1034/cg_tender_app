import { NextResponse } from 'next/server'
import crypto from 'crypto'
import { createAdminClient } from '@/lib/supabase/admin'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

/**
 * POST /api/payments/webhook
 * Razorpay server-to-server webhook. Verifies the X-Razorpay-Signature HMAC
 * against RAZORPAY_WEBHOOK_SECRET, then marks the matching payment paid.
 * Signature verification is the source of truth — never trust client callbacks.
 */
export async function POST(req: Request) {
  const secret = process.env.RAZORPAY_WEBHOOK_SECRET
  if (!secret) {
    return NextResponse.json({ error: 'Webhook not configured' }, { status: 503 })
  }

  const signature = req.headers.get('x-razorpay-signature') || ''
  const raw = await req.text() // must hash the raw body, not re-serialized JSON

  const expected = crypto.createHmac('sha256', secret).update(raw).digest('hex')
  const ok =
    signature.length === expected.length &&
    crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))
  if (!ok) {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  let event: {
    event?: string
    payload?: { payment?: { entity?: { id?: string; order_id?: string } } }
  }
  try { event = JSON.parse(raw) } catch {
    return NextResponse.json({ error: 'Bad payload' }, { status: 400 })
  }

  const admin = createAdminClient()
  if (admin && event.event === 'payment.captured') {
    const pay = event.payload?.payment?.entity
    if (pay?.order_id) {
      await admin
        .from('payments')
        .update({
          status: 'paid',
          razorpay_payment_id: pay.id ?? null,
          paid_at: new Date().toISOString(),
        })
        .eq('razorpay_order_id', pay.order_id)
    }
  }

  return NextResponse.json({ received: true })
}
