import { AnalyticsClient } from '@/components/analytics-client'
import { getAnalytics } from '@/lib/data'

export const dynamic = 'force-dynamic'

export default async function AnalyticsPage() {
  const analytics = await getAnalytics()
  return <AnalyticsClient analytics={analytics} />
}
