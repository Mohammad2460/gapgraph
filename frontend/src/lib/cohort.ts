// Simulated cohort for the teacher view.  [Pillar C — task C8]
// 5 fake learners come from scripts/fake_learners.py (scripts/out/learner_N.json), scored
// against the demo quiz key. No backend involved: this is a demo of the idea.
import quizKey from '@fixtures/sample_quiz_key.json'
import l1 from '../../../scripts/out/learner_1.json'
import l2 from '../../../scripts/out/learner_2.json'
import l3 from '../../../scripts/out/learner_3.json'
import l4 from '../../../scripts/out/learner_4.json'
import l5 from '../../../scripts/out/learner_5.json'

interface LearnerFile {
  answers: { question_id: string; choice_index: number }[]
}

export const LEARNER_NAMES = ['Strong', 'Weak at maths', 'Careless & fast', 'Guesser', 'Average']
const LEARNERS: LearnerFile[] = [l1, l2, l3, l4, l5]

export interface CohortStat {
  concept_id: string
  weak: number // learners who missed a question on this concept
  total: number // learners who were tested on it
  fraction: number | null // weak / total, null when nobody was tested
}

export function cohortStats(): CohortStat[] {
  const byConcept = new Map<string, { weak: number; total: number }>()
  for (const learner of LEARNERS) {
    const answered = new Map(learner.answers.map((a) => [a.question_id, a.choice_index]))
    for (const q of quizKey.questions) {
      const choice = answered.get(q.id)
      if (choice === undefined) continue
      const s = byConcept.get(q.concept_id) ?? { weak: 0, total: 0 }
      s.total += 1
      if (choice !== q.answer_index) s.weak += 1
      byConcept.set(q.concept_id, s)
    }
  }
  return [...byConcept.entries()].map(([concept_id, s]) => ({
    concept_id,
    ...s,
    fraction: s.total ? s.weak / s.total : null,
  }))
}

export const LEARNER_COUNT = LEARNERS.length
