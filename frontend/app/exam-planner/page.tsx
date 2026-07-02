import { ExamPlannerClient } from '@/components/exam-planner-client'
import { getJobs } from '@/lib/data'

export const revalidate = 300

export default async function ExamPlannerPage() {
  const jobs = await getJobs()
  return <ExamPlannerClient jobs={jobs} />
}
