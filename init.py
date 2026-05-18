"""
Chapter registry.

To add a new chapter:
  1. Create a new file `chXX_name.py` in this directory.
  2. In that file, define generator functions and a CHAPTER instance at the bottom.
  3. Import it below and add it to CHAPTERS_LIST in the desired position.
"""

from .base import Chapter, ProblemType

from .ch01_parenteral import CHAPTER as ch01
from .ch02_powdered import CHAPTER as ch02
from .ch03_percents import CHAPTER as ch03
from .ch04_solutions import CHAPTER as ch04
from .ch05_body_weight import CHAPTER as ch05
from .ch06_bsa import CHAPTER as ch06
from .ch07_infusion import CHAPTER as ch07
from .ch08_dilutions import CHAPTER as ch08
from .ch09_pn import CHAPTER as ch09
from .ch10_labels import CHAPTER as ch10

# Ordered list (curriculum order). Index here drives display order.
CHAPTERS_LIST = [ch01, ch02, ch03, ch04, ch05, ch06, ch07, ch08, ch09, ch10]

# Lookup by key.
CHAPTERS = {chapter.key: chapter for chapter in CHAPTERS_LIST}


def get_chapter(key: str) -> Chapter:
    return CHAPTERS[key]


def get_problem_type(chapter_key: str, problem_type_key: str) -> ProblemType:
    chapter = CHAPTERS[chapter_key]
    return next(pt for pt in chapter.problem_types if pt.key == problem_type_key)


__all__ = [
    "Chapter",
    "ProblemType",
    "CHAPTERS_LIST",
    "CHAPTERS",
    "get_chapter",
    "get_problem_type",
]
