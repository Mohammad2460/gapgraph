// Click a node -> definition, grounding quote, prerequisites.  [Pillar C — task C3]
import { STATUS_COLOR, STATUS_LABEL } from '../lib/status'
import type { Concept, ConceptMastery, Edge } from '../types'

interface Props {
  concept: Concept
  concepts: Concept[]
  edges: Edge[]
  mastery?: ConceptMastery
}

export function NodeDetail({ concept, concepts, edges, mastery }: Props) {
  const name = (id: string) => concepts.find((c) => c.id === id)?.name ?? id
  const prereqs = edges.filter((e) => e.target === concept.id)
  const status = mastery?.status ?? 'pending'

  return (
    <div className="space-y-2 text-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold">{concept.name}</h3>
        <span className="rounded px-2 py-0.5 text-xs text-white" style={{ background: STATUS_COLOR[status] }}>
          {STATUS_LABEL[status]}
          {mastery && ` · ${Math.round(mastery.p_known * 100)}%`}
        </span>
      </div>
      <p>{concept.definition}</p>
      {concept.source_excerpt && (
        <blockquote className="border-l-2 border-slate-300 pl-2 text-slate-600 italic">
          “{concept.source_excerpt}”
        </blockquote>
      )}
      {prereqs.length > 0 && (
        <div>
          <div className="font-medium">Needs first:</div>
          <ul className="list-disc pl-5">
            {prereqs.map((e) => (
              <li key={e.source} title={e.evidence}>
                {name(e.source)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
