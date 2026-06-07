
"""Pharmacy Tech Math Practice — Streamlit app (v6.5 + Timed Practice setup page).

Layout overview:
    Sidebar    : session metrics, session-goal progress, page nav,
                 difficulty selector, chapter list. UNCHANGED from v6.5.
    Dashboard  : hero → feature highlights → action cards
                 (Recommended Focus + Timed Practice) → optional queue
                 expander → learning path. The Timed Practice card is now
                 a single-CTA card that opens a setup picker overlay.
    Setup      : transient overlay reached by clicking the dashboard's
                 "Start Timed Practice" button. Shows the four sprint
                 options and a Back-to-Dashboard button. Driven by a
                 single boolean (timed_setup_open). Not part of the page
                 nav radio.
    Practice   : when a chapter is active, runs the coach-mode problem
                 flow. When no chapter is active, the diagnostic empty
                 state. When a timed sprint is active, a status bar wraps
                 the problem and a summary view shows once the end
                 condition is met. UNCHANGED.
    Calculator : dose-to-volume reference. UNCHANGED.

Run with:
    streamlit run app.py
"""

import html
import re
import time
import streamlit as st

from chapters import CHAPTERS, CHAPTERS_LIST, get_chapter, get_problem_type
from tracker import (
    init_tracker,
    record_attempt,
    reset_helpers,
    pick_adaptive_chapter,
    pick_adaptive_problem_type,
    chapter_accuracy,
    chapter_mastery,
    chapter_status,
    difficulty_tolerance_multiplier,
    get_weak_chapters,
    total_attempts,
    current_accuracy,
    recommend_weak_topic,
    recommended_focus_chapter,
    push_review_queue,
    pop_review_queue_at,
    clear_review_queue,
    review_queue_size,
    daily_goal_progress,
)

st.set_page_config(
    page_title="DoseDrill",
    page_icon="💊",
    layout="wide",
)
init_tracker()

# Valid pages after the v6.4 nav simplification. Progress is gone; its
# content lives on the Practice page's empty state.
_VALID_PAGES = ["Dashboard", "Practice", "Calculator"]

# Internal routing key. Kept separate from any widget key so it can be
# updated safely from anywhere in the script.
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Migration guard: an existing session that came from v6.3 may have
# current_page == "Progress". Coerce to Dashboard before the nav radio
# tries to render that no-longer-valid option.
if st.session_state.current_page not in _VALID_PAGES:
    st.session_state.current_page = "Dashboard"

# --- Timed Practice state ---
# Seven sprint-state keys, all live in app.py rather than tracker.py to keep
# tracker.py at exactly the v6.5 state. The sprint is "over" when either:
#   - time-based:    time.time() - timed_started_at >= timed_target_seconds
#   - question-based: timed_answered >= timed_target_questions AND
#                     current_problem is None
if "timed_mode" not in st.session_state:
    st.session_state.timed_mode = False
if "timed_type" not in st.session_state:
    st.session_state.timed_type = None
if "timed_target_questions" not in st.session_state:
    st.session_state.timed_target_questions = None
if "timed_target_seconds" not in st.session_state:
    st.session_state.timed_target_seconds = None
if "timed_started_at" not in st.session_state:
    st.session_state.timed_started_at = None
if "timed_answered" not in st.session_state:
    st.session_state.timed_answered = 0
if "timed_correct" not in st.session_state:
    st.session_state.timed_correct = 0

# Timed setup overlay flag. When True, the routing renders the sprint-type
# picker view instead of the underlying page. Cleared by any navigation
# action that changes the underlying page.
if "timed_setup_open" not in st.session_state:
    st.session_state.timed_setup_open = False


# Maps the four sprint type strings to their target_questions / target_seconds.
# Used by start_timed_sprint() and the status-bar / summary labels.
_TIMED_CONFIGS = {
    "5q":   {"label": "5-question sprint",  "target_questions": 5,  "target_seconds": None},
    "10q":  {"label": "10-question sprint", "target_questions": 10, "target_seconds": None},
    "2min": {"label": "2-minute sprint",    "target_questions": None, "target_seconds": 120},
    "5min": {"label": "5-minute sprint",    "target_questions": None, "target_seconds": 300},
}


# ============================================================
# Core actions
# ============================================================

def _clear_timed_state():
    """Reset all timed_* sprint-state keys back to their initial values.
    Does NOT touch timed_setup_open — that's UI overlay state, handled
    separately by each navigation entry point."""
    st.session_state.timed_mode = False
    st.session_state.timed_type = None
    st.session_state.timed_target_questions = None
    st.session_state.timed_target_seconds = None
    st.session_state.timed_started_at = None
    st.session_state.timed_answered = 0
    st.session_state.timed_correct = 0


def new_problem():
    """Generate a problem based on current selection state."""
    if st.session_state.mixed_mode:
        chapter_key = pick_adaptive_chapter()
        chapter = get_chapter(chapter_key)
        pt_key = pick_adaptive_problem_type(chapter)
    else:
        chapter = get_chapter(st.session_state.selected_chapter_key)
        choice = st.session_state.problem_type_choice
        if choice == "_adaptive":
            pt_key = pick_adaptive_problem_type(chapter)
        else:
            pt_key = choice

    problem_type = get_problem_type(chapter.key, pt_key)
    problem = problem_type.generator()

    problem["chapter_key"] = chapter.key
    problem["problem_type_key"] = pt_key
    problem["chapter_title"] = chapter.title
    problem["chapter_number"] = chapter.number
    problem["problem_type_label"] = problem_type.label

    st.session_state.current_problem = problem
    st.session_state.last_result = None
    st.session_state.input_version += 1
    reset_helpers()


def go_to_dashboard():
    """Clear practice state and return to the dashboard.
    Also clears any active timed sprint and the timed setup overlay."""
    st.session_state.selected_chapter_key = None
    st.session_state.mixed_mode = False
    st.session_state.current_problem = None
    st.session_state.last_result = None
    st.session_state.problem_type_choice = "_adaptive"
    st.session_state.current_page = "Dashboard"
    st.session_state.timed_setup_open = False
    _clear_timed_state()
    reset_helpers()


def start_chapter(chapter_key, problem_type_key="_adaptive"):
    """Enter practice mode for a specific chapter and route to Practice.
    Clears any active timed sprint and the timed setup overlay."""
    st.session_state.selected_chapter_key = chapter_key
    st.session_state.mixed_mode = False
    st.session_state.problem_type_choice = problem_type_key
    st.session_state.current_page = "Practice"
    st.session_state.timed_setup_open = False
    _clear_timed_state()
    new_problem()


