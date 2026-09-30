// Single entry point for backend calls. Set VITE_USE_MOCK=false in frontend/.env.local
// to hit the real backend (via the Vite /api proxy); default is mock mode.
import type {
  Answer,
  AssessmentResult,
  Concept,
  DocumentCreated,
  Edge,
  Graph,
  Quiz,
  StreamStatus,
} from '../types'
import { mockApi } from './mock'

export interface StreamHandlers {
  onStatus: (s: StreamStatus) => void
  onConcept: (c: Concept) => void
  onEdge: (e: Edge) => void
  onDone: (g: Graph) => void
  onError: (message: string) => void
}

export interface Api {
  createDocument(input: { file?: File; text?: string; title?: string }): Promise<DocumentCreated>
  /** Returns a function that closes the stream. */
  streamDocument(docId: string, h: StreamHandlers): () => void
  createQuiz(graphId: string, numQuestions?: number): Promise<Quiz>
  assess(quizId: string, answers: Answer[]): Promise<AssessmentResult>
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
  return res.json() as Promise<T>
}

const realApi: Api = {
  async createDocument({ file, text, title }) {
    const form = new FormData()
    if (file) form.append('file', file)
    if (text) form.append('text', text)
    if (title) form.append('title', title)
    return json(await fetch('/api/documents', { method: 'POST', body: form }))
  },

  streamDocument(docId, h) {
    const es = new EventSource(`/api/documents/${docId}/stream`)
    es.addEventListener('status', (e) => h.onStatus(JSON.parse(e.data)))
    es.addEventListener('concept', (e) => h.onConcept(JSON.parse(e.data)))
    es.addEventListener('edge', (e) => h.onEdge(JSON.parse(e.data)))
    es.addEventListener('done', (e) => {
      h.onDone(JSON.parse(e.data))
      es.close()
    })
    es.addEventListener('error', (e) => {
      const data = (e as MessageEvent).data
      h.onError(data ? JSON.parse(data).message : 'Stream connection lost')
      es.close()
    })
    return () => es.close()
  },

  async createQuiz(graphId, numQuestions = 8) {
    return json(
      await fetch('/api/quiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ graph_id: graphId, num_questions: numQuestions }),
      }),
    )
  },

  async assess(quizId, answers) {
    return json(
      await fetch('/api/assess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quiz_id: quizId, answers }),
      }),
    )
  },
}

export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
export const api: Api = USE_MOCK ? mockApi : realApi
