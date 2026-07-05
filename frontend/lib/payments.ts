/**
 * Payments feature flag + plan catalog. Everything stays FREE until Razorpay
 * keys are present in the environment AND a plan is defined. No pricing is
 * charged or shown while this returns false.
 */
export function paymentsEnabled(): boolean {
  return Boolean(
    process.env.RAZORPAY_KEY_ID &&
    process.env.RAZORPAY_KEY_SECRET &&
    process.env.NEXT_PUBLIC_PAYMENTS_ENABLED === 'true'
  )
}

/** Public flag for client components (no secrets). */
export function paymentsEnabledClient(): boolean {
  return process.env.NEXT_PUBLIC_PAYMENTS_ENABLED === 'true'
}

export interface Plan {
  id: string
  name: string
  amount: number // paise
  period: 'monthly' | 'yearly' | 'one_time'
  features: string[]
}

/**
 * Placeholder catalog — finalize names/prices/features once you decide the
 * model. Amounts are in paise (₹499 = 49900). Nothing is billed until
 * paymentsEnabled() is true.
 */
export const PLANS: Plan[] = [
  {
    id: 'pro_monthly',
    name: 'Opporta Pro',
    amount: 49900,
    period: 'monthly',
    features: [
      'Unlimited AI bid drafting',
      'AI eligibility checks',
      'Daily email alerts',
      'Priority tender matching',
    ],
  },
]
