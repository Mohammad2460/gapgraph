// API CONTRACT — mirror of backend/app/models.py and docs/CONTRACT.md.
// Change only via a "contract:" PR that updates all three + /fixtures.

export type MasteryStatus = 'mastered' | 'shaky' | 'gap' | 'careless' | 'untested'
export type Difficulty = 'easy' | 'medium' | 'hard'

export interface Concept {
  id: string
  name: string
  definition: string
  source_excerpt: string
  importance: number
  cluster: string | null
}

export interface Edge {
  source: string // prerequisite
  target: string // dependent
  relation: 'prerequisite'
  confidence: number
  evidence: string
}

export interface Graph {
  id: string
  title: string
  concepts: Concept[]
  edges: Edge[]
}

export interface DocumentCreated {
  doc_id: string
  title: string
}

export interface StreamStatus {
  message: string
  progress: number
}

export interface Question {
  id: string
  concept_id: string
  prompt: string
  options: string[]
  difficulty: Difficulty
}

export interface Quiz {
  quiz_id: string
  graph_id: string
  questions: Question[]
}

export interface Answer {
  question_id: string
  choice_index: number
  confidence: number // 0..1
  time_ms: number | null
}

// B6 adaptive probing: POST /api/quiz/{quiz_id}/next
export interface AssessRequest {
  quiz_id: string
  answers: Answer[]
  learner_id?: string | null // opt in to B7 per-learner history
}

export interface NextQuestionRequest {
  answers: Answer[] // answered so far, in order
}

export interface NextQuestion {
  question: Question | null // null when every question is answered
  target_concept_id: string | null
  reason: string
  remaining: number // unanswered questions left after this one
}

export interface ConceptMastery {
  concept_id: string
  p_known: number
  status: MasteryStatus
  evidence_count: number
}

export interface RootGap {
  concept_id: string
  failed_concept_id: string
  path: string[] // root -> failed
  explanation: string
}

export interface NextTopic {
  concept_id: string
  order: number
  reason: string
}

export interface QuestionResult {
  question_id: string
  correct: boolean
  correct_index: number
  explanation: string
}

export interface AssessmentResult {
  quiz_id: string
  graph_id: string
  score: { correct: number; total: number }
  mastery: ConceptMastery[]
  root_gaps: RootGap[]
  careless_slips: string[]
  next_topics: NextTopic[]
  per_question: QuestionResult[]
}
