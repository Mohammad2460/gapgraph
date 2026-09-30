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
  if (!res.ok) {
    let detail = await res.text()
    try {
      const body = JSON.parse(detail)
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // not JSON, keep the raw text
    }
    throw new Error(`${res.status}: ${detail || res.statusText}`)
  }
  return res.json() as Promise<T>
}

/** fetch() that turns "backend is down" into a readable message. */
async function call(input: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init)
  } catch {
    throw new Error("Can't reach the server. Is the backend running on :8000?")
  }
}

const realApi: Api = {
  async createDocument({ file, text, title }) {
    const form = new FormData()
    if (file) form.append('file', file)
    if (text) form.append('text', text)
    if (title) form.append('title', title)
    return json(await call('/api/documents', { method: 'POST', body: form }))
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
      let message = 'Stream connection lost. Is the backend running?'
      try {
        if (data) message = JSON.parse(data).message ?? message
      } catch {
        // malformed error payload, use the default message
      }
      h.onError(message)
      es.close()
    })
    return () => es.close()
  },

  async createQuiz(graphId, numQuestions = 8) {
    return json(
      await call('/api/quiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ graph_id: graphId, num_questions: numQuestions }),
      }),
    )
  },

  async assess(quizId, answers) {
    return json(
      await call('/api/assess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quiz_id: quizId, answers }),
      }),
    )
  },
}

export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
export const api: Api = USE_MOCK ? mockApi : realApi
