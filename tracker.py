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

    # Difficulty selector (affects answer-check tolerance only).
    if "difficulty" not in st.session_state:
        st.session_state.difficulty = "Standard"

    # Page routing. "Dashboard" is the landing view.
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"

    # Coach-mode state (per-problem; reset by reset_helpers).
    #   "answering"   = input visible, no Check submitted yet (or user clicked Try again)
    #   "first_wrong" = one wrong submission; coach intervention buttons shown
    #   "revealed"    = full solution visible; either correct, late-correct, or gave up
    if "problem_phase" not in st.session_state:
        st.session_state.problem_phase = "answering"
    if "attempt_count" not in st.session_state:
        # Counts Check submissions on the current problem. Only the first
        # submission feeds record_attempt; retries are pure learning.
        st.session_state.attempt_count = 0

    # Session-wide review queue. Holds metadata for problems missed on the
    # first attempt so the student can practice the same problem type again.
    if "review_queue" not in st.session_state:
        st.session_state.review_queue = []

    # Today's-goal target (count of problems). Resets when the browser
    # session ends, since there is no persistence layer.
    if "daily_goal_target" not in st.session_state:
        st.session_state.daily_goal_target = 5

    # Timed practice session. None when not in a sprint. When active,
    # a dict with keys: mode, target_questions, target_seconds, started_at,
    # answered, correct, question_start, per_question_seconds, completed,
    # end_reason. Set by start_timed_sprint() in app.py.
    if "timed_session" not in st.session_state:
        st.session_state.timed_session = None


def reset_helpers():
    """Clear the helper toggles, cached example, and per-problem coach state.

    Call this whenever a new problem is generated so the formula/hint/example
    panels close, the worked example regenerates fresh, and the coach state
    machine resets to "answering" with a zeroed attempt count.
    """
    st.session_state.show_formula = False
    st.session_state.show_hint = False
    st.session_state.show_example = False
    st.session_state.example_problem = None
    st.session_state.problem_phase = "answering"
    st.session_state.attempt_count = 0


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


def chapter_mastery(chapter_key):
    """Mastery score 0-100, combining accuracy and practice volume.

    Formula:  mastery = accuracy × confidence × 100
    where confidence = min(attempts / 10, 1.0).

    A student with 100% accuracy but only 3 attempts has mastery = 30,
    not 100 — because we don't have enough evidence yet. By 10 attempts,
    confidence saturates and mastery == accuracy × 100.
    """
    s = st.session_state.stats[chapter_key]["_overall"]
    if s["attempts"] == 0:
        return 0
    accuracy = s["correct"] / s["attempts"]
    confidence = min(s["attempts"] / 10, 1.0)
    return round(accuracy * confidence * 100)


def chapter_status(chapter_key):
    """Return (emoji, label) for a chapter's status. Used on chapter cards."""
    s = st.session_state.stats[chapter_key]["_overall"]
    if s["attempts"] == 0:
        return "⚪", "Not started"
    mastery = chapter_mastery(chapter_key)
    if mastery >= 85:
        return "🟢", "Mastered"
    if mastery >= 60:
        return "🔵", "Strong"
    if mastery >= 30:
        return "🟡", "Building"
    return "🟠", "Needs practice"


def difficulty_tolerance_multiplier():
    """How the difficulty setting scales answer-check tolerance.

    Beginner gets a wider tolerance (more forgiving rounding).
    Challenge demands tighter precision. Standard is the textbook tolerance.
    """
    return {
        "Beginner": 2.0,
        "Standard": 1.0,
        "Challenge": 0.5,
    }.get(st.session_state.difficulty, 1.0)


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


def recommended_focus_chapter():
    """Return the chapter key of the weakest attempted chapter, or None.

    Used by both the sidebar dashboard (display string) and the chapter-grid
    Recommended Focus card. Picks the attempted chapter with the lowest
    mastery score, but only if it's below the 'Mastered' threshold.
    """
    attempted = [
        (c.key, chapter_mastery(c.key))
        for c in CHAPTERS_LIST
        if st.session_state.stats[c.key]["_overall"]["attempts"] > 0
    ]
    if not attempted:
        return None
    attempted.sort(key=lambda pair: pair[1])
    weakest_key, mastery = attempted[0]
    if mastery >= 85:
        return None  # everything is solid, no recommendation needed
    return weakest_key


def recommend_weak_topic():
    """Return a short display label for the recommended focus chapter, or None."""
    key = recommended_focus_chapter()
    if not key:
        return None
    # Local import to avoid circular dependency at module-load time.
    from chapters import CHAPTERS
    chapter = CHAPTERS[key]
    return f"Ch. {chapter.number} — {chapter.title}"


# ============================================================
# Review queue (session-wide, FIFO-capped)
# ============================================================

REVIEW_QUEUE_MAX = 20


def push_review_queue(chapter_key, problem_type_key, question,
                      correct_answer=None, unit=None, explanation_steps=None):
    """Add a missed problem's metadata to the review queue.

    Stores enough to regenerate a fresh problem of the same type AND to
    surface the missed problem's answer/explanation in the Study Report.
    The answer/unit/explanation_steps params are optional for backward
    compatibility with any existing callers; the Study Report renders
    whichever fields are populated.
    """
    preview = question if len(question) <= 140 else question[:137] + "..."
    entry = {
        "chapter_key": chapter_key,
        "problem_type_key": problem_type_key,
        "question_preview": preview,
        "correct_answer": correct_answer,
        "unit": unit,
        "explanation_steps": explanation_steps,
    }
    queue = st.session_state.review_queue
    queue.append(entry)
    if len(queue) > REVIEW_QUEUE_MAX:
        # Drop oldest entries to stay within the cap.
        st.session_state.review_queue = queue[-REVIEW_QUEUE_MAX:]


def pop_review_queue_at(index):
    """Remove and return the entry at the given index. None if out of range."""
    queue = st.session_state.review_queue
    if 0 <= index < len(queue):
        return queue.pop(index)
    return None


def clear_review_queue():
    """Empty the review queue."""
    st.session_state.review_queue = []


def review_queue_size():
    return len(st.session_state.review_queue)


# ============================================================
# Today's-goal progress (session-only)
# ============================================================

def daily_goal_progress():
    """Return (count, target) for the Today's-goal display.

    Count is total attempts this session (sum of every chapter's _overall
    attempts), capped at the target so the progress bar never exceeds 1.0.
    "Today" is approximate here since session state resets per browser session.
    """
    count = total_attempts()
    target = st.session_state.daily_goal_target
    return count, target
