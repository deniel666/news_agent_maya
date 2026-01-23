import { useQuery, useMutation } from '@tanstack/react-query'
import {
  getSettingsStatus,
  getNewsSources,
  getCurrentConfig,
  testConnection,
} from '../lib/api'
import {
  CheckCircle,
  XCircle,
  RefreshCw,
  Database,
  Video,
  Share2,
  MessageSquare,
  Bot,
  Rss,
} from 'lucide-react'
import { useState } from 'react'

export default function Settings() {
  const { data: status } = useQuery({
    queryKey: ['settings-status'],
    queryFn: getSettingsStatus,
  })

  const { data: sources } = useQuery({
    queryKey: ['news-sources'],
    queryFn: getNewsSources,
  })

  const { data: config } = useQuery({
    queryKey: ['current-config'],
    queryFn: getCurrentConfig,
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="text-gray-400 mt-1">
          Configure Maya AI News Anchor integrations
        </p>
      </div>

      {/* Connection Status */}
      <div className="card">
        <h2 className="text-xl font-semibold text-white mb-4">Integration Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <ConnectionCard
            name="OpenAI"
            icon={Bot}
            configured={status?.openai_configured}
            service="openai"
          />
          <ConnectionCard
            name="HeyGen"
            icon={Video}
            configured={status?.heygen_configured}
            service="heygen"
          />
          <ConnectionCard
            name="Blotato"
            icon={Share2}
            configured={status?.blotato_configured}
            service="blotato"
          />
          <ConnectionCard
            name="Supabase"
            icon={Database}
            configured={status?.supabase_configured}
            service="supabase"
          />
          <ConnectionCard
            name="Telegram"
            icon={MessageSquare}
            configured={status?.telegram_configured}
            service="telegram"
          />
          <ConnectionCard
            name="Slack"
            icon={MessageSquare}
            configured={status?.slack_configured}
            service="slack"
          />
        </div>
      </div>

      {/* Current Configuration */}
      <div className="card">
        <h2 className="text-xl font-semibold text-white mb-4">Current Configuration</h2>
        <div className="space-y-4">
          <ConfigRow label="Avatar ID" value={config?.avatar_id} />
          <ConfigRow label="Voice ID" value={config?.voice_id} />
          <ConfigRow label="OpenAI Model" value={config?.openai_model} />
          <ConfigRow label="LangChain Project" value={config?.langchain_project} />
          <ConfigRow label="Frontend URL" value={config?.frontend_url} />
          <ConfigRow label="Backend URL" value={config?.backend_url} />
        </div>
      </div>

      {/* News Sources */}
      <div className="card">
        <h2 className="text-xl font-semibold text-white mb-4">News Sources</h2>

        {/* RSS Feeds */}
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-300 mb-3 flex items-center gap-2">
            <Rss className="w-5 h-5" />
            RSS Feeds
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {sources?.rss_feeds?.map((feed: any) => (
              <div
                key={feed.name}
                className="flex items-center justify-between p-3 bg-dark-bg rounded-lg"
              >
                <span className="text-gray-300">{feed.name}</span>
                <span className="text-xs text-gray-500 truncate max-w-[200px]">
                  {feed.url}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Twitter/Nitter */}
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-300 mb-3">Twitter (via Nitter)</h3>
          <div className="flex flex-wrap gap-2">
            {sources?.twitter_accounts?.map((account: string) => (
              <span
                key={account}
                className="px-3 py-1 bg-dark-bg rounded-full text-sm text-gray-300"
              >
                @{account}
              </span>
            ))}
          </div>
        </div>

        {/* Telegram */}
        <div>
          <h3 className="text-lg font-medium text-gray-300 mb-3 flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Telegram Channels
          </h3>
          <div className="flex flex-wrap gap-2">
            {sources?.telegram_channels?.map((channel: string) => (
              <span
                key={channel}
                className="px-3 py-1 bg-dark-bg rounded-full text-sm text-gray-300"
              >
                {channel}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Environment Setup */}
      <div className="card">
        <h2 className="text-xl font-semibold text-white mb-4">Environment Setup</h2>
        <p className="text-gray-400 mb-4">
          Configure the following environment variables in your .env file:
        </p>
        <pre className="bg-dark-bg p-4 rounded-lg text-sm text-gray-300 overflow-x-auto">
{`# Required
OPENAI_API_KEY=sk-...
HEYGEN_API_KEY=...
MAYA_AVATAR_ID=...
MAYA_VOICE_ID=...
SUPABASE_URL=https://...
SUPABASE_KEY=...

# Optional
BLOTATO_API_KEY=...
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
SLACK_WEBHOOK_URL=...`}
        </pre>
      </div>
    </div>
  )
}

function ConnectionCard({
  name,
  icon: Icon,
  configured,
  service,
}: {
  name: string
  icon: any
  configured?: boolean
  service: string
}) {
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ status: string; message: string } | null>(null)

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const result = await testConnection(service)
      setTestResult(result)
    } catch (error) {
      setTestResult({ status: 'error', message: 'Connection test failed' })
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="p-4 bg-dark-bg rounded-lg">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              configured ? 'bg-green-900/50' : 'bg-red-900/50'
            }`}
          >
            <Icon
              className={`w-5 h-5 ${
                configured ? 'text-green-400' : 'text-red-400'
              }`}
            />
          </div>
          <div>
            <p className="font-medium text-white">{name}</p>
            <p className="text-xs text-gray-500">
              {configured ? 'Configured' : 'Not configured'}
            </p>
          </div>
        </div>
        {configured ? (
          <CheckCircle className="w-5 h-5 text-green-400" />
        ) : (
          <XCircle className="w-5 h-5 text-red-400" />
        )}
      </div>

      {configured && (
        <button
          onClick={handleTest}
          disabled={testing}
          className="w-full btn btn-secondary text-sm flex items-center justify-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${testing ? 'animate-spin' : ''}`} />
          {testing ? 'Testing...' : 'Test Connection'}
        </button>
      )}

      {testResult && (
        <div
          className={`mt-2 p-2 rounded text-xs ${
            testResult.status === 'success'
              ? 'bg-green-900/30 text-green-400'
              : 'bg-red-900/30 text-red-400'
          }`}
        >
          {testResult.message}
        </div>
      )}
    </div>
  )
}

function ConfigRow({ label, value }: { label: string; value?: string }) {
  return (
    <div className="flex items-center justify-between p-3 bg-dark-bg rounded-lg">
      <span className="text-gray-400">{label}</span>
      <span className="text-gray-300 font-mono text-sm">
        {value || 'Not set'}
      </span>
    </div>
  )
}
