// Live prerequisite graph.  [Pillar C — tasks C2/C5]
import { useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { STATUS_COLOR } from '../lib/status'
import type { Concept, ConceptMastery, Edge } from '../types'

interface Props {
  concepts: Concept[]
  edges: Edge[]
  mastery?: Record<string, ConceptMastery>
  highlightPath?: string[] // root -> failed, drawn in red
  selectedId?: string | null
  onSelect?: (id: string) => void
}

type Node = { id: string; name: string; importance: number; x?: number; y?: number }
type Link = { source: string | Node; target: string | Node; key: string }

export function GraphView({ concepts, edges, mastery, highlightPath = [], selectedId, onSelect }: Props) {
  const box = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState({ width: 600, height: 500 })
  // Reuse node objects across renders so existing nodes keep their positions
  // while new ones stream in.
  const nodeCache = useRef(new Map<string, Node>())

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
      const cached = nodeCache.current.get(c.id) ?? { id: c.id, name: c.name, importance: c.importance }
      nodeCache.current.set(c.id, cached)
      return cached
    })
    const links: Link[] = edges.map((e) => ({ source: e.source, target: e.target, key: `${e.source}->${e.target}` }))
    return { nodes, links }
  }, [concepts, edges])

  const pathEdges = useMemo(() => {
    const s = new Set<string>()
    for (let i = 0; i < highlightPath.length - 1; i++) s.add(`${highlightPath[i]}->${highlightPath[i + 1]}`)
    return s
  }, [highlightPath])

  return (
    <div ref={box} className="h-full w-full">
      <ForceGraph2D<Node, Link>
        graphData={data}
        width={size.width}
        height={size.height}
        cooldownTicks={120}
        linkDirectionalArrowLength={5}
        linkDirectionalArrowRelPos={1}
        linkColor={(l) => (pathEdges.has(l.key) ? STATUS_COLOR.gap : '#cbd5e1')}
        linkWidth={(l) => (pathEdges.has(l.key) ? 4 : 1)}
        linkDirectionalParticles={(l) => (pathEdges.has(l.key) ? 4 : 0)}
        linkDirectionalParticleColor={() => STATUS_COLOR.gap}
        onNodeClick={(n) => onSelect?.(n.id)}
        nodeCanvasObject={(node, ctx, scale) => {
          const status = mastery?.[node.id]?.status ?? 'pending'
          const r = 5 + node.importance * 7
          const x = node.x ?? 0
          const y = node.y ?? 0
          ctx.beginPath()
          ctx.arc(x, y, r, 0, 2 * Math.PI)
          ctx.fillStyle = STATUS_COLOR[status]
          ctx.fill()
          if (node.id === selectedId || highlightPath[0] === node.id) {
            ctx.lineWidth = 3 / scale
            ctx.strokeStyle = '#0f172a'
            ctx.stroke()
          }
          ctx.font = `${12 / scale}px Inter, system-ui, sans-serif`
          ctx.textAlign = 'center'
          ctx.fillStyle = '#0f172a'
          ctx.fillText(node.name, x, y + r + 12 / scale)
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
