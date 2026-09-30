import { useCallback, useRef, useState } from 'react'
import { api } from '../api/client'
import type { Concept, Edge, Graph, StreamStatus } from '../types'

/** Accumulates concepts/edges as they stream in. [Pillar C — task C2] */
export function useGraphStream() {
  const [concepts, setConcepts] = useState<Concept[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [status, setStatus] = useState<StreamStatus | null>(null)
  const [graph, setGraph] = useState<Graph | null>(null)
  const [error, setError] = useState<string | null>(null)
  const close = useRef<(() => void) | null>(null)

  const start = useCallback((docId: string) => {
    close.current?.()
    setConcepts([])
    setEdges([])
    setGraph(null)
    setError(null)
    close.current = api.streamDocument(docId, {
      onStatus: setStatus,
      onConcept: (c) => setConcepts((prev) => (prev.some((p) => p.id === c.id) ? prev : [...prev, c])),
      onEdge: (e) => setEdges((prev) => [...prev, e]),
      onDone: (g) => {
        setGraph(g)
        setConcepts(g.concepts)
        setEdges(g.edges)
      },
      onError: setError,
    })
  }, [])

  return { concepts, edges, status, graph, error, start }
}
