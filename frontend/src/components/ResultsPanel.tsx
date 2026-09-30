// Score, root gaps, careless slips, next topics.  [Pillar C — task C5]
import type { AssessmentResult, Concept } from '../types'

interface Props {
  result: AssessmentResult
  concepts: Concept[]
  activeGap: number
  onSelectGap: (i: number) => void
  onSelectConcept: (id: string) => void
}

export function ResultsPanel({ result, concepts, activeGap, onSelectGap, onSelectConcept }: Props) {
  const name = (id: string) => concepts.find((c) => c.id === id)?.name ?? id

  return (
    <div className="space-y-4 text-sm">
      <div className="text-2xl font-bold">
        {result.score.correct}/{result.score.total}
        <span className="ml-2 text-sm font-normal text-slate-500">correct</span>
      </div>

      <section>
        <h3 className="mb-1 font-semibold">Root-cause gaps</h3>
        {result.root_gaps.length === 0 && <p className="text-slate-500">No real gaps found.</p>}
        {result.root_gaps.map((g, i) => (
          <button
            key={`${g.concept_id}-${g.failed_concept_id}`}
            onClick={() => onSelectGap(i)}
            className={`mb-2 block w-full rounded-lg border p-2 text-left ${
              i === activeGap ? 'border-red-500 bg-red-50' : 'border-slate-200'
            }`}
          >
            <div className="font-medium">{g.path.map(name).join(' → ')}</div>
            <div className="text-slate-600">{g.explanation}</div>
          </button>
        ))}
      </section>

      {result.careless_slips.length > 0 && (
        <section>
          <h3 className="mb-1 font-semibold">Careless slips (not real gaps)</h3>
          <p className="text-slate-600">{result.careless_slips.map(name).join(', ')}</p>
        </section>
      )}

      <section>
        <h3 className="mb-1 font-semibold">Study next</h3>
        <ol className="space-y-1">
          {result.next_topics.map((t) => (
            <li key={t.concept_id}>
              <button
                onClick={() => onSelectConcept(t.concept_id)}
                className="block w-full rounded-lg border border-slate-200 p-2 text-left hover:bg-slate-50"
              >
                <span className="font-medium">
                  {t.order}. {name(t.concept_id)}
                </span>
                <span className="block text-slate-600">{t.reason}</span>
              </button>
            </li>
          ))}
        </ol>
      </section>
    </div>
  )
}
