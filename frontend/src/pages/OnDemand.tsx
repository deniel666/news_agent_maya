import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Link2,
  Play,
  Clock,
  CheckCircle,
  XCircle,
  ChevronRight,
  Trash2,
  Globe,
  Languages,
} from 'lucide-react'
import { cn, formatDateTime } from '../lib/utils'
import { LoadingSpinner } from '../components/LoadingSpinner'
import {
  generateFromArticle,
  listOnDemandJobs,
  getOnDemandJob,
  approveOnDemandScript,
  approveOnDemandVideo,
  deleteOnDemandJob,
} from '../lib/api'

const PLATFORMS = [
  { id: 'instagram', label: 'Instagram', icon: '📸' },
  { id: 'facebook', label: 'Facebook', icon: '📘' },
  { id: 'tiktok', label: 'TikTok', icon: '🎵' },
  { id: 'youtube', label: 'YouTube', icon: '▶️' },
]

const LANGUAGES = [
  { id: 'en', label: 'English', flag: '🇬🇧' },
  { id: 'ms', label: 'Bahasa Melayu', flag: '🇲🇾' },
]

export default function OnDemand() {
  const queryClient = useQueryClient()
  const [articleUrl, setArticleUrl] = useState('')
  const [selectedLanguages, setSelectedLanguages] = useState(['en'])
  const [selectedPlatforms, setSelectedPlatforms] = useState([
    'instagram',
    'facebook',
    'tiktok',
    'youtube',
  ])

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['ondemand-jobs'],
    queryFn: () => listOnDemandJobs(),
    refetchInterval: 5000,
  })

  const generateMutation = useMutation({
    mutationFn: generateFromArticle,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ondemand-jobs'] })
      setArticleUrl('')
    },
  })

  const handleGenerate = () => {
    if (!articleUrl) return
    generateMutation.mutate({
      article_url: articleUrl,
      languages: selectedLanguages,
      platforms: selectedPlatforms,
    })
  }

  const toggleLanguage = (lang: string) => {
    if (selectedLanguages.includes(lang)) {
      if (selectedLanguages.length > 1) {
        setSelectedLanguages(selectedLanguages.filter((l) => l !== lang))
      }
    } else {
      setSelectedLanguages([...selectedLanguages, lang])
    }
  }

  const togglePlatform = (platform: string) => {
    if (selectedPlatforms.includes(platform)) {
      if (selectedPlatforms.length > 1) {
        setSelectedPlatforms(selectedPlatforms.filter((p) => p !== platform))
      }
    } else {
      setSelectedPlatforms([...selectedPlatforms, platform])
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">On-Demand Generation</h1>
        <p className="text-gray-400 mt-1">
          Generate videos from any article URL in English or Malay
        </p>
      </div>

      {/* Generate Form */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">
          Generate from Article
        </h2>

        <div className="space-y-4">
          {/* URL Input */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Article URL
            </label>
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  type="url"
                  value={articleUrl}
                  onChange={(e) => setArticleUrl(e.target.value)}
                  placeholder="https://example.com/news-article"
                  className="input w-full pl-10"
                />
              </div>
              <button
                onClick={handleGenerate}
                disabled={!articleUrl || generateMutation.isPending}
                className="btn btn-primary flex items-center gap-2"
              >
                {generateMutation.isPending ? (
                  <>
                    <LoadingSpinner size="sm" className="text-white" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Generate
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Language Selection */}
          <div>
            <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
              <Languages className="w-4 h-4" />
              Languages
            </label>
            <div className="flex gap-2">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.id}
                  onClick={() => toggleLanguage(lang.id)}
                  className={cn(
                    'px-4 py-2 rounded-lg flex items-center gap-2 transition-colors',
                    selectedLanguages.includes(lang.id)
                      ? 'bg-maya-600 text-white'
                      : 'bg-dark-bg text-gray-400 hover:text-white'
                  )}
                >
                  <span>{lang.flag}</span>
                  {lang.label}
                </button>
              ))}
            </div>
          </div>

          {/* Platform Selection */}
          <div>
            <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
              <Globe className="w-4 h-4" />
              Platforms
            </label>
            <div className="flex flex-wrap gap-2">
              {PLATFORMS.map((platform) => (
                <button
                  key={platform.id}
                  onClick={() => togglePlatform(platform.id)}
                  className={cn(
                    'px-4 py-2 rounded-lg flex items-center gap-2 transition-colors',
                    selectedPlatforms.includes(platform.id)
                      ? 'bg-maya-600 text-white'
                      : 'bg-dark-bg text-gray-400 hover:text-white'
                  )}
                >
                  <span>{platform.icon}</span>
                  {platform.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {generateMutation.isSuccess && (
          <div className="mt-4 p-4 bg-green-900/20 border border-green-500/30 rounded-lg">
            <p className="text-green-400 flex items-center gap-2">
              <CheckCircle className="w-5 h-5" />
              Article submitted! Check Telegram for approval request.
            </p>
          </div>
        )}
      </div>

      {/* Jobs List */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Recent Jobs</h2>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        ) : !jobs?.length ? (
          <div className="text-center py-12">
            <Link2 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No jobs yet</p>
            <p className="text-gray-500 text-sm mt-1">
              Paste an article URL above to get started
            </p>
          </div>
        ) : (
          <div className="divide-y divide-dark-border">
            {jobs.map((job: any) => (
              <JobRow key={job.id} job={job} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function JobRow({ job }: { job: any }) {
  const queryClient = useQueryClient()
  const [expanded, setExpanded] = useState(false)

  const deleteMutation = useMutation({
    mutationFn: deleteOnDemandJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ondemand-jobs'] })
    },
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-400" />
      case 'failed':
      case 'rejected':
        return <XCircle className="w-5 h-5 text-red-400" />
      case 'awaiting_approval':
      case 'awaiting_video_approval':
        return <Clock className="w-5 h-5 text-yellow-400" />
      default:
        return <LoadingSpinner className="w-5 h-5" />
    }
  }

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: 'Pending',
      scraping: 'Scraping Article',
      generating_script: 'Generating Script',
      awaiting_approval: 'Awaiting Script Approval',
      generating_video: 'Generating Video',
      awaiting_video_approval: 'Awaiting Video Approval',
      publishing: 'Publishing',
      completed: 'Completed',
      failed: 'Failed',
      rejected: 'Rejected',
    }
    return labels[status] || status
  }

  return (
    <div className="p-4">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-4">
          {getStatusIcon(job.status)}
          <div>
            <h3 className="font-medium text-white">
              {job.title || 'Untitled Article'}
            </h3>
            <p className="text-sm text-gray-500 truncate max-w-md">
              {job.article_url}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <span
              className={cn(
                'text-sm',
                job.status === 'completed'
                  ? 'text-green-400'
                  : job.status === 'failed' || job.status === 'rejected'
                  ? 'text-red-400'
                  : 'text-gray-400'
              )}
            >
              {getStatusLabel(job.status)}
            </span>
            <p className="text-xs text-gray-500">
              {formatDateTime(job.created_at)}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {job.languages?.map((lang: string) => (
              <span
                key={lang}
                className="text-xs bg-dark-bg px-2 py-1 rounded"
              >
                {lang === 'en' ? '🇬🇧' : '🇲🇾'}
              </span>
            ))}
          </div>
          <ChevronRight
            className={cn(
              'w-5 h-5 text-gray-500 transition-transform',
              expanded && 'rotate-90'
            )}
          />
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pl-9 space-y-4">
          {/* Scripts Preview */}
          {(job.has_english || job.has_malay) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {job.has_english && (
                <div className="bg-dark-bg p-4 rounded-lg">
                  <h4 className="text-sm font-medium text-gray-300 mb-2">
                    🇬🇧 English Script
                  </h4>
                  <p className="text-xs text-gray-500">Script generated</p>
                </div>
              )}
              {job.has_malay && (
                <div className="bg-dark-bg p-4 rounded-lg">
                  <h4 className="text-sm font-medium text-gray-300 mb-2">
                    🇲🇾 Malay Script
                  </h4>
                  <p className="text-xs text-gray-500">Script generated</p>
                </div>
              )}
            </div>
          )}

          {/* Platforms */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Platforms:</span>
            {job.platforms?.map((platform: string) => (
              <span
                key={platform}
                className="text-xs bg-dark-bg px-2 py-1 rounded capitalize"
              >
                {platform}
              </span>
            ))}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Link
              to={`/on-demand/${job.id}`}
              className="btn btn-secondary text-sm"
            >
              View Details
            </Link>
            <button
              onClick={() => {
                if (confirm('Delete this job?')) {
                  deleteMutation.mutate(job.id)
                }
              }}
              className="btn btn-secondary text-sm text-red-400 hover:text-red-300"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
