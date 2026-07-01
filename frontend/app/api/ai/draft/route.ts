import { NextResponse } from 'next/server'
import { generateWithGemini } from '@/lib/gemini'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

interface DraftInput {
  firmName?: string
  contractorClass?: string
  turnover?: string
  experience?: string
  tenderTitle?: string
  department?: string
  nitNumber?: string
  estimatedValue?: string
  emd?: string
  deadline?: string
  scope?: string
  firmDocs?: string[]
  tenderDocName?: string
}

function buildPrompt(d: DraftInput): string {
  return `You are an expert Indian government tender bid writer. Write a complete, professional,
ready-to-submit bid proposal (technical + commercial cover) in formal English for the tender below.
Use standard Indian government tender conventions. Output plain text only (no markdown), with clear
numbered sections: Introduction, Firm Credentials, Understanding of Scope & Methodology, Eligibility
& EMD, Documents Enclosed, and Declaration. Where information is missing, insert a clearly bracketed
placeholder like [To be filled]. Keep it concise and credible.

FIRM DETAILS
- Name: ${d.firmName || '[Firm name]'}
- Contractor class/registration: ${d.contractorClass || '[Class]'}
- Average annual turnover (₹ lakhs): ${d.turnover || '[Turnover]'}
- Years of experience: ${d.experience || '[Experience]'}
- Firm documents available: ${(d.firmDocs && d.firmDocs.length) ? d.firmDocs.join(', ') : '[list of documents]'}

TENDER DETAILS
- Title: ${d.tenderTitle || '[Tender title]'}
- Department/Organization: ${d.department || '[Department]'}
- NIT/Tender No.: ${d.nitNumber || '[NIT number]'}
- Estimated value: ${d.estimatedValue || '[Value]'}
- EMD: ${d.emd || '[EMD]'}
- Submission deadline: ${d.deadline || '[Deadline]'}
- Reference tender document: ${d.tenderDocName || '[not provided]'}
- Scope/methodology notes from bidder: ${d.scope || '[none provided]'}`
}

export async function POST(req: Request) {
  let body: DraftInput | null = null
  try {
    body = (await req.json()) as DraftInput
  } catch {
    return NextResponse.json({ ok: false, reason: 'bad_request' }, { status: 400 })
  }
  const result = await generateWithGemini(buildPrompt(body ?? {}))
  return NextResponse.json(result)
}
