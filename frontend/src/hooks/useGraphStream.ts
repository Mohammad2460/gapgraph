import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { Concept, Edge, Graph, StreamStatus } from '../types'

/** Accumulates concepts/edges as they stream in. [Pillar C — task C2] */
export function useGraphStream() {
  const [concepts, setConcepts] = useState<Concept[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [status, setStatus] = useState<StreamStatus | null>(null)
  const [graph, setGraph] = useState<Graph | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [slow, setSlow] = useState(false)
  const close = useRef<(() => void) | null>(null)
  const slowTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const clearSlow = () => {
    clearTimeout(slowTimer.current)
    setSlow(false)
  }

  useEffect(() => () => clearTimeout(slowTimer.current), [])

  const start = useCallback((docId: string) => {
    close.current?.()
    setConcepts([])
    setEdges([])
    setGraph(null)
    setError(null)
    setStatus(null)
    clearSlow()
    // The first Claude response can take a while; tell the user we're still alive.
    slowTimer.current = setTimeout(() => setSlow(true), 6000)
    close.current = api.streamDocument(docId, {
      onStatus: (s) => {
        clearSlow()
        setStatus(s)
      },
      onConcept: (c) => {
        clearSlow()
        setConcepts((prev) => (prev.some((p) => p.id === c.id) ? prev : [...prev, c]))
      },
      onEdge: (e) => setEdges((prev) => [...prev, e]),
      onDone: (g) => {
        clearSlow()
        setGraph(g)
        setConcepts(g.concepts)
        setEdges(g.edges)
      },
      onError: (m) => {
        clearSlow()
        setError(m)
      },
    })
  }, [])

  const reset = useCallback(() => {
    close.current?.()
    clearTimeout(slowTimer.current)
    setSlow(false)
    setError(null)
    setStatus(null)
  }, [])

  return { concepts, edges, status, graph, error, slow, start, reset }
}
