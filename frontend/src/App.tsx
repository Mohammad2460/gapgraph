// App shell + flow: upload -> live graph -> quiz -> results.  [Pillar C — task C6]
import { useMemo, useState } from 'react'
import { clusterColors } from './lib/clusters'
import { api, USE_MOCK } from './api/client'
import { GraphView } from './components/GraphView'
import { Legend } from './components/Legend'
import { NodeDetail } from './components/NodeDetail'
import { QuizPanel } from './components/QuizPanel'
import { ResultsPanel } from './components/ResultsPanel'
import { TeacherView } from './components/TeacherView'
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
  const [teacher, setTeacher] = useState(false)

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

  const reset = () => {
    stream.reset()
    stream.clear()
    setPhase('upload')
    setQuiz(null)
    setResult(null)
    setSelected(null)
    setActiveGap(0)
    setError(null)
  }

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
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 px-4 py-2">
        <div>
          <span className="text-lg font-bold">GapGraph</span>
          <span className="ml-2 text-sm text-slate-500">{stream.graph?.title ?? 'Live Knowledge Graph + Learning Gap Locator'}</span>
        </div>
        <div className="flex items-center gap-4">
          <Legend clusters={result || Object.keys(clusters).length === 0 ? undefined : clusters} />
          <button onClick={() => setTeacher((t) => !t)} className="rounded border border-slate-300 px-2 py-0.5 text-xs hover:bg-slate-100">
            {teacher ? 'Learner view' : 'Teacher view'}
          </button>
          {phase !== 'upload' && (
            <button onClick={reset} className="rounded border border-slate-300 px-2 py-0.5 text-xs hover:bg-slate-100">
              Start over
            </button>
          )}
          {USE_MOCK && <span className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800">MOCK</span>}
        </div>
      </header>

      {teacher ? (
        <TeacherView />
      ) : (
      <main className="flex min-h-0 flex-1 flex-col overflow-y-auto md:flex-row md:overflow-hidden">
        <section className="relative h-[50vh] min-w-0 shrink-0 bg-slate-50 md:h-auto md:flex-1">
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
            phase === 'building' && !stream.error ? (
              <div className="flex h-full animate-pulse items-center justify-center gap-6" aria-label="Loading graph">
                {[10, 16, 12, 18, 11].map((r, i) => (
                  <div key={i} className="rounded-full bg-slate-200" style={{ width: r * 3, height: r * 3 }} />
                ))}
              </div>
            ) : (
              <div className="flex h-full flex-col items-center justify-center gap-4 p-6 text-center">
                <h2 className="text-2xl font-bold">
                  Find the gap <span className="text-red-500">behind</span> the gap
                </h2>
                <p className="max-w-md text-slate-500">
                  Upload a chapter and watch its concepts and prerequisites appear as a live graph. Then take a short
                  quiz to see your real root-cause gaps — and which mistakes were just careless slips.
                </p>
                <ol className="flex flex-wrap justify-center gap-2 text-xs text-slate-600">
                  {['Upload', 'Graph', 'Quiz', 'Root gap'].map((t, i) => (
                    <li key={t} className="rounded-full border border-slate-300 bg-white px-3 py-1">
                      {i + 1}. {t}
                    </li>
                  ))}
                </ol>
              </div>
            )
          )}
          {phase === 'building' && !graphReady && !stream.error && (
            <div className="absolute inset-x-0 top-0">
              <div className="h-1 bg-slate-200">
                <div
                  className="h-1 bg-red-500 transition-all duration-300"
                  style={{ width: `${Math.round((stream.status?.progress ?? 0) * 100)}%` }}
                />
              </div>
              <div className="ml-3 mt-2 inline-block rounded bg-white/90 px-3 py-1 text-sm shadow">
                {stream.status
                  ? `${stream.status.message} · ${Math.round(stream.status.progress * 100)}%`
                  : 'Starting…'}
                {stream.slow && (
                  <span className="block text-xs text-slate-500">
                    Still working — the first response from Claude can take a few seconds.
                  </span>
                )}
              </div>
            </div>
          )}
        </section>

        <aside className="w-full space-y-4 border-t border-slate-200 p-4 md:w-96 md:overflow-y-auto md:border-t-0 md:border-l">
          {(error || stream.error) && (
            <div role="alert" className="space-y-2 rounded bg-red-50 p-2 text-sm text-red-700">
              <div>{error || stream.error}</div>
              {phase === 'building' && (
                <button onClick={() => {
                    setError(null)
                    stream.reset()
                    setPhase('upload')
                  }} className="font-medium underline">
                  Try again
                </button>
              )}
            </div>
          )}

          {(phase === 'upload' || phase === 'building') && <UploadPanel busy={busy || (phase === 'building' && !graphReady && !stream.error)} onSubmit={upload} />}

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
              <NodeDetail concept={selectedConcept} concepts={stream.concepts} edges={stream.edges} mastery={mastery?.[selectedConcept.id]} onSelect={setSelected} />
            </div>
          )}
        </aside>
      </main>
      )}
    </div>
  )
}
