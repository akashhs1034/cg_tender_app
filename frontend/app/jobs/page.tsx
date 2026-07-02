import { JobsClient } from '@/components/jobs-client'
import { getJobsPage } from '@/lib/data'

export const dynamic = 'force-dynamic'

type SP = Record<string, string | string[] | undefined>
const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v) ?? ''

export default async function JobsPage({ searchParams }: { searchParams: Promise<SP> }) {
  const sp = await searchParams
  const page = Math.max(1, parseInt(one(sp.page) || '1', 10) || 1)
  const q = one(sp.q)
  const state = one(sp.state) || 'All'
  const category = one(sp.category) || 'All'
  const mode = one(sp.mode) || 'All'
  const district = one(sp.district) || 'All'

  const { rows, total, pageSize } = await getJobsPage({ q, state, category, mode, district, page })

  return (
    <JobsClient
      jobs={rows}
      total={total}
      page={page}
      pageSize={pageSize}
      q={q}
      state={state}
      category={category}
      mode={mode}
      district={district}
    />
  )
}
