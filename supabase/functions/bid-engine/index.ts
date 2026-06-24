// Supabase Edge Function: bid-engine
// Reads a tender document with Gemini (server-side key — never shipped in the
// app) and returns extracted fields + a drafted bid. The Flutter app computes
// the Eligible / Not-Eligible verdict locally from the returned requirements.
//
// Deploy:
//   supabase functions deploy bid-engine
//   supabase secrets set GEMINI_API_KEY=<your AQ. key>
//
// Mirrors the web app's bid_engine.py prompts (gemini-2.5-flash, thinking off).

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });

// Gemini's free tier intermittently returns 503/429 ("high demand"); retry a few
// times with backoff so a transient spike doesn't fail the whole request.
async function callGemini(key: string, body: unknown): Promise<Response> {
  const url =
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent";
  let resp!: Response;
  for (let attempt = 0; attempt < 3; attempt++) {
    resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-goog-api-key": key },
      body: JSON.stringify(body),
    });
    if (resp.status !== 503 && resp.status !== 429) return resp;
    if (attempt < 2) await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
  }
  return resp;
}

const PROMPT = `You are an expert Indian government tender bid consultant. You are given a tender / NIT document (and the contractor's profile). Do TWO things and return ONE JSON object.

1) EXTRACT these tender fields (use null if absent):
 title, organization, state, district, value_lakhs (number), deadline (YYYY-MM-DD if possible),
 contractor_class (e.g. "Class C"), required_turnover_lakhs (number), required_experience_years (number),
 emd, required_documents (array of strings), scope_of_work.

2) DRAFT a professional, tender-specific bid:
 cover_letter (a complete formal letter as a single string, addressed to the issuing authority,
   citing the contractor's class/turnover/experience and the specific scope — no placeholders),
 compliance (array of {requirement, our_response, status} rows),
 manual_actions (array of strings — physical/legal docs the contractor must arrange themselves,
   e.g. non-blacklisting affidavit on stamp paper, bank solvency certificate, CA net-worth with UDIN, EMD DD).

Return ONLY valid raw JSON (no markdown fences), shape:
{"tender":{...extracted fields...},"cover_letter":"...","compliance":[...],"manual_actions":[...]}`;

serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  try {
    const key = Deno.env.get("GEMINI_API_KEY");
    if (!key) return json({ error: "GEMINI_API_KEY not configured" }, 500);

    const { docBase64, mimeType, profile } = await req.json();

    const parts: unknown[] = [];
    if (docBase64) {
      let mime = (mimeType || "application/pdf").toLowerCase();
      if (!mime.includes("pdf") && !mime.includes("image")) mime = "application/pdf";
      parts.push({ inline_data: { mime_type: mime, data: docBase64 } });
    }
    const profileLine = profile
      ? `\n\nContractor profile: company=${profile.company_name ?? "-"}, class=${profile.contractor_class ?? "-"}, turnover=${profile.turnover_lakhs ?? "-"}L, experience=${profile.experience_years ?? "-"}yrs, sectors=${(profile.sectors ?? []).join(", ")}.`
      : "";
    parts.push({ text: PROMPT + profileLine });

    const resp = await callGemini(key, {
      contents: [{ parts }],
      generationConfig: {
        responseMimeType: "application/json",
        thinkingConfig: { thinkingBudget: 0 },
      },
    });

    if (!resp.ok) {
      const detail = await resp.text();
      return json({ error: "gemini_error", status: resp.status, detail }, 502);
    }

    const data = await resp.json();
    let text: string =
      (data?.candidates?.[0]?.content?.parts ?? [])
        .map((p: { text?: string }) => p.text ?? "")
        .join("")
        .trim();
    text = text.replace(/^```json/i, "").replace(/^```/, "").replace(/```$/, "").trim();

    let result: unknown;
    try {
      result = JSON.parse(text);
    } catch {
      return json({ error: "parse_failed", raw: text.slice(0, 500) }, 502);
    }
    return json(result, 200);
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});
