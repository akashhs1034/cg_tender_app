# Historical credential response

Verification date: 2026-07-28

Secret values are intentionally absent. Rotation or revocation is not treated
as confirmed without independent provider-side evidence.

## Findings

| Finding ID | Credential category | Provider/category | Historical commit SHA | Historical file path | Current tracked-tree presence | Rotation/revocation status | Required human action | Verification date | Notes without sensitive material |
|---|---|---|---|---|---|---|---|---|---|
| HCR-001 | Supabase publishable key | Supabase public client configuration | `3404020ca58b92fc9df84d2bfad0dd84c8667069` | `mobile/lib/config.dart` | yes | not applicable/public client configuration | Confirm that the key belongs to the intended public project; review exposed-schema grants and RLS before launch. | 2026-07-28 | The scanner classified this as a generic API key, but its key class and client use identify it as publishable configuration, not a server secret. |
| HCR-002 | Supabase publishable key | Supabase public client configuration | `ed9c6502545b6a5ee2732164f62163a991cecfa3` | `mobile/lib/config.dart` | no | not applicable/public client configuration | Confirm the historical project association and retain provider-side restrictions appropriate for a public client. | 2026-07-28 | A public key can still expose data when grants or RLS are unsafe. |
| HCR-003 | Supabase anon key | Supabase public client configuration | `5f6b19fdcc5b6a8b047411824e3808192008df66` | `mobile/lib/config.dart` | no | not applicable/public client configuration | Confirm the historical project association and review RLS for all client-accessible schemas. | 2026-07-28 | JWT metadata identified the public `anon` role; no token value was retained in this evidence. |
| HCR-004 | Supabase secret key | Supabase server credential | `e134e0853335b91f47eada71adcfbb4f7b0b201e` | `scraper_entry.py` | no | unconfirmed | A Supabase project owner must identify the corresponding historical server key in the dashboard, revoke or rotate it, and record provider-side confirmation without copying the key. | 2026-07-28 | The key class is secret/server-only and can bypass RLS. Absence from the current tree does not revoke it. |
| HCR-005 | Supabase publishable key | Supabase public client configuration | `a368e57d5363331a85b03c8a6a8b1a3ca19ef5f3` | `.streamlit/secrets.toml` | no | not applicable/public client configuration | Confirm the historical project association and RLS posture; do not treat the filename alone as proof that a public key is private. | 2026-07-28 | The file also contained configuration outside this scanner finding; no values were copied. |
| HCR-006 | Service-account private key | Google Cloud service account | `a368e57d5363331a85b03c8a6a8b1a3ca19ef5f3` | `client_secret.json` | no | unconfirmed | A Google Cloud owner must disable or delete the matching service-account key, review its access logs and IAM scope, and record the key identifier and revocation time in a restricted incident system. | 2026-07-28 | Structural inspection identified service-account JSON with private signing material; this was not an OAuth client-secret record. |
| HCR-007 | Gemini/Google private API key | Google Generative AI | `cfdcbb9dbf773890188ab7109dab170219f817a7` | `master_pipeline.py` | no | unconfirmed | A Google AI/Cloud owner must revoke or rotate the corresponding API key, review restrictions and usage, and record provider-side confirmation in a restricted incident system. | 2026-07-28 | Code context passed the value to the Google GenAI client. |

## Human confirmation checklist

- [ ] Supabase owner confirms HCR-004 is revoked or rotated in the relevant
  project and records provider-side evidence without pasting a credential.
- [ ] Google Cloud owner confirms HCR-006 signing material is disabled or
  deleted, reviews IAM scope and access, and records restricted evidence.
- [ ] Google AI/Cloud owner confirms HCR-007 is revoked or rotated and reviews
  historical usage and API restrictions.
- [ ] Database/security owner reviews RLS and grants for the public Supabase
  configurations in HCR-001, HCR-002, HCR-003, and HCR-005.
- [ ] Credential owners check provider consoles for Google OAuth client secrets,
  Anthropic keys, Resend keys, Razorpay secrets or webhook secrets, signing
  keystores, and private signing material not identified by this scan.
- [ ] Credential owners record any additional finding using the same fields
  above; never paste a key into chat, a terminal command, a pull request, or an
  issue.

## Category disposition notes

| Finding ID | Credential category | Provider/category | Rotation/revocation status | Required human action | Notes without sensitive material |
|---|---|---|---|---|---|
| HCR-C01 | Google OAuth client secret | Google OAuth | unconfirmed | Confirm in the owning Google Cloud projects whether any historical OAuth client secret was exposed and rotate if found. | The JSON finding in this audit was a service account, not an OAuth client secret. |
| HCR-C02 | Supabase service-role or secret key | Supabase server credential | unconfirmed | Complete HCR-004 and check for legacy service-role keys in the same project. | Server credentials bypass RLS and must remain server-only. |
| HCR-C03 | Supabase anon/publishable key | Supabase public client configuration | not applicable/public client configuration | Complete the RLS/grant review for HCR-001, HCR-002, HCR-003, and HCR-005. | Public client configuration is not automatically a private-secret incident. |
| HCR-C04 | Gemini/Google private API key | Google Generative AI | unconfirmed | Complete HCR-007. | Private API keys require provider-side revocation evidence. |
| HCR-C05 | Anthropic key | Anthropic | unconfirmed | Check the owner console and restricted credential inventory; revoke and investigate if a historical key is found. | No distinct Anthropic finding was classified in the redacted Gitleaks results. |
| HCR-C06 | Resend key | Resend | unconfirmed | Check the owner console and restricted credential inventory; revoke and investigate if a historical key is found. | No distinct Resend finding was classified in the redacted Gitleaks results. |
| HCR-C07 | Razorpay secret or webhook secret | Razorpay | unconfirmed | Check the owner console and restricted credential inventory; revoke and investigate if historical secret material is found. | Public Razorpay key identifiers must not be confused with private secrets. |
| HCR-C08 | Signing keystore/private signing material | Google Cloud / Android signing | unconfirmed | Complete HCR-006 and separately inventory Android signing keystores outside Git. | The service-account private key is confirmed historical signing material; no Android keystore finding was classified. |
| HCR-C09 | Public Firebase/mobile configuration | Firebase/mobile client configuration | not applicable/public client configuration | Review backend authorization, API restrictions, and RLS; rotate only if provider guidance or misuse requires it. | Public mobile configuration is not automatically secret. |
| HCR-C10 | Placeholder/example value | Local/test configuration | not applicable/public client configuration | Keep examples synthetic and scan them before commit. | No scanner suppression is based on a placeholder in this milestone. |
