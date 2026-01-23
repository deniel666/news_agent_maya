import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  Plus,
  Trash2,
  Edit2,
  ExternalLink,
  ToggleLeft,
  ToggleRight,
  Rss,
  MessageCircle,
  Twitter,
  RefreshCw,
  Upload,
} from 'lucide-react'
import { cn } from '../lib/utils'
import {
  listSources,
  createSource,
  updateSource,
  deleteSource,
  toggleSource,
  testSource,
  importDefaultSources,
} from '../lib/api'

type SourceType = 'rss' | 'telegram' | 'twitter'

interface Source {
  id: string
  name: string
  source_type: SourceType
  url: string
  category: string | null
  enabled: boolean
  created_at: string
}

export default function Sources() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingSource, setEditingSource] = useState<Source | null>(null)
  const [filter, setFilter] = useState<SourceType | 'all'>('all')

  const { data: sources, isLoading } = useQuery({
    queryKey: ['sources'],
    queryFn: () => listSources(),
  })

  const createMutation = useMutation({
    mutationFn: createSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
      setShowForm(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateSource(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
      setEditingSource(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
    },
  })

  const toggleMutation = useMutation({
    mutationFn: toggleSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
    },
  })

  const importMutation = useMutation({
    mutationFn: importDefaultSources,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
    },
  })

  const filteredSources = sources?.filter(
    (s: Source) => filter === 'all' || s.source_type === filter
  ) || []

  const sourcesByType = {
    rss: filteredSources.filter((s: Source) => s.source_type === 'rss'),
    telegram: filteredSources.filter((s: Source) => s.source_type === 'telegram'),
    twitter: filteredSources.filter((s: Source) => s.source_type === 'twitter'),
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">News Sources</h1>
          <p className="text-gray-400 mt-1">
            Manage RSS feeds, Telegram channels, and Twitter accounts
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => importMutation.mutate()}
            disabled={importMutation.isPending}
            className="btn btn-secondary flex items-center gap-2"
          >
            <Upload className="w-4 h-4" />
            {importMutation.isPending ? 'Importing...' : 'Import Defaults'}
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Source
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {(['all', 'rss', 'telegram', 'twitter'] as const).map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={cn(
              'px-4 py-2 rounded-lg capitalize flex items-center gap-2',
              filter === type
                ? 'bg-maya-600 text-white'
                : 'bg-dark-card text-gray-400 hover:text-white'
            )}
          >
            {type === 'rss' && <Rss className="w-4 h-4" />}
            {type === 'telegram' && <MessageCircle className="w-4 h-4" />}
            {type === 'twitter' && <Twitter className="w-4 h-4" />}
            {type === 'all' ? 'All Sources' : type}
            <span className="text-xs bg-dark-bg px-2 py-0.5 rounded-full">
              {type === 'all'
                ? sources?.length || 0
                : sourcesByType[type]?.length || 0}
            </span>
          </button>
        ))}
      </div>

      {/* Sources List */}
      <div className="card">
        {isLoading ? (
          <div className="text-center py-8 text-gray-400">Loading...</div>
        ) : filteredSources.length === 0 ? (
          <div className="text-center py-12">
            <Rss className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No sources configured</p>
            <p className="text-gray-500 text-sm mt-1">
              Add your first news source or import defaults
            </p>
          </div>
        ) : (
          <div className="divide-y divide-dark-border">
            {filteredSources.map((source: Source) => (
              <SourceRow
                key={source.id}
                source={source}
                onToggle={() => toggleMutation.mutate(source.id)}
                onEdit={() => setEditingSource(source)}
                onDelete={() => {
                  if (confirm('Delete this source?')) {
                    deleteMutation.mutate(source.id)
                  }
                }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Add/Edit Modal */}
      {(showForm || editingSource) && (
        <SourceModal
          source={editingSource}
          onClose={() => {
            setShowForm(false)
            setEditingSource(null)
          }}
          onSubmit={(data) => {
            if (editingSource) {
              updateMutation.mutate({ id: editingSource.id, data })
            } else {
              createMutation.mutate(data)
            }
          }}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      )}
    </div>
  )
}

function SourceRow({
  source,
  onToggle,
  onEdit,
  onDelete,
}: {
  source: Source
  onToggle: () => void
  onEdit: () => void
  onDelete: () => void
}) {
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const result = await testSource(source.id)
      setTestResult(result)
    } catch (error) {
      setTestResult({ status: 'error', message: 'Test failed' })
    } finally {
      setTesting(false)
    }
  }

  const iconMap = {
    rss: Rss,
    telegram: MessageCircle,
    twitter: Twitter,
  }
  const Icon = iconMap[source.source_type]

  return (
    <div className="p-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div
          className={cn(
            'w-10 h-10 rounded-lg flex items-center justify-center',
            source.enabled ? 'bg-maya-900/50' : 'bg-dark-bg'
          )}
        >
          <Icon
            className={cn(
              'w-5 h-5',
              source.enabled ? 'text-maya-400' : 'text-gray-500'
            )}
          />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h3
              className={cn(
                'font-medium',
                source.enabled ? 'text-white' : 'text-gray-500'
              )}
            >
              {source.name}
            </h3>
            {source.category && (
              <span className="text-xs bg-dark-bg text-gray-400 px-2 py-0.5 rounded">
                {source.category}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 truncate max-w-md">
            {source.url}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {testResult && (
          <span
            className={cn(
              'text-xs px-2 py-1 rounded',
              testResult.status === 'success'
                ? 'bg-green-900/30 text-green-400'
                : 'bg-red-900/30 text-red-400'
            )}
          >
            {testResult.status === 'success'
              ? `${testResult.articles_found} articles`
              : testResult.message}
          </span>
        )}
        <button
          onClick={handleTest}
          disabled={testing}
          className="p-2 hover:bg-dark-bg rounded-lg transition-colors"
          title="Test source"
        >
          <RefreshCw
            className={cn('w-4 h-4 text-gray-400', testing && 'animate-spin')}
          />
        </button>
        <button
          onClick={onToggle}
          className="p-2 hover:bg-dark-bg rounded-lg transition-colors"
          title={source.enabled ? 'Disable' : 'Enable'}
        >
          {source.enabled ? (
            <ToggleRight className="w-5 h-5 text-green-400" />
          ) : (
            <ToggleLeft className="w-5 h-5 text-gray-500" />
          )}
        </button>
        <button
          onClick={onEdit}
          className="p-2 hover:bg-dark-bg rounded-lg transition-colors"
          title="Edit"
        >
          <Edit2 className="w-4 h-4 text-gray-400" />
        </button>
        <button
          onClick={onDelete}
          className="p-2 hover:bg-dark-bg rounded-lg transition-colors"
          title="Delete"
        >
          <Trash2 className="w-4 h-4 text-red-400" />
        </button>
      </div>
    </div>
  )
}

function SourceModal({
  source,
  onClose,
  onSubmit,
  isLoading,
}: {
  source: Source | null
  onClose: () => void
  onSubmit: (data: any) => void
  isLoading: boolean
}) {
  const [formData, setFormData] = useState({
    name: source?.name || '',
    source_type: source?.source_type || 'rss',
    url: source?.url || '',
    category: source?.category || '',
    enabled: source?.enabled ?? true,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-dark-card rounded-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold text-white mb-4">
          {source ? 'Edit Source' : 'Add Source'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input w-full"
              placeholder="e.g., CNA Singapore"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Type</label>
            <select
              value={formData.source_type}
              onChange={(e) =>
                setFormData({ ...formData, source_type: e.target.value as SourceType })
              }
              className="input w-full"
            >
              <option value="rss">RSS Feed</option>
              <option value="telegram">Telegram Channel</option>
              <option value="twitter">Twitter (via Nitter)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">
              {formData.source_type === 'rss'
                ? 'RSS Feed URL'
                : formData.source_type === 'telegram'
                ? 'Channel (e.g., @channelnewsasia)'
                : 'Twitter Username'}
            </label>
            <input
              type="text"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              className="input w-full"
              placeholder={
                formData.source_type === 'rss'
                  ? 'https://example.com/feed.xml'
                  : formData.source_type === 'telegram'
                  ? '@channelname'
                  : 'username'
              }
              required
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Category</label>
            <select
              value={formData.category}
              onChange={(e) =>
                setFormData({ ...formData, category: e.target.value })
              }
              className="input w-full"
            >
              <option value="">No category</option>
              <option value="local">Local News</option>
              <option value="business">Business</option>
              <option value="ai_tech">AI & Tech</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="enabled"
              checked={formData.enabled}
              onChange={(e) =>
                setFormData({ ...formData, enabled: e.target.checked })
              }
              className="rounded"
            />
            <label htmlFor="enabled" className="text-sm text-gray-300">
              Enabled
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary"
            >
              {isLoading ? 'Saving...' : source ? 'Update' : 'Add Source'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
