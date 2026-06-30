import { JobsClient } from '@/components/jobs-client'
import { getJobs } from '@/lib/data'

export const dynamic = 'force-dynamic'

export default async function JobsPage() {
  const jobs = await getJobs()
  return <JobsClient jobs={jobs} />
}
