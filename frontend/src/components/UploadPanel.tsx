// Upload a chapter (PDF / text / code) or paste text.  [Pillar C — task C1]
import { useState } from 'react'
import sampleChapter from '@fixtures/sample_chapter.txt?raw'

interface Props {
  busy: boolean
  onSubmit: (input: { file?: File; text?: string; title?: string }) => void
}

const ACCEPT = ['.pdf', '.txt', '.md', '.py', '.js', '.ts', '.java', '.c', '.cpp']
const MAX_MB = 20

const extOf = (name: string) => name.slice(name.lastIndexOf('.')).toLowerCase()

function badge(ext: string) {
  if (ext === '.pdf') return { label: 'PDF', cls: 'bg-red-100 text-red-700' }
  if (ext === '.txt' || ext === '.md') return { label: 'TEXT', cls: 'bg-blue-100 text-blue-700' }
  return { label: 'CODE', cls: 'bg-purple-100 text-purple-700' }
}

export function UploadPanel({ busy, onSubmit }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [text, setText] = useState('')
  const [title, setTitle] = useState('')
  const [dragging, setDragging] = useState(false)
  const [fileError, setFileError] = useState<string | null>(null)

  const pick = (f: File | null | undefined) => {
    if (!f) return
    if (!ACCEPT.includes(extOf(f.name))) {
      setFileError(`Unsupported file type. Use: ${ACCEPT.join(' ')}`)
      return
    }
    if (f.size === 0) {
      setFileError('That file is empty.')
      return
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setFileError(`File is larger than ${MAX_MB} MB.`)
      return
    }
    setFileError(null)
    setFile(f)
  }

  const b = file ? badge(extOf(file.name)) : null

  return (
    <div className="space-y-3">
      <label
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
          pick(e.dataTransfer.files[0])
        }}
        className={`block cursor-pointer rounded-lg border-2 border-dashed p-4 text-center text-sm transition ${
          dragging ? 'border-red-500 bg-red-50' : 'border-slate-300 hover:border-slate-500'
        }`}
      >
        <input
          type="file"
          accept={ACCEPT.join(',')}
          className="hidden"
          onChange={(e) => pick(e.target.files?.[0])}
        />
        {file && b ? (
          <span className="flex items-center justify-center gap-2">
            <span className={`rounded px-1.5 py-0.5 text-xs font-semibold ${b.cls}`}>{b.label}</span>
            <span className="truncate">{file.name}</span>
            <span className="text-xs text-slate-500">{(file.size / 1024).toFixed(0)} KB</span>
          </span>
        ) : (
          'Drop a chapter PDF, notes or code file — or click to choose'
        )}
      </label>
      {fileError && <p className="text-xs text-red-600">{fileError}</p>}

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="…or paste chapter text"
        className="h-28 w-full rounded-lg border border-slate-300 p-2 text-sm"
      />
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Title (optional)"
        className="w-full rounded-lg border border-slate-300 p-2 text-sm"
      />
      <button
        disabled={busy || (!file && !text.trim())}
        onClick={() =>
          onSubmit({ file: file ?? undefined, text: text.trim() || undefined, title: title.trim() || undefined })
        }
        className="w-full rounded-lg bg-slate-900 py-2 font-medium text-white disabled:opacity-40"
      >
        {busy ? 'Building graph…' : 'Build knowledge graph'}
      </button>

      <div className="flex justify-center gap-4 text-xs text-slate-500">
        <button
          disabled={busy}
          onClick={() => onSubmit({ title: 'Demo chapter', text: 'demo' })}
          className="underline disabled:opacity-40"
        >
          Use demo chapter
        </button>
        <button
          disabled={busy}
          onClick={() => onSubmit({ title: 'Sample: How Neural Networks Learn', text: sampleChapter })}
          className="underline disabled:opacity-40"
        >
          Use sample text
        </button>
      </div>
    </div>
  )
}
