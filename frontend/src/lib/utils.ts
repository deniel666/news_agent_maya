import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    aggregating: 'badge-info',
    categorizing: 'badge-info',
    synthesizing: 'badge-info',
    awaiting_script_approval: 'badge-warning',
    generating_video: 'badge-info',
    awaiting_video_approval: 'badge-warning',
    publishing: 'badge-info',
    completed: 'badge-success',
    failed: 'badge-error',
  }
  return colors[status] || 'badge-info'
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    aggregating: 'Aggregating',
    categorizing: 'Categorizing',
    synthesizing: 'Synthesizing',
    awaiting_script_approval: 'Awaiting Script Approval',
    generating_video: 'Generating Video',
    awaiting_video_approval: 'Awaiting Video Approval',
    publishing: 'Publishing',
    completed: 'Completed',
    failed: 'Failed',
  }
  return labels[status] || status
}
