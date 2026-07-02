import { TendersClient } from '@/components/tenders-client'
import { getTendersPage } from '@/lib/data'

export const dynamic = 'force-dynamic'

type SP = Record<string, string | string[] | undefined>
const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v) ?? ''

export default async function TendersPage({ searchParams }: { searchParams: Promise<SP> }) {
  const sp = await searchParams
  const page = Math.max(1, parseInt(one(sp.page) || '1', 10) || 1)
  const q = one(sp.q)
  const state = one(sp.state) || 'All'
  const category = one(sp.category) || 'All'
  const mode = one(sp.mode) || 'All'
  const district = one(sp.district) || 'All'

  const { rows, total, pageSize } = await getTendersPage({ q, state, category, mode, district, page })

  return (
    <TendersClient
      tenders={rows}
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
