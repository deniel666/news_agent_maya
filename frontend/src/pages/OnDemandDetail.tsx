import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { useState } from 'react'
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  Video,
  FileText,
  ExternalLink,
  RefreshCw,
  Share2,
} from 'lucide-react'
import { cn, formatDateTime } from '../lib/utils'
import {
  getOnDemandJob,
  approveOnDemandScript,
  approveOnDemandVideo,
  regenerateOnDemandJob,
} from '../lib/api'
import ScriptEditor from '../components/ScriptEditor'

export default function OnDemandDetail() {
  const { jobId } = useParams<{ jobId: string }>()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'scripts' | 'videos'>('scripts')
  const [editedScripts, setEditedScripts] = useState<Record<string, string>>({})

  const { data: job, isLoading } = useQuery({
    queryKey: ['ondemand-job', jobId],
    queryFn: () => getOnDemandJob(jobId!),
    enabled: !!jobId,
    refetchInterval: 5000,
  })

  const scriptApproval = useMutation({
    mutationFn: ({
      approved,
      feedback,
    }: {
      approved: boolean
      feedback?: string
    }) =>
      approveOnDemandScript(
        jobId!,
        approved,
        feedback,
        Object.keys(editedScripts).length > 0 ? editedScripts : undefined
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ondemand-job', jobId] })
    },
  })

  const videoApproval = useMutation({
    mutationFn: ({ approved }: { approved: boolean }) =>
      approveOnDemandVideo(jobId!, approved),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ondemand-job', jobId] })
    },
  })

  const regenerate = useMutation({
    mutationFn: ({
      regenerateScript,
      regenerateVideo,
    }: {
      regenerateScript?: boolean
      regenerateVideo?: boolean
    }) => regenerateOnDemandJob(jobId!, regenerateScript, regenerateVideo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ondemand-job', jobId] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading...</div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">Job not found</p>
        <Link to="/on-demand" className="btn btn-primary mt-4">
          Back to On-Demand
        </Link>
      </div>
    )
  }

  const needsScriptApproval = job.status === 'awaiting_approval'
  const needsVideoApproval = job.status === 'awaiting_video_approval'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/on-demand"
          className="p-2 hover:bg-dark-card rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-400" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-white">
            {job.title || 'Untitled Article'}
          </h1>
          <a
            href={job.article_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-maya-400 hover:text-maya-300 flex items-center gap-1"
          >
            {job.article_url}
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
        <StatusBadge status={job.status} />
      </div>

      {/* Script Approval Action */}
      {needsScriptApproval && (
        <div className="card border-yellow-500/50 bg-yellow-900/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Clock className="w-6 h-6 text-yellow-400" />
              <div>
                <h3 className="font-semibold text-white">
                  Script Approval Required
                </h3>
                <p className="text-sm text-gray-400">
                  Review the scripts below and approve to generate videos
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() =>
                  scriptApproval.mutate({ approved: false, feedback: 'Rejected' })
                }
                disabled={scriptApproval.isPending}
                className="btn btn-danger flex items-center gap-2"
              >
                <XCircle className="w-4 h-4" />
                Reject
              </button>
              <button
                onClick={() => scriptApproval.mutate({ approved: true })}
                disabled={scriptApproval.isPending}
                className="btn btn-success flex items-center gap-2"
              >
                <CheckCircle className="w-4 h-4" />
                Approve Scripts
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Video Approval Action */}
      {needsVideoApproval && (
        <div className="card border-yellow-500/50 bg-yellow-900/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Clock className="w-6 h-6 text-yellow-400" />
              <div>
                <h3 className="font-semibold text-white">
                  Video Approval Required
                </h3>
                <p className="text-sm text-gray-400">
                  Review the videos and approve to publish
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => videoApproval.mutate({ approved: false })}
                disabled={videoApproval.isPending}
                className="btn btn-danger flex items-center gap-2"
              >
                <XCircle className="w-4 h-4" />
                Reject
              </button>
              <button
                onClick={() => videoApproval.mutate({ approved: true })}
                disabled={videoApproval.isPending}
                className="btn btn-success flex items-center gap-2"
              >
                <CheckCircle className="w-4 h-4" />
                Approve & Publish
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Job Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-sm text-gray-400">Languages</p>
          <div className="flex gap-2 mt-2">
            {job.languages?.map((lang: string) => (
              <span
                key={lang}
                className="px-3 py-1 bg-dark-bg rounded-full text-sm"
              >
                {lang === 'en' ? '🇬🇧 English' : '🇲🇾 Bahasa Melayu'}
              </span>
            ))}
          </div>
        </div>
        <div className="card">
          <p className="text-sm text-gray-400">Platforms</p>
          <div className="flex gap-2 mt-2 flex-wrap">
            {job.platforms?.map((platform: string) => (
              <span
                key={platform}
                className="px-3 py-1 bg-dark-bg rounded-full text-sm capitalize"
              >
                {platform}
              </span>
            ))}
          </div>
        </div>
        <div className="card">
          <p className="text-sm text-gray-400">Created</p>
          <p className="text-white mt-2">{formatDateTime(job.created_at)}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-dark-border">
        <button
          onClick={() => setActiveTab('scripts')}
          className={cn(
            'flex items-center gap-2 px-4 py-3 border-b-2 transition-colors',
            activeTab === 'scripts'
              ? 'border-maya-500 text-maya-400'
              : 'border-transparent text-gray-400 hover:text-white'
          )}
        >
          <FileText className="w-4 h-4" />
          Scripts
        </button>
        <button
          onClick={() => setActiveTab('videos')}
          className={cn(
            'flex items-center gap-2 px-4 py-3 border-b-2 transition-colors',
            activeTab === 'videos'
              ? 'border-maya-500 text-maya-400'
              : 'border-transparent text-gray-400 hover:text-white'
          )}
        >
          <Video className="w-4 h-4" />
          Videos
        </button>
      </div>

      {/* Scripts Tab */}
      {activeTab === 'scripts' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {job.scripts?.en && (
            <ScriptEditor
              title="🇬🇧 English Script"
              script={job.scripts.en}
              onSave={(script) =>
                setEditedScripts({ ...editedScripts, en: script })
              }
              readOnly={!needsScriptApproval}
            />
          )}
          {job.scripts?.ms && (
            <ScriptEditor
              title="🇲🇾 Malay Script"
              script={job.scripts.ms}
              onSave={(script) =>
                setEditedScripts({ ...editedScripts, ms: script })
              }
              readOnly={!needsScriptApproval}
            />
          )}
          {!job.scripts?.en && !job.scripts?.ms && (
            <div className="card col-span-2 text-center py-12">
              <FileText className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">Scripts not yet generated</p>
            </div>
          )}
        </div>
      )}

      {/* Videos Tab */}
      {activeTab === 'videos' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {job.videos?.en && (
            <div className="card">
              <h3 className="font-semibold text-white mb-4">
                🇬🇧 English Video
              </h3>
              <div className="aspect-[9/16] bg-black rounded-lg overflow-hidden max-h-[400px]">
                <video
                  src={job.videos.en}
                  controls
                  className="w-full h-full object-contain"
                />
              </div>
              {job.captions?.en && (
                <div className="mt-4">
                  <p className="text-sm text-gray-400 mb-1">Caption:</p>
                  <p className="text-sm text-gray-300">{job.captions.en}</p>
                </div>
              )}
            </div>
          )}
          {job.videos?.ms && (
            <div className="card">
              <h3 className="font-semibold text-white mb-4">
                🇲🇾 Malay Video
              </h3>
              <div className="aspect-[9/16] bg-black rounded-lg overflow-hidden max-h-[400px]">
                <video
                  src={job.videos.ms}
                  controls
                  className="w-full h-full object-contain"
                />
              </div>
              {job.captions?.ms && (
                <div className="mt-4">
                  <p className="text-sm text-gray-400 mb-1">Caption:</p>
                  <p className="text-sm text-gray-300">{job.captions.ms}</p>
                </div>
              )}
            </div>
          )}
          {!job.videos?.en && !job.videos?.ms && (
            <div className="card col-span-2 text-center py-12">
              <Video className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">Videos not yet generated</p>
            </div>
          )}
        </div>
      )}

      {/* Regenerate Actions */}
      {(job.status === 'failed' ||
        job.status === 'rejected' ||
        job.status === 'completed') && (
        <div className="card">
          <h3 className="font-semibold text-white mb-4">Actions</h3>
          <div className="flex gap-3">
            <button
              onClick={() =>
                regenerate.mutate({
                  regenerateScript: true,
                  regenerateVideo: false,
                })
              }
              disabled={regenerate.isPending}
              className="btn btn-secondary flex items-center gap-2"
            >
              <RefreshCw
                className={cn('w-4 h-4', regenerate.isPending && 'animate-spin')}
              />
              Regenerate Scripts
            </button>
            {job.scripts?.en || job.scripts?.ms ? (
              <button
                onClick={() =>
                  regenerate.mutate({
                    regenerateScript: false,
                    regenerateVideo: true,
                  })
                }
                disabled={regenerate.isPending}
                className="btn btn-secondary flex items-center gap-2"
              >
                <Video className="w-4 h-4" />
                Regenerate Videos
              </button>
            ) : null}
          </div>
        </div>
      )}

      {/* Error Display */}
      {job.error && (
        <div className="card border-red-500/50 bg-red-900/10">
          <h3 className="font-semibold text-red-400 mb-2">Error</h3>
          <p className="text-gray-300">{job.error}</p>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { color: string; label: string }> = {
    pending: { color: 'bg-gray-500', label: 'Pending' },
    scraping: { color: 'bg-blue-500', label: 'Scraping' },
    generating_script: { color: 'bg-blue-500', label: 'Generating Script' },
    awaiting_approval: { color: 'bg-yellow-500', label: 'Awaiting Approval' },
    generating_video: { color: 'bg-purple-500', label: 'Generating Video' },
    awaiting_video_approval: {
      color: 'bg-yellow-500',
      label: 'Awaiting Video Approval',
    },
    publishing: { color: 'bg-blue-500', label: 'Publishing' },
    completed: { color: 'bg-green-500', label: 'Completed' },
    failed: { color: 'bg-red-500', label: 'Failed' },
    rejected: { color: 'bg-red-500', label: 'Rejected' },
  }

  const { color, label } = config[status] || {
    color: 'bg-gray-500',
    label: status,
  }

  return (
    <span className={`px-3 py-1 rounded-full text-sm text-white ${color}`}>
      {label}
    </span>
  )
}
