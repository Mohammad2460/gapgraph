"""Generate 5 simulated learners' answer files into scripts/out/.

Usage: python scripts/fake_learners.py
Same seed -> same output every run. Output shape matches fixtures/sample_answers.json.
"""

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = Path(__file__).resolve().parent / "out"
MATH_CLUSTERS = {"math", "linear_algebra"}

# p_correct: chance of a right answer. conf/time: (low, high) ranges.
# p_slip: chance a question the learner would get right becomes a fast, confident mistake.
PERSONALITIES = {
    "strong": {"p_correct": 0.9, "conf": (0.7, 1.0), "time": (6000, 15000)},
    "weak_at_maths": {
        "p_correct": 0.8, "p_correct_math": 0.2,
        "conf": (0.2, 0.5), "time": (15000, 35000),
    },
    "careless_fast": {
        "p_correct": 0.9, "p_slip": 0.3,
        "conf": (0.7, 1.0), "time": (5000, 12000),
        "slip_time": (1500, 3000),
    },
    "guesser": {"p_correct": 0.25, "conf": (0.1, 0.4), "time": (2000, 6000)},
    "average": {"p_correct": 0.6, "conf": (0.4, 0.7), "time": (8000, 20000)},
}


def load(name: str) -> dict:
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def wrong_choice(question: dict) -> int:
    options = range(len(question["options"]))
    return random.choice([i for i in options if i != question["answer_index"]])


def answer(question: dict, cluster: str, p: dict) -> dict:
    p_correct = p["p_correct"]
    if cluster in MATH_CLUSTERS:
        p_correct = p.get("p_correct_math", p_correct)

    correct = random.random() < p_correct
    conf = random.uniform(*p["conf"])
    time_ms = random.randint(*p["time"])

    # Careless slip: knew it, but rushed and got it wrong while feeling sure.
    if correct and random.random() < p.get("p_slip", 0):
        correct = False
        time_ms = random.randint(*p["slip_time"])

    choice = question["answer_index"] if correct else wrong_choice(question)
    return {
        "question_id": question["id"],
        "choice_index": choice,
        "confidence": round(conf, 2),
        "time_ms": time_ms,
    }


def main() -> None:
    random.seed(42)
    key = load("sample_quiz_key.json")
    cluster_of = {c["id"]: c["cluster"] for c in load("sample_graph.json")["concepts"]}

    OUT_DIR.mkdir(exist_ok=True)
    for n, (name, p) in enumerate(PERSONALITIES.items(), start=1):
        answers = [
            answer(q, cluster_of.get(q["concept_id"], ""), p) for q in key["questions"]
        ]
        data = {"quiz_id": key["quiz_id"], "answers": answers}
        path = OUT_DIR / f"learner_{n}.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        right = sum(
            a["choice_index"] == q["answer_index"] for a, q in zip(answers, key["questions"])
        )
        print(f"{path.name}: {name:14} {right}/{len(answers)} correct")


if __name__ == "__main__":
    main()
