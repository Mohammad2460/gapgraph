// Teacher view: heatmap of how many students are weak on each concept.  [Pillar C — task C8]
import { useMemo, useState } from 'react'
import graphJson from '@fixtures/sample_graph.json'
import { LEARNER_COUNT, cohortStats } from '../lib/cohort'
import type { Graph } from '../types'
import { GraphView } from './GraphView'

const graph = graphJson as Graph

export function TeacherView() {
  const stats = useMemo(() => cohortStats(), [])
  const heat = useMemo(
    () => Object.fromEntries(stats.filter((s) => s.fraction !== null).map((s) => [s.concept_id, s.fraction!])),
    [stats],
  )
  const [selected, setSelected] = useState<string | null>(null)
  const name = (id: string) => graph.concepts.find((c) => c.id === id)?.name ?? id
  const ranked = [...stats].sort((a, b) => (b.fraction ?? 0) - (a.fraction ?? 0))

  return (
    <main className="flex min-h-0 flex-1 flex-col overflow-y-auto md:flex-row md:overflow-hidden">
      <section className="relative h-[50vh] min-w-0 shrink-0 bg-slate-50 md:h-auto md:flex-1">
        <GraphView
          concepts={graph.concepts}
          edges={graph.edges}
          heat={heat}
          selectedId={selected}
          fitSignal={1}
          onSelect={setSelected}
        />
        <div className="absolute bottom-3 left-3 flex items-center gap-2 rounded bg-white/90 px-3 py-1 text-xs shadow">
          <span>0% weak</span>
          <span className="h-2 w-24 rounded" style={{ background: 'linear-gradient(to right, #22c55e, #eab308, #ef4444)' }} />
          <span>100% weak</span>
        </div>
      </section>

      <aside className="w-full space-y-3 border-t border-slate-200 p-4 text-sm md:w-96 md:overflow-y-auto md:border-t-0 md:border-l">
        <h2 className="text-base font-semibold">Class overview</h2>
        <p className="text-slate-500">
          Simulated cohort of {LEARNER_COUNT} learners (demo data). Click a concept to see who is struggling.
        </p>
        <ol className="space-y-1">
          {ranked.map((s) => (
            <li key={s.concept_id}>
              <button
                onClick={() => setSelected(s.concept_id)}
                className={`w-full rounded-lg border p-2 text-left ${
                  selected === s.concept_id ? 'border-slate-900 bg-slate-100' : 'border-slate-200'
                }`}
              >
                <div className="flex justify-between">
                  <span className="font-medium">{name(s.concept_id)}</span>
                  <span>
                    {s.weak}/{s.total} weak
                  </span>
                </div>
                <div className="mt-1 h-1.5 rounded bg-slate-200">
                  <div
                    className="h-1.5 rounded bg-red-500"
                    style={{ width: `${Math.round((s.fraction ?? 0) * 100)}%` }}
                  />
                </div>
              </button>
            </li>
          ))}
        </ol>
      </aside>
    </main>
  )
}
