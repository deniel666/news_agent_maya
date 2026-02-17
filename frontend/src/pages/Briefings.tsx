import { useQuery } from '@tanstack/react-query'
import { listBriefings, createBriefing } from '../lib/api'
import { Link } from 'react-router-dom'
import { FileText, Plus, ChevronRight } from 'lucide-react'
import { formatDateTime, getStatusColor, getStatusLabel } from '../lib/utils'
import { useState } from 'react'
import { LoadingSpinner } from '../components/LoadingSpinner'

export default function Briefings() {
  const [isCreating, setIsCreating] = useState(false)

  const { data: briefings, isLoading, refetch } = useQuery({
    queryKey: ['briefings'],
    queryFn: () => listBriefings({ limit: 50 }),
  })

  const handleCreateBriefing = async () => {
    setIsCreating(true)
    try {
      await createBriefing()
      refetch()
    } catch (error) {
      console.error('Failed to create briefing:', error)
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Briefings</h1>
          <p className="text-gray-400 mt-1">
            Manage your weekly news briefings
          </p>
        </div>
        <button
          onClick={handleCreateBriefing}
          disabled={isCreating}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          {isCreating ? 'Creating...' : 'New Briefing'}
        </button>
      </div>

      {/* Briefings List */}
      <div className="card">
        {isLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : briefings?.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No briefings yet</p>
            <p className="text-gray-500 text-sm mt-1">
              Create your first briefing to get started
            </p>
          </div>
        ) : (
          <div className="divide-y divide-dark-border">
            {briefings?.map((briefing) => (
              <BriefingRow key={briefing.id} briefing={briefing} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function BriefingRow({ briefing }: { briefing: any }) {
  return (
    <Link
      to={`/briefings/${briefing.thread_id}`}
      className="flex items-center justify-between p-4 hover:bg-dark-bg transition-colors"
    >
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-maya-900/50 rounded-xl flex items-center justify-center">
          <FileText className="w-6 h-6 text-maya-400" />
        </div>
        <div>
          <h3 className="font-semibold text-white">
            Week {briefing.week_number}, {briefing.year}
          </h3>
          <p className="text-sm text-gray-400">{briefing.thread_id}</p>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="text-right">
          <span className={`badge ${getStatusColor(briefing.status)}`}>
            {getStatusLabel(briefing.status)}
          </span>
          <p className="text-xs text-gray-500 mt-1">
            {formatDateTime(briefing.created_at)}
          </p>
        </div>
        <ChevronRight className="w-5 h-5 text-gray-500" />
      </div>
    </Link>
  )
}
