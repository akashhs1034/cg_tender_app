import { AnalyticsClient } from '@/components/analytics-client'
import { getAnalytics } from '@/lib/data'

export const revalidate = 300

export default async function AnalyticsPage() {
  const analytics = await getAnalytics()
  return <AnalyticsClient analytics={analytics} />
}
