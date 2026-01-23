import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPendingApprovals, approveScript, approveVideo } from '../lib/api'
import { Link } from 'react-router-dom'
import {
  FileText,
  Video,
  CheckCircle,
  XCircle,
  Clock,
  ExternalLink,
} from 'lucide-react'
import { formatDateTime } from '../lib/utils'
import { useState } from 'react'

export default function Approvals() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['pending-approvals'],
    queryFn: getPendingApprovals,
    refetchInterval: 10000,
  })

  const scriptApproval = useMutation({
    mutationFn: ({ threadId, approved, feedback }: { threadId: string; approved: boolean; feedback?: string }) =>
      approveScript(threadId, approved, feedback),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
    },
  })

  const videoApproval = useMutation({
    mutationFn: ({ threadId, approved }: { threadId: string; approved: boolean }) =>
      approveVideo(threadId, approved),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
    },
  })

  const scriptApprovals = data?.script_approvals || []
  const videoApprovals = data?.video_approvals || []
  const totalPending = scriptApprovals.length + videoApprovals.length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Approvals</h1>
        <p className="text-gray-400 mt-1">
          Review and approve scripts and videos before publishing
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 bg-yellow-900/50 rounded-xl flex items-center justify-center">
            <Clock className="w-6 h-6 text-yellow-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{totalPending}</p>
            <p className="text-sm text-gray-400">Total Pending</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 bg-maya-900/50 rounded-xl flex items-center justify-center">
            <FileText className="w-6 h-6 text-maya-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{scriptApprovals.length}</p>
            <p className="text-sm text-gray-400">Scripts to Review</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 bg-purple-900/50 rounded-xl flex items-center justify-center">
            <Video className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{videoApprovals.length}</p>
            <p className="text-sm text-gray-400">Videos to Review</p>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="card text-center py-8 text-gray-400">Loading...</div>
      ) : totalPending === 0 ? (
        <div className="card text-center py-12">
          <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-4" />
          <p className="text-white font-medium">All caught up!</p>
          <p className="text-gray-400 text-sm mt-1">
            No pending approvals at the moment
          </p>
        </div>
      ) : (
        <>
          {/* Script Approvals */}
          {scriptApprovals.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-white">Script Approvals</h2>
              {scriptApprovals.map((item: any) => (
                <ScriptApprovalCard
                  key={item.thread_id}
                  item={item}
                  onApprove={(approved, feedback) =>
                    scriptApproval.mutate({ threadId: item.thread_id, approved, feedback })
                  }
                  isLoading={scriptApproval.isPending}
                />
              ))}
            </div>
          )}

          {/* Video Approvals */}
          {videoApprovals.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-white">Video Approvals</h2>
              {videoApprovals.map((item: any) => (
                <VideoApprovalCard
                  key={item.thread_id}
                  item={item}
                  onApprove={(approved) =>
                    videoApproval.mutate({ threadId: item.thread_id, approved })
                  }
                  isLoading={videoApproval.isPending}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function ScriptApprovalCard({
  item,
  onApprove,
  isLoading,
}: {
  item: any
  onApprove: (approved: boolean, feedback?: string) => void
  isLoading: boolean
}) {
  const [expanded, setExpanded] = useState(false)
  const [feedback, setFeedback] = useState('')

  return (
    <div className="card border-yellow-500/30">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-semibold text-white">
            Week {item.week_number}, {item.year}
          </h3>
          <p className="text-sm text-gray-400">{item.thread_id}</p>
          <p className="text-xs text-gray-500 mt-1">
            Created {formatDateTime(item.created_at)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to={`/briefings/${item.thread_id}`}
            className="btn btn-secondary text-sm flex items-center gap-1"
          >
            View Details
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* Script Preview */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-maya-400 text-sm hover:underline mb-4"
      >
        {expanded ? 'Hide Scripts' : 'Show Scripts'}
      </button>

      {expanded && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-dark-bg rounded-lg p-3">
            <h4 className="text-sm font-medium text-gray-400 mb-2">Local News</h4>
            <p className="text-sm text-gray-300 line-clamp-6">
              {item.scripts?.local || 'N/A'}
            </p>
          </div>
          <div className="bg-dark-bg rounded-lg p-3">
            <h4 className="text-sm font-medium text-gray-400 mb-2">Business</h4>
            <p className="text-sm text-gray-300 line-clamp-6">
              {item.scripts?.business || 'N/A'}
            </p>
          </div>
          <div className="bg-dark-bg rounded-lg p-3">
            <h4 className="text-sm font-medium text-gray-400 mb-2">AI & Tech</h4>
            <p className="text-sm text-gray-300 line-clamp-6">
              {item.scripts?.ai || 'N/A'}
            </p>
          </div>
        </div>
      )}

      {/* Feedback & Actions */}
      <div className="flex items-center gap-4">
        <input
          type="text"
          placeholder="Optional feedback..."
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          className="input flex-1"
        />
        <button
          onClick={() => onApprove(false, feedback || 'Rejected')}
          disabled={isLoading}
          className="btn btn-danger flex items-center gap-2"
        >
          <XCircle className="w-4 h-4" />
          Reject
        </button>
        <button
          onClick={() => onApprove(true)}
          disabled={isLoading}
          className="btn btn-success flex items-center gap-2"
        >
          <CheckCircle className="w-4 h-4" />
          Approve
        </button>
      </div>
    </div>
  )
}

function VideoApprovalCard({
  item,
  onApprove,
  isLoading,
}: {
  item: any
  onApprove: (approved: boolean) => void
  isLoading: boolean
}) {
  return (
    <div className="card border-purple-500/30">
      <div className="flex items-start gap-6">
        {/* Video Preview */}
        <div className="w-48 aspect-[9/16] bg-black rounded-lg overflow-hidden flex-shrink-0">
          {item.video_url ? (
            <video
              src={item.video_url}
              controls
              className="w-full h-full object-contain"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-600">
              <Video className="w-8 h-8" />
            </div>
          )}
        </div>

        {/* Details */}
        <div className="flex-1">
          <div className="mb-4">
            <h3 className="font-semibold text-white">
              Week {item.week_number}, {item.year}
            </h3>
            <p className="text-sm text-gray-400">{item.thread_id}</p>
            <p className="text-xs text-gray-500 mt-1">
              Created {formatDateTime(item.created_at)}
            </p>
          </div>

          <div className="flex items-center gap-4">
            <Link
              to={`/briefings/${item.thread_id}`}
              className="btn btn-secondary text-sm flex items-center gap-1"
            >
              View Details
              <ExternalLink className="w-3 h-3" />
            </Link>
            <button
              onClick={() => onApprove(false)}
              disabled={isLoading}
              className="btn btn-danger flex items-center gap-2"
            >
              <XCircle className="w-4 h-4" />
              Reject
            </button>
            <button
              onClick={() => onApprove(true)}
              disabled={isLoading}
              className="btn btn-success flex items-center gap-2"
            >
              <CheckCircle className="w-4 h-4" />
              Approve & Publish
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
