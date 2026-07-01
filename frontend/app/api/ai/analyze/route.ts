import { NextResponse } from 'next/server'
import { generateWithGemini } from '@/lib/gemini'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

interface AnalyzeInput {
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
  const result = await generateWithGemini(buildPrompt(body ?? {}))
  return NextResponse.json(result)
}
