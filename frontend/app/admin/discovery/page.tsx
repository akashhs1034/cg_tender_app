import { AdminDiscoveryClient } from '@/components/admin-discovery-client'
import { getDiscoveredSources } from '@/lib/data'

export const revalidate = 300

export default async function AdminDiscoveryPage() {
  const sources = await getDiscoveredSources()
  return <AdminDiscoveryClient sources={sources} />
}
