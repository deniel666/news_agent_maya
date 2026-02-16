import { useState, useEffect, useId } from 'react'
import { Save, RotateCcw, Maximize2, Minimize2 } from 'lucide-react'
import { cn } from '../lib/utils'

interface ScriptEditorProps {
  title: string
  script: string | null
  onSave: (script: string) => void
  readOnly?: boolean
}

export default function ScriptEditor({
  title,
  script,
  onSave,
  readOnly = false,
}: ScriptEditorProps) {
  const [content, setContent] = useState(script || '')
  const [isExpanded, setIsExpanded] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const titleId = useId()

  useEffect(() => {
    setContent(script || '')
    setHasChanges(false)
  }, [script])

  const handleChange = (value: string) => {
    setContent(value)
    setHasChanges(value !== script)
  }

  const handleSave = () => {
    onSave(content)
    setHasChanges(false)
  }

  const handleReset = () => {
    setContent(script || '')
    setHasChanges(false)
  }

  // Word count
  const wordCount = content.trim().split(/\s+/).filter(Boolean).length
  const estimatedSeconds = Math.round(wordCount / 2.5) // ~150 words per minute

  return (
    <div
      className={cn(
        'card transition-all duration-300',
        isExpanded && 'fixed inset-4 z-50 overflow-auto'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 id={titleId} className="font-semibold text-white">
          {title}
        </h3>
        <div className="flex items-center gap-2">
          {!readOnly && hasChanges && (
            <>
              <button
                onClick={handleReset}
                className="p-2 hover:bg-dark-bg rounded-lg transition-colors"
                title="Reset changes"
                aria-label="Reset changes"
              >
                <RotateCcw className="w-4 h-4 text-gray-400" />
              </button>
              <button
                onClick={handleSave}
                className="btn btn-primary text-sm flex items-center gap-1"
              >
                <Save className="w-3 h-3" />
                Save
              </button>
            </>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 hover:bg-dark-bg rounded-lg transition-colors"
            title={isExpanded ? 'Minimize' : 'Expand'}
            aria-label={isExpanded ? 'Minimize editor' : 'Expand editor'}
            aria-pressed={isExpanded}
          >
            {isExpanded ? (
              <Minimize2 className="w-4 h-4 text-gray-400" />
            ) : (
              <Maximize2 className="w-4 h-4 text-gray-400" />
            )}
          </button>
        </div>
      </div>

      {/* Editor */}
      {readOnly ? (
        <pre
          aria-labelledby={titleId}
          className="whitespace-pre-wrap text-gray-300 text-sm font-sans bg-dark-bg p-4 rounded-lg min-h-[200px]"
        >
          {content || 'No script available'}
        </pre>
      ) : (
        <textarea
          aria-labelledby={titleId}
          value={content}
          onChange={(e) => handleChange(e.target.value)}
          className={cn(
            'w-full bg-dark-bg text-gray-300 text-sm font-sans p-4 rounded-lg',
            'border border-dark-border focus:border-maya-500 focus:ring-1 focus:ring-maya-500',
            'resize-none transition-colors',
            isExpanded ? 'min-h-[calc(100vh-200px)]' : 'min-h-[200px]'
          )}
          placeholder="Enter script content..."
        />
      )}

      {/* Footer stats */}
      <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
        <div className="flex items-center gap-4">
          <span>{wordCount} words</span>
          <span>~{estimatedSeconds}s</span>
        </div>
        {hasChanges && (
          <span className="text-yellow-400">Unsaved changes</span>
        )}
      </div>
    </div>
  )
}

interface ScriptEditorGroupProps {
  scripts: {
    local: string | null
    business: string | null
    ai: string | null
  }
  onSave: (scripts: { local?: string; business?: string; ai?: string }) => void
  readOnly?: boolean
}

export function ScriptEditorGroup({
  scripts,
  onSave,
  readOnly = false,
}: ScriptEditorGroupProps) {
  const [editedScripts, setEditedScripts] = useState<{
    local?: string
    business?: string
    ai?: string
  }>({})

  const handleSave = (key: 'local' | 'business' | 'ai', value: string) => {
    const updated = { ...editedScripts, [key]: value }
    setEditedScripts(updated)
    onSave(updated)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <ScriptEditor
        title="Local & International News"
        script={scripts.local}
        onSave={(value) => handleSave('local', value)}
        readOnly={readOnly}
      />
      <ScriptEditor
        title="Business News"
        script={scripts.business}
        onSave={(value) => handleSave('business', value)}
        readOnly={readOnly}
      />
      <ScriptEditor
        title="AI & Tech News"
        script={scripts.ai}
        onSave={(value) => handleSave('ai', value)}
        readOnly={readOnly}
      />
    </div>
  )
}
