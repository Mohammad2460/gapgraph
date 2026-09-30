// Live prerequisite graph.  [Pillar C — tasks C2/C5]
import { useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d'
import { NO_CLUSTER_COLOR, clusterColors } from '../lib/clusters'
import { STATUS_COLOR } from '../lib/status'
import type { Concept, ConceptMastery, Edge } from '../types'

interface Props {
  concepts: Concept[]
  edges: Edge[]
  mastery?: Record<string, ConceptMastery>
  /** Teacher view: 0..1 share of learners weak on each concept, drawn green -> red. */
  heat?: Record<string, number>
  highlightPath?: string[] // root -> failed, drawn in red
  selectedId?: string | null
  /** Change this value to re-fit the whole graph in view (e.g. when streaming is done). */
  fitSignal?: number
  onSelect?: (id: string) => void
}

type Node = {
  id: string
  name: string
  importance: number
  cluster: string | null
  x?: number
  y?: number
}
type Link = { source: string | Node; target: string | Node; key: string }

// green (0) -> yellow (0.5) -> red (1); grey when nobody was tested.
function heatColor(v: number | undefined): string {
  if (v === undefined) return STATUS_COLOR.untested
  const hue = 120 - 120 * Math.min(1, Math.max(0, v))
  return `hsl(${hue}, 75%, 48%)`
}

const POP_MS = 400
const easeOutBack = (t: number) => 1 + 2.7 * Math.pow(t - 1, 3) + 1.7 * Math.pow(t - 1, 2)

export function GraphView({
  concepts,
  edges,
  mastery,
  heat,
  highlightPath = [],
  selectedId,
  fitSignal = 0,
  onSelect,
}: Props) {
  const box = useRef<HTMLDivElement>(null)
  const fg = useRef<ForceGraphMethods<Node, Link> | undefined>(undefined)
  const [size, setSize] = useState({ width: 600, height: 500 })
  // Reuse node objects across renders so existing nodes keep their positions
  // while new ones stream in.
  const [nodeCache] = useState(() => new Map<string, Node>())
  // When each node was first drawn, for the pop-in animation.
  const born = useRef(new Map<string, number>())
  const colors = useMemo(() => clusterColors(concepts.map((c) => c.cluster)), [concepts])

  // Last fitSignal we re-fitted for once the layout settled (the 500ms fit can fire mid-layout).
  const settledFit = useRef(0)

  useEffect(() => {
    if (fitSignal === 0) return
    const t = setTimeout(() => fg.current?.zoomToFit(600, 60), 500)
    return () => clearTimeout(t)
  }, [fitSignal])

  useEffect(() => {
    if (!box.current) return
    const ro = new ResizeObserver(([entry]) =>
      setSize({ width: entry.contentRect.width, height: entry.contentRect.height }),
    )
    ro.observe(box.current)
    return () => ro.disconnect()
  }, [])

  const data = useMemo(() => {
    const nodes = concepts.map((c) => {
      const cached = nodeCache.get(c.id) ?? { id: c.id, name: c.name, importance: c.importance, cluster: c.cluster }
      nodeCache.set(c.id, cached)
      return cached
    })
    const links: Link[] = edges.map((e) => ({ source: e.source, target: e.target, key: `${e.source}->${e.target}` }))
    return { nodes, links }
  }, [concepts, edges, nodeCache])

  const pathEdges = useMemo(() => {
    const s = new Set<string>()
    for (let i = 0; i < highlightPath.length - 1; i++) s.add(`${highlightPath[i]}->${highlightPath[i + 1]}`)
    return s
  }, [highlightPath])

  const pathNodes = useMemo(() => new Set(highlightPath), [highlightPath])
  const focusing = highlightPath.length > 0

  // Glide to the selected node (e.g. from the "Study next" list).
  useEffect(() => {
    if (!selectedId) return
    const n = nodeCache.get(selectedId)
    if (n?.x !== undefined && n.y !== undefined) fg.current?.centerAt(n.x, n.y, 600)
  }, [selectedId, nodeCache])

  return (
    <div ref={box} className="h-full w-full">
      <ForceGraph2D<Node, Link>
        ref={fg}
        graphData={data}
        autoPauseRedraw={false}
        width={size.width}
        height={size.height}
        cooldownTicks={120}
        onEngineStop={() => {
          if (fitSignal === 0 || settledFit.current === fitSignal) return
          settledFit.current = fitSignal
          fg.current?.zoomToFit(400, 60)
        }}
        linkDirectionalArrowLength={5}
        linkDirectionalArrowRelPos={1}
        linkColor={(l) => (pathEdges.has(l.key) ? STATUS_COLOR.gap : focusing ? '#e2e8f0' : '#cbd5e1')}
        linkWidth={(l) => (pathEdges.has(l.key) ? 4 : 1)}
        linkDirectionalParticles={(l) => (pathEdges.has(l.key) ? 4 : 0)}
        linkDirectionalParticleColor={() => STATUS_COLOR.gap}
        onNodeClick={(n) => onSelect?.(n.id)}
        nodeCanvasObject={(node, ctx, scale) => {
          const now = performance.now()
          if (!born.current.has(node.id)) born.current.set(node.id, now)
          const t = Math.min(1, (now - born.current.get(node.id)!) / POP_MS)
          const grow = easeOutBack(t)

          const m = mastery?.[node.id]
          const fill = heat
            ? heatColor(heat[node.id])
            : m
            ? STATUS_COLOR[m.status]
            : node.cluster
              ? (colors[node.cluster] ?? NO_CLUSTER_COLOR)
              : NO_CLUSTER_COLOR
          const r = (5 + node.importance * 7) * grow
          const x = node.x ?? 0
          const y = node.y ?? 0
          // Dim everything that is not on the active root-gap path.
          ctx.globalAlpha = t * (focusing && !pathNodes.has(node.id) ? 0.25 : 1)
          ctx.beginPath()
          ctx.arc(x, y, Math.max(r, 0), 0, 2 * Math.PI)
          ctx.fillStyle = fill
          ctx.fill()
          if (m?.status === 'careless') {
            ctx.save()
            ctx.setLineDash([3 / scale, 2 / scale])
            ctx.lineWidth = 2 / scale
            ctx.strokeStyle = STATUS_COLOR.careless
            ctx.beginPath()
            ctx.arc(x, y, r + 4 / scale, 0, 2 * Math.PI)
            ctx.stroke()
            ctx.restore()
          }
          if (highlightPath[0] === node.id) {
            // Pulsing halo on the root cause.
            const pulse = (now % 1200) / 1200
            ctx.beginPath()
            ctx.arc(x, y, r + (4 + pulse * 14) / scale, 0, 2 * Math.PI)
            ctx.strokeStyle = STATUS_COLOR.gap
            ctx.globalAlpha = 0.6 * (1 - pulse)
            ctx.lineWidth = 3 / scale
            ctx.stroke()
            ctx.globalAlpha = t
          }
          if (node.id === selectedId || highlightPath[0] === node.id) {
            ctx.lineWidth = 3 / scale
            ctx.strokeStyle = '#0f172a'
            ctx.stroke()
          }
          ctx.font = `${12 / scale}px Inter, system-ui, sans-serif`
          ctx.textAlign = 'center'
          ctx.fillStyle = '#0f172a'
          ctx.fillText(node.name, x, y + r + 12 / scale)
          ctx.globalAlpha = 1
        }}
        nodePointerAreaPaint={(node, color, ctx) => {
          ctx.fillStyle = color
          ctx.beginPath()
          ctx.arc(node.x ?? 0, node.y ?? 0, 5 + node.importance * 7, 0, 2 * Math.PI)
          ctx.fill()
        }}
      />
    </div>
  )
}
