import type { MasteryStatus } from '../types'

export const STATUS_COLOR: Record<MasteryStatus | 'pending', string> = {
  pending: '#94a3b8', // before the quiz
  untested: '#cbd5e1',
  mastered: '#22c55e',
  shaky: '#eab308',
  careless: '#f97316',
  gap: '#ef4444',
}

export const STATUS_LABEL: Record<MasteryStatus | 'pending', string> = {
  pending: 'Not assessed yet',
  untested: 'Not tested',
  mastered: 'Mastered',
  shaky: 'Shaky',
  careless: 'Careless slip',
  gap: 'Real gap',
}
