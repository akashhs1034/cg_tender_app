import { redirect } from 'next/navigation'
import { AdminHealthClient } from '@/components/admin-health-client'
import { getSourceHealth, getAdminOverview } from '@/lib/data'
import { isCurrentUserAdmin } from '@/lib/admin'

export const dynamic = 'force-dynamic'

export default async function AdminPage() {
  if (!(await isCurrentUserAdmin())) redirect('/login?next=/admin')
  const [sources, overview] = await Promise.all([
    getSourceHealth(),
    getAdminOverview(),
  ])
  return <AdminHealthClient sources={sources} overview={overview} />
}
