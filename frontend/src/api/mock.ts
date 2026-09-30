// Offline mock of the backend, driven by the shared /fixtures. Lets Pillar C
// build the whole UI without a running backend or API key.
import assessment from '@fixtures/sample_assessment.json'
import graphJson from '@fixtures/sample_graph.json'
import quizKey from '@fixtures/sample_quiz_key.json'
import type { AssessmentResult, Graph, Quiz } from '../types'
import type { Api } from './client'

const graph = graphJson as Graph
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

export const mockApi: Api = {
  async createDocument({ title }) {
    await sleep(300)
    return { doc_id: 'demo', title: title || graph.title }
  },

  streamDocument(_docId, h) {
    let cancelled = false
    ;(async () => {
      h.onStatus({ message: 'Reading chapter…', progress: 0 })
      const sent = new Set<string>()
      for (const [i, c] of graph.concepts.entries()) {
        await sleep(250)
        if (cancelled) return
        sent.add(c.id)
        h.onConcept(c)
        graph.edges
          .filter((e) => (e.source === c.id || e.target === c.id) && sent.has(e.source) && sent.has(e.target))
          .forEach(h.onEdge)
        h.onStatus({ message: `Found ${c.name}`, progress: (i + 1) / graph.concepts.length })
      }
      h.onDone(graph)
    })()
    return () => {
      cancelled = true
    }
  },

  async createQuiz() {
    await sleep(400)
    // Strip answers exactly like the backend does.
    const questions = quizKey.questions.map(({ answer_index: _a, explanation: _e, ...q }) => q)
    return { ...quizKey, questions } as Quiz
  },

  async assess() {
    await sleep(600)
    return assessment as AssessmentResult
  },
}
