// Supabase Edge Function: intelligence
// Server-side Gemini for the two AI features the mobile app needs (the key never
// ships in the app). Mirrors the web app's evaluator.py prompts:
//   task "resume"     -> resume ↔ job match  (_llm_resume_eval)
//   task "study_plan" -> exam study plan      (generate_study_plan)
// The Flutter app has rule-based fallbacks for both, so this is an enhancement,
// not a hard dependency.
//
// Deploy:
//   supabase functions deploy intelligence
//   supabase secrets set GEMINI_API_KEY=<your key>

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

function resumePrompt(job: Record<string, unknown>, resume: string): string {
  const qual = (job.qualification as string) ||
    "Not specified — infer from job title and category";
  return `You are an HR screening assistant. Evaluate a candidate's resume against a government job posting.

JOB DETAILS:
Title: ${job.title ?? ""}
Department: ${job.department ?? job.dept ?? ""}
State: ${job.state ?? ""}
Category: ${job.category ?? ""}
Qualification required: ${qual}
Description: ${job.description ?? ""}

CANDIDATE RESUME:
${(resume || "").slice(0, 4000)}

Return ONLY valid JSON:
{
  "requirements": [
    {"label": "B.Tech/B.E. in Civil Engineering", "status": "met"},
    {"label": "3+ years site experience", "status": "missing"}
  ],
  "match_pct": 60,
  "verdict": "The candidate holds the required degree but lacks the stated field experience."
}`;
}

function studyPrompt(exam: string, examDate: string, hours: number): string {
  const daysTxt = examDate ? `exam date ${examDate}` : "an unspecified date";
  return `You are an expert mentor for Indian government recruitment exams,
specialising in Uttar Pradesh and Chhattisgarh state exams. Build a focused,
realistic, time-aware study plan tailored to THIS exam.

EXAM: ${exam}
EXAM DATE: ${examDate || "not specified"} (${daysTxt})
DAILY STUDY TIME: about ${hours} hours/day

Scale the number and length of phases to the time available. Name the most
scoring/important topics specific to this exam's typical syllabus.

Return ONLY valid JSON (no markdown):
{
  "exam": "${exam}",
  "days_left": 0,
  "overview": "2-3 sentence realistic strategy for the available time",
  "phases": [
    {"name": "Phase 1 — Foundation", "duration": "first ~X days", "focus": "what to achieve", "topics": ["topic", "topic", "topic"]}
  ],
  "high_priority_topics": ["6-10 highest-scoring / most-important topics for this exam"],
  "daily_routine": ["concrete daily time blocks"],
  "free_resources": ["which free platform for what, e.g. 'NCERT for Polity & History basics'"],
  "tips": ["3-5 practical preparation tips"]
}`;
}

serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  try {
    const key = Deno.env.get("GEMINI_API_KEY");
    if (!key) return json({ error: "GEMINI_API_KEY not configured" }, 500);

    const payload = await req.json();
    const task = payload.task as string;

    let prompt: string;
    if (task === "resume") {
      prompt = resumePrompt(payload.job ?? {}, payload.resume ?? "");
    } else if (task === "study_plan") {
      prompt = studyPrompt(
        String(payload.exam ?? "Government Exam"),
        String(payload.exam_date ?? ""),
        Number(payload.hours ?? 4),
      );
    } else {
      return json({ error: "unknown task" }, 400);
    }

    prompt +=
      "\n\nRespond strictly with valid raw JSON only. Do not wrap in markdown code blocks or fences.";

    const resp = await callGemini(key, {
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: { thinkingConfig: { thinkingBudget: 0 } },
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
