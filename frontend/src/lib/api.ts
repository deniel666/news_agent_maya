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

// ==================
// Content Library
// ==================

export interface Story {
  id: string
  title: string
  description: string | null
  source_url: string | null
  story_type: string
  status: string
  tags: string[]
  featured: boolean
  script_en: string | null
  script_ms: string | null
  thumbnail_url: string | null
  briefing_id: string | null
  ondemand_job_id: string | null
  created_at: string
  updated_at: string | null
  published_at: string | null
}

export interface VideoAsset {
  id: string
  story_id: string
  language: string
  video_url: string
  thumbnail_url: string | null
  duration_seconds: number | null
  file_size_bytes: number | null
  heygen_video_id: string | null
  resolution: string | null
  format: string | null
  created_at: string
}

export interface PublishRecord {
  id: string
  story_id: string
  video_id: string
  platform: string
  language: string
  post_url: string | null
  post_id: string | null
  caption: string | null
  status: string
  error: string | null
  scheduled_at: string | null
  published_at: string | null
  created_at: string
}

export interface ContentStats {
  total_stories: number
  draft_stories: number
  script_ready_stories: number
  video_ready_stories: number
  published_stories: number
  total_videos: number
  english_videos: number
  malay_videos: number
  total_published: number
  this_week: number
  this_month: number
}

export async function listStories(params?: {
  status?: string
  story_type?: string
  featured?: boolean
  tag?: string
  search?: string
  limit?: number
  offset?: number
}): Promise<Story[]> {
  const { data } = await api.get('/content/stories', { params })
  return data
}

export async function createStory(story: {
  title: string
  description?: string
  source_url?: string
  story_type?: string
  tags?: string[]
  script_en?: string
  script_ms?: string
}) {
  const { data } = await api.post('/content/stories', story)
  return data
}

export async function getStory(storyId: string): Promise<Story> {
  const { data } = await api.get(`/content/stories/${storyId}`)
  return data
}

export async function updateStory(
  storyId: string,
  update: {
    title?: string
    description?: string
    source_url?: string
    status?: string
    tags?: string[]
    featured?: boolean
    script_en?: string
    script_ms?: string
    thumbnail_url?: string
  }
) {
  const { data } = await api.patch(`/content/stories/${storyId}`, update)
  return data
}

export async function deleteStory(storyId: string) {
  const { data } = await api.delete(`/content/stories/${storyId}`)
  return data
}

export async function toggleFeatured(storyId: string) {
  const { data } = await api.post(`/content/stories/${storyId}/toggle-featured`)
  return data
}

export async function archiveStory(storyId: string) {
  const { data } = await api.post(`/content/stories/${storyId}/archive`)
  return data
}

export async function getContentStats(): Promise<ContentStats> {
  const { data } = await api.get('/content/stats')
  return data
}

export async function getAllTags(): Promise<string[]> {
  const { data } = await api.get('/content/tags')
  return data
}

export async function getStoryVideos(storyId: string): Promise<VideoAsset[]> {
  const { data } = await api.get(`/content/stories/${storyId}/videos`)
  return data
}

export async function deleteVideo(videoId: string) {
  const { data } = await api.delete(`/content/videos/${videoId}`)
  return data
}

export async function getStoryPublishRecords(storyId: string): Promise<PublishRecord[]> {
  const { data } = await api.get(`/content/stories/${storyId}/publish-records`)
  return data
}

export async function createPublishRecord(record: {
  story_id: string
  video_id: string
  platform: string
  language: string
  caption?: string
  scheduled_at?: string
}) {
  const { data } = await api.post('/content/publish-records', record)
  return data
}

export async function updatePublishRecord(
  recordId: string,
  update: {
    status?: string
    post_url?: string
    post_id?: string
    error?: string
    published_at?: string
  }
) {
  const { data } = await api.patch(`/content/publish-records/${recordId}`, update)
  return data
}

// ==================
// Editorial System
// ==================

export interface EditorialStats {
  total_raw_stories: number
  pending_review: number
  reviewed_this_week: number
  promoted_this_week: number
  top_priority_stories: number
  high_stories: number
  medium_stories: number
  low_stories: number
  rejected_stories: number
  average_score: number
  total_reviews: number
  latest_review_date: string | null
}

export interface BrandProfile {
  id: string
  name: string
  tagline: string | null
  mission: string
  vision: string
  values: string[]
  target_audience: string
  tone_of_voice: string
  content_pillars: string[]
  differentiators: string[]
  competitors: string[]
  ai_prompt_context: string | null
  created_at: string
  updated_at: string | null
}

export interface EditorialGuideline {
  id: string
  name: string
  category: string
  description: string
  criteria: string
  weight: number
  enabled: boolean
  created_at: string
  updated_at: string | null
}

export interface RawStory {
  id: string
  title: string
  content_markdown: string
  summary: string | null
  source_name: string
  source_type: string
  source_url: string | null
  original_url: string | null
  media_urls: string[]
  category: string | null
  author: string | null
  tags: string[]
  published_at: string | null
  status: string
  rank: string | null
  score: number | null
  rank_reason: string | null
  promoted_story_id: string | null
  editorial_review_id: string | null
  created_at: string
  reviewed_at: string | null
}

