// Click a node -> definition, grounding quote, prerequisites.  [Pillar C — task C3]
import { STATUS_COLOR, STATUS_LABEL } from '../lib/status'
import type { Concept, ConceptMastery, Edge } from '../types'

interface Props {
  concept: Concept
  concepts: Concept[]
  edges: Edge[]
  mastery?: ConceptMastery
  /** Jump to another concept (click in the prerequisite / dependent lists). */
  onSelect?: (id: string) => void
}

export function NodeDetail({ concept, concepts, edges, mastery, onSelect }: Props) {
  const name = (id: string) => concepts.find((c) => c.id === id)?.name ?? id
  const prereqs = edges.filter((e) => e.target === concept.id)
  const dependents = edges.filter((e) => e.source === concept.id)
  const status = mastery?.status ?? 'pending'

  const list = (title: string, items: Edge[], side: 'source' | 'target') =>
    items.length > 0 && (
      <div>
        <div className="mb-1 font-medium">{title}</div>
        <ul className="space-y-1">
          {items.map((e) => (
            <li key={`${e.source}->${e.target}`}>
              <button
                onClick={() => onSelect?.(e[side])}
                title={e.evidence}
                className="text-left text-blue-700 hover:underline"
              >
                {name(e[side])}
              </button>
              {e.evidence && <div className="text-xs text-slate-500">“{e.evidence}”</div>}
            </li>
          ))}
        </ul>
      </div>
    )

  return (
    <div className="space-y-3 text-sm">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-base font-semibold">{concept.name}</h3>
        <span
          className="shrink-0 rounded px-2 py-0.5 text-xs text-white"
          style={{ background: STATUS_COLOR[status] }}
        >
          {STATUS_LABEL[status]}
          {mastery && ` · ${Math.round(mastery.p_known * 100)}%`}
        </span>
      </div>
      <p>{concept.definition}</p>

      {concept.source_excerpt && (
        <figure className="rounded-lg border-l-4 border-amber-400 bg-amber-50 p-3">
          <figcaption className="mb-1 text-xs font-semibold tracking-wide text-amber-700 uppercase">
            From your document
          </figcaption>
          <blockquote className="text-slate-800 italic">“{concept.source_excerpt}”</blockquote>
        </figure>
      )}

      {list('Needs first', prereqs, 'source')}
      {list('Unlocks', dependents, 'target')}
    </div>
  )
}
