import { getCurrentUser } from '@/lib/supabase/server'

/**
 * Admin allowlist. Set ADMIN_EMAILS (comma-separated) in the environment;
 * falls back to the founder's email so admin never locks out by misconfig.
 */
export function adminEmails(): string[] {
  return (process.env.ADMIN_EMAILS || 'akashhs1034@gmail.com')
    .split(',')
    .map((e) => e.trim().toLowerCase())
    .filter(Boolean)
}

export function isAdminEmail(email: string | null | undefined): boolean {
  if (!email) return false
  return adminEmails().includes(email.toLowerCase())
}

/** Server-side: current signed-in user's email is on the admin allowlist. */
export async function isCurrentUserAdmin(): Promise<boolean> {
  const user = await getCurrentUser()
  return isAdminEmail(user?.email)
}