def start_mixed():
    """Enter mixed-practice mode across all chapters (untimed).
    Clears any active timed sprint and the timed setup overlay."""
    st.session_state.mixed_mode = True
    st.session_state.selected_chapter_key = None
    st.session_state.problem_type_choice = "_adaptive"
    st.session_state.current_page = "Practice"
    st.session_state.timed_setup_open = False
    _clear_timed_state()
    new_problem()


def practice_from_review(index):
    """Pop an entry from the review queue and start practicing that type."""
    entry = pop_review_queue_at(index)
    if entry:
        start_chapter(entry["chapter_key"], entry["problem_type_key"])


def start_timed_sprint(timed_type):
    """Begin a timed sprint. Sets the timed_* keys, enables mixed-mode
    adaptive selection, routes to Practice, and generates the first problem.
    Also closes the timed setup overlay since the user has made a choice.
    timed_type must be one of: '5q', '10q', '2min', '5min'.
    """
    cfg = _TIMED_CONFIGS.get(timed_type)
    if cfg is None:
        return

    now = time.time()
    st.session_state.timed_mode = True
    st.session_state.timed_type = timed_type
    st.session_state.timed_target_questions = cfg["target_questions"]
    st.session_state.timed_target_seconds = cfg["target_seconds"]
    st.session_state.timed_started_at = now
    st.session_state.timed_answered = 0
    st.session_state.timed_correct = 0

    # Sprint runs in mixed adaptive mode, same as Start Mixed Practice.
    st.session_state.mixed_mode = True
    st.session_state.selected_chapter_key = None
    st.session_state.problem_type_choice = "_adaptive"
    st.session_state.current_page = "Practice"
    st.session_state.timed_setup_open = False
    new_problem()


def check_answer(problem, user_answer):
    """Verify the answer and drive the coach state machine.

    Stats math preserved: record_attempt fires only on the FIRST submission,
    so retries and self-corrections don't affect mastery or streak. Timed
    counters increment alongside on the FIRST submission only.
    """
    correct_value = problem["answer"]
    base_tolerance = max(abs(correct_value) * 0.01, problem["tolerance"])
    tolerance = base_tolerance * difficulty_tolerance_multiplier()
    is_correct = abs(user_answer - correct_value) <= tolerance

    st.session_state.attempt_count += 1
    is_first_submission = st.session_state.attempt_count == 1

    if is_first_submission:
        record_attempt(problem["chapter_key"], problem["problem_type_key"], is_correct)
        if not is_correct:
            push_review_queue(
                problem["chapter_key"],
                problem["problem_type_key"],
                problem["question"],
            )
        # Timed sprint counters. Independent of record_attempt above.
        if st.session_state.timed_mode:
            st.session_state.timed_answered += 1
            if is_correct:
                st.session_state.timed_correct += 1

    if is_correct:
        st.session_state.problem_phase = "revealed"
    elif is_first_submission:
        st.session_state.problem_phase = "first_wrong"
    else:
        st.session_state.problem_phase = "revealed"

    st.session_state.last_result = {
        "correct": is_correct,
        "user_answer": user_answer,
        "correct_answer": correct_value,
        "steps": problem["steps"],
        "unit": problem["unit"],
        "attempt_number": st.session_state.attempt_count,
    }


def coach_retry(open_hint=False):
    """Transition first_wrong → answering for a second attempt."""
    st.session_state.problem_phase = "answering"
    st.session_state.last_result = None
    st.session_state.input_version += 1
    if open_hint:
        st.session_state.show_hint = True


def coach_reveal():
    """User clicked Show solution from the first_wrong intervention."""
    st.session_state.problem_phase = "revealed"


# ============================================================
# Sidebar (UNCHANGED)
# ============================================================

def _on_nav_change():
    """Sync current_page when the user clicks the navigation radio.
    Also closes the timed setup overlay since a nav change implies the
    user wants to leave the dashboard context."""
    st.session_state.current_page = st.session_state.nav_choice
    st.session_state.timed_setup_open = False


