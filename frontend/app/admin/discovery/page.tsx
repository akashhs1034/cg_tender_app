import { redirect } from 'next/navigation'
import { AdminDiscoveryClient } from '@/components/admin-discovery-client'
import { getDiscoveredSources } from '@/lib/data'
import { isCurrentUserAdmin } from '@/lib/admin'

export const dynamic = 'force-dynamic'

export default async function AdminDiscoveryPage() {
  if (!(await isCurrentUserAdmin())) redirect('/login?next=/admin/discovery')
  const sources = await getDiscoveredSources()
  return <AdminDiscoveryClient sources={sources} />
}
