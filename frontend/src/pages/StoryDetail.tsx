import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { useState } from 'react'
import {
  ArrowLeft,
  Video,
  FileText,
  Share2,
  Star,
  ExternalLink,
  Trash2,
  Plus,
  CheckCircle,
  Clock,
  XCircle,
  Play,
  Download,
  Copy,
  Edit2,
} from 'lucide-react'
import { cn, formatDateTime } from '../lib/utils'
import {
  getStory,
  updateStory,
  deleteVideo,
  createPublishRecord,
  getStoryPublishRecords,
  toggleFeatured,
} from '../lib/api'
import ScriptEditor from '../components/ScriptEditor'

const PLATFORMS = [
  { id: 'instagram', label: 'Instagram', icon: '📸' },
  { id: 'facebook', label: 'Facebook', icon: '📘' },
  { id: 'tiktok', label: 'TikTok', icon: '🎵' },
  { id: 'youtube', label: 'YouTube', icon: '▶️' },
]

export default function StoryDetail() {
  const { storyId } = useParams<{ storyId: string }>()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'videos' | 'scripts' | 'publishing'>(
    'videos'
  )

  const { data: story, isLoading } = useQuery({
    queryKey: ['story', storyId],
    queryFn: () => getStory(storyId!),
    enabled: !!storyId,
  })

  const featureMutation = useMutation({
    mutationFn: () => toggleFeatured(storyId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['story', storyId] })
    },
  })

  const deleteVideoMutation = useMutation({
    mutationFn: deleteVideo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['story', storyId] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading...</div>
      </div>
    )
  }

  if (!story) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">Story not found</p>
        <Link to="/content" className="btn btn-primary mt-4">
          Back to Library
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link
          to="/content"
          className="p-2 hover:bg-dark-card rounded-lg transition-colors mt-1"
        >
          <ArrowLeft className="w-5 h-5 text-gray-400" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">{story.title}</h1>
            <button
              onClick={() => featureMutation.mutate()}
              className="p-1 hover:bg-dark-card rounded"
            >
              <Star
                className={cn(
                  'w-5 h-5',
                  story.featured
                    ? 'text-yellow-400 fill-yellow-400'
                    : 'text-gray-500'
                )}
              />
            </button>
          </div>
          {story.description && (
            <p className="text-gray-400 mt-1">{story.description}</p>
          )}
          {story.source_url && (
            <a
              href={story.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-maya-400 hover:text-maya-300 flex items-center gap-1 mt-1"
            >
              {story.source_url}
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
        <StatusBadge status={story.status} />
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <p className="text-2xl font-bold text-white">{story.videos?.length || 0}</p>
          <p className="text-sm text-gray-400">Videos</p>
        </div>
        <div className="card p-4">
          <p className="text-2xl font-bold text-white">
            {story.publish_records?.filter((r: any) => r.status === 'published')
              .length || 0}
          </p>
          <p className="text-sm text-gray-400">Published</p>
        </div>
        <div className="card p-4">
          <div className="flex gap-1">
            {story.script_en && <span className="text-lg">🇬🇧</span>}
            {story.script_ms && <span className="text-lg">🇲🇾</span>}
            {!story.script_en && !story.script_ms && (
              <span className="text-gray-500">-</span>
            )}
          </div>
          <p className="text-sm text-gray-400">Scripts</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-400">Created</p>
          <p className="text-white">{formatDateTime(story.created_at)}</p>
        </div>
      </div>

      {/* Tags */}
      {story.tags?.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {story.tags.map((tag: string) => (
            <span
              key={tag}
              className="px-3 py-1 bg-dark-card rounded-full text-sm text-gray-300"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-dark-border">
        <TabButton
          active={activeTab === 'videos'}
          onClick={() => setActiveTab('videos')}
          icon={Video}
          label="Videos"
          count={story.videos?.length}
        />
        <TabButton
          active={activeTab === 'scripts'}
          onClick={() => setActiveTab('scripts')}
          icon={FileText}
          label="Scripts"
        />
        <TabButton
          active={activeTab === 'publishing'}
          onClick={() => setActiveTab('publishing')}
          icon={Share2}
          label="Publishing"
          count={story.publish_records?.length}
        />
      </div>

      {/* Videos Tab */}
      {activeTab === 'videos' && (
        <div className="space-y-6">
          {!story.videos?.length ? (
            <div className="card text-center py-12">
              <Video className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">No videos yet</p>
              <p className="text-gray-500 text-sm mt-1">
                Generate videos from the scripts tab
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {story.videos.map((video: any) => (
                <VideoCard
                  key={video.id}
                  video={video}
                  onDelete={() => {
                    if (confirm('Delete this video?')) {
                      deleteVideoMutation.mutate(video.id)
                    }
                  }}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Scripts Tab */}
      {activeTab === 'scripts' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ScriptEditor
            title="🇬🇧 English Script"
            script={story.script_en}
            onSave={async (script) => {
              await updateStory(storyId!, { script_en: script } as any)
              queryClient.invalidateQueries({ queryKey: ['story', storyId] })
            }}
            readOnly={false}
          />
          <ScriptEditor
            title="🇲🇾 Malay Script"
            script={story.script_ms}
            onSave={async (script) => {
              await updateStory(storyId!, { script_ms: script } as any)
              queryClient.invalidateQueries({ queryKey: ['story', storyId] })
            }}
            readOnly={false}
          />
        </div>
      )}

      {/* Publishing Tab */}
      {activeTab === 'publishing' && (
        <PublishingTab story={story} storyId={storyId!} />
      )}
    </div>
  )
}

function TabButton({
  active,
  onClick,
  icon: Icon,
  label,
  count,
}: {
  active: boolean
  onClick: () => void
  icon: any
  label: string
  count?: number
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
      {count !== undefined && (
        <span className="text-xs bg-dark-bg px-2 py-0.5 rounded-full">
          {count}
        </span>
      )}
    </button>
  )
}

function VideoCard({
  video,
  onDelete,
}: {
  video: any
  onDelete: () => void
}) {
  const [showControls, setShowControls] = useState(false)

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-white">
          {video.language === 'en' ? '🇬🇧 English' : '🇲🇾 Malay'} Video
        </h3>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          {video.duration_seconds && (
            <span>{Math.floor(video.duration_seconds / 60)}:{(video.duration_seconds % 60).toString().padStart(2, '0')}</span>
          )}
          {video.resolution && <span>{video.resolution}</span>}
        </div>
      </div>

      {/* Video Player */}
      <div
        className="aspect-[9/16] bg-black rounded-lg overflow-hidden relative max-h-[400px] mx-auto"
        onMouseEnter={() => setShowControls(true)}
        onMouseLeave={() => setShowControls(false)}
      >
        <video
          src={video.video_url}
          controls
          className="w-full h-full object-contain"
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between mt-4">
        <div className="flex items-center gap-2">
          <a
            href={video.video_url}
            download
            className="btn btn-secondary text-sm flex items-center gap-1"
          >
            <Download className="w-4 h-4" />
            Download
          </a>
          <button
            onClick={() => navigator.clipboard.writeText(video.video_url)}
            className="btn btn-secondary text-sm flex items-center gap-1"
          >
            <Copy className="w-4 h-4" />
            Copy URL
          </button>
        </div>
        <button
          onClick={onDelete}
          className="p-2 hover:bg-dark-bg rounded-lg text-red-400"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

function PublishingTab({ story, storyId }: { story: any; storyId: string }) {
  const queryClient = useQueryClient()
  const [selectedVideo, setSelectedVideo] = useState<string | null>(null)
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null)

  const createPublishMutation = useMutation({
    mutationFn: (data: any) => createPublishRecord(storyId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['story', storyId] })
      setSelectedVideo(null)
      setSelectedPlatform(null)
    },
  })

  const publishedPlatforms = new Set(
    story.publish_records
      ?.filter((r: any) => r.status === 'published')
      .map((r: any) => `${r.platform}-${r.language}`)
  )

  return (
    <div className="space-y-6">
      {/* Publishing Status Grid */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">
          Publishing Status
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 text-sm">
                <th className="pb-3">Platform</th>
                <th className="pb-3">🇬🇧 English</th>
                <th className="pb-3">🇲🇾 Malay</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-border">
              {PLATFORMS.map((platform) => (
                <tr key={platform.id}>
                  <td className="py-3">
                    <span className="flex items-center gap-2">
                      {platform.icon} {platform.label}
                    </span>
                  </td>
                  <td className="py-3">
                    <PublishStatusCell
                      published={publishedPlatforms.has(`${platform.id}-en`)}
                      hasVideo={story.videos?.some((v: any) => v.language === 'en')}
                      record={story.publish_records?.find(
                        (r: any) => r.platform === platform.id && r.language === 'en'
                      )}
                    />
                  </td>
                  <td className="py-3">
                    <PublishStatusCell
                      published={publishedPlatforms.has(`${platform.id}-ms`)}
                      hasVideo={story.videos?.some((v: any) => v.language === 'ms')}
                      record={story.publish_records?.find(
                        (r: any) => r.platform === platform.id && r.language === 'ms'
                      )}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Publish Records List */}
      {story.publish_records?.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4">
            Publish History
          </h3>
          <div className="divide-y divide-dark-border">
            {story.publish_records.map((record: any) => (
              <div key={record.id} className="py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span>
                    {PLATFORMS.find((p) => p.id === record.platform)?.icon}
                  </span>
                  <div>
                    <p className="text-white capitalize">
                      {record.platform} ({record.language === 'en' ? '🇬🇧' : '🇲🇾'})
                    </p>
                    {record.post_url && (
                      <a
                        href={record.post_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-maya-400 hover:text-maya-300 flex items-center gap-1"
                      >
                        View Post <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <PublishStatusBadge status={record.status} />
                  {record.published_at && (
                    <span className="text-sm text-gray-500">
                      {formatDateTime(record.published_at)}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function PublishStatusCell({
  published,
  hasVideo,
  record,
}: {
  published: boolean
  hasVideo: boolean
  record?: any
}) {
  if (published) {
    return (
      <span className="flex items-center gap-1 text-green-400">
        <CheckCircle className="w-4 h-4" />
        Published
      </span>
    )
  }

  if (record?.status === 'pending') {
    return (
      <span className="flex items-center gap-1 text-yellow-400">
        <Clock className="w-4 h-4" />
        Pending
      </span>
    )
  }

  if (record?.status === 'failed') {
    return (
      <span className="flex items-center gap-1 text-red-400">
        <XCircle className="w-4 h-4" />
        Failed
      </span>
    )
  }

  if (!hasVideo) {
    return <span className="text-gray-500">No video</span>
  }

  return <span className="text-gray-500">Not published</span>
}

function PublishStatusBadge({ status }: { status: string }) {
  const config: Record<string, { color: string; label: string }> = {
    pending: { color: 'bg-yellow-500', label: 'Pending' },
    published: { color: 'bg-green-500', label: 'Published' },
    failed: { color: 'bg-red-500', label: 'Failed' },
  }

  const { color, label } = config[status] || { color: 'bg-gray-500', label: status }

  return (
    <span className={`px-2 py-1 rounded text-xs text-white ${color}`}>
      {label}
    </span>
  )
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { color: string; label: string }> = {
    draft: { color: 'bg-gray-500', label: 'Draft' },
    script_ready: { color: 'bg-blue-500', label: 'Script Ready' },
    video_ready: { color: 'bg-purple-500', label: 'Video Ready' },
    published: { color: 'bg-green-500', label: 'Published' },
    archived: { color: 'bg-gray-600', label: 'Archived' },
  }

  const { color, label } = config[status] || config.draft

  return (
    <span className={`px-3 py-1 rounded-full text-sm text-white ${color}`}>
      {label}
    </span>
  )
}
