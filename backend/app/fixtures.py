"""Loaders for /fixtures — the shared demo data every pillar develops against."""

import json
from functools import cache

from app.config import FIXTURES_DIR
from app.models import Answer, AssessmentResult, Graph, QuizKey


def _load(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


@cache
def sample_chapter() -> str:
    return (FIXTURES_DIR / "sample_chapter.txt").read_text()


def sample_graph() -> Graph:
    return Graph.model_validate(_load("sample_graph.json"))


def sample_quiz_key() -> QuizKey:
    return QuizKey.model_validate(_load("sample_quiz_key.json"))


def sample_answers() -> list[Answer]:
    return [Answer.model_validate(a) for a in _load("sample_answers.json")["answers"]]


def sample_assessment() -> AssessmentResult:
    return AssessmentResult.model_validate(_load("sample_assessment.json"))
