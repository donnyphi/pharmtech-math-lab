"""
Base data structures for curriculum chapters.

A Chapter is a curriculum unit (e.g., "Body Weight Dosing").
Each Chapter contains one or more ProblemTypes, which are specific sub-skills
within the chapter (e.g., "single mg/kg dose" vs "divided daily dose").

Each ProblemType has a generator: a zero-argument function that returns a
problem dict shaped like:

    {
        "question": str,
        "answer": float,
        "unit": str,
        "tolerance": float,    # absolute tolerance floor; relative tol added in app.py
        "steps": list[str],    # solution walkthrough shown after answer
    }

The Chapter dataclass also reserves space for future features (Learn and
Guided Examples). Those fields are None for now; the architecture is ready,
the content isn't.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class ProblemType:
    """A specific problem type within a chapter."""
    key: str               # unique within its chapter, e.g., "single_dose"
    label: str             # display label, e.g., "Single dose (mg/kg)"
    generator: Callable    # zero-arg function returning a problem dict


@dataclass
class Chapter:
    """A curriculum chapter."""
    key: str                                       # globally unique, e.g., "body_weight"
    number: int                                    # curriculum order (1-10)
    title: str                                     # full title shown in the UI
    summary: str                                   # one-line description
    problem_types: List[ProblemType]               # one or more problem types

    # Future hooks. Leave as None until implemented.
    learn_content: Optional[str] = None            # markdown body for a Learn tab
    guided_examples: Optional[List[dict]] = None   # worked examples for an Examples tab
