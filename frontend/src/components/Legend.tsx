import { STATUS_COLOR, STATUS_LABEL } from '../lib/status'

const SHOWN = ['mastered', 'shaky', 'careless', 'gap', 'untested'] as const

export function Legend() {
  return (
    <div className="flex flex-wrap gap-3 text-xs">
      {SHOWN.map((s) => (
        <span key={s} className="flex items-center gap-1">
          <span className="inline-block h-3 w-3 rounded-full" style={{ background: STATUS_COLOR[s] }} />
          {STATUS_LABEL[s]}
        </span>
      ))}
    </div>
  )
}
