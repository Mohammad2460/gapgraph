import { STATUS_COLOR, STATUS_LABEL } from '../lib/status'

const SHOWN = ['mastered', 'shaky', 'careless', 'gap', 'untested'] as const

interface Props {
  /** Before the quiz, show cluster colours instead of mastery colours. */
  clusters?: Record<string, string>
}

export function Legend({ clusters }: Props) {
  const items = clusters
    ? Object.entries(clusters).map(([name, color]) => ({ key: name, label: name.replace(/_/g, ' '), color }))
    : SHOWN.map((s) => ({ key: s, label: STATUS_LABEL[s], color: STATUS_COLOR[s] }))

  return (
    <div className="flex flex-wrap gap-3 text-xs">
      {items.map((it) => (
        <span key={it.key} className="flex items-center gap-1">
          <span className="inline-block h-3 w-3 rounded-full" style={{ background: it.color }} />
          {it.label}
        </span>
      ))}
    </div>
  )
}
