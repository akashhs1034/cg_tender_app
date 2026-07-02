import { notFound } from 'next/navigation'
import { TenderDetailClient } from '@/components/tender-detail-client'
import { getTenderById } from '@/lib/data'

export const revalidate = 300

export default async function TenderDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const tender = await getTenderById(id)
  if (!tender) notFound()
  return <TenderDetailClient tender={tender} />
}
