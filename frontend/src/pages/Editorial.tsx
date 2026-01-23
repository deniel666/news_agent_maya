import { useState, useEffect } from 'react'
import {
  Scale,
  FileText,
  Building2,
  ListChecks,
  Play,
  Star,
  ArrowUp,
  ArrowDown,
  ChevronRight,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  BarChart3,
  Clock,
  Filter,
  RefreshCw,
  Archive,
  ExternalLink,
} from 'lucide-react'
import { cn } from '../lib/utils'
import {
  getEditorialStats,
  getBrandProfile,
  updateBrandProfile,
  listGuidelines,
  createGuideline,
  updateGuideline,
  deleteGuideline,
  toggleGuideline,
  importDefaultGuidelines,
  listRawStories,
  scoreRawStory,
  promoteRawStory,
  archiveRawStory,
  listReviews,
  runEditorialReview,
  getGuidelineCategories,
  aggregateNews,
  runFullEditorialCycle,
  EditorialStats,
  BrandProfile,
  EditorialGuideline,
  RawStory,
  EditorialReview,
} from '../lib/api'

type TabType = 'overview' | 'brand' | 'guidelines' | 'stories' | 'reviews'

const rankColors: Record<string, string> = {
  top_priority: 'bg-green-500/20 text-green-400 border-green-500/30',
  high: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  rejected: 'bg-red-500/20 text-red-400 border-red-500/30',
}

const rankLabels: Record<string, string> = {
  top_priority: 'Top Priority',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  rejected: 'Rejected',
}

export default function Editorial() {
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [stats, setStats] = useState<EditorialStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  async function loadStats() {
    try {
      const data = await getEditorialStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'overview' as TabType, label: 'Overview', icon: BarChart3 },
    { id: 'brand' as TabType, label: 'Brand Profile', icon: Building2 },
    { id: 'guidelines' as TabType, label: 'Guidelines', icon: ListChecks },
    { id: 'stories' as TabType, label: 'Raw Stories', icon: FileText },
    { id: 'reviews' as TabType, label: 'Reviews', icon: Scale },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Editorial</h1>
          <p className="text-gray-400 mt-1">
            Manage brand guidelines, curate stories, and review content rankings
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-dark-border">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-3 border-b-2 transition-colors',
                activeTab === tab.id
                  ? 'border-maya-500 text-maya-400'
                  : 'border-transparent text-gray-400 hover:text-white'
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && <OverviewTab stats={stats} loading={loading} />}
      {activeTab === 'brand' && <BrandTab />}
      {activeTab === 'guidelines' && <GuidelinesTab />}
      {activeTab === 'stories' && <StoriesTab onStatsChange={loadStats} />}
      {activeTab === 'reviews' && <ReviewsTab />}
    </div>
  )
}

// ===================
// Overview Tab
// ===================