export interface EditorialReview {
  id: string
  week_number: number
  year: number
  review_period_start: string
  review_period_end: string
  status: string
  total_stories_reviewed: number
  top_priority_count: number
  high_count: number
  medium_count: number
  low_count: number
  rejected_count: number
  executive_summary: string | null
  key_themes: string[]
  recommendations: any[]
  editorial_notes: string | null
  created_at: string
  completed_at: string | null
}

// Brand Profile
export async function getBrandProfile(): Promise<BrandProfile | null> {
  const { data } = await api.get('/editorial/brand-profile')
  return data
}

export async function updateBrandProfile(profile: {
  name: string
  tagline?: string
  mission: string
  vision: string
  values: string[]
  target_audience: string
  tone_of_voice: string
  content_pillars: string[]
  differentiators?: string[]
  competitors?: string[]
  ai_prompt_context?: string
}) {
  const { data } = await api.post('/editorial/brand-profile', profile)
  return data
}

// Guidelines
export async function listGuidelines(
  category?: string,
  enabled?: boolean
): Promise<EditorialGuideline[]> {
  const { data } = await api.get('/editorial/guidelines', {
    params: { category, enabled },
  })
  return data
}

export async function createGuideline(guideline: {
  name: string
  category: string
  description: string
  criteria: string
  weight?: number
  enabled?: boolean
}) {
  const { data } = await api.post('/editorial/guidelines', guideline)
  return data
}

export async function updateGuideline(
  guidelineId: string,
  update: {
    name?: string
    description?: string
    criteria?: string
    weight?: number
    enabled?: boolean
  }
) {
  const { data } = await api.patch(`/editorial/guidelines/${guidelineId}`, update)
  return data
}

export async function deleteGuideline(guidelineId: string) {
  const { data } = await api.delete(`/editorial/guidelines/${guidelineId}`)
  return data
}

export async function toggleGuideline(guidelineId: string) {
  const { data } = await api.post(`/editorial/guidelines/${guidelineId}/toggle`)
  return data
}

export async function importDefaultGuidelines() {
  const { data } = await api.post('/editorial/guidelines/import/defaults')
  return data
}

export async function getGuidelineCategories() {
  const { data } = await api.get('/editorial/categories')
  return data
}

// Raw Stories
export async function listRawStories(params?: {
  status?: string
  rank?: string
  category?: string
  source_type?: string
  min_score?: number
  limit?: number
  offset?: number
  sort_by?: string
}): Promise<RawStory[]> {
  const { data } = await api.get('/editorial/raw-stories', { params })
  return data
}

export async function createRawStory(story: {
  title: string
  content_markdown: string
  summary?: string
  source_name: string
  source_type: string
  source_url?: string
  original_url?: string
  media_urls?: string[]
  category?: string
  author?: string
  tags?: string[]
  published_at?: string
}) {
  const { data } = await api.post('/editorial/raw-stories', story)
  return data
}

export async function getRawStory(storyId: string): Promise<RawStory> {
  const { data } = await api.get(`/editorial/raw-stories/${storyId}`)
  return data
}

export async function scoreRawStory(storyId: string) {
  const { data } = await api.post(`/editorial/raw-stories/${storyId}/score`)
  return data
}

export async function promoteRawStory(storyId: string, title?: string) {
  const { data } = await api.post(`/editorial/raw-stories/${storyId}/promote`, null, {
    params: { title },
  })
  return data
}

export async function archiveRawStory(storyId: string) {
  const { data } = await api.post(`/editorial/raw-stories/${storyId}/archive`)
  return data
}

export async function deleteRawStory(storyId: string) {
  const { data } = await api.delete(`/editorial/raw-stories/${storyId}`)
  return data
}

// Editorial Reviews
export async function listReviews(limit?: number): Promise<EditorialReview[]> {
  const { data } = await api.get('/editorial/reviews', { params: { limit } })
  return data
}

export async function getReview(reviewId: string): Promise<EditorialReview> {
  const { data } = await api.get(`/editorial/reviews/${reviewId}`)
  return data
}

export async function getReviewByWeek(year: number, weekNumber: number): Promise<EditorialReview> {
  const { data } = await api.get(`/editorial/reviews/week/${year}/${weekNumber}`)
  return data
}

export async function runEditorialReview(weekNumber?: number, year?: number) {
  const { data } = await api.post('/editorial/reviews/run', null, {
    params: { week_number: weekNumber, year },
  })
  return data
}

// Stats
export async function getEditorialStats(): Promise<EditorialStats> {
  const { data } = await api.get('/editorial/stats')
  return data
}

// Pipeline Operations
export async function aggregateNews(days?: number, autoScore?: boolean) {
  const { data } = await api.post('/editorial/pipeline/aggregate', null, {
    params: { days, auto_score: autoScore },
  })
  return data
}

export async function getTopStories(limit?: number) {
  const { data } = await api.get('/editorial/pipeline/top-stories', {
    params: { limit },
  })
  return data
}

export async function runFullEditorialCycle(days?: number) {
  const { data } = await api.post('/editorial/pipeline/full-cycle', null, {
    params: { days },
  })
  return data
}

export default api
