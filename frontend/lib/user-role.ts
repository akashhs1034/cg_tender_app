export type UserRole = 'contractor' | 'jobseeker'

export function normalizeUserRole(value: unknown): UserRole | null {
  return value === 'contractor' || value === 'jobseeker' ? value : null
}

export function roleLabel(role: UserRole | null): string {
  if (role === 'contractor') return 'Contractor / Business'
  if (role === 'jobseeker') return 'Job Seeker'
  return 'Choose experience'
}
