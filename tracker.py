"""
Session-state tracker for stats, streaks, and adaptive selection.

Stats shape (nested):

    {
        "<chapter_key>": {
            "_overall": {"attempts": int, "correct": int},
            "<problem_type_key>": {"attempts": int, "correct": int},
            ...more problem types...
        },
        ...more chapters...
    }

The "_overall" key rolls up all problem types in a chapter. The other keys
match each ProblemType.key in that chapter.
"""

import random
import streamlit as st

from chapters import CHAPTERS_LIST


def init_tracker():
    """Initialize all session-state keys if they don't exist yet."""
    if "stats" not in st.session_state:
        stats = {}
        for chapter in CHAPTERS_LIST:
            stats[chapter.key] = {"_overall": {"attempts": 0, "correct": 0}}
            for pt in chapter.problem_types:
                stats[chapter.key][pt.key] = {"attempts": 0, "correct": 0}
        st.session_state.stats = stats
    if "streak" not in st.session_state:
        st.session_state.streak = 0
    if "best_streak" not in st.session_state:
        st.session_state.best_streak = 0
    if "current_problem" not in st.session_state:
        st.session_state.current_problem = None
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "input_version" not in st.session_state:
        # Incremented each time we generate a new problem so the input widget resets.
        st.session_state.input_version = 0

    # Navigation state
    if "selected_chapter_key" not in st.session_state:
        st.session_state.selected_chapter_key = None    # None = show chapter grid
    if "mixed_mode" not in st.session_state:
        st.session_state.mixed_mode = False
    if "problem_type_choice" not in st.session_state:
        st.session_state.problem_type_choice = "_adaptive"

    # Helper-button toggles (reset on every new problem)
    if "show_formula" not in st.session_state:
        st.session_state.show_formula = False
    if "show_hint" not in st.session_state:
        st.session_state.show_hint = False
    if "show_example" not in st.session_state:
        st.session_state.show_example = False
    if "example_problem" not in st.session_state:
        st.session_state.example_problem = None


def reset_helpers():
    """Clear the three helper toggles and the cached example problem.

    Call this whenever a new problem is generated so the formula/hint/example
    panels close and the worked example regenerates fresh next time.
    """
    st.session_state.show_formula = False
    st.session_state.show_hint = False
    st.session_state.show_example = False
    st.session_state.example_problem = None


def record_attempt(chapter_key, problem_type_key, is_correct):
    """Update both the problem-type stats and the chapter rollup."""
    chap_stats = st.session_state.stats[chapter_key]
    chap_stats["_overall"]["attempts"] += 1
    chap_stats[problem_type_key]["attempts"] += 1
    if is_correct:
        chap_stats["_overall"]["correct"] += 1
        chap_stats[problem_type_key]["correct"] += 1
        st.session_state.streak += 1
        if st.session_state.streak > st.session_state.best_streak:
            st.session_state.best_streak = st.session_state.streak
    else:
        st.session_state.streak = 0


def _adaptive_weight(stats):
    """Selection weight: lower accuracy -> higher weight.

    Topics with fewer than 3 attempts get a flat baseline weight so the
    student gets exposure across every topic before adaptive logic kicks in.
    """
    if stats["attempts"] < 3:
        return 1.0
    accuracy = stats["correct"] / stats["attempts"]
    return max(1.0 - accuracy, 0.1) * 2


def pick_adaptive_chapter():
    """Pick a chapter key, weighted by inverse overall accuracy."""
    chapter_keys = [chapter.key for chapter in CHAPTERS_LIST]
    weights = [
        _adaptive_weight(st.session_state.stats[ck]["_overall"])
        for ck in chapter_keys
    ]
    return random.choices(chapter_keys, weights=weights, k=1)[0]


def pick_adaptive_problem_type(chapter):
    """Pick a problem-type key from a chapter, weighted by inverse accuracy."""
    keys = [pt.key for pt in chapter.problem_types]
    weights = [
        _adaptive_weight(st.session_state.stats[chapter.key][k])
        for k in keys
    ]
    return random.choices(keys, weights=weights, k=1)[0]


def chapter_accuracy(chapter_key):
    s = st.session_state.stats[chapter_key]["_overall"]
    return None if s["attempts"] == 0 else s["correct"] / s["attempts"]


def problem_type_accuracy(chapter_key, problem_type_key):
    s = st.session_state.stats[chapter_key][problem_type_key]
    return None if s["attempts"] == 0 else s["correct"] / s["attempts"]


def get_weak_chapters(threshold=0.7, min_attempts=3):
    """Return (chapter_key, accuracy) pairs for chapters below threshold, weakest first."""
    weak = []
    for chapter in CHAPTERS_LIST:
        overall = st.session_state.stats[chapter.key]["_overall"]
        if overall["attempts"] >= min_attempts:
            accuracy = overall["correct"] / overall["attempts"]
            if accuracy < threshold:
                weak.append((chapter.key, accuracy))
    return sorted(weak, key=lambda pair: pair[1])


def total_attempts():
    """Total problems answered across every chapter and problem type."""
    return sum(
        st.session_state.stats[c.key]["_overall"]["attempts"]
        for c in CHAPTERS_LIST
    )


def current_accuracy():
    """Overall accuracy across the entire session, or None if no attempts yet."""
    attempts = total_attempts()
    if attempts == 0:
        return None
    correct = sum(
        st.session_state.stats[c.key]["_overall"]["correct"]
        for c in CHAPTERS_LIST
    )
    return correct / attempts


def recommend_weak_topic():
    """Return a short label naming the weakest chapter, or None if there isn't enough data.

    Used by the right-side stats panel to surface a single 'focus here next' hint.
    """
    weak = get_weak_chapters(threshold=0.85, min_attempts=3)
    if not weak:
        return None
    chapter_key, _accuracy = weak[0]
    # Local import to avoid circular dependency at module-load time.
    from chapters import CHAPTERS
    chapter = CHAPTERS[chapter_key]
    return f"Ch. {chapter.number} — {chapter.title}"
