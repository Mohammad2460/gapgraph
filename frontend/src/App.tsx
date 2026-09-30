// App shell + flow: upload -> live graph -> quiz -> results.  [Pillar C — task C6]
import { useMemo, useState } from 'react'
import { clusterColors } from './lib/clusters'
import { api, USE_MOCK } from './api/client'
import { GraphView } from './components/GraphView'
import { Legend } from './components/Legend'
import { NodeDetail } from './components/NodeDetail'
import { QuizPanel } from './components/QuizPanel'
import { ResultsPanel } from './components/ResultsPanel'
import { UploadPanel } from './components/UploadPanel'
import { useGraphStream } from './hooks/useGraphStream'
import type { Answer, AssessmentResult, Quiz } from './types'

type Phase = 'upload' | 'building' | 'graph' | 'quiz' | 'results'

export default function App() {
  const stream = useGraphStream()
  const [phase, setPhase] = useState<Phase>('upload')
  const [busy, setBusy] = useState(false)
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [result, setResult] = useState<AssessmentResult | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [activeGap, setActiveGap] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const mastery = useMemo(
    () => (result ? Object.fromEntries(result.mastery.map((m) => [m.concept_id, m])) : undefined),
    [result],
  )
  const selectedConcept = stream.concepts.find((c) => c.id === selected)
  const graphReady = stream.graph !== null
  const clusters = useMemo(() => clusterColors(stream.concepts.map((c) => c.cluster)), [stream.concepts])

  const run = async (fn: () => Promise<void>) => {
    setBusy(true)
    setError(null)
    try {
      await fn()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  const upload = (input: { file?: File; text?: string; title?: string }) =>
    run(async () => {
      const doc = await api.createDocument(input)
      setResult(null)
      setPhase('building')
      stream.start(doc.doc_id)
    })

  const startQuiz = () =>
    run(async () => {
      setQuiz(await api.createQuiz(stream.graph!.id))
      setPhase('quiz')
    })

  const submit = (answers: Answer[]) =>
    run(async () => {
      const r = await api.assess(quiz!.quiz_id, answers)
      setResult(r)
      setActiveGap(0)
      setSelected(r.root_gaps[0]?.concept_id ?? null)
      setPhase('results')
    })

  return (
    <div className="flex h-screen flex-col bg-white text-slate-900">
      <header className="flex items-center justify-between border-b border-slate-200 px-4 py-2">
        <div>
          <span className="text-lg font-bold">GapGraph</span>
          <span className="ml-2 text-sm text-slate-500">{stream.graph?.title ?? 'Live Knowledge Graph + Learning Gap Locator'}</span>
        </div>
        <div className="flex items-center gap-4">
          <Legend clusters={result || Object.keys(clusters).length === 0 ? undefined : clusters} />
          {USE_MOCK && <span className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800">MOCK</span>}
        </div>
      </header>

      <main className="flex min-h-0 flex-1">
        <section className="relative min-w-0 flex-1 bg-slate-50">
          {stream.concepts.length > 0 ? (
            <GraphView
              concepts={stream.concepts}
              edges={stream.edges}
              mastery={mastery}
              highlightPath={result?.root_gaps[activeGap]?.path}
              selectedId={selected}
              fitSignal={graphReady ? 1 : 0}
              onSelect={setSelected}
            />
          ) : (
            <div className="flex h-full items-center justify-center text-slate-400">
              Upload a chapter to build its knowledge graph
            </div>
          )}
          {phase === 'building' && stream.status && !graphReady && (
            <div className="absolute inset-x-0 top-0">
              <div className="h-1 bg-slate-200">
                <div
                  className="h-1 bg-red-500 transition-all duration-300"
                  style={{ width: `${Math.round(stream.status.progress * 100)}%` }}
                />
              </div>
              <div className="ml-3 mt-2 inline-block rounded bg-white/90 px-3 py-1 text-sm shadow">
                {stream.status.message} · {Math.round(stream.status.progress * 100)}%
              </div>
            </div>
          )}
        </section>

        <aside className="w-96 space-y-4 overflow-y-auto border-l border-slate-200 p-4">
          {(error || stream.error) && (
            <div className="rounded bg-red-50 p-2 text-sm text-red-700">{error || stream.error}</div>
          )}

          {(phase === 'upload' || phase === 'building') && <UploadPanel busy={busy || (phase === 'building' && !graphReady)} onSubmit={upload} />}

          {graphReady && phase !== 'quiz' && phase !== 'results' && (
            <button onClick={startQuiz} disabled={busy} className="w-full rounded-lg bg-red-600 py-2 font-medium text-white disabled:opacity-40">
              Find my learning gaps ({stream.concepts.length} concepts)
            </button>
          )}

          {phase === 'quiz' && quiz && <QuizPanel quiz={quiz} busy={busy} onSubmit={submit} />}

          {phase === 'results' && result && (
            <ResultsPanel
              result={result}
              concepts={stream.concepts}
              activeGap={activeGap}
              onSelectGap={(i) => {
                setActiveGap(i)
                setSelected(result.root_gaps[i].concept_id)
              }}
              onSelectConcept={setSelected}
            />
          )}

          {selectedConcept && (
            <div className="rounded-lg border border-slate-200 p-3">
              <NodeDetail concept={selectedConcept} concepts={stream.concepts} edges={stream.edges} mastery={mastery?.[selectedConcept.id]} />
            </div>
          )}
        </aside>
      </main>
    </div>
  )
}
