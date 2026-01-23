import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import {
  getBriefing,
  getPipelineStatus,
  approveScript,
  approveVideo,
} from '../lib/api'
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  Play,
  FileText,
  Video,
  Share2,
} from 'lucide-react'
import { formatDateTime, getStatusLabel, cn } from '../lib/utils'
import { useState } from 'react'

export default function BriefingDetail() {
  const { threadId } = useParams<{ threadId: string }>()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'scripts' | 'video' | 'posts'>('scripts')

  const { data, isLoading } = useQuery({
    queryKey: ['briefing', threadId],
    queryFn: () => getBriefing(threadId!),
    enabled: !!threadId,
    refetchInterval: 5000, // Poll for updates
  })

  const { data: pipelineData } = useQuery({
    queryKey: ['pipeline-status', threadId],
    queryFn: () => getPipelineStatus(threadId!),
    enabled: !!threadId,
    refetchInterval: 5000,
  })

  const scriptApproval = useMutation({
    mutationFn: ({ approved, feedback }: { approved: boolean; feedback?: string }) =>
      approveScript(threadId!, approved, feedback),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['briefing', threadId] })
      queryClient.invalidateQueries({ queryKey: ['pipeline-status', threadId] })
    },
  })

  const videoApproval = useMutation({
    mutationFn: ({ approved }: { approved: boolean }) =>
      approveVideo(threadId!, approved),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['briefing', threadId] })
      queryClient.invalidateQueries({ queryKey: ['pipeline-status', threadId] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading...</div>
      </div>
    )
  }

  const briefing = data?.briefing
  const state = data?.state

  if (!briefing) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">Briefing not found</p>
        <Link to="/briefings" className="btn btn-primary mt-4">
          Back to Briefings
        </Link>
      </div>
    )
  }

  const needsScriptApproval = briefing.status === 'awaiting_script_approval'
  const needsVideoApproval = briefing.status === 'awaiting_video_approval'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/briefings"
          className="p-2 hover:bg-dark-card rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-400" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white">
            Week {briefing.week_number}, {briefing.year}
          </h1>
          <p className="text-gray-400">{briefing.thread_id}</p>
        </div>
      </div>

      {/* Pipeline Progress */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Pipeline Progress</h2>
        <PipelineStages stages={pipelineData?.stages || []} />
      </div>

      {/* Approval Actions */}
      {needsScriptApproval && (
        <div className="card border-yellow-500/50 bg-yellow-900/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Clock className="w-6 h-6 text-yellow-400" />
              <div>
                <h3 className="font-semibold text-white">Script Approval Required</h3>
                <p className="text-sm text-gray-400">
                  Review the scripts below and approve to continue
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => scriptApproval.mutate({ approved: false, feedback: 'Rejected' })}
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

      {needsVideoApproval && (
        <div className="card border-yellow-500/50 bg-yellow-900/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Clock className="w-6 h-6 text-yellow-400" />
              <div>
                <h3 className="font-semibold text-white">Video Approval Required</h3>
                <p className="text-sm text-gray-400">
                  Review the video and approve to publish
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

      {/* Tabs */}
      <div className="flex gap-2 border-b border-dark-border">
        <TabButton
          active={activeTab === 'scripts'}
          onClick={() => setActiveTab('scripts')}
          icon={FileText}
          label="Scripts"
        />
        <TabButton
          active={activeTab === 'video'}
          onClick={() => setActiveTab('video')}
          icon={Video}
          label="Video"
        />
        <TabButton
          active={activeTab === 'posts'}
          onClick={() => setActiveTab('posts')}
          icon={Share2}
          label="Posts"
        />
      </div>

      {/* Tab Content */}
      {activeTab === 'scripts' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <ScriptCard
            title="Local & International News"
            script={briefing.local_script}
          />
          <ScriptCard
            title="Business News"
            script={briefing.business_script}
          />
          <ScriptCard
            title="AI & Tech News"
            script={briefing.ai_script}
          />
        </div>
      )}

      {activeTab === 'video' && (
        <div className="card">
          {state?.video_url ? (
            <div className="aspect-[9/16] max-w-sm mx-auto bg-black rounded-lg overflow-hidden">
              <video
                src={state.video_url}
                controls
                className="w-full h-full object-contain"
              />
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400">
              <Video className="w-12 h-12 mx-auto mb-4 text-gray-600" />
              <p>Video not yet generated</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'posts' && (
        <div className="card">
          {state?.post_results ? (
            <div className="space-y-4">
              {state.post_results.posts?.map((post: any, i: number) => (
                <div
                  key={i}
                  className="p-4 bg-dark-bg rounded-lg flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium text-white capitalize">
                      {post.platform}
                    </p>
                    <p className="text-sm text-gray-400">
                      {post.status === 'success' ? post.post_url : post.error}
                    </p>
                  </div>
                  <span
                    className={`badge ${
                      post.status === 'success' ? 'badge-success' : 'badge-error'
                    }`}
                  >
                    {post.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400">
              <Share2 className="w-12 h-12 mx-auto mb-4 text-gray-600" />
              <p>Not yet published</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function PipelineStages({ stages }: { stages: any[] }) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-2">
      {stages.map((stage, index) => (
        <div key={stage.name} className="flex items-center">
          <div
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap',
              stage.status === 'completed' && 'bg-green-900/30 text-green-400',
              stage.status === 'current' && 'bg-maya-900/50 text-maya-400 ring-2 ring-maya-500',
              stage.status === 'pending' && 'bg-dark-bg text-gray-500'
            )}
          >
            {stage.status === 'completed' ? (
              <CheckCircle className="w-4 h-4" />
            ) : stage.status === 'current' ? (
              <Play className="w-4 h-4" />
            ) : (
              <Clock className="w-4 h-4" />
            )}
            <span className="text-sm">{stage.label}</span>
          </div>
          {index < stages.length - 1 && (
            <div className="w-8 h-0.5 bg-dark-border mx-1" />
          )}
        </div>
      ))}
    </div>
  )
}

function TabButton({
  active,
  onClick,
  icon: Icon,
  label,
}: {
  active: boolean
  onClick: () => void
  icon: any
  label: string
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-2 px-4 py-3 border-b-2 transition-colors',
        active
          ? 'border-maya-500 text-maya-400'
          : 'border-transparent text-gray-400 hover:text-white'
      )}
    >
      <Icon className="w-4 h-4" />
      {label}
    </button>
  )
}

function ScriptCard({ title, script }: { title: string; script: string | null }) {
  return (
    <div className="card">
      <h3 className="font-semibold text-white mb-3">{title}</h3>
      {script ? (
        <div className="prose prose-invert prose-sm max-w-none">
          <pre className="whitespace-pre-wrap text-gray-300 text-sm font-sans bg-dark-bg p-4 rounded-lg">
            {script}
          </pre>
        </div>
      ) : (
        <p className="text-gray-500 italic">Not yet generated</p>
      )}
    </div>
  )
}
