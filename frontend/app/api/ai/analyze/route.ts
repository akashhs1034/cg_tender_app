import { NextResponse } from 'next/server'
import { generateWithGemini } from '@/lib/gemini'
import { supabase } from '@/lib/supabase'
import { createAdminClient } from '@/lib/supabase/admin'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

interface AnalyzeInput {
  id?: string
  title?: string
  department?: string
  category?: string
  state?: string
  estimatedValue?: string
  emd?: string
  deadline?: string
  eligibility?: string[]
  description?: string
}

function buildPrompt(d: AnalyzeInput): string {
  return `You are an expert Indian government tender advisor. Analyze the tender below for a contractor
deciding whether to bid. Output plain text (no markdown) with these short sections:
1. Summary (2 sentences)
2. Key eligibility requirements
3. Risk assessment (Low/Medium/High + why)
4. Recommended action (bid / review / skip) with a one-line reason
5. Documents likely required
Be concise and practical.

TENDER
- Title: ${d.title || '[unknown]'}
- Department: ${d.department || '[unknown]'}
- Category: ${d.category || '[unknown]'}
- State: ${d.state || '[unknown]'}
- Estimated value: ${d.estimatedValue || '[unknown]'}
- EMD: ${d.emd || '[unknown]'}
- Deadline: ${d.deadline || '[unknown]'}
- Stated eligibility: ${(d.eligibility && d.eligibility.length) ? d.eligibility.join('; ') : '[not provided]'}
- Description: ${d.description || '[not provided]'}`
}

export async function POST(req: Request) {
  let body: AnalyzeInput | null = null
  try {
    body = (await req.json()) as AnalyzeInput
  } catch {
    return NextResponse.json({ ok: false, reason: 'bad_request' }, { status: 400 })
  }
  const id = body?.id

  // 1) Cache hit — a tender's analysis is the same for everyone, so return the
  //    stored result and skip Gemini entirely.
  if (id) {
    const { data } = await supabase.from('tenders').select('ai_analysis').eq('source_id', id).maybeSingle()
    if (data?.ai_analysis) {
      return NextResponse.json({ ok: true, text: data.ai_analysis, cached: true })
    }
  }

  // 2) Generate once.
  const result = await generateWithGemini(buildPrompt(body ?? {}))

  // 3) Write back with the service role so the next user is free. Best-effort:
  //    if the service key isn't configured, we simply don't cache.
  if (result.ok && result.text && id) {
    const admin = createAdminClient()
    if (admin) {
      await admin.from('tenders')
        .update({ ai_analysis: result.text, ai_analysis_at: new Date().toISOString() })
        .eq('source_id', id)
    }
  }

  return NextResponse.json(result)
}
