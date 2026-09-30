"""Print quick stats and sanity checks for a GapGraph graph JSON file.

Usage: python scripts/graph_stats.py fixtures/sample_graph.json
"""

import json
import sys
from collections import Counter
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/graph_stats.py <graph.json>")
        return 2

    path = Path(sys.argv[1])
    try:
        graph = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        print(f"Could not read {path}: {err}")
        return 2

    concepts = graph.get("concepts", [])
    edges = graph.get("edges", [])

    print(f"Graph: {graph.get('title', '(untitled)')}")
    print(f"Concepts: {len(concepts)}")
    print(f"Edges:    {len(edges)}")

    print("\nConcepts per cluster:")
    per_cluster = Counter(c.get("cluster", "(none)") for c in concepts)
    for cluster, count in sorted(per_cluster.items()):
        print(f"  {cluster}: {count}")

    print("\nTop 3 by importance:")
    top3 = sorted(concepts, key=lambda c: c.get("importance", 0), reverse=True)[:3]
    for c in top3:
        print(f"  {c['name']} ({c.get('importance', 0)})")

    # Anything below is a bug in the graph.
    problems = []
    ids = {c["id"] for c in concepts}

    for c in concepts:
        if not c.get("source_excerpt", "").strip():
            problems.append(f"concept '{c['id']}' has an empty source_excerpt")

    for e in edges:
        label = f"{e.get('source')} -> {e.get('target')}"
        if not e.get("evidence", "").strip():
            problems.append(f"edge {label} has empty evidence")
        for end in ("source", "target"):
            if e.get(end) not in ids:
                problems.append(f"edge {label}: {end} '{e.get(end)}' is not a concept id")

    print()
    if problems:
        print(f"Found {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("No problems found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
