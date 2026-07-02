import { NextResponse } from 'next/server'
import { generateWithGemini } from '@/lib/gemini'
import { supabase } from '@/lib/supabase'
import { createAdminClient } from '@/lib/supabase/admin'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

interface EligibilityInput {
  id?: string
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
  const id = body?.id

  // Cache hit — a job's eligibility read is the same for everyone.
  if (id) {
    const { data } = await supabase.from('jobs').select('ai_eligibility').eq('source_id', id).maybeSingle()
    if (data?.ai_eligibility) {
      return NextResponse.json({ ok: true, text: data.ai_eligibility, cached: true })
    }
  }

  const result = await generateWithGemini(buildPrompt(body ?? {}))

  if (result.ok && result.text && id) {
    const admin = createAdminClient()
    if (admin) {
      await admin.from('jobs')
        .update({ ai_eligibility: result.text, ai_eligibility_at: new Date().toISOString() })
        .eq('source_id', id)
    }
  }

  return NextResponse.json(result)
}
