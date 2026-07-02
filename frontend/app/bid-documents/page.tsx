import { BidDocumentsClient } from '@/components/bid-documents-client'
import { getTenders } from '@/lib/data'

export const revalidate = 300

export default async function BidDocumentsPage() {
  const tenders = await getTenders()
  return <BidDocumentsClient tenders={tenders} />
}
