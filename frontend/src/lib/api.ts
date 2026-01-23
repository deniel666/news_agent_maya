import axios from 'axios'

const API_BASE = '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface DashboardStats {
  total_briefings: number
  completed_briefings: number
  pending_approvals: number
  total_videos: number
  total_posts: number
}

export interface Briefing {
  id: string
  thread_id: string
  year: number
  week_number: number
  local_script: string | null
  business_script: string | null
  ai_script: string | null
  full_script: string | null
  status: string
  created_at: string
  script_approved_at: string | null
  video_approved_at: string | null
  published_at: string | null
}

export interface Video {
  id: string
  briefing_id: string
  heygen_video_id: string | null
  video_url: string | null
  duration_seconds: number | null
  status: string
  created_at: string
}

export interface PipelineStage {
  name: string
  label: string
  status: 'pending' | 'current' | 'completed'
}

export interface NewsSource {
  name: string
  type: string
  url: string | null
  status: string
}

// Dashboard
export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get('/dashboard/stats')
  return data
}

export async function getRecentActivity() {
  const { data } = await api.get('/dashboard/recent-activity')
  return data.activity
}

export async function getWeeklySummary() {
  const { data } = await api.get('/dashboard/weekly-summary')
  return data.weeks
}

export async function getPipelineStatus(threadId: string) {
  const { data } = await api.get(`/dashboard/pipeline-status/${threadId}`)
  return data
}

export async function getSourcesStatus(): Promise<NewsSource[]> {
  const { data } = await api.get('/dashboard/sources-status')
  return data.sources
}

// Briefings
export async function listBriefings(params?: {
  limit?: number
  offset?: number
  status?: string
}): Promise<Briefing[]> {
  const { data } = await api.get('/briefings/', { params })
  return data
}

export async function getBriefing(threadId: string) {
  const { data } = await api.get(`/briefings/${threadId}`)
  return data
}

export async function getBriefingScripts(threadId: string) {
  const { data } = await api.get(`/briefings/${threadId}/scripts`)
  return data
}

export async function getBriefingVideo(threadId: string) {
  const { data } = await api.get(`/briefings/${threadId}/video`)
  return data
}

export async function createBriefing(weekNumber?: number, year?: number) {
  const { data } = await api.post('/briefings/', null, {
    params: { week_number: weekNumber, year },
  })
  return data
}

export async function getCurrentBriefing(): Promise<Briefing | null> {
  const { data } = await api.get('/briefings/current')
  return data
}

// Approvals
export async function getPendingApprovals() {
  const { data } = await api.get('/approvals/pending')
  return data
}

export async function approveScript(
  threadId: string,
  approved: boolean,
  feedback?: string,
  editedScripts?: Record<string, string>
) {
  const { data } = await api.post('/approvals/script', {
    thread_id: threadId,
    approved,
    feedback,
    edited_scripts: editedScripts,
  })
  return data
}

export async function approveVideo(threadId: string, approved: boolean) {
  const { data } = await api.post('/approvals/video', {
    thread_id: threadId,
    approved,
  })
  return data
}

// Settings
export async function getSettingsStatus() {
  const { data } = await api.get('/settings/status')
  return data
}

export async function getAvatars() {
  const { data } = await api.get('/settings/avatars')
  return data
}

export async function getVoices() {
  const { data } = await api.get('/settings/voices')
  return data
}

export async function getSocialAccounts() {
  const { data } = await api.get('/settings/social-accounts')
  return data.accounts
}

export async function getNewsSources() {
  const { data } = await api.get('/settings/news-sources')
  return data
}

export async function getCurrentConfig() {
  const { data } = await api.get('/settings/current-config')
  return data
}

export async function testConnection(service: string) {
  const { data } = await api.post('/settings/test-connection', { service })
  return data
}

// ==================
// Sources Management
// ==================

export async function listSources(sourceType?: string, enabled?: boolean) {
  const { data } = await api.get('/sources/', {
    params: { source_type: sourceType, enabled },
  })
  return data
}

export async function createSource(source: {
  name: string
  source_type: string
  url: string
  category?: string
  enabled?: boolean
}) {
  const { data } = await api.post('/sources/', source)
  return data
}

export async function updateSource(
  id: string,
  update: {
    name?: string
    url?: string
    category?: string
    enabled?: boolean
  }
) {
  const { data } = await api.patch(`/sources/${id}`, update)
  return data
}

export async function deleteSource(id: string) {
  const { data } = await api.delete(`/sources/${id}`)
  return data
}

export async function toggleSource(id: string) {
  const { data } = await api.post(`/sources/${id}/toggle`)
  return data
}

export async function testSource(id: string) {
  const { data } = await api.post(`/sources/test/${id}`)
  return data
}

export async function importDefaultSources() {
  const { data } = await api.post('/sources/import/defaults')
  return data
}

// ==================
// Cron Schedules
// ==================

export async function listSchedules() {
  const { data } = await api.get('/cron/')
  return data
}

export async function createSchedule(schedule: {
  name: string
  cron_expression: string
  enabled?: boolean
}) {
  const { data } = await api.post('/cron/', schedule)
  return data
}

export async function updateSchedule(
  id: string,
  update: {
    name?: string
    cron_expression?: string
    enabled?: boolean
  }
) {
  const { data } = await api.patch(`/cron/${id}`, update)
  return data
}

export async function deleteSchedule(id: string) {
  const { data } = await api.delete(`/cron/${id}`)
  return data
}

export async function toggleSchedule(id: string) {
  const { data } = await api.post(`/cron/${id}/toggle`)
  return data
}

export async function runScheduleNow(id: string) {
  const { data } = await api.post(`/cron/${id}/run-now`)
  return data
}

export async function getCronPresets() {
  const { data } = await api.get('/cron/presets/common')
  return data
}

export async function validateCronExpression(expression: string) {
  const { data } = await api.post('/cron/validate', null, {
    params: { expression },
  })
  return data
}

// ==================
// On-Demand Generation
// ==================

export async function generateFromArticle(request: {
  article_url: string
  title?: string
  languages: string[]
  platforms: string[]
}) {
  const { data } = await api.post('/on-demand/generate', request)
  return data
}

export async function listOnDemandJobs(status?: string, limit?: number) {
  const { data } = await api.get('/on-demand/jobs', {
    params: { status, limit },
  })
  return data
}

export async function getOnDemandJob(jobId: string) {
  const { data } = await api.get(`/on-demand/jobs/${jobId}`)
  return data
}

export async function approveOnDemandScript(
  jobId: string,
  approved: boolean,
  feedback?: string,
  editedScripts?: Record<string, string>
) {
  const { data } = await api.post(`/on-demand/jobs/${jobId}/approve`, {
    approved,
    feedback,
    edited_scripts: editedScripts,
  })
  return data
}

export async function approveOnDemandVideo(jobId: string, approved: boolean) {
  const { data } = await api.post(`/on-demand/jobs/${jobId}/approve-video`, {
    approved,
  })
  return data
}

export async function regenerateOnDemandJob(
  jobId: string,
  regenerateScript?: boolean,
  regenerateVideo?: boolean
) {
  const { data } = await api.post(`/on-demand/jobs/${jobId}/regenerate`, {
    regenerate_script: regenerateScript,
    regenerate_video: regenerateVideo,
  })
  return data
}

export async function deleteOnDemandJob(jobId: string) {
  const { data } = await api.delete(`/on-demand/jobs/${jobId}`)
  return data
}

export default api
