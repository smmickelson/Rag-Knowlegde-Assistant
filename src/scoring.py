"""Stub for backlog item #1: port the 15-question scoring logic to Python.

This module exists only so the tests in tests/test_scoring.py can import
score_assessment() and run -- and each fail on its own -- instead of stopping
at import with a missing-module error. No scoring logic is implemented yet.
"""


def score_assessment(answers):
    """Score the 15 answers against the four styles (see specs/01-scoring-port.md).

    Not yet implemented: raises so every test fails at the call site until the
    real scoring logic lands.
    """
    raise NotImplementedError("scoring logic not implemented yet")
