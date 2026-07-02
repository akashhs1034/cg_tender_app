import { TendersClient } from '@/components/tenders-client'
import { getTenders } from '@/lib/data'

export const revalidate = 300

export default async function TendersPage() {
  const tenders = await getTenders()
  return <TendersClient tenders={tenders} />
}