with st.sidebar:
    st.title("💊 DoseDrill")
    st.caption("Built by Donny Phi")

    st.markdown("**📊 This session**")
    row1 = st.columns(2)
    row1[0].metric("Answered", total_attempts())
    acc = current_accuracy()
    row1[1].metric("Accuracy", f"{acc:.0%}" if acc is not None else "—")
    row2 = st.columns(2)
    row2[0].metric("Streak", st.session_state.streak)
    row2[1].metric("Best", st.session_state.best_streak)

    goal_count, goal_target = daily_goal_progress()
    goal_pct = min(goal_count / goal_target, 1.0) if goal_target > 0 else 0.0
    st.markdown(f"**🎯 Session goal:** {min(goal_count, goal_target)} / {goal_target}")
    st.progress(goal_pct)

    st.divider()

    st.markdown("**Navigate**")
    if st.session_state.get("nav_choice") != st.session_state.current_page:
        st.session_state.nav_choice = st.session_state.current_page
    st.radio(
        "Page",
        _VALID_PAGES,
        key="nav_choice",
        on_change=_on_nav_change,
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("**🎚️ Difficulty**")
    st.radio(
        "Difficulty",
        ["Beginner", "Standard", "Challenge"],
        key="difficulty",
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("**📚 Chapters**")
    for chapter in CHAPTERS_LIST:
        emoji, _ = chapter_status(chapter.key)
        label = f"{emoji} Ch. {chapter.number}: {chapter.title}"
        if st.button(label, key=f"sidebar_ch_{chapter.key}", use_container_width=True):
            start_chapter(chapter.key)
            st.rerun()


# ============================================================
# Dashboard
# ============================================================

def _render_dashboard_styles():
    """Dashboard-only visual polish."""
    st.markdown(
        """
        <style>
            div.stButton > button[kind="primary"] {
                background-color: #0f766e;
                border-color: #0f766e;
                color: #ffffff;
            }
            div.stButton > button[kind="primary"]:hover {
                background-color: #115e59;
                border-color: #115e59;
                color: #ffffff;
            }
            .dashboard-strip {
                background: #f0fdfa;
                border-left: 3px solid #0f766e;
                border-radius: 6px;
                color: #134e4a;
                font-size: 0.9rem;
                margin-bottom: 1rem;
                padding: 0.55rem 0.85rem;
            }
            .dashboard-hero {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 1.05rem 1.1rem;
            }
            .dashboard-eyebrow {
                color: #475569;
                font-size: 0.74rem;
                font-weight: 750;
                letter-spacing: 0.08em;
                margin-bottom: 0.45rem;
                text-transform: uppercase;
            }
            .dashboard-hero h1 {
                color: #0f172a;
                font-size: 1.72rem;
                line-height: 1.2;
                margin: 0;
            }
            .dashboard-hero p {
                color: #475569;
                font-size: 0.98rem;
                line-height: 1.5;
                margin: 0.65rem 0 0;
                max-width: 52rem;
            }
            .dashboard-stat-grid {
                display: grid;
                gap: 0.55rem;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                margin-top: 0.9rem;
            }
            .dashboard-stat {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 0.65rem 0.75rem;
            }
            .dashboard-stat span {
                color: #64748b;
                display: block;
                font-size: 0.72rem;
                font-weight: 750;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }
            .dashboard-stat strong {
                color: #0f172a;
                display: block;
                font-size: 1rem;
                margin-top: 0.2rem;
            }
            .dashboard-card-body {
                min-height: 8.5rem;
                padding: 0.8rem 0.15rem 0.25rem;
            }
            .dashboard-card-kicker {
                color: #64748b;
                font-size: 0.72rem;
                font-weight: 750;
                letter-spacing: 0.06em;
                margin-bottom: 0.45rem;
                text-transform: uppercase;
            }
            .dashboard-card-title {
                color: #0f172a;
                font-size: 1.08rem;
                font-weight: 750;
                line-height: 1.25;
                margin-bottom: 0.45rem;
            }
            .dashboard-card-copy {
                color: #475569;
                font-size: 0.92rem;
                line-height: 1.45;
            }
            .curriculum-topics {
                color: #475569;
                font-size: 0.9rem;
                line-height: 1.5;
                margin-top: 0.45rem;
            }
            @media (max-width: 700px) {
                .dashboard-stat-grid {
                    grid-template-columns: 1fr;
                }
                .dashboard-hero h1 {
                    font-size: 1.45rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _section_label(text):
    """Small uppercase section label."""
    st.markdown(
        f'<p style="color:#475569; font-size:0.78rem; '
        f'text-transform:uppercase; letter-spacing:0.06em; '
        f'margin: 0 0 0.55rem; font-weight:750;">{text}</p>',
        unsafe_allow_html=True,
    )


def render_dashboard():
    """Training dashboard landing page."""
    _render_dashboard_styles()
    _render_announcement_strip()
    _render_hero()
    st.write("")
    _render_feature_highlights()
    st.write("")
    _render_action_cards()
    _render_review_expander()
    st.write("")
    _render_learning_path()


def _render_announcement_strip():
    """Thin notification banner. Context-aware."""
    if review_queue_size() > 0:
        message = "<strong>Review queue ready:</strong> Practice fresh problems from the calculation types you missed."
    else:
        message = "<strong>Coach Mode:</strong> missed answers route through a hint, retry, and solution walkthrough."

    st.markdown(
        f'<div class="dashboard-strip">{message}</div>',
        unsafe_allow_html=True,
    )


def _render_hero():
    """Compact dashboard hero."""
    queue_size = review_queue_size()
    attempts = total_attempts()
    acc = current_accuracy()
    accuracy_text = f"{acc:.0%}" if acc is not None else "Not started"
    st.markdown(
        f"""
        <div class="dashboard-hero">
            <div class="dashboard-eyebrow">Pharmacy technician math practice</div>
            <h1>DoseDrill</h1>
            <p>
                Daily calculation practice for dosage, reconstitution, dilutions,
                IV flow rates, parenteral nutrition, and medication label math.
            </p>
            <div class="dashboard-stat-grid">
                <div class="dashboard-stat">
                    <span>Session answered</span>
                    <strong>{attempts}</strong>
                </div>
                <div class="dashboard-stat">
                    <span>Session accuracy</span>
                    <strong>{accuracy_text}</strong>
                </div>
                <div class="dashboard-stat">
                    <span>Missed review</span>
                    <strong>{queue_size}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    b1, b2 = st.columns(2)
    with b1:
        if st.button(
            "Start Mixed Practice",
            key="hero_start_mixed",
            type="primary",
            use_container_width=True,
        ):
            start_mixed()
            st.rerun()
    with b2:
        review_label = (
            f"Review Missed Problems ({queue_size})"
            if queue_size > 0
            else "Review Missed Problems"
        )
        if st.button(
            review_label,
            key="hero_start_review",
            type="secondary",
            use_container_width=True,
            disabled=queue_size == 0,
        ):
            practice_from_review(0)
            st.rerun()


def _render_feature_highlights():
    """Three concrete training tools."""
    _section_label("Training tools")

    features = [
        ("Practice", "Mixed Dosage Practice",
         "Adaptive problems across the pharmacy math chapters, including dose, concentration, and IV calculations."),
        ("Coach", "Step-by-Step Coach Mode",
         "Missed answers prompt a hint, another attempt, and a structured solution walkthrough."),
        ("Review", "Missed Problem Review",
         "First-attempt misses are saved by calculation type so review stays targeted."),
    ]

    cols = st.columns(3, gap="medium")
    for col, (kicker, title, body) in zip(cols, features):
        with col:
            with st.container(border=True):
                st.markdown(
                    f'<div class="dashboard-card-body">'
                    f'<div class="dashboard-card-kicker">{kicker}</div>'
                    f'<div class="dashboard-card-title">{title}</div>'
                    f'<div class="dashboard-card-copy">{body}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


def _render_action_cards():
    """Side-by-side Recommended Focus + Timed Practice."""
    _section_label("Practice plan")
    col_focus, col_timed = st.columns(2, gap="medium")
    with col_focus:
        _render_focus_card()
    with col_timed:
        _render_timed_practice_card()


def _render_focus_card():
    """Dashboard training tool: recommended focus."""
    focus_key = recommended_focus_chapter()
    with st.container(border=True):
        st.markdown("### Recommended focus")
        if focus_key:
            ch = get_chapter(focus_key)
            _, status_label = chapter_status(focus_key)
            mastery = chapter_mastery(focus_key)
            st.caption("Lowest mastery score from attempted chapters.")
            st.markdown(f"**Ch. {ch.number} — {ch.title}**")
            st.markdown(f"{status_label}  •  Mastery: {mastery}")
            if st.button(
                "Practice this chapter",
                key="focus_card_practice",
                type="secondary",
                use_container_width=True,
            ):
                start_chapter(focus_key)
                st.rerun()
        elif total_attempts() == 0:
            st.caption("Complete a short mixed set so DoseDrill can identify a focus chapter.")
            st.write("")
            st.write("")
            if st.button(
                "Start Mixed Practice",
                key="focus_card_no_data",
                type="secondary",
                use_container_width=True,
            ):
                start_mixed()
                st.rerun()
        else:
            st.caption("No clear weak chapter yet. Mixed practice will continue sampling across topics.")
            st.write("")
            st.write("")
            if st.button(
                "Start Mixed Practice",
                key="focus_card_all_mastered",
                type="secondary",
                use_container_width=True,
            ):
                start_mixed()
                st.rerun()


def _render_timed_practice_card():
    """Dashboard training tool: timed drills."""
    with st.container(border=True):
        st.markdown("### Timed drills")
        st.caption("Short mixed sets for speed and accuracy under a clock.")
        # Two blank lines roughly match the visual height of _render_focus_card
        # so the practice plan row keeps its parity across states.
        st.write("")
        st.write("")
        if st.button(
            "Choose timed drill",
            key="timed_card_start",
            type="secondary",
            use_container_width=True,
        ):
            st.session_state.timed_setup_open = True
            st.rerun()


def _render_review_expander():
    """Compact per-item queue list. Renders only when queue is non-empty."""
    queue_size = review_queue_size()
    if queue_size == 0:
        return

    with st.expander(f"Missed problem queue ({queue_size})"):
        st.caption(
            "Each row starts a fresh problem from the same calculation type."
        )
        for i, entry in enumerate(st.session_state.review_queue):
            ch = get_chapter(entry["chapter_key"])
            c_text, c_btn = st.columns([5, 1])
            with c_text:
                st.markdown(
                    f"**Ch. {ch.number}.** {ch.title}  \n"
                    f"_{entry['question_preview']}_"
                )
            with c_btn:
                st.write("")
                if st.button(
                    "Practice",
                    key=f"review_expander_{i}",
                    use_container_width=True,
                ):
                    practice_from_review(i)
                    st.rerun()
        st.write("")
        if st.button("Clear review queue", key="review_expander_clear"):
            clear_review_queue()
            st.rerun()


def _render_learning_path():
    """Compact curriculum preview."""
    _section_label("Curriculum map")

    tiers = [
        ("Ch. 1-4", "Foundation calculations",
         "Parenteral doses · Powdered drugs · Percents · Ratio-strength solutions"),
        ("Ch. 5-7", "Patient-based dosing",
         "Body weight · Body surface area · Infusion and drip rates"),
        ("Ch. 8-10", "Advanced pharmacy math",
         "Dilutions · Parenteral nutrition · Medication labels"),
    ]

    cols = st.columns(3, gap="medium")
    for col, (ch_range, tier_name, topics) in zip(cols, tiers):
        with col:
            with st.container(border=True):
                st.markdown(
                    f'<div class="dashboard-card-body">'
                    f'<div class="dashboard-card-kicker">{ch_range}</div>'
                    f'<div class="dashboard-card-title">{tier_name}</div>'
                    f'<div class="curriculum-topics">{topics}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ============================================================
# Timed Practice setup (NEW)
# ============================================================

def render_timed_setup():
    """Sprint-type picker overlay. Reached by clicking 'Start Timed Practice'
    on the dashboard card. Shows the four sprint options as rows with a
    brief description each, plus a Back-to-Dashboard button at the top.

    Clicking any sprint button calls start_timed_sprint, which sets up the
    timed_* state and routes the user to the Practice page. Clicking Back
    closes the overlay without starting a sprint.

    This view is NOT a member of _VALID_PAGES. It's an overlay driven by
    timed_setup_open, so the page nav radio still shows 'Dashboard' while
    the user is choosing a sprint.
    """
    back_col, title_col = st.columns([1, 5])
    with back_col:
        if st.button(
            "← Back to Dashboard",
            key="ts_setup_back",
            use_container_width=True,
        ):
            st.session_state.timed_setup_open = False
            st.session_state.current_page = "Dashboard"
            st.rerun()
    with title_col:
        st.markdown("### ⏱  Timed Practice")
        st.caption("Pick a sprint type to get started.")

    st.write("")

    sprints = [
        ("5q", "5-question sprint",
         "Short adaptive set, no clock. Answer five and see how you did."),
        ("10q", "10-question sprint",
         "A longer set for a more representative score."),
        ("2min", "2-minute sprint",
         "Race against the clock. Answer as many as you can in two minutes."),
        ("5min", "5-minute sprint",
         "Same drill, with five minutes on the clock."),
    ]

    for key, label, desc in sprints:
        with st.container(border=True):
            c_label, c_btn = st.columns([3, 1])
            with c_label:
                st.markdown(f"**{label}**")
                st.caption(desc)
            with c_btn:
                st.write("")
                if st.button(
                    "Start →",
                    key=f"setup_{key}",
                    type="primary",
                    use_container_width=True,
                ):
                    start_timed_sprint(key)
                    st.rerun()


# ============================================================
# Practice
# ============================================================

_VALUE_TOKEN_RE = re.compile(
    r"\b\d[\d,]*(?:\.\d+)?(?:\s*(?:"
    r"mg/kg|mg/mL|mcg/mL|units/mL|mEq/mL|gtt/min|mL/hr|"
    r"mg|mcg|g|mL|L|kg|lb|pounds?|units?|mEq|hours?|hrs?|"
    r"minutes?|mins?|min|%))?",
    re.IGNORECASE,
)


def _html(text):
    """Escape generated problem text before rendering custom markup."""
    return html.escape(str(text), quote=True)


def _highlight_problem_values(text):
    """Emphasize numbers and units in the prompt without changing the problem."""
    escaped = _html(text)
    return _VALUE_TOKEN_RE.sub(
        lambda match: f'<span class="practice-value">{match.group(0)}</span>',
        escaped,
    )


def _render_practice_styles():
    """Practice-only visual system."""
    st.markdown(
        """
        <style>
            .practice-eyebrow {
                color: #64748b;
                font-size: 0.74rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                margin: 0 0 0.45rem;
                text-transform: uppercase;
            }
            .practice-header {
                border-bottom: 1px solid #e2e8f0;
                margin-bottom: 1.1rem;
                padding-bottom: 0.95rem;
            }
            .practice-header h2 {
                color: #111827;
                font-size: 1.45rem;
                line-height: 1.25;
                margin: 0;
            }
            .practice-header p {
                color: #64748b;
                font-size: 0.94rem;
                margin: 0.35rem 0 0;
            }
            .practice-meta-grid {
                display: grid;
                gap: 0.6rem;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                margin-bottom: 1rem;
            }
            .practice-meta-item {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 0.7rem 0.8rem;
            }
            .practice-meta-label {
                color: #64748b;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.06em;
                margin-bottom: 0.22rem;
                text-transform: uppercase;
            }
            .practice-meta-value {
                color: #0f172a;
                font-size: 0.9rem;
                font-weight: 650;
                line-height: 1.35;
            }
            .practice-prompt {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-left: 4px solid #0f766e;
                border-radius: 6px;
                margin: 0.35rem 0 0.85rem;
                padding: 1rem 1.05rem;
            }
            .practice-prompt-label {
                color: #475569;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.06em;
                margin-bottom: 0.45rem;
                text-transform: uppercase;
            }
            .practice-question {
                color: #111827;
                font-size: 1.22rem;
                font-weight: 650;
                line-height: 1.55;
            }
            .practice-value {
                background: #ecfdf5;
                border: 1px solid #a7f3d0;
                border-radius: 4px;
                color: #064e3b;
                display: inline-block;
                font-weight: 750;
                padding: 0 0.22rem;
            }
            .practice-target {
                align-items: center;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                display: flex;
                justify-content: space-between;
                gap: 0.75rem;
                margin-bottom: 1rem;
                padding: 0.75rem 0.85rem;
            }
            .practice-target span {
                color: #64748b;
                display: block;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }
            .practice-target strong {
                color: #0f172a;
                display: block;
                font-size: 1rem;
                margin-top: 0.12rem;
            }
            .practice-unit-badge {
                background: #0f766e;
                border-radius: 999px;
                color: #ffffff;
                font-size: 0.92rem;
                font-weight: 750;
                min-width: 4.5rem;
                padding: 0.35rem 0.7rem;
                text-align: center;
            }
            .practice-tool-label {
                color: #475569;
                font-size: 0.82rem;
                font-weight: 700;
                margin: 0.25rem 0 0.45rem;
            }
            .practice-panel {
                background: #f8fafc;
                border: 1px solid #dbe4ee;
                border-radius: 6px;
                margin: 0.75rem 0;
                padding: 0.9rem 1rem;
            }
            .practice-panel-title {
                color: #0f172a;
                font-size: 0.95rem;
                font-weight: 750;
                margin-bottom: 0.35rem;
            }
            .practice-panel-body {
                color: #334155;
                font-size: 0.94rem;
                line-height: 1.55;
            }
            .practice-answer-shell {
                border-top: 1px solid #e2e8f0;
                margin-top: 1.1rem;
                padding-top: 1rem;
            }
            .practice-feedback {
                border-radius: 6px;
                margin: 0.15rem 0 0.9rem;
                padding: 0.85rem 1rem;
            }
            .practice-feedback-title {
                font-weight: 750;
                margin-bottom: 0.2rem;
            }
            .practice-feedback-body {
                line-height: 1.5;
            }
            .practice-feedback.correct {
                background: #f0fdf4;
                border: 1px solid #bbf7d0;
                color: #14532d;
            }
            .practice-feedback.coach {
                background: #fffbeb;
                border: 1px solid #fde68a;
                color: #713f12;
            }
            .practice-feedback.review {
                background: #fff7ed;
                border: 1px solid #fed7aa;
                color: #7c2d12;
            }
            .solution-list {
                color: #1f2937;
                line-height: 1.55;
                margin: 0.25rem 0 0;
                padding-left: 1.25rem;
            }
            .solution-list li {
                margin: 0.45rem 0;
                padding-left: 0.15rem;
            }
            @media (max-width: 700px) {
                .practice-meta-grid {
                    grid-template-columns: 1fr;
                }
                .practice-target {
                    align-items: flex-start;
                    flex-direction: column;
                }
                .practice-question {
                    font-size: 1.08rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_practice_header(chapter):
    if st.session_state.mixed_mode:
        title = "Mixed practice"
        subtitle = f"Current chapter: Ch. {chapter.number} - {chapter.title}"
    else:
        title = f"Ch. {chapter.number}. {chapter.title}"
        subtitle = chapter.summary

    st.markdown(
        f"""
        <div class="practice-header">
            <div class="practice-eyebrow">Practice worksheet</div>
            <h2>{_html(title)}</h2>
            <p>{_html(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_problem_metadata(chapter, problem):
    difficulty = st.session_state.get("difficulty", "Standard")
    mode = "Mixed adaptive" if st.session_state.mixed_mode else "Chapter focus"

    st.markdown(
        f"""
        <div class="practice-meta-grid">
            <div class="practice-meta-item">
                <div class="practice-meta-label">Chapter</div>
                <div class="practice-meta-value">Ch. {chapter.number}: {_html(chapter.title)}</div>
            </div>
            <div class="practice-meta-item">
                <div class="practice-meta-label">Calculation type</div>
                <div class="practice-meta-value">{_html(problem["problem_type_label"])}</div>
            </div>
            <div class="practice-meta-item">
                <div class="practice-meta-label">Mode / difficulty</div>
                <div class="practice-meta-value">{_html(mode)} - {_html(difficulty)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_problem_prompt(problem):
    st.markdown(
        f"""
        <div class="practice-prompt">
            <div class="practice-prompt-label">Calculation prompt</div>
            <div class="practice-question">{_highlight_problem_values(problem["question"])}</div>
        </div>
        <div class="practice-target">
            <div>
                <span>Target answer</span>
                <strong>Enter a numeric value using the required unit.</strong>
            </div>
            <div class="practice-unit-badge">{_html(problem["unit"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_panel(title, body):
    st.markdown(
        f"""
        <div class="practice-panel">
            <div class="practice-panel-title">{_html(title)}</div>
            <div class="practice-panel-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_feedback(kind, title, body):
    st.markdown(
        f"""
        <div class="practice-feedback {kind}">
            <div class="practice-feedback-title">{_html(title)}</div>
            <div class="practice-feedback-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_solution_steps(steps):
    items = "".join(f"<li>{_html(step)}</li>" for step in steps)
    st.markdown(f'<ol class="solution-list">{items}</ol>', unsafe_allow_html=True)

def render_practice_view():
    """Practice page entry point."""
    if st.session_state.timed_mode:
        if st.session_state.timed_target_seconds is not None:
            elapsed = time.time() - st.session_state.timed_started_at
            if elapsed >= st.session_state.timed_target_seconds:
                render_timed_summary()
                return
        if (
            st.session_state.timed_target_questions is not None
            and st.session_state.timed_answered >= st.session_state.timed_target_questions
            and st.session_state.current_problem is None
        ):
            render_timed_summary()
            return

    if (
        st.session_state.selected_chapter_key is None
        and not st.session_state.mixed_mode
    ):
        render_practice_empty_state()
        return

    if st.session_state.current_problem is None:
        new_problem()

    if st.session_state.timed_mode:
        _render_timed_status_bar()

    problem = st.session_state.current_problem
    chapter = get_chapter(problem["chapter_key"])
    _render_practice_styles()

    top_back, top_title = st.columns([1, 5])
    with top_back:
        if st.button("← Dashboard", use_container_width=True):
            go_to_dashboard()
            st.rerun()
    with top_title:
        _render_practice_header(chapter)

    st.write("")
    render_problem_card(chapter, problem)

    result = st.session_state.last_result
    if (
        result is not None
        and not result["correct"]
        and st.session_state.problem_phase == "revealed"
        and chapter.prerequisite_chapter
    ):
        st.write("")
        render_work_it_out(chapter)


def _timed_status_bar_body():
    """Render the active-sprint status strip.

    Reads elapsed/remaining from time.time() and timed_started_at on each
    invocation — no counter to drift. Wrapped below with
    st.fragment(run_every="1s") so this body re-renders every second
    without rerunning the rest of the app.

    For time-based sprints (2-minute / 5-minute), when elapsed crosses the
    target this function triggers a full app rerun. render_practice_view's
    top-level check then detects the expiry and routes to render_timed_summary.

    Defensive early-returns guard against stale-state renders during the
    transition frames where timed_mode is being flipped off.
    """
    if not st.session_state.get("timed_mode", False):
        return

    started_at = st.session_state.timed_started_at
    if started_at is None:
        return

    timed_type = st.session_state.timed_type
    answered = st.session_state.timed_answered
    correct = st.session_state.timed_correct
    target_q = st.session_state.timed_target_questions
    target_s = st.session_state.timed_target_seconds

    cfg = _TIMED_CONFIGS.get(timed_type, {"label": "Timed sprint"})
    mode_label = cfg["label"]

    elapsed = time.time() - started_at
    accuracy = (correct / answered) if answered > 0 else 0.0
    accuracy_text = f"Accuracy: {accuracy:.0%}" if answered > 0 else "Accuracy: —"

    if target_q:
        # Question-based: show elapsed time. No auto-end on time.
        progress_text = f"Question {min(answered + 1, target_q)} of {target_q}"
        em, es = int(elapsed // 60), int(elapsed % 60)
        time_text = f"Elapsed {em}:{es:02d}"
        time_expired = False
    else:
        # Time-based: show remaining time. Auto-end when elapsed >= target.
        progress_text = f"Answered: {answered}"
        remaining = max(0, int(target_s - elapsed))
        rm, rs = remaining // 60, remaining % 60
        time_text = f"Remaining {rm}:{rs:02d}"
        time_expired = elapsed >= target_s

    st.markdown(
        f'<div style="background-color: rgba(245, 158, 11, 0.10); '
        f'padding: 0.55rem 0.95rem; border-radius: 6px; '
        f'border-left: 4px solid #f59e0b; margin-bottom: 1rem; '
        f'display: flex; align-items: center; justify-content: space-between; '
        f'flex-wrap: wrap; gap: 0.75rem;">'
        f'<div style="font-size: 0.92rem;">'
        f'<strong>Timed sprint: {mode_label}</strong> &nbsp;·&nbsp; {progress_text} &nbsp;·&nbsp; {accuracy_text}'
        f'</div>'
        f'<div style="font-family: ui-monospace, SFMono-Regular, Menlo, monospace; '
        f'font-size: 1rem; font-weight: 600;">'
        f'{time_text}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Auto-end on time-up: trigger a full app rerun so the page-routing
    # logic in render_practice_view can detect the expiry and switch to
    # the summary view. scope="app" is required to escape the fragment;
    # falls back to plain st.rerun() on older Streamlit (<1.37).
    if time_expired:
        try:
            st.rerun(scope="app")
        except TypeError:
            st.rerun()


# Apply st.fragment(run_every="1s") if the API is available so the status
# bar auto-refreshes every second WITHOUT rerunning the rest of the app.
# Streamlit 1.37+ exposes st.fragment; 1.33-1.36 had it as
# st.experimental_fragment. Older Streamlit has neither — in that case we
# bind the body directly and the bar updates only on user interaction
# (same behavior as before this fix, no regression).
_fragment_factory = (
    getattr(st, "fragment", None)
    or getattr(st, "experimental_fragment", None)
)

if _fragment_factory is not None:
    _render_timed_status_bar = _fragment_factory(run_every="1s")(_timed_status_bar_body)
else:
    _render_timed_status_bar = _timed_status_bar_body


def render_timed_summary():
    """Post-sprint summary."""
    timed_type = st.session_state.timed_type
    answered = st.session_state.timed_answered
    correct = st.session_state.timed_correct
    started_at = st.session_state.timed_started_at
    target_s = st.session_state.timed_target_seconds

    cfg = _TIMED_CONFIGS.get(timed_type, {"label": "Timed sprint"})
    mode_label = cfg["label"]

    elapsed = time.time() - started_at if started_at else 0.0
    if target_s is not None:
        elapsed = min(elapsed, float(target_s))

    accuracy = (correct / answered) if answered > 0 else 0.0
    avg_time = (elapsed / answered) if answered > 0 else 0.0

    _render_practice_styles()
    st.markdown("### Sprint complete")
    st.caption(mode_label)
    st.write("")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Answered", answered)
    m2.metric("Correct", f"{correct} of {answered}" if answered else "—")
    m3.metric("Accuracy", f"{accuracy:.0%}" if answered else "—")
    m4.metric("Avg time/Q", f"{avg_time:.1f}s" if answered else "—")

    st.write("")

    focus_key = recommended_focus_chapter()
    if focus_key:
        focus_ch = get_chapter(focus_key)
        focus_mastery = chapter_mastery(focus_key)
        st.info(
            f"**Recommended focus:** Ch. {focus_ch.number} — {focus_ch.title} "
            f"(Mastery {focus_mastery}). Practicing here may strengthen the "
            "area you missed most."
        )
        st.write("")

    b1, b2 = st.columns(2)
    with b1:
        if st.button(
            "← Return to Dashboard",
            key="ts_return",
            use_container_width=True,
        ):
            _clear_timed_state()
            go_to_dashboard()
            st.rerun()
    with b2:
        if st.button(
            "Start another sprint →",
            key="ts_again",
            type="primary",
            use_container_width=True,
        ):
            same_type = st.session_state.timed_type
            _clear_timed_state()
            if same_type is not None:
                start_timed_sprint(same_type)
            else:
                go_to_dashboard()
            st.rerun()


def render_practice_empty_state():
    """Practice page when no chapter is active. UNCHANGED."""
    st.title("Practice")
    st.caption("Pick a chapter from the sidebar, or use the quick-start options below.")
    st.write("")

    queue_size = review_queue_size()
    if queue_size > 0:
        c1, c2 = st.columns(2)
        with c1:
            if st.button(
                "🎯 Start Mixed Practice",
                key="practice_empty_mixed",
                type="primary",
                use_container_width=True,
            ):
                start_mixed()
                st.rerun()
        with c2:
            if st.button(
                f"🔁 Review Missed Problems ({queue_size})",
                key="practice_empty_review",
                type="primary",
                use_container_width=True,
            ):
                practice_from_review(0)
                st.rerun()
    else:
        with st.container(border=True):
            c_text, c_btn = st.columns([4, 1])
            with c_text:
                st.markdown("### 🎯  Mixed practice")
                st.caption("Adaptive across all ten chapters.")
            with c_btn:
                st.write("")
                if st.button(
                    "Start",
                    key="practice_empty_mixed_solo",
                    type="primary",
                    use_container_width=True,
                ):
                    start_mixed()
                    st.rerun()

    st.divider()

    focus_key = recommended_focus_chapter()
    if focus_key:
        focus_chapter = get_chapter(focus_key)
        focus_emoji, focus_status_label = chapter_status(focus_key)
        focus_mastery = chapter_mastery(focus_key)
        with st.container(border=True):
            st.markdown("### ⭐  Recommended focus")
            st.caption("Your weakest attempted chapter.")
            st.markdown(f"**Ch. {focus_chapter.number} — {focus_chapter.title}**")
            st.markdown(f"{focus_emoji} {focus_status_label}  •  Mastery: {focus_mastery}")
            if st.button(
                "Practice this →",
                key="practice_empty_focus_practice",
                type="primary",
                use_container_width=True,
            ):
                start_chapter(focus_key)
                st.rerun()

    st.subheader("Mastery by chapter")
    for chapter in CHAPTERS_LIST:
        mastery = chapter_mastery(chapter.key)
        emoji, status_label = chapter_status(chapter.key)
        attempts = st.session_state.stats[chapter.key]["_overall"]["attempts"]

        c_label, c_bar, c_btn = st.columns([4, 4, 1])
        with c_label:
            st.markdown(f"{emoji} **Ch. {chapter.number}.** {chapter.title}")
            if attempts == 0:
                st.caption(status_label)
            else:
                st.caption(f"{status_label}  •  Mastery: {mastery}  •  {attempts} attempts")
        with c_bar:
            st.write("")
            st.progress(mastery / 100)
        with c_btn:
            st.write("")
            if st.button("Practice", key=f"practice_empty_practice_{chapter.key}", use_container_width=True):
                start_chapter(chapter.key)
                st.rerun()

    st.subheader("Accuracy by chapter")
    for chapter in CHAPTERS_LIST:
        overall = st.session_state.stats[chapter.key]["_overall"]
        header = f"**Ch. {chapter.number}. {chapter.title}**"
        if overall["attempts"] == 0:
            st.write(f"{header} — not attempted yet")
            continue
        accuracy = overall["correct"] / overall["attempts"]
        st.write(
            f"{header} — {overall['correct']}/{overall['attempts']} correct ({accuracy:.0%})"
        )
        st.progress(accuracy)
        with st.expander("Breakdown by problem type"):
            for pt in chapter.problem_types:
                s = st.session_state.stats[chapter.key][pt.key]
                if s["attempts"] == 0:
                    st.write(f"  • {pt.label}: not attempted")
                else:
                    pt_acc = s["correct"] / s["attempts"]
                    st.write(
                        f"  • {pt.label}: {s['correct']}/{s['attempts']} ({pt_acc:.0%})"
                    )

    weak = get_weak_chapters()
    if weak:
        st.subheader("Chapters to focus on")
        for chapter_key, accuracy in weak:
            chapter = CHAPTERS[chapter_key]
            st.write(
                f"• Ch. {chapter.number}. {chapter.title} — {accuracy:.0%} accuracy"
            )
    else:
        st.caption(
            "Attempt at least 3 problems in a chapter to see weak-chapter recommendations."
        )


def render_problem_card(chapter, problem):
    """Render the active practice problem as a focused worksheet."""
    with st.container(border=True):
        _render_problem_metadata(chapter, problem)

        if not st.session_state.mixed_mode:
            st.markdown('<div class="practice-tool-label">Skill focus</div>', unsafe_allow_html=True)
            render_skill_picker(chapter)

        _render_problem_prompt(problem)
        render_helper_buttons(chapter, problem)
        render_helper_content(chapter, problem)

        st.markdown(
            '<div class="practice-answer-shell">'
            '<div class="practice-tool-label">Your response</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        phase = st.session_state.problem_phase
        if phase == "answering":
            render_answer_input(problem)
        elif phase == "first_wrong":
            render_coach_intervention(problem)
        else:
            render_revealed_result()


def render_answer_input(problem):
    """Collect the student's numeric answer without changing scoring logic."""
    entry_col, unit_col = st.columns([3, 1])
    with entry_col:
        user_answer = st.number_input(
            "Numeric answer",
            value=0.0,
            step=0.1,
            format="%.2f",
            key=f"answer_input_{st.session_state.input_version}",
        )
    with unit_col:
        st.markdown(
            f"""
            <div class="practice-meta-item">
                <div class="practice-meta-label">Required unit</div>
                <div class="practice-meta-value">{_html(problem["unit"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("Check answer", type="primary", use_container_width=True):
        check_answer(problem, user_answer)
        st.rerun()


def render_coach_intervention(problem):
    """Offer the same first-wrong coach choices with calmer feedback."""
    result = st.session_state.last_result
    _render_feedback(
        "coach",
        "Review before submitting again",
        (
            f"You entered <strong>{_html(result['user_answer'])} "
            f"{_html(result['unit'])}</strong>. Check the setup, unit conversion, "
            "and final unit before your next attempt."
        ),
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(
            "Use hint",
            type="secondary",
            use_container_width=True,
            key="coach_hint",
        ):
            coach_retry(open_hint=True)
            st.rerun()
    with c2:
        if st.button(
            "Try again",
            type="primary",
            use_container_width=True,
            key="coach_retry",
        ):
            coach_retry(open_hint=False)
            st.rerun()
    with c3:
        if st.button(
            "Show solution",
            type="secondary",
            use_container_width=True,
            key="coach_show",
        ):
            coach_reveal()
            st.rerun()


def render_revealed_result():
    """Show instructional feedback and preserve sprint-end branching."""
    result = st.session_state.last_result
    attempt_number = result.get("attempt_number", 1)

    if result["correct"] and attempt_number == 1:
        _render_feedback(
            "correct",
            "Correct",
            (
                f"Your answer was <strong>{_html(result['user_answer'])} "
                f"{_html(result['unit'])}</strong>. Keep the same setup discipline "
                "on the next calculation."
            ),
        )
    elif result["correct"] and attempt_number > 1:
        _render_feedback(
            "correct",
            "Correct on retry",
            (
                "Good correction. This retry does not change your streak, "
                "but it reinforces the calculation path."
            ),
        )
    else:
        _render_feedback(
            "review",
            "Review this calculation",
            (
                f"Expected result: <strong>{_html(result['correct_answer'])} "
                f"{_html(result['unit'])}</strong>. Compare your setup with the "
                "walkthrough before moving on."
            ),
        )

    with st.expander("Solution walkthrough", expanded=not result["correct"]):
        _render_solution_steps(result["steps"])

    if st.button("Next problem", type="primary", use_container_width=True):
        if (
            st.session_state.timed_mode
            and st.session_state.timed_target_questions is not None
            and st.session_state.timed_answered >= st.session_state.timed_target_questions
        ):
            st.session_state.current_problem = None
            st.rerun()
        else:
            new_problem()
            st.rerun()


def render_skill_picker(chapter):
    """UNCHANGED."""
    options = [("_adaptive", "Adaptive")] + [(pt.key, pt.label) for pt in chapter.problem_types]
    keys = [k for k, _ in options]
    labels = [lbl for _, lbl in options]

    current = st.session_state.problem_type_choice
    if current not in keys:
        current = "_adaptive"
        st.session_state.problem_type_choice = current

    picked_label = st.radio(
        "Skill",
        labels,
        index=keys.index(current),
        horizontal=True,
        label_visibility="collapsed",
        key=f"skill_radio_{chapter.key}",
    )
    picked_key = keys[labels.index(picked_label)]
    if picked_key != current:
        st.session_state.problem_type_choice = picked_key
        new_problem()
        st.rerun()


def render_helper_buttons(chapter, problem):
    """Render worksheet support tools as secondary actions."""
    st.markdown('<div class="practice-tool-label">Calculation support</div>', unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    with b1:
        ex_label = "Hide example" if st.session_state.show_example else "Worked example"
        if st.button(
            ex_label,
            type="secondary",
            use_container_width=True,
            key="btn_example",
        ):
            st.session_state.show_example = not st.session_state.show_example
            if st.session_state.show_example and st.session_state.example_problem is None:
                pt = get_problem_type(problem["chapter_key"], problem["problem_type_key"])
                st.session_state.example_problem = pt.generator()
            st.rerun()
    with b2:
        fm_label = "Hide formula" if st.session_state.show_formula else "Formula setup"
        if st.button(
            fm_label,
            type="secondary",
            use_container_width=True,
            key="btn_formula",
        ):
            st.session_state.show_formula = not st.session_state.show_formula
            st.rerun()
    with b3:
        hint_label = "Hide hint" if st.session_state.show_hint else "Hint"
        if st.button(
            hint_label,
            type="secondary",
            use_container_width=True,
            key="btn_hint",
        ):
            st.session_state.show_hint = not st.session_state.show_hint
            st.rerun()


def render_helper_content(chapter, problem):
    """Render formula, hint, and example as learning panels."""
    if st.session_state.show_formula:
        formula_body = _html(chapter.formula).replace("\n", "<br>")
        _render_panel("Formula / setup", formula_body)

    if st.session_state.show_hint:
        first_steps = problem["steps"][:2]
        body = "<br><br>".join(_html(step) for step in first_steps)
        _render_panel("Hint: first setup steps", body)

    if st.session_state.show_example and st.session_state.example_problem:
        ex = st.session_state.example_problem
        steps = "".join(f"<li>{_html(step)}</li>" for step in ex["steps"])
        st.markdown(
            f"""
            <div class="practice-panel">
                <div class="practice-panel-title">Worked example: same calculation type</div>
                <div class="practice-panel-body">
                    <strong>Question:</strong> {_html(ex["question"])}
                    <ol class="solution-list">{steps}</ol>
                    <strong>Answer:</strong> {_html(ex["answer"])} {_html(ex["unit"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_work_it_out(chapter):
    """Suggest a prerequisite chapter without changing practice routing."""
    prereq = get_chapter(chapter.prerequisite_chapter)
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="practice-panel-title">Foundation review</div>
            <div class="practice-panel-body">
                This topic builds on <strong>Ch. {prereq.number}: {_html(prereq.title)}</strong>.
                A short review set can help confirm the setup before returning here.
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            f"Practice Ch. {prereq.number} first",
            key="prereq_jump",
            use_container_width=True,
        ):
            start_chapter(prereq.key)
            st.rerun()


# ============================================================
# Page routing
# ============================================================

# NEW: timed setup overlay takes precedence. When timed_setup_open is True,
# render the picker overlay instead of the normal current_page routing.
if st.session_state.timed_setup_open:
    render_timed_setup()
else:
    page = st.session_state.current_page

    if page == "Dashboard":
        render_dashboard()

    elif page == "Practice":
        render_practice_view()

    elif page == "Calculator":
        st.title("Calculator")
        st.caption("Quick reference. Results here are not tracked in practice stats.")
        dose = st.number_input("Ordered dose (mg)", min_value=0.0, value=500.0, step=10.0)
        strength = st.number_input(
            "Stock strength (mg per mL)", min_value=0.01, value=250.0, step=10.0
        )
        volume = dose / strength
        st.write(f"Volume needed: **{volume:.2f} mL**")
        st.caption(
            f"Formula: volume = dose / strength = {dose} / {strength} = {volume:.2f} mL."
        )
