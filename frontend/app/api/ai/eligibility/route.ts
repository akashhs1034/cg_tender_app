import { NextResponse } from 'next/server'
import { generateWithGemini } from '@/lib/gemini'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

interface EligibilityInput {
  title?: string
  department?: string
  category?: string
  qualification?: string
  ageLimit?: string
  eligibility?: string[]
  selectionProcess?: string[]
  description?: string
}

function buildPrompt(d: EligibilityInput): string {
  return `You are an expert Indian government-jobs advisor. Assess this recruitment for a candidate.
Output plain text (no markdown) with short sections:
1. Who is eligible (education, age, other must-haves)
2. Who should NOT apply
3. Selection process at a glance
4. Preparation tips (2-3 bullets)
5. Verdict: apply / maybe / skip, with a one-line reason
Be concise and practical.

JOB
- Title: ${d.title || '[unknown]'}
- Department: ${d.department || '[unknown]'}
- Category: ${d.category || '[unknown]'}
- Qualification: ${d.qualification || '[unknown]'}
- Age limit: ${d.ageLimit || '[unknown]'}
- Stated eligibility: ${(d.eligibility && d.eligibility.length) ? d.eligibility.join('; ') : '[not provided]'}
- Selection process: ${(d.selectionProcess && d.selectionProcess.length) ? d.selectionProcess.join(' → ') : '[not provided]'}
- Description: ${d.description || '[not provided]'}`
}

export async function POST(req: Request) {
  let body: EligibilityInput | null = null
  try {
    body = (await req.json()) as EligibilityInput
  } catch {
    return NextResponse.json({ ok: false, reason: 'bad_request' }, { status: 400 })
  }
  const result = await generateWithGemini(buildPrompt(body ?? {}))
  return NextResponse.json(result)
}
