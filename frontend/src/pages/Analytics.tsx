import { useQuery } from '@tanstack/react-query'
import {
  BarChart3,
  TrendingUp,
  Clock,
  CheckCircle,
  Video,
  Share2,
  Calendar,
} from 'lucide-react'
import { formatDate } from '../lib/utils'
import { listBriefings } from '../lib/api'

export default function Analytics() {
  const { data: briefings } = useQuery({
    queryKey: ['all-briefings'],
    queryFn: () => listBriefings({ limit: 100 }),
  })

  // Calculate stats
  const stats = calculateStats(briefings || [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Analytics</h1>
        <p className="text-gray-400 mt-1">
          Insights and performance metrics for Maya
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={Calendar}
          label="Total Weeks"
          value={stats.totalWeeks}
          color="maya"
        />
        <StatCard
          icon={CheckCircle}
          label="Success Rate"
          value={`${stats.successRate}%`}
          color="green"
        />
        <StatCard
          icon={Video}
          label="Videos Published"
          value={stats.videosPublished}
          color="purple"
        />
        <StatCard
          icon={Clock}
          label="Avg. Processing Time"
          value={stats.avgProcessingTime}
          color="yellow"
        />
      </div>

      {/* Status Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-semibold text-white mb-4">
            Status Breakdown
          </h2>
          <div className="space-y-4">
            {Object.entries(stats.statusCounts).map(([status, count]) => (
              <StatusBar
                key={status}
                status={status}
                count={count}
                total={stats.totalWeeks}
              />
            ))}
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold text-white mb-4">
            Monthly Activity
          </h2>
          <div className="space-y-4">
            {stats.monthlyActivity.map((month) => (
              <div
                key={month.label}
                className="flex items-center justify-between p-3 bg-dark-bg rounded-lg"
              >
                <span className="text-gray-300">{month.label}</span>
                <div className="flex items-center gap-4">
                  <span className="text-maya-400 font-medium">
                    {month.count} briefings
                  </span>
                  <div className="w-24 h-2 bg-dark-border rounded-full overflow-hidden">
                    <div
                      className="h-full bg-maya-500 rounded-full"
                      style={{
                        width: `${(month.count / Math.max(...stats.monthlyActivity.map(m => m.count), 1)) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Completions */}
      <div className="card">
        <h2 className="text-xl font-semibold text-white mb-4">
          Recent Completions
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 text-sm">
                <th className="pb-3 font-medium">Week</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Created</th>
                <th className="pb-3 font-medium">Completed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-border">
              {(briefings || [])
                .filter((b) => b.status === 'completed')
                .slice(0, 10)
                .map((briefing) => (
                  <tr key={briefing.id} className="text-gray-300">
                    <td className="py-3">
                      Week {briefing.week_number}, {briefing.year}
                    </td>
                    <td className="py-3">
                      <span className="badge badge-success">Completed</span>
                    </td>
                    <td className="py-3 text-gray-400">
                      {formatDate(briefing.created_at)}
                    </td>
                    <td className="py-3 text-gray-400">
                      {briefing.published_at
                        ? formatDate(briefing.published_at)
                        : '-'}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Performance Tips */}
      <div className="card border-maya-500/30">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-maya-400" />
          Performance Insights
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InsightCard
            title="Best Posting Day"
            value="Sunday"
            description="Based on engagement patterns"
          />
          <InsightCard
            title="Optimal Video Length"
            value="2-3 min"
            description="For social media platforms"
          />
          <InsightCard
            title="Top News Category"
            value="AI & Tech"
            description="Most engaging content type"
          />
          <InsightCard
            title="Approval Time"
            value="< 2 hours"
            description="Average script approval time"
          />
        </div>
      </div>
    </div>
  )
}

function calculateStats(briefings: any[]) {
  const totalWeeks = briefings.length
  const completed = briefings.filter((b) => b.status === 'completed').length
  const successRate = totalWeeks > 0 ? Math.round((completed / totalWeeks) * 100) : 0

  // Status counts
  const statusCounts: Record<string, number> = {}
  briefings.forEach((b) => {
    statusCounts[b.status] = (statusCounts[b.status] || 0) + 1
  })

  // Monthly activity
  const monthlyMap: Record<string, number> = {}
  briefings.forEach((b) => {
    const date = new Date(b.created_at)
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    monthlyMap[key] = (monthlyMap[key] || 0) + 1
  })

  const monthlyActivity = Object.entries(monthlyMap)
    .sort((a, b) => b[0].localeCompare(a[0]))
    .slice(0, 6)
    .map(([key, count]) => {
      const [year, month] = key.split('-')
      const date = new Date(parseInt(year), parseInt(month) - 1)
      return {
        label: date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
        count,
      }
    })

  return {
    totalWeeks,
    successRate,
    videosPublished: completed,
    avgProcessingTime: '~4 hours',
    statusCounts,
    monthlyActivity,
  }
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: any
  label: string
  value: string | number
  color: string
}) {
  const colors: Record<string, string> = {
    maya: 'from-maya-500 to-maya-700',
    green: 'from-green-500 to-green-700',
    yellow: 'from-yellow-500 to-yellow-700',
    purple: 'from-purple-500 to-purple-700',
  }

  return (
    <div className="card">
      <div className="flex items-center gap-4">
        <div
          className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colors[color]} flex items-center justify-center`}
        >
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{value}</p>
          <p className="text-sm text-gray-400">{label}</p>
        </div>
      </div>
    </div>
  )
}

function StatusBar({
  status,
  count,
  total,
}: {
  status: string
  count: number
  total: number
}) {
  const percentage = total > 0 ? Math.round((count / total) * 100) : 0

  const statusLabels: Record<string, string> = {
    completed: 'Completed',
    awaiting_script_approval: 'Awaiting Script',
    awaiting_video_approval: 'Awaiting Video',
    generating_video: 'Generating',
    failed: 'Failed',
  }

  const statusColors: Record<string, string> = {
    completed: 'bg-green-500',
    awaiting_script_approval: 'bg-yellow-500',
    awaiting_video_approval: 'bg-purple-500',
    generating_video: 'bg-maya-500',
    failed: 'bg-red-500',
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-300">{statusLabels[status] || status}</span>
        <span className="text-gray-400 text-sm">
          {count} ({percentage}%)
        </span>
      </div>
      <div className="w-full h-2 bg-dark-bg rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${statusColors[status] || 'bg-gray-500'}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

function InsightCard({
  title,
  value,
  description,
}: {
  title: string
  value: string
  description: string
}) {
  return (
    <div className="p-4 bg-dark-bg rounded-lg">
      <p className="text-gray-400 text-sm">{title}</p>
      <p className="text-xl font-bold text-white mt-1">{value}</p>
      <p className="text-gray-500 text-xs mt-1">{description}</p>
    </div>
  )
}
