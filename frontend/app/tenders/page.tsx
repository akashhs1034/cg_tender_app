import { TendersClient } from '@/components/tenders-client'
import { getTenders } from '@/lib/data'

export const dynamic = 'force-dynamic'

export default async function TendersPage() {
  const tenders = await getTenders()
  return <TendersClient tenders={tenders} />
}
