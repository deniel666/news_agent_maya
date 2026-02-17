import { useQuery } from '@tanstack/react-query'
import {
  getDashboardStats,
  getRecentActivity,
  getWeeklySummary,
  createBriefing,
} from '../lib/api'
import {
  FileText,
  Video,
  Clock,
  Play,
  CheckCircle,
  AlertCircle,
} from 'lucide-react'
import { formatDateTime, getStatusColor, getStatusLabel } from '../lib/utils'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import { LoadingSpinner } from '../components/LoadingSpinner'

export default function Dashboard() {
  const [isCreating, setIsCreating] = useState(false)

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
  })

  const { data: activity, isLoading: activityLoading } = useQuery({
    queryKey: ['recent-activity'],
    queryFn: getRecentActivity,
  })

  const { data: weeks, isLoading: weeksLoading } = useQuery({
    queryKey: ['weekly-summary'],
    queryFn: getWeeklySummary,
  })

  const handleCreateBriefing = async () => {
    setIsCreating(true)
    try {
      await createBriefing()
      // Refetch data
      window.location.reload()
    } catch (error) {
      console.error('Failed to create briefing:', error)
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 mt-1">
            Welcome to Maya AI News Anchor control panel
          </p>
        </div>
        <button
          onClick={handleCreateBriefing}
          disabled={isCreating}
          className="btn btn-primary flex items-center gap-2"
        >
          <Play className="w-4 h-4" />
          {isCreating ? 'Starting...' : 'Start New Briefing'}
        </button>
      </div>

      {/* Stats Grid */}
      {statsLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={FileText}
            label="Total Briefings"
            value={stats?.total_briefings || 0}
            color="maya"
          />
          <StatCard
            icon={CheckCircle}
            label="Completed"
            value={stats?.completed_briefings || 0}
            color="green"
          />
          <StatCard
            icon={Clock}
            label="Pending Approvals"
            value={stats?.pending_approvals || 0}
            color="yellow"
          />
          <StatCard
            icon={Video}
            label="Videos Generated"
            value={stats?.total_videos || 0}
            color="purple"
          />
        </div>
      )}

      {/* Weekly Summary */}
      <div className="card">
        <h2 className="text-xl font-semibold text-white mb-4">Weekly Summary</h2>
        {weeksLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="md" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {weeks?.map((week: any) => (
              <WeekCard key={`${week.year}-${week.week_number}`} week={week} />
            ))}
          </div>
        )}
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-xl font-semibold text-white mb-4">Recent Activity</h2>
        {activityLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="md" />
          </div>
        ) : (
          <div className="space-y-4">
            {activity?.length === 0 && (
              <p className="text-gray-400 text-center py-8">
                No activity yet. Start your first briefing!
              </p>
            )}
            {activity?.map((item: any) => (
              <ActivityItem key={item.thread_id} item={item} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: any
  label: string
  value: number
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

function WeekCard({ week }: { week: any }) {
  const statusIcons: Record<string, any> = {
    completed: CheckCircle,
    not_started: AlertCircle,
  }

  const Icon = statusIcons[week.status] || Clock

  return (
    <Link
      to={week.thread_id ? `/briefings/${week.thread_id}` : '#'}
      className="p-4 bg-dark-bg rounded-lg border border-dark-border hover:border-maya-500 transition-colors"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-lg font-semibold text-white">
          Week {week.week_number}
        </span>
        <Icon
          className={`w-5 h-5 ${
            week.status === 'completed'
              ? 'text-green-400'
              : week.status === 'not_started'
              ? 'text-gray-500'
              : 'text-yellow-400'
          }`}
        />
      </div>
      <p className="text-sm text-gray-400">{week.year}</p>
      <span className={`badge ${getStatusColor(week.status)} mt-2`}>
        {getStatusLabel(week.status)}
      </span>
    </Link>
  )
}

function ActivityItem({ item }: { item: any }) {
  return (
    <Link
      to={`/briefings/${item.thread_id}`}
      className="flex items-center justify-between p-4 bg-dark-bg rounded-lg hover:bg-dark-border transition-colors"
    >
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 bg-maya-900/50 rounded-lg flex items-center justify-center">
          <FileText className="w-5 h-5 text-maya-400" />
        </div>
        <div>
          <p className="font-medium text-white">
            Week {item.week_number}, {item.year}
          </p>
          <p className="text-sm text-gray-400">{item.thread_id}</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <span className={`badge ${getStatusColor(item.status)}`}>
          {getStatusLabel(item.status)}
        </span>
        <span className="text-sm text-gray-500">
          {formatDateTime(item.updated_at)}
        </span>
      </div>
    </Link>
  )
}