function OverviewTab({ stats, loading }: { stats: EditorialStats | null; loading: boolean }) {
  const [aggregating, setAggregating] = useState(false)
  const [runningCycle, setRunningCycle] = useState(false)

  async function handleAggregate() {
    setAggregating(true)
    try {
      const result = await aggregateNews(7, false)
      alert(`Aggregated ${result.stored} stories (${result.skipped_duplicates} duplicates skipped)`)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to aggregate news')
    } finally {
      setAggregating(false)
    }
  }

  async function handleFullCycle() {
    if (!confirm('This will aggregate news and run a full editorial review. Continue?')) return
    setRunningCycle(true)
    try {
      await runFullEditorialCycle(7)
      alert('Full editorial cycle started in background. Check Reviews tab for results.')
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to run editorial cycle')
    } finally {
      setRunningCycle(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 text-maya-500 animate-spin" />
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="text-center py-12 text-gray-400">
        Failed to load editorial statistics
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Quick Actions */}
      <div className="bg-dark-card rounded-xl border border-dark-border p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
        <div className="flex gap-4">
          <button
            onClick={handleAggregate}
            disabled={aggregating}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {aggregating ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            Aggregate News
          </button>
          <button
            onClick={handleFullCycle}
            disabled={runningCycle || aggregating}
            className="flex items-center gap-2 px-4 py-2 bg-maya-600 text-white rounded-lg hover:bg-maya-700 transition-colors disabled:opacity-50"
          >
            {runningCycle ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Run Full Editorial Cycle
          </button>
        </div>
        <p className="text-sm text-gray-400 mt-3">
          Aggregate pulls news from RSS, Nitter, and Telegram. Full cycle also runs the AI editorial review.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Total Raw Stories"
          value={stats.total_raw_stories}
          icon={FileText}
        />
        <StatCard
          label="Pending Review"
          value={stats.pending_review}
          icon={Clock}
          highlight={stats.pending_review > 0}
        />
        <StatCard
          label="Reviewed This Week"
          value={stats.reviewed_this_week}
          icon={Check}
        />
        <StatCard
          label="Promoted This Week"
          value={stats.promoted_this_week}
          icon={ArrowUp}
        />
      </div>

      {/* Rank Distribution */}
      <div className="bg-dark-card rounded-xl border border-dark-border p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Story Rankings</h3>
        <div className="grid grid-cols-5 gap-4">
          <RankCard rank="top_priority" count={stats.top_priority_stories} />
          <RankCard rank="high" count={stats.high_stories} />
          <RankCard rank="medium" count={stats.medium_stories} />
          <RankCard rank="low" count={stats.low_stories} />
          <RankCard rank="rejected" count={stats.rejected_stories} />
        </div>
      </div>

      {/* Average Score */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-dark-card rounded-xl border border-dark-border p-6">
          <h3 className="text-lg font-semibold text-white mb-2">Average Score</h3>
          <div className="flex items-end gap-2">
            <span className="text-4xl font-bold text-maya-400">
              {stats.average_score.toFixed(1)}
            </span>
            <span className="text-gray-400 mb-1">/ 100</span>
          </div>
          <div className="mt-4 h-2 bg-dark-border rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500"
              style={{ width: `${stats.average_score}%` }}
            />
          </div>
        </div>

        <div className="bg-dark-card rounded-xl border border-dark-border p-6">
          <h3 className="text-lg font-semibold text-white mb-2">Editorial Reviews</h3>
          <div className="flex items-end gap-2">
            <span className="text-4xl font-bold text-white">{stats.total_reviews}</span>
            <span className="text-gray-400 mb-1">total</span>
          </div>
          {stats.latest_review_date && (
            <p className="text-sm text-gray-400 mt-2">
              Last review: {new Date(stats.latest_review_date).toLocaleDateString()}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  icon: Icon,
  highlight = false,
}: {
  label: string
  value: number
  icon: any
  highlight?: boolean
}) {
  return (
    <div className="bg-dark-card rounded-xl border border-dark-border p-4">
      <div className="flex items-center gap-3">
        <div
          className={cn(
            'w-10 h-10 rounded-lg flex items-center justify-center',
            highlight ? 'bg-maya-500/20' : 'bg-dark-border'
          )}
        >
          <Icon className={cn('w-5 h-5', highlight ? 'text-maya-400' : 'text-gray-400')} />
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{value}</p>
          <p className="text-sm text-gray-400">{label}</p>
        </div>
      </div>
    </div>
  )
}

function RankCard({ rank, count }: { rank: string; count: number }) {
  return (
    <div
      className={cn(
        'rounded-lg border p-4 text-center',
        rankColors[rank] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'
      )}
    >
      <p className="text-2xl font-bold">{count}</p>
      <p className="text-sm opacity-80">{rankLabels[rank] || rank}</p>
    </div>
  )
}

// ===================
// Brand Tab
// ===================

function BrandTab() {
  const [profile, setProfile] = useState<BrandProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editing, setEditing] = useState(false)

  const [formData, setFormData] = useState({
    name: '',
    tagline: '',
    mission: '',
    vision: '',
    values: [] as string[],
    target_audience: '',
    tone_of_voice: '',
    content_pillars: [] as string[],
    differentiators: [] as string[],
    competitors: [] as string[],
    ai_prompt_context: '',
  })

  useEffect(() => {
    loadProfile()
  }, [])

  async function loadProfile() {
    try {
      const data = await getBrandProfile()
      if (data) {
        setProfile(data)
        setFormData({
          name: data.name || '',
          tagline: data.tagline || '',
          mission: data.mission || '',
          vision: data.vision || '',
          values: data.values || [],
          target_audience: data.target_audience || '',
          tone_of_voice: data.tone_of_voice || '',
          content_pillars: data.content_pillars || [],
          differentiators: data.differentiators || [],
          competitors: data.competitors || [],
          ai_prompt_context: data.ai_prompt_context || '',
        })
      }
    } catch (error) {
      console.error('Failed to load profile:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    setSaving(true)
    try {
      await updateBrandProfile(formData)
      await loadProfile()
      setEditing(false)
    } catch (error) {
      console.error('Failed to save profile:', error)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 text-maya-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Brand Profile</h2>
        {!editing ? (
          <button
            onClick={() => setEditing(true)}
            className="flex items-center gap-2 px-4 py-2 bg-maya-600 text-white rounded-lg hover:bg-maya-700 transition-colors"
          >
            <Edit2 className="w-4 h-4" />
            Edit Profile
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => setEditing(false)}
              className="px-4 py-2 border border-dark-border text-gray-300 rounded-lg hover:bg-dark-border transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              Save
            </button>
          </div>
        )}
      </div>

      <div className="bg-dark-card rounded-xl border border-dark-border p-6 space-y-6">
        {/* Basic Info */}
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Brand Name
            </label>
            {editing ? (
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-maya-500"
                placeholder="e.g., Erzy Media"
              />
            ) : (
              <p className="text-white">{profile?.name || 'Not set'}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Tagline
            </label>
            {editing ? (
              <input
                type="text"
                value={formData.tagline}
                onChange={(e) => setFormData({ ...formData, tagline: e.target.value })}
                className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-maya-500"
                placeholder="Your brand tagline"
              />
            ) : (
              <p className="text-white">{profile?.tagline || 'Not set'}</p>
            )}
          </div>
        </div>

        {/* Mission & Vision */}
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Mission
            </label>
            {editing ? (
              <textarea
                value={formData.mission}
                onChange={(e) => setFormData({ ...formData, mission: e.target.value })}
                className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-maya-500 h-24"
                placeholder="What does your company do?"
              />
            ) : (
              <p className="text-white">{profile?.mission || 'Not set'}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Vision
            </label>
            {editing ? (
              <textarea
                value={formData.vision}
                onChange={(e) => setFormData({ ...formData, vision: e.target.value })}
                className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-maya-500 h-24"
                placeholder="What do you aspire to achieve?"
              />
            ) : (
              <p className="text-white">{profile?.vision || 'Not set'}</p>
            )}
          </div>
        </div>

        {/* Target Audience & Tone */}
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Target Audience
            </label>
            {editing ? (
              <textarea
                value={formData.target_audience}
                onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-maya-500 h-24"
                placeholder="Who are you creating content for?"
              />
            ) : (
              <p className="text-white">{profile?.target_audience || 'Not set'}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Tone of Voice
            </label>
            {editing ? (
              <textarea
                value={formData.tone_of_voice}
                onChange={(e) => setFormData({ ...formData, tone_of_voice: e.target.value })}
                className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-maya-500 h-24"
                placeholder="How do you communicate? (e.g., professional, friendly, authoritative)"
              />
            ) : (
              <p className="text-white">{profile?.tone_of_voice || 'Not set'}</p>
            )}
          </div>
        </div>

        {/* Lists */}
        <div className="grid grid-cols-2 gap-6">
          <ArrayField
            label="Core Values"
            values={formData.values}
            onChange={(values) => setFormData({ ...formData, values })}
            editing={editing}
            placeholder="Add a value"
          />
          <ArrayField
            label="Content Pillars"
            values={formData.content_pillars}
            onChange={(values) => setFormData({ ...formData, content_pillars: values })}
            editing={editing}
            placeholder="Add a pillar"
          />
        </div>

        {/* AI Context */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            AI Prompt Context
          </label>
          <p className="text-xs text-gray-500 mb-2">
            Custom context included in AI prompts when evaluating stories
          </p>
          {editing ? (
            <textarea
              value={formData.ai_prompt_context}
              onChange={(e) => setFormData({ ...formData, ai_prompt_context: e.target.value })}
              className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-maya-500 h-32 font-mono text-sm"
              placeholder="Additional context for the AI when scoring stories..."
            />
          ) : (
            <pre className="text-white text-sm whitespace-pre-wrap bg-dark-bg p-4 rounded-lg">
              {profile?.ai_prompt_context || 'Not set'}
            </pre>
          )}
        </div>
      </div>
    </div>
  )
}

function ArrayField({
  label,
  values,
  onChange,
  editing,
  placeholder,
}: {
  label: string
  values: string[]
  onChange: (values: string[]) => void
  editing: boolean
  placeholder: string
}) {
  const [newItem, setNewItem] = useState('')

  function addItem() {
    if (newItem.trim()) {
      onChange([...values, newItem.trim()])
      setNewItem('')
    }
  }

  function removeItem(index: number) {
    onChange(values.filter((_, i) => i !== index))
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-300 mb-2">{label}</label>
      <div className="flex flex-wrap gap-2">
        {values.map((value, index) => (
          <span
            key={index}
            className="inline-flex items-center gap-1 px-3 py-1 bg-maya-500/20 text-maya-400 rounded-full text-sm"
          >
            {value}
            {editing && (
              <button onClick={() => removeItem(index)} className="hover:text-white">
                <X className="w-3 h-3" />
              </button>
            )}
          </span>
        ))}
        {editing && (
          <div className="flex items-center gap-1">
            <input
              type="text"
              value={newItem}
              onChange={(e) => setNewItem(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addItem()}
              className="px-3 py-1 bg-dark-bg border border-dark-border rounded-full text-white text-sm focus:outline-none focus:border-maya-500"
              placeholder={placeholder}
            />
            <button
              onClick={addItem}
              className="p-1 text-maya-400 hover:text-white"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ===================
// Guidelines Tab
// ===================

function GuidelinesTab() {
  const [guidelines, setGuidelines] = useState<EditorialGuideline[]>([])
  const [categories, setCategories] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [importing, setImporting] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [guidelinesData, categoriesData] = await Promise.all([
        listGuidelines(),
        getGuidelineCategories(),
      ])
      setGuidelines(guidelinesData)
      setCategories(categoriesData)
    } catch (error) {
      console.error('Failed to load guidelines:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleImportDefaults() {
    setImporting(true)
    try {
      await importDefaultGuidelines()
      await loadData()
    } catch (error) {
      console.error('Failed to import defaults:', error)
    } finally {
      setImporting(false)
    }
  }

  async function handleToggle(id: string) {
    try {
      await toggleGuideline(id)
      await loadData()
    } catch (error) {
      console.error('Failed to toggle guideline:', error)
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this guideline?')) return
    try {
      await deleteGuideline(id)
      await loadData()
    } catch (error) {
      console.error('Failed to delete guideline:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 text-maya-500 animate-spin" />
      </div>
    )
  }

  // Group by category
  const grouped = guidelines.reduce((acc, g) => {
    const cat = g.category || 'other'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(g)
    return acc
  }, {} as Record<string, EditorialGuideline[]>)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Editorial Guidelines</h2>
        <div className="flex gap-2">
          {guidelines.length === 0 && (
            <button
              onClick={handleImportDefaults}
              disabled={importing}
              className="flex items-center gap-2 px-4 py-2 border border-dark-border text-gray-300 rounded-lg hover:bg-dark-border transition-colors disabled:opacity-50"
            >
              {importing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Import Defaults
            </button>
          )}
          <button
            onClick={() => setShowAdd(true)}
            className="flex items-center gap-2 px-4 py-2 bg-maya-600 text-white rounded-lg hover:bg-maya-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Guideline
          </button>
        </div>
      </div>

      {Object.entries(grouped).map(([category, items]) => {
        const catInfo = categories.find((c) => c.value === category)
        return (
          <div key={category} className="space-y-3">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
              {catInfo?.label || category}
            </h3>
            {items.map((guideline) => (
              <div
                key={guideline.id}
                className={cn(
                  'bg-dark-card rounded-lg border p-4',
                  guideline.enabled ? 'border-dark-border' : 'border-dark-border opacity-50'
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-white">{guideline.name}</h4>
                      <span className="text-xs text-yellow-400">
                        {'★'.repeat(Math.round(guideline.weight))}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mt-1">{guideline.description}</p>
                    <p className="text-xs text-gray-500 mt-2">{guideline.criteria}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleToggle(guideline.id)}
                      className={cn(
                        'px-3 py-1 text-xs rounded-full transition-colors',
                        guideline.enabled
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-gray-500/20 text-gray-400'
                      )}
                    >
                      {guideline.enabled ? 'Enabled' : 'Disabled'}
                    </button>
                    <button
                      onClick={() => handleDelete(guideline.id)}
                      className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )
      })}

      {showAdd && (
        <AddGuidelineModal
          categories={categories}
          onClose={() => setShowAdd(false)}
          onSave={async (data) => {
            await createGuideline(data)
            await loadData()
            setShowAdd(false)
          }}
        />
      )}
    </div>
  )
}

function AddGuidelineModal({
  categories,
  onClose,
  onSave,
}: {
  categories: any[]
  onClose: () => void
  onSave: (data: any) => Promise<void>
}) {
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    name: '',
    category: 'topic_priority',
    description: '',
    criteria: '',
    weight: 1.0,
    enabled: true,
  })

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      await onSave(form)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-dark-card rounded-xl border border-dark-border p-6 w-full max-w-lg">
        <h3 className="text-lg font-semibold text-white mb-4">Add Guideline</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Category</label>
            <select
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white"
            >
              {categories.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
            <input
              type="text"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Criteria (for AI evaluation)
            </label>
            <textarea
              value={form.criteria}
              onChange={(e) => setForm({ ...form, criteria: e.target.value })}
              className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-white h-24"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Weight ({form.weight.toFixed(1)}x)
            </label>
            <input
              type="range"
              min="0.5"
              max="2"
              step="0.1"
              value={form.weight}
              onChange={(e) => setForm({ ...form, weight: parseFloat(e.target.value) })}
              className="w-full"
            />
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-dark-border text-gray-300 rounded-lg hover:bg-dark-border"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-maya-600 text-white rounded-lg hover:bg-maya-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ===================
// Stories Tab
// ===================

function StoriesTab({ onStatsChange }: { onStatsChange: () => void }) {
  const [stories, setStories] = useState<RawStory[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({
    status: '',
    rank: '',
    sortBy: 'created_at',
  })

  useEffect(() => {
    loadStories()
  }, [filter])

  async function loadStories() {
    setLoading(true)
    try {
      const data = await listRawStories({
        status: filter.status || undefined,
        rank: filter.rank || undefined,
        sort_by: filter.sortBy,
        limit: 100,
      })
      setStories(data)
    } catch (error) {
      console.error('Failed to load stories:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleScore(storyId: string) {
    try {
      await scoreRawStory(storyId)
      await loadStories()
      onStatsChange()
    } catch (error) {
      console.error('Failed to score story:', error)
    }
  }

  async function handlePromote(storyId: string) {
    try {
      await promoteRawStory(storyId)
      await loadStories()
      onStatsChange()
    } catch (error) {
      console.error('Failed to promote story:', error)
    }
  }

  async function handleArchive(storyId: string) {
    try {
      await archiveRawStory(storyId)
      await loadStories()
      onStatsChange()
    } catch (error) {
      console.error('Failed to archive story:', error)
    }
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-4">
        <select
          value={filter.status}
          onChange={(e) => setFilter({ ...filter, status: e.target.value })}
          className="px-4 py-2 bg-dark-card border border-dark-border rounded-lg text-white"
        >
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="reviewing">Reviewing</option>
          <option value="ranked">Ranked</option>
          <option value="promoted">Promoted</option>
          <option value="archived">Archived</option>
        </select>
        <select
          value={filter.rank}
          onChange={(e) => setFilter({ ...filter, rank: e.target.value })}
          className="px-4 py-2 bg-dark-card border border-dark-border rounded-lg text-white"
        >
          <option value="">All Ranks</option>
          <option value="top_priority">Top Priority</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="rejected">Rejected</option>
        </select>
        <select
          value={filter.sortBy}
          onChange={(e) => setFilter({ ...filter, sortBy: e.target.value })}
          className="px-4 py-2 bg-dark-card border border-dark-border rounded-lg text-white"
        >
          <option value="created_at">Newest First</option>
          <option value="score">Highest Score</option>
        </select>
        <button
          onClick={loadStories}
          className="p-2 text-gray-400 hover:text-white"
        >
          <RefreshCw className={cn('w-5 h-5', loading && 'animate-spin')} />
        </button>
      </div>

      {/* Stories List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-6 h-6 text-maya-500 animate-spin" />
        </div>
      ) : stories.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          No stories found
        </div>
      ) : (
        <div className="space-y-3">
          {stories.map((story) => (
            <div
              key={story.id}
              className="bg-dark-card rounded-lg border border-dark-border p-4"
            >
              <div className="flex items-start gap-4">
                {/* Score Badge */}
                <div className="flex-shrink-0 w-16 text-center">
                  {story.score !== null ? (
                    <div
                      className={cn(
                        'text-2xl font-bold',
                        story.score >= 80
                          ? 'text-green-400'
                          : story.score >= 60
                          ? 'text-blue-400'
                          : story.score >= 40
                          ? 'text-yellow-400'
                          : 'text-gray-400'
                      )}
                    >
                      {story.score}
                    </div>
                  ) : (
                    <div className="text-gray-500">—</div>
                  )}
                  {story.rank && (
                    <span
                      className={cn(
                        'inline-block px-2 py-0.5 text-xs rounded-full mt-1',
                        rankColors[story.rank]
                      )}
                    >
                      {rankLabels[story.rank]}
                    </span>
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-white truncate">{story.title}</h4>
                  <div className="flex items-center gap-2 mt-1 text-sm text-gray-400">
                    <span>{story.source_name}</span>
                    <span>•</span>
                    <span>{story.source_type}</span>
                    {story.category && (
                      <>
                        <span>•</span>
                        <span className="text-maya-400">{story.category}</span>
                      </>
                    )}
                  </div>
                  {story.rank_reason && (
                    <p className="text-xs text-gray-500 mt-2">{story.rank_reason}</p>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  {story.status === 'pending' && (
                    <button
                      onClick={() => handleScore(story.id)}
                      className="flex items-center gap-1 px-3 py-1 bg-maya-600 text-white text-sm rounded-lg hover:bg-maya-700"
                    >
                      <Scale className="w-4 h-4" />
                      Score
                    </button>
                  )}
                  {story.rank && story.rank !== 'rejected' && story.status !== 'promoted' && (
                    <button
                      onClick={() => handlePromote(story.id)}
                      className="flex items-center gap-1 px-3 py-1 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700"
                    >
                      <ArrowUp className="w-4 h-4" />
                      Promote
                    </button>
                  )}
                  {story.status !== 'archived' && story.status !== 'promoted' && (
                    <button
                      onClick={() => handleArchive(story.id)}
                      className="p-2 text-gray-400 hover:text-white"
                    >
                      <Archive className="w-4 h-4" />
                    </button>
                  )}
                  {story.original_url && (
                    <a
                      href={story.original_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 text-gray-400 hover:text-white"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ===================
// Reviews Tab
// ===================

function ReviewsTab() {
  const [reviews, setReviews] = useState<EditorialReview[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  useEffect(() => {
    loadReviews()
  }, [])

  async function loadReviews() {
    try {
      const data = await listReviews()
      setReviews(data)
    } catch (error) {
      console.error('Failed to load reviews:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleRunReview() {
    setRunning(true)
    try {
      await runEditorialReview()
      await loadReviews()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to run review')
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 text-maya-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Editorial Reviews</h2>
        <button
          onClick={handleRunReview}
          disabled={running}
          className="flex items-center gap-2 px-4 py-2 bg-maya-600 text-white rounded-lg hover:bg-maya-700 transition-colors disabled:opacity-50"
        >
          {running ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          Run New Review
        </button>
      </div>

      {reviews.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          No editorial reviews yet. Run your first review to get started.
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <div
              key={review.id}
              className="bg-dark-card rounded-xl border border-dark-border p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">
                    Week {review.week_number}, {review.year}
                  </h3>
                  <p className="text-sm text-gray-400">
                    {review.total_stories_reviewed} stories reviewed
                  </p>
                </div>
                <span
                  className={cn(
                    'px-3 py-1 text-sm rounded-full',
                    review.status === 'completed'
                      ? 'bg-green-500/20 text-green-400'
                      : review.status === 'in_progress'
                      ? 'bg-yellow-500/20 text-yellow-400'
                      : 'bg-red-500/20 text-red-400'
                  )}
                >
                  {review.status}
                </span>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-5 gap-2 mb-4">
                <div className="text-center p-2 rounded-lg bg-green-500/10">
                  <p className="text-lg font-bold text-green-400">{review.top_priority_count}</p>
                  <p className="text-xs text-gray-400">Top Priority</p>
                </div>
                <div className="text-center p-2 rounded-lg bg-blue-500/10">
                  <p className="text-lg font-bold text-blue-400">{review.high_count}</p>
                  <p className="text-xs text-gray-400">High</p>
                </div>
                <div className="text-center p-2 rounded-lg bg-yellow-500/10">
                  <p className="text-lg font-bold text-yellow-400">{review.medium_count}</p>
                  <p className="text-xs text-gray-400">Medium</p>
                </div>
                <div className="text-center p-2 rounded-lg bg-gray-500/10">
                  <p className="text-lg font-bold text-gray-400">{review.low_count}</p>
                  <p className="text-xs text-gray-400">Low</p>
                </div>
                <div className="text-center p-2 rounded-lg bg-red-500/10">
                  <p className="text-lg font-bold text-red-400">{review.rejected_count}</p>
                  <p className="text-xs text-gray-400">Rejected</p>
                </div>
              </div>

              {/* Key Themes */}
              {review.key_themes && review.key_themes.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Key Themes</h4>
                  <div className="flex flex-wrap gap-2">
                    {review.key_themes.map((theme, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 bg-maya-500/20 text-maya-400 rounded-full text-sm"
                      >
                        {theme}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Executive Summary */}
              {review.executive_summary && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Executive Summary</h4>
                  <p className="text-gray-400 text-sm whitespace-pre-wrap">
                    {review.executive_summary}
                  </p>
                </div>
              )}

              {/* Editorial Notes */}
              {review.editorial_notes && (
                <div className="p-4 bg-dark-bg rounded-lg">
                  <h4 className="text-sm font-medium text-gray-300 mb-1">Editorial Notes</h4>
                  <p className="text-gray-400 text-sm">{review.editorial_notes}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
