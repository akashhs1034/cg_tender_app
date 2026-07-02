import { notFound } from 'next/navigation'
import { JobDetailClient } from '@/components/job-detail-client'
import { getJobById } from '@/lib/data'

export const revalidate = 300

export default async function JobDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const job = await getJobById(id)
  if (!job) notFound()
  return <JobDetailClient job={job} />
}
