// Server-only Google Gemini helper. The API key lives in a server env var and
// is never exposed to the browser. All callers must run on the server (API
// routes / server actions).

export interface GeminiResult {
  ok: boolean
  text?: string
  /** Why generation was unavailable: no_key | api_error_* | empty | network | bad_request */
  reason?: string
}

/** Returns true when a Gemini/Google API key is configured. */
export function hasGeminiKey(): boolean {
  return Boolean(process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY)
}

/**
 * Generate text with Gemini. Returns { ok:false, reason } instead of throwing so
 * callers can degrade gracefully (e.g. fall back to a local template) whenever
 * the key is missing or the API is unreachable.
 */
export async function generateWithGemini(prompt: string): Promise<GeminiResult> {
  const key = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY
  if (!key) return { ok: false, reason: 'no_key' }

  const model = process.env.GEMINI_MODEL || 'gemini-2.0-flash'
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${key}`

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { temperature: 0.6, maxOutputTokens: 2048 },
      }),
    })
    if (!res.ok) {
      const detail = await res.text().catch(() => '')
      console.error('[gemini] API error', res.status, detail.slice(0, 300))
      return { ok: false, reason: `api_error_${res.status}` }
    }
    const data = await res.json()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const text: string = (data?.candidates?.[0]?.content?.parts ?? [])
      .map((p: { text?: string }) => p.text ?? '')
      .join('')
      .trim()
    if (!text) return { ok: false, reason: 'empty' }
    return { ok: true, text }
  } catch (e) {
    console.error('[gemini] request failed', e)
    return { ok: false, reason: 'network' }
  }
}
