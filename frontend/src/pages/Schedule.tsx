import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  Plus,
  Trash2,
  Edit2,
  Play,
  Clock,
  ToggleLeft,
  ToggleRight,
  Calendar,
  AlertCircle,
} from 'lucide-react'
import { cn, formatDateTime } from '../lib/utils'
import {
  listSchedules,
  createSchedule,
  updateSchedule,
  deleteSchedule,
  toggleSchedule,
  runScheduleNow,
  getCronPresets,
  validateCronExpression,
} from '../lib/api'

interface Schedule {
  id: string
  name: string
  cron_expression: string
  enabled: boolean
  last_run: string | null
  next_run: string | null
  created_at: string
}

export default function Schedule() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null)

  const { data: schedules, isLoading } = useQuery({
    queryKey: ['schedules'],
    queryFn: listSchedules,
    refetchInterval: 30000, // Refresh every 30s to update next_run
  })

  const { data: presets } = useQuery({
    queryKey: ['cron-presets'],
    queryFn: getCronPresets,
  })

  const createMutation = useMutation({
    mutationFn: createSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      setShowForm(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      updateSchedule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      setEditingSchedule(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
    },
  })

  const toggleMutation = useMutation({
    mutationFn: toggleSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
    },
  })

  const runNowMutation = useMutation({
    mutationFn: runScheduleNow,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      alert(`Pipeline started! Thread ID: ${data.thread_id}`)
    },
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Schedule</h1>
          <p className="text-gray-400 mt-1">
            Configure automated weekly briefing schedules
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add Schedule
        </button>
      </div>

      {/* Info Card */}
      <div className="card border-maya-500/30 bg-maya-900/10">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-maya-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-white">How Scheduling Works</h3>
            <p className="text-sm text-gray-400 mt-1">
              Schedules use cron expressions to trigger weekly briefing pipelines automatically.
              When triggered, Maya will aggregate news, generate scripts, and send you
              a Telegram message for approval before creating videos.
            </p>
          </div>
        </div>
      </div>

      {/* Schedules List */}
      <div className="card">
        {isLoading ? (
          <div className="text-center py-8 text-gray-400">Loading...</div>
        ) : !schedules?.length ? (
          <div className="text-center py-12">
            <Calendar className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No schedules configured</p>
            <p className="text-gray-500 text-sm mt-1">
              Add a schedule to automate your weekly briefings
            </p>
          </div>
        ) : (
          <div className="divide-y divide-dark-border">
            {schedules.map((schedule: Schedule) => (
              <ScheduleRow
                key={schedule.id}
                schedule={schedule}
                onToggle={() => toggleMutation.mutate(schedule.id)}
                onEdit={() => setEditingSchedule(schedule)}
                onDelete={() => {
                  if (confirm('Delete this schedule?')) {
                    deleteMutation.mutate(schedule.id)
                  }
                }}
                onRunNow={() => {
                  if (confirm('Run this schedule now?')) {
                    runNowMutation.mutate(schedule.id)
                  }
                }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Presets Reference */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Common Schedules</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {presets?.presets?.map((preset: any) => (
            <div
              key={preset.expression}
              className="p-4 bg-dark-bg rounded-lg cursor-pointer hover:bg-dark-border transition-colors"
              onClick={() => {
                setShowForm(true)
                // Pre-fill form with preset
              }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-white">{preset.name}</p>
                  <p className="text-sm text-gray-400">{preset.description}</p>
                </div>
                <code className="text-xs bg-dark-card px-2 py-1 rounded text-maya-400">
                  {preset.expression}
                </code>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Add/Edit Modal */}
      {(showForm || editingSchedule) && (
        <ScheduleModal
          schedule={editingSchedule}
          presets={presets?.presets || []}
          onClose={() => {
            setShowForm(false)
            setEditingSchedule(null)
          }}
          onSubmit={(data) => {
            if (editingSchedule) {
              updateMutation.mutate({ id: editingSchedule.id, data })
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

function ScheduleRow({
  schedule,
  onToggle,
  onEdit,
  onDelete,
  onRunNow,
}: {
  schedule: Schedule
  onToggle: () => void
  onEdit: () => void
  onDelete: () => void
  onRunNow: () => void
}) {
  return (
    <div className="p-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div
          className={cn(
            'w-10 h-10 rounded-lg flex items-center justify-center',
            schedule.enabled ? 'bg-green-900/50' : 'bg-dark-bg'
          )}
        >
          <Clock
            className={cn(
              'w-5 h-5',
              schedule.enabled ? 'text-green-400' : 'text-gray-500'
            )}
          />
        </div>
        <div>
          <h3
            className={cn(
              'font-medium',
              schedule.enabled ? 'text-white' : 'text-gray-500'
            )}
          >
            {schedule.name}
          </h3>
          <div className="flex items-center gap-4 text-sm">
            <code className="text-maya-400 bg-dark-bg px-2 py-0.5 rounded">
              {schedule.cron_expression}
            </code>
            {schedule.next_run && schedule.enabled && (
              <span className="text-gray-400">
                Next: {formatDateTime(schedule.next_run)}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {schedule.last_run && (
          <span className="text-xs text-gray-500">
            Last run: {formatDateTime(schedule.last_run)}
          </span>
        )}
        <button
          onClick={onRunNow}
          className="p-2 hover:bg-dark-bg rounded-lg transition-colors"
          title="Run now"
        >
          <Play className="w-4 h-4 text-green-400" />
        </button>
        <button
          onClick={onToggle}
          className="p-2 hover:bg-dark-bg rounded-lg transition-colors"
          title={schedule.enabled ? 'Disable' : 'Enable'}
        >
          {schedule.enabled ? (
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

function ScheduleModal({
  schedule,
  presets,
  onClose,
  onSubmit,
  isLoading,
}: {
  schedule: Schedule | null
  presets: any[]
  onClose: () => void
  onSubmit: (data: any) => void
  isLoading: boolean
}) {
  const [formData, setFormData] = useState({
    name: schedule?.name || '',
    cron_expression: schedule?.cron_expression || '0 6 * * 0',
    enabled: schedule?.enabled ?? true,
  })
  const [validationResult, setValidationResult] = useState<any>(null)

  const handleValidate = async () => {
    try {
      const result = await validateCronExpression(formData.cron_expression)
      setValidationResult(result)
    } catch {
      setValidationResult({ valid: false, error: 'Validation failed' })
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-dark-card rounded-xl p-6 w-full max-w-lg">
        <h2 className="text-xl font-semibold text-white mb-4">
          {schedule ? 'Edit Schedule' : 'Add Schedule'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input w-full"
              placeholder="e.g., Sunday Weekly Briefing"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Cron Expression
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={formData.cron_expression}
                onChange={(e) => {
                  setFormData({ ...formData, cron_expression: e.target.value })
                  setValidationResult(null)
                }}
                className="input flex-1 font-mono"
                placeholder="0 6 * * 0"
                required
              />
              <button
                type="button"
                onClick={handleValidate}
                className="btn btn-secondary"
              >
                Validate
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Format: minute hour day month weekday (0=Sunday)
            </p>
            {validationResult && (
              <div
                className={cn(
                  'mt-2 p-2 rounded text-sm',
                  validationResult.valid
                    ? 'bg-green-900/30 text-green-400'
                    : 'bg-red-900/30 text-red-400'
                )}
              >
                {validationResult.valid
                  ? validationResult.description
                  : validationResult.error}
              </div>
            )}
          </div>

          {/* Preset Buttons */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Quick Presets
            </label>
            <div className="flex flex-wrap gap-2">
              {presets.slice(0, 4).map((preset: any) => (
                <button
                  key={preset.expression}
                  type="button"
                  onClick={() =>
                    setFormData({
                      ...formData,
                      cron_expression: preset.expression,
                      name: formData.name || preset.name,
                    })
                  }
                  className="text-xs px-3 py-1.5 bg-dark-bg hover:bg-dark-border rounded-lg text-gray-300 transition-colors"
                >
                  {preset.name}
                </button>
              ))}
            </div>
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
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary"
            >
              {isLoading ? 'Saving...' : schedule ? 'Update' : 'Create Schedule'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
