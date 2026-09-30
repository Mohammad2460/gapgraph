"""Adaptive probing (STRETCH — only if ahead of schedule).  [Pillar B — task B6]

Idea: after a wrong answer on concept C, ask next about C's weakest-evidence
prerequisite, to locate the root gap in fewer questions. Would need a new
endpoint POST /api/quiz/{quiz_id}/next — agree the contract change first.
"""
