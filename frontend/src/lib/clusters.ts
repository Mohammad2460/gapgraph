// Stable colour per cluster so the graph is readable before the quiz.  [Pillar C — task C2]
const PALETTE = ['#3b82f6', '#8b5cf6', '#14b8a6', '#ec4899', '#0ea5e9', '#84cc16', '#a855f7', '#06b6d4']

export function clusterColors(clusters: (string | null)[]): Record<string, string> {
  const unique = [...new Set(clusters.filter((c): c is string => !!c))].sort()
  return Object.fromEntries(unique.map((c, i) => [c, PALETTE[i % PALETTE.length]]))
}

export const NO_CLUSTER_COLOR = '#94a3b8'
