// 5-10 question diagnostic quiz with confidence + timing capture.  [Pillar C — task C4]
import { useEffect, useRef, useState } from 'react'
import type { Answer, Quiz } from '../types'

interface Props {
  quiz: Quiz
  busy: boolean
  onSubmit: (answers: Answer[]) => void
}

export function QuizPanel({ quiz, busy, onSubmit }: Props) {
  const [idx, setIdx] = useState(0)
  const [choice, setChoice] = useState<number | null>(null)
  const [confidence, setConfidence] = useState(0.5)
  const [answers, setAnswers] = useState<Answer[]>([])
  const shownAt = useRef(0) // set when each question is shown
  const q = quiz.questions[idx]

  useEffect(() => {
    shownAt.current = performance.now()
  }, [idx])

  const next = () => {
    if (choice === null) return
    const all = [
      ...answers,
      { question_id: q.id, choice_index: choice, confidence, time_ms: Math.round(performance.now() - shownAt.current) },
    ]
    setAnswers(all)
    setChoice(null)
    setConfidence(0.5)
    if (idx + 1 < quiz.questions.length) setIdx(idx + 1)
    else onSubmit(all)
  }

  return (
    <div className="space-y-3 text-sm">
      <div className="text-xs text-slate-500">
        Question {idx + 1} / {quiz.questions.length} · {q.difficulty}
      </div>
      <p className="font-medium">{q.prompt}</p>
      <div className="space-y-2">
        {q.options.map((opt, i) => (
          <button
            key={i}
            onClick={() => setChoice(i)}
            className={`block w-full rounded-lg border p-2 text-left ${
              choice === i ? 'border-slate-900 bg-slate-100' : 'border-slate-300'
            }`}
          >
            {opt}
          </button>
        ))}
      </div>
      <label className="block">
        <span className="text-xs text-slate-500">How sure are you? {Math.round(confidence * 100)}%</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.1}
          value={confidence}
          onChange={(e) => setConfidence(Number(e.target.value))}
          className="w-full"
        />
      </label>
      <button
        disabled={choice === null || busy}
        onClick={next}
        className="w-full rounded-lg bg-slate-900 py-2 font-medium text-white disabled:opacity-40"
      >
        {idx + 1 < quiz.questions.length ? 'Next' : busy ? 'Analysing…' : 'Find my gaps'}
      </button>
    </div>
  )
}
