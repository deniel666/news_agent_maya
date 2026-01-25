import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Plus,
  Search,
  Filter,
  Grid,
  List,
  Star,
  Video,
  FileText,
  ExternalLink,
  MoreVertical,
  Trash2,
  Archive,
  Eye,
  CheckCircle,
  Clock,
  XCircle,
} from 'lucide-react'
import { cn, formatDateTime } from '../lib/utils'
import {
  listStories,
  createStory,
  deleteStory,
  toggleFeatured,
  archiveStory,
  getContentStats,
  getAllTags,
} from '../lib/api'

type ViewMode = 'grid' | 'list'
type StatusFilter = 'all' | 'draft' | 'script_ready' | 'video_ready' | 'published' | 'archived'

export default function ContentLibrary() {
  const queryClient = useQueryClient()
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTag, setSelectedTag] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)

  const { data: stories, isLoading } = useQuery({
    queryKey: ['stories', statusFilter, selectedTag, searchQuery],
    queryFn: () =>
      listStories({
        status: statusFilter !== 'all' ? statusFilter : undefined,
        tag: selectedTag || undefined,
        search: searchQuery || undefined,
      }),
  })

  const { data: stats } = useQuery({
    queryKey: ['content-stats'],
    queryFn: getContentStats,
  })

  const { data: tagsData } = useQuery({
    queryKey: ['all-tags'],
    queryFn: getAllTags,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteStory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stories'] })
      queryClient.invalidateQueries({ queryKey: ['content-stats'] })
    },
  })

  const featureMutation = useMutation({
    mutationFn: toggleFeatured,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stories'] })
    },
  })

  const archiveMutation = useMutation({
    mutationFn: archiveStory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stories'] })
      queryClient.invalidateQueries({ queryKey: ['content-stats'] })
    },
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Content Library</h1>
          <p className="text-gray-400 mt-1">
            Manage all your stories and videos
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Story
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <StatCard
          label="Total Stories"
          value={stats?.total_stories || 0}
          color="maya"
        />
        <StatCard
          label="Videos"
          value={stats?.total_videos || 0}
          color="purple"
        />
        <StatCard
          label="Published"
          value={stats?.total_published || 0}
          color="green"
        />
        <StatCard
          label="This Week"
          value={stats?.this_week || 0}
          color="blue"
        />
        <StatCard
          label="English"
          value={stats?.videos_by_language?.en || 0}
          icon="🇬🇧"
        />
        <StatCard
          label="Malay"
          value={stats?.videos_by_language?.ms || 0}
          icon="🇲🇾"
        />
      </div>

      {/* Filters & Search */}
      <div className="card">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search stories..."
              className="input w-full pl-10"
            />
          </div>

          {/* Status Filter */}
          <div className="flex gap-2 flex-wrap">
            {(['all', 'draft', 'script_ready', 'video_ready', 'published', 'archived'] as const).map(
              (status) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={cn(
                    'px-3 py-2 rounded-lg text-sm capitalize',
                    statusFilter === status
                      ? 'bg-maya-600 text-white'
                      : 'bg-dark-bg text-gray-400 hover:text-white'
                  )}
                >
                  {status.replace('_', ' ')}
                </button>
              )
            )}
          </div>

          {/* View Mode */}
          <div className="flex gap-1 bg-dark-bg rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={cn(
                'p-2 rounded',
                viewMode === 'grid' ? 'bg-dark-card text-white' : 'text-gray-500'
              )}
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={cn(
                'p-2 rounded',
                viewMode === 'list' ? 'bg-dark-card text-white' : 'text-gray-500'
              )}
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tags */}
        {tagsData?.tags?.length > 0 && (
          <div className="flex gap-2 flex-wrap mt-4 pt-4 border-t border-dark-border">
            <span className="text-sm text-gray-400 py-1">Tags:</span>
            {tagsData.tags.map((tag: string) => (
              <button
                key={tag}
                onClick={() =>
                  setSelectedTag(selectedTag === tag ? null : tag)
                }
                className={cn(
                  'px-3 py-1 rounded-full text-sm',
                  selectedTag === tag
                    ? 'bg-maya-600 text-white'
                    : 'bg-dark-bg text-gray-400 hover:text-white'
                )}
              >
                #{tag}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Stories Grid/List */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : !stories?.length ? (
        <div className="card text-center py-12">
          <FileText className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">No stories found</p>
          <p className="text-gray-500 text-sm mt-1">
            Create your first story or import from briefings
          </p>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {stories.map((story: any) => (
            <StoryCard
              key={story.id}
              story={story}
              onDelete={() => {
                if (confirm('Delete this story?')) {
                  deleteMutation.mutate(story.id)
                }
              }}
              onToggleFeatured={() => featureMutation.mutate(story.id)}
              onArchive={() => archiveMutation.mutate(story.id)}
            />
          ))}
        </div>
      ) : (
        <div className="card divide-y divide-dark-border">
          {stories.map((story: any) => (
            <StoryRow
              key={story.id}
              story={story}
              onDelete={() => {
                if (confirm('Delete this story?')) {
                  deleteMutation.mutate(story.id)
                }
              }}
              onToggleFeatured={() => featureMutation.mutate(story.id)}
              onArchive={() => archiveMutation.mutate(story.id)}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateStoryModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false)
            queryClient.invalidateQueries({ queryKey: ['stories'] })
          }}
        />
      )}
    </div>
  )
}

function StatCard({
  label,
  value,
  color,
  icon,
}: {
  label: string
  value: number
  color?: string
  icon?: string
}) {
  const colors: Record<string, string> = {
    maya: 'text-maya-400',
    purple: 'text-purple-400',
    green: 'text-green-400',
    blue: 'text-blue-400',
  }

  return (
    <div className="card p-4">
      <p className="text-2xl font-bold text-white flex items-center gap-2">
        {icon && <span>{icon}</span>}
        <span className={color ? colors[color] : ''}>{value}</span>
      </p>
      <p className="text-sm text-gray-400">{label}</p>
    </div>
  )
}

function StoryCard({
  story,
  onDelete,
  onToggleFeatured,
  onArchive,
}: {
  story: any
  onDelete: () => void
  onToggleFeatured: () => void
  onArchive: () => void
}) {
  const [showMenu, setShowMenu] = useState(false)

  return (
    <div className="card group relative overflow-hidden">
      {/* Thumbnail or placeholder */}
      <div className="aspect-video bg-dark-bg rounded-lg mb-4 flex items-center justify-center relative">
        {story.thumbnail_url ? (
          <img
            src={story.thumbnail_url}
            alt={story.title}
            className="w-full h-full object-cover rounded-lg"
          />
        ) : (
          <Video className="w-12 h-12 text-gray-600" />
        )}

        {/* Video count badge */}
        {story.video_count > 0 && (
          <div className="absolute bottom-2 right-2 bg-black/70 px-2 py-1 rounded text-xs text-white flex items-center gap-1">
            <Video className="w-3 h-3" />
            {story.video_count}
          </div>
        )}

        {/* Featured star */}
        {story.featured && (
          <div className="absolute top-2 left-2">
            <Star className="w-5 h-5 text-yellow-400 fill-yellow-400" />
          </div>
        )}
      </div>

      {/* Content */}
      <div>
        <div className="flex items-start justify-between gap-2">
          <Link
            to={`/content/${story.id}`}
            className="font-semibold text-white hover:text-maya-400 line-clamp-2"
          >
            {story.title}
          </Link>

          {/* Menu */}
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1 hover:bg-dark-bg rounded"
            >
              <MoreVertical className="w-4 h-4 text-gray-500" />
            </button>

            {showMenu && (
              <div className="absolute right-0 top-full mt-1 bg-dark-card border border-dark-border rounded-lg shadow-xl z-10 min-w-[150px]">
                <Link
                  to={`/content/${story.id}`}
                  className="flex items-center gap-2 px-4 py-2 hover:bg-dark-bg text-gray-300 text-sm"
                >
                  <Eye className="w-4 h-4" />
                  View
                </Link>
                <button
                  onClick={() => {
                    onToggleFeatured()
                    setShowMenu(false)
                  }}
                  className="flex items-center gap-2 px-4 py-2 hover:bg-dark-bg text-gray-300 text-sm w-full"
                >
                  <Star className="w-4 h-4" />
                  {story.featured ? 'Unfeature' : 'Feature'}
                </button>
                <button
                  onClick={() => {
                    onArchive()
                    setShowMenu(false)
                  }}
                  className="flex items-center gap-2 px-4 py-2 hover:bg-dark-bg text-gray-300 text-sm w-full"
                >
                  <Archive className="w-4 h-4" />
                  Archive
                </button>
                <button
                  onClick={() => {
                    onDelete()
                    setShowMenu(false)
                  }}
                  className="flex items-center gap-2 px-4 py-2 hover:bg-dark-bg text-red-400 text-sm w-full"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Meta */}
        <div className="flex items-center gap-2 mt-2 flex-wrap">
          <StatusBadge status={story.status} />
          <TypeBadge type={story.story_type} />
        </div>

        {/* Tags */}
        {story.tags?.length > 0 && (
          <div className="flex gap-1 mt-2 flex-wrap">
            {story.tags.slice(0, 3).map((tag: string) => (
              <span
                key={tag}
                className="text-xs bg-dark-bg text-gray-500 px-2 py-0.5 rounded"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}

        {/* Date */}
        <p className="text-xs text-gray-500 mt-2">
          {formatDateTime(story.created_at)}
        </p>
      </div>
    </div>
  )
}

function StoryRow({
  story,
  onDelete,
  onToggleFeatured,
  onArchive,
}: {
  story: any
  onDelete: () => void
  onToggleFeatured: () => void
  onArchive: () => void
}) {
  return (
    <div className="p-4 flex items-center gap-4">
      {/* Thumbnail */}
      <div className="w-20 h-12 bg-dark-bg rounded flex-shrink-0 flex items-center justify-center">
        {story.thumbnail_url ? (
          <img
            src={story.thumbnail_url}
            alt=""
            className="w-full h-full object-cover rounded"
          />
        ) : (
          <Video className="w-6 h-6 text-gray-600" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          {story.featured && (
            <Star className="w-4 h-4 text-yellow-400 fill-yellow-400 flex-shrink-0" />
          )}
          <Link
            to={`/content/${story.id}`}
            className="font-medium text-white hover:text-maya-400 truncate"
          >
            {story.title}
          </Link>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <StatusBadge status={story.status} small />
          <TypeBadge type={story.story_type} small />
          {story.video_count > 0 && (
            <span className="text-xs text-gray-500">
              {story.video_count} video{story.video_count !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>

      {/* Date */}
      <div className="text-sm text-gray-500 hidden md:block">
        {formatDateTime(story.created_at)}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1">
        <Link
          to={`/content/${story.id}`}
          className="p-2 hover:bg-dark-bg rounded-lg"
          title="View"
        >
          <Eye className="w-4 h-4 text-gray-400" />
        </Link>
        <button
          onClick={onToggleFeatured}
          className="p-2 hover:bg-dark-bg rounded-lg"
          title={story.featured ? 'Unfeature' : 'Feature'}
        >
          <Star
            className={cn(
              'w-4 h-4',
              story.featured
                ? 'text-yellow-400 fill-yellow-400'
                : 'text-gray-400'
            )}
          />
        </button>
        <button
          onClick={onArchive}
          className="p-2 hover:bg-dark-bg rounded-lg"
          title="Archive"
        >
          <Archive className="w-4 h-4 text-gray-400" />
        </button>
        <button
          onClick={onDelete}
          className="p-2 hover:bg-dark-bg rounded-lg"
          title="Delete"
        >
          <Trash2 className="w-4 h-4 text-red-400" />
        </button>
      </div>
    </div>
  )
}

function StatusBadge({ status, small }: { status: string; small?: boolean }) {
  const config: Record<string, { color: string; icon: any; label: string }> = {
    draft: { color: 'bg-gray-500', icon: FileText, label: 'Draft' },
    script_ready: { color: 'bg-blue-500', icon: FileText, label: 'Script Ready' },
    video_ready: { color: 'bg-purple-500', icon: Video, label: 'Video Ready' },
    published: { color: 'bg-green-500', icon: CheckCircle, label: 'Published' },
    archived: { color: 'bg-gray-600', icon: Archive, label: 'Archived' },
  }

  const { color, icon: Icon, label } = config[status] || config.draft

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full text-white',
        color,
        small ? 'px-2 py-0.5 text-xs' : 'px-2 py-1 text-xs'
      )}
    >
      <Icon className={small ? 'w-3 h-3' : 'w-3 h-3'} />
      {label}
    </span>
  )
}

function TypeBadge({ type, small }: { type: string; small?: boolean }) {
  const labels: Record<string, string> = {
    weekly_briefing: 'Weekly',
    on_demand: 'On-Demand',
    manual: 'Manual',
  }

  return (
    <span
      className={cn(
        'bg-dark-bg text-gray-400 rounded-full',
        small ? 'px-2 py-0.5 text-xs' : 'px-2 py-1 text-xs'
      )}
    >
      {labels[type] || type}
    </span>
  )
}

function CreateStoryModal({
  onClose,
  onCreated,
}: {
  onClose: () => void
  onCreated: () => void
}) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    source_url: '',
    tags: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await createStory({
        title: formData.title,
        description: formData.description || undefined,
        source_url: formData.source_url || undefined,
        tags: formData.tags
          ? formData.tags.split(',').map((t) => t.trim())
          : [],
      })
      onCreated()
    } catch (error) {
      console.error('Failed to create story:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-dark-card rounded-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold text-white mb-4">Create Story</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              className="input w-full"
              placeholder="Story title"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Description (optional)
            </label>
            <textarea
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              className="input w-full"
              rows={3}
              placeholder="Brief description"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Source URL (optional)
            </label>
            <input
              type="url"
              value={formData.source_url}
              onChange={(e) =>
                setFormData({ ...formData, source_url: e.target.value })
              }
              className="input w-full"
              placeholder="https://..."
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Tags (comma-separated)
            </label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) =>
                setFormData({ ...formData, tags: e.target.value })
              }
              className="input w-full"
              placeholder="news, tech, malaysia"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary"
            >
              {isSubmitting ? 'Creating...' : 'Create Story'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
