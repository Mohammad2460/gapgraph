// 5-10 question diagnostic quiz with confidence + timing capture.  [Pillar C — task C4]
import { useEffect, useRef, useState } from 'react'
import type { Answer, Quiz } from '../types'

interface Props {
  quiz: Quiz
  busy: boolean
  onSubmit: (answers: Answer[]) => void
}

const CONFIDENCE = [
  { label: 'Guessing', value: 0.2 },
  { label: 'Unsure', value: 0.5 },
  { label: 'Sure', value: 0.9 },
] as const

export function QuizPanel({ quiz, busy, onSubmit }: Props) {
  const [idx, setIdx] = useState(0)
  const [choice, setChoice] = useState<number | null>(null)
  const [confidence, setConfidence] = useState<number>(0.5)
  const [answers, setAnswers] = useState<Answer[]>([])
  const shownAt = useRef(0) // set when each question is shown
  const q = quiz.questions[idx]
  const last = idx + 1 >= quiz.questions.length

  useEffect(() => {
    shownAt.current = performance.now()
  }, [idx])

  const next = () => {
    if (choice === null || busy) return
    const all = [
      ...answers,
      { question_id: q.id, choice_index: choice, confidence, time_ms: Math.round(performance.now() - shownAt.current) },
    ]
    setAnswers(all)
    setChoice(null)
    setConfidence(0.5)
    if (!last) setIdx(idx + 1)
    else onSubmit(all)
  }

  // Keyboard: 1-4 pick an option, Enter continues. Handler is re-created each render
  // so it always sees the current choice.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLElement && /^(INPUT|TEXTAREA)$/.test(e.target.tagName)) return
      const n = Number(e.key)
      if (n >= 1 && n <= q.options.length) setChoice(n - 1)
      else if (e.key === 'Enter') next()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  return (
    <div className="space-y-3 text-sm">
      <div>
        <div className="mb-1 flex justify-between text-xs text-slate-500">
          <span>
            Question {idx + 1} / {quiz.questions.length}
          </span>
          <span>{q.difficulty}</span>
        </div>
        <div className="h-1.5 rounded bg-slate-200">
          <div
            className="h-1.5 rounded bg-slate-900 transition-all"
            style={{ width: `${(idx / quiz.questions.length) * 100}%` }}
          />
        </div>
      </div>

      <p className="font-medium">{q.prompt}</p>
      <div className="space-y-2">
        {q.options.map((opt, i) => (
          <button
            key={i}
            onClick={() => setChoice(i)}
            className={`flex w-full items-start gap-2 rounded-lg border p-2 text-left ${
              choice === i ? 'border-slate-900 bg-slate-100' : 'border-slate-300 hover:bg-slate-50'
            }`}
          >
            <kbd className="mt-0.5 rounded border border-slate-300 bg-white px-1.5 text-xs text-slate-500">
              {i + 1}
            </kbd>
            <span>{opt}</span>
          </button>
        ))}
      </div>

      <div>
        <div className="mb-1 text-xs text-slate-500">How sure are you?</div>
        <div className="grid grid-cols-3 gap-2">
          {CONFIDENCE.map((c) => (
            <button
              key={c.label}
              onClick={() => setConfidence(c.value)}
              className={`rounded-lg border py-1.5 ${
                confidence === c.value ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      <button
        disabled={choice === null || busy}
        onClick={next}
        className="w-full rounded-lg bg-slate-900 py-2 font-medium text-white disabled:opacity-40"
      >
        {!last ? 'Next' : busy ? 'Analysing…' : 'Find my gaps'}
      </button>
      <p className="text-center text-xs text-slate-400">Tip: press 1–4 to answer, Enter to continue</p>
    </div>
  )
}
