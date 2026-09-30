"""Orchestrates the learner model into one AssessmentResult.  [Pillar B — task B5]"""

from app.learner.careless import classify_careless
from app.learner.gaps import find_root_gaps
from app.learner.mastery import estimate_mastery
from app.learner.path import suggest_next_topics
from app.models import Answer, AssessmentResult, Graph, QuestionResult, QuizKey, Score


def assess(graph: Graph, quiz: QuizKey, answers: list[Answer]) -> AssessmentResult:
    by_id = {q.id: q for q in quiz.questions}
    # A retried submission replaces the earlier response to the same question.
    answers = list({
        answer.question_id: answer for answer in answers if answer.question_id in by_id
    }.values())
    per_question = [
        QuestionResult(
            question_id=a.question_id,
            correct=a.choice_index == by_id[a.question_id].answer_index,
            correct_index=by_id[a.question_id].answer_index,
            explanation=by_id[a.question_id].explanation,
        )
        for a in answers
        if a.question_id in by_id
    ]

    mastery = estimate_mastery(graph, quiz.questions, answers)
    careless = classify_careless(graph, quiz.questions, answers, mastery)
    root_gaps = find_root_gaps(graph, mastery)
    next_topics = suggest_next_topics(graph, mastery, root_gaps, careless)

    return AssessmentResult(
        quiz_id=quiz.quiz_id,
        graph_id=graph.id,
        score=Score(correct=sum(r.correct for r in per_question), total=len(per_question)),
        mastery=list(mastery.values()),
        root_gaps=root_gaps,
        careless_slips=careless,
        next_topics=next_topics,
        per_question=per_question,
    )
