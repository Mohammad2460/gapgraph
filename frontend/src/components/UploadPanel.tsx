// Upload a chapter (PDF / text / code) or paste text.  [Pillar C — task C1]
import { useState } from 'react'

interface Props {
  busy: boolean
  onSubmit: (input: { file?: File; text?: string; title?: string }) => void
}

export function UploadPanel({ busy, onSubmit }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [text, setText] = useState('')

  return (
    <div className="space-y-3">
      <label className="block rounded-lg border-2 border-dashed border-slate-300 p-4 text-center text-sm hover:border-slate-500">
        <input
          type="file"
          accept=".pdf,.txt,.md,.py,.js,.ts,.java,.c,.cpp"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        {file ? file.name : 'Drop a chapter PDF, notes or code file — or click to choose'}
      </label>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="…or paste chapter text"
        className="h-28 w-full rounded-lg border border-slate-300 p-2 text-sm"
      />
      <button
        disabled={busy || (!file && !text.trim())}
        onClick={() => onSubmit({ file: file ?? undefined, text: text.trim() || undefined })}
        className="w-full rounded-lg bg-slate-900 py-2 font-medium text-white disabled:opacity-40"
      >
        {busy ? 'Building graph…' : 'Build knowledge graph'}
      </button>
      <button
        disabled={busy}
        onClick={() => onSubmit({ title: 'Demo chapter', text: 'demo' })}
        className="w-full text-xs text-slate-500 underline"
      >
        Use demo chapter
      </button>
    </div>
  )
}
