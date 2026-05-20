"""
DoseDrill — v8 (centered command-center layout, pill tabs, action card).

Top region (always visible):
    Hero card     : bordered, bigger title, new tagline, byline, and the
                    four stat chips right-aligned in the same card.
    Pill tab nav  : three buttons styled as pill tabs (active = primary
                    coral, inactive = outline). Difficulty radio to the
                    right of the tabs.

Dashboard sections:
    1. Main action card   "Ready to practice?" with three primary CTAs
                          (Start Mixed Practice / Timed Sprint / Review
                          Missed) and a tinted checklist box at the bottom
                          with three dynamic session goals.
    2. Today's focus      Two cards side-by-side: Recommended Focus on the
                          left, Timed Practice (grouped Question-based /
                          Time-based) on the right. Optional review-queue
                          expander appears below when the queue has items.
    3. Study report       Single full-width card with locked/unlocked
                          states. Markdown download via st.download_button.
    4. Learning path      Three compact tier cards. Lower visual weight.
    5. Browse chapters    Collapsed expander at the bottom for direct
                          chapter access. The Practice empty state still
                          has chapter access via its mastery list.

Practice and Calculator pages unchanged from v7.

Layout notes:
    The whole UI sits inside a centered ~1180px max-width container set
    via CSS. All buttons get border-radius: 999px so primary CTAs and pill
    tabs share a unified visual language. The sidebar is hidden entirely.

Run with:
    streamlit run app.py
"""

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
    initial_sidebar_state="collapsed",
)

# Global styles. The .block-container max-width is what gives the whole
# app its centered, focused feel rather than the default Streamlit wide
# stretch. Pill-shaped buttons unify primary CTAs and the page-nav tabs.
st.markdown(
    """
    <style>
    /* Hide the sidebar entirely; v8 uses a top command-center layout. */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }

    /* Centered max-width container. This is the single biggest lever for
       making DoseDrill feel like a focused practice platform rather than
       a generic wide-layout Streamlit page. */
    .main .block-container {
        max-width: 1180px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        margin: 0 auto !important;
    }

    /* Pill-shaped buttons everywhere. Unifies the pill-tab nav with the
       primary CTAs and gives the dashboard a polished, study-platform
       feel rather than the default rectangular Streamlit look. */
    .stButton > button,
    .stDownloadButton > button {
        border-radius: 999px !important;
        font-weight: 500 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

init_tracker()

# Valid pages. No more Progress; that content lives on Practice's empty state.
_VALID_PAGES = ["Dashboard", "Practice", "Calculator"]

if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"
if st.session_state.current_page not in _VALID_PAGES:
    st.session_state.current_page = "Dashboard"


# ============================================================
# Core actions (preserved from v7)
# ============================================================

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

    # Timed mode: record when this problem was shown for per-question timing.
    if st.session_state.timed_session is not None:
        st.session_state.timed_session["question_start"] = time.time()


def go_to_dashboard():
    """Clear practice state and return to the dashboard. Also clears any
    active timed sprint so navigating away ends the sprint cleanly."""
    st.session_state.selected_chapter_key = None
    st.session_state.mixed_mode = False
    st.session_state.current_problem = None
    st.session_state.last_result = None
    st.session_state.problem_type_choice = "_adaptive"
    st.session_state.timed_session = None
    st.session_state.current_page = "Dashboard"
    reset_helpers()


def start_chapter(chapter_key, problem_type_key="_adaptive"):
    """Enter untimed chapter practice and route to Practice."""
    st.session_state.selected_chapter_key = chapter_key
    st.session_state.mixed_mode = False
    st.session_state.problem_type_choice = problem_type_key
    st.session_state.timed_session = None
    st.session_state.current_page = "Practice"
    new_problem()


def start_mixed():
    """Enter untimed mixed-practice mode and route to Practice."""
    st.session_state.mixed_mode = True
    st.session_state.selected_chapter_key = None
    st.session_state.problem_type_choice = "_adaptive"
    st.session_state.timed_session = None
    st.session_state.current_page = "Practice"
    new_problem()


def practice_from_review(index):
    """Pop the entry at index and start a fresh problem of that type."""
    entry = pop_review_queue_at(index)
    if entry:
        start_chapter(entry["chapter_key"], entry["problem_type_key"])


def check_answer(problem, user_answer):
    """Verify the answer and drive the coach state machine."""
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
                correct_answer=problem["answer"],
                unit=problem["unit"],
                explanation_steps=problem["steps"][:3],
            )

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
# Timed practice (preserved from v7)
# ============================================================

_TIMED_MODES = {
    "5q":   {"label": "5-question sprint",  "target_questions": 5,  "target_seconds": None},
    "10q":  {"label": "10-question sprint", "target_questions": 10, "target_seconds": None},
    "2min": {"label": "2-minute sprint",    "target_questions": None, "target_seconds": 120},
    "5min": {"label": "5-minute sprint",    "target_questions": None, "target_seconds": 300},
}


def start_timed_sprint(mode):
    """Begin a timed sprint in adaptive mixed mode."""
    cfg = _TIMED_MODES.get(mode)
    if cfg is None:
        return

    now = time.time()
    st.session_state.timed_session = {
        "mode": mode,
        "target_questions": cfg["target_questions"],
        "target_seconds": cfg["target_seconds"],
        "started_at": now,
        "answered": 0,
        "correct": 0,
        "question_start": now,
        "per_question_seconds": [],
        "completed": False,
        "end_reason": None,
    }

    st.session_state.mixed_mode = True
    st.session_state.selected_chapter_key = None
    st.session_state.problem_type_choice = "_adaptive"
    st.session_state.current_page = "Practice"
    new_problem()


def end_timed_sprint(reason):
    """Mark the active sprint as completed with the given reason."""
    if st.session_state.timed_session is None:
        return
    st.session_state.timed_session["completed"] = True
    st.session_state.timed_session["end_reason"] = reason


def _maybe_finalize_timed_question():
    """Record the just-completed question into sprint stats and end the
    sprint if the question target has been reached."""
    ts = st.session_state.timed_session
    if ts is None or ts["completed"]:
        return

    result = st.session_state.last_result
    if result is None:
        return

    elapsed = time.time() - ts["question_start"]
    ts["per_question_seconds"].append(elapsed)
    ts["answered"] += 1
    if result["correct"] and result["attempt_number"] == 1:
        ts["correct"] += 1

    if ts["target_questions"] and ts["answered"] >= ts["target_questions"]:
        end_timed_sprint("target")
        return

    if ts["target_seconds"]:
        total_elapsed = time.time() - ts["started_at"]
        if total_elapsed >= ts["target_seconds"]:
            end_timed_sprint("time_up")


# ============================================================
# Study report (preserved from v7)
# ============================================================

def generate_study_report_markdown():
    """Build a printable/downloadable Markdown study report from current
    session state. Pure function: no side effects, only reads session_state."""
    lines = []
    lines.append("# DoseDrill Study Report")
    lines.append("")
    lines.append("Adaptive pharmacy math practice — session summary")
    lines.append("")

    attempts = total_attempts()
    correct_total = sum(
        st.session_state.stats[c.key]["_overall"]["correct"] for c in CHAPTERS_LIST
    )
    acc = current_accuracy()
    acc_display = f"{acc:.0%}" if acc is not None else "—"

    lines.append("## Overall")
    lines.append("")
    lines.append(f"- Total questions attempted: **{attempts}**")
    lines.append(f"- First-try accuracy: **{acc_display}** ({correct_total} of {attempts} correct)")
    lines.append(f"- Current streak: **{st.session_state.streak}**")
    lines.append(f"- Best streak this session: **{st.session_state.best_streak}**")
    lines.append("")

    focus_key = recommended_focus_chapter()
    if focus_key:
        focus_ch = get_chapter(focus_key)
        focus_mastery = chapter_mastery(focus_key)
        _, focus_status_label = chapter_status(focus_key)
        lines.append("## Recommended focus")
        lines.append("")
        lines.append(
            f"- **Ch. {focus_ch.number} — {focus_ch.title}** "
            f"({focus_status_label} · Mastery {focus_mastery})"
        )
        lines.append("")

    lines.append("## Mastery by chapter")
    lines.append("")
    lines.append("| # | Chapter | Status | Mastery | Attempts |")
    lines.append("|---|---------|--------|---------|----------|")
    for ch in CHAPTERS_LIST:
        overall = st.session_state.stats[ch.key]["_overall"]
        emoji, status_label = chapter_status(ch.key)
        mastery_val = chapter_mastery(ch.key)
        lines.append(
            f"| {ch.number} | {ch.title} | {emoji} {status_label} "
            f"| {mastery_val} | {overall['attempts']} |"
        )
    lines.append("")

    missed_chapter_counts = {}
    missed_pt_counts = {}
    for ch in CHAPTERS_LIST:
        for pt in ch.problem_types:
            s = st.session_state.stats[ch.key][pt.key]
            missed = s["attempts"] - s["correct"]
            if missed > 0:
                missed_chapter_counts[ch.key] = missed_chapter_counts.get(ch.key, 0) + missed
                missed_pt_counts[(ch.key, pt.key)] = missed

    if missed_chapter_counts:
        lines.append("## Chapters with missed problems")
        lines.append("")
        ranked = sorted(missed_chapter_counts.items(), key=lambda x: -x[1])
        for ch_key, count in ranked:
            ch = CHAPTERS[ch_key]
            lines.append(f"- Ch. {ch.number}. {ch.title} — {count} missed")
        lines.append("")

    if missed_pt_counts:
        lines.append("## Problem types with missed problems")
        lines.append("")
        ranked = sorted(missed_pt_counts.items(), key=lambda x: -x[1])
        for (ch_key, pt_key), count in ranked[:10]:
            ch = CHAPTERS[ch_key]
            pt = next((p for p in ch.problem_types if p.key == pt_key), None)
            if pt:
                lines.append(f"- Ch. {ch.number} · {pt.label} — {count} missed")
        lines.append("")

    queue = st.session_state.review_queue
    if queue:
        lines.append("## Recent missed problems")
        lines.append("")
        for entry in reversed(queue):
            ch = get_chapter(entry["chapter_key"])
            lines.append(f"### Ch. {ch.number}. {ch.title}")
            lines.append("")
            lines.append(f"**Question:** {entry['question_preview']}")
            lines.append("")
            if entry.get("correct_answer") is not None and entry.get("unit"):
                lines.append(f"**Correct answer:** {entry['correct_answer']} {entry['unit']}")
                lines.append("")
            steps = entry.get("explanation_steps") or []
            if steps:
                lines.append("**Setup:**")
                lines.append("")
                for step in steps:
                    lines.append(f"- {step}")
                lines.append("")

    weak = get_weak_chapters()
    if weak:
        lines.append("## Chapters to focus on next")
        lines.append("")
        for chapter_key, accuracy in weak:
            ch = CHAPTERS[chapter_key]
            lines.append(f"- Ch. {ch.number}. {ch.title} — {accuracy:.0%} accuracy")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_Generated by DoseDrill. Session goal resets when the browser session ends._")

    return "\n".join(lines)


# ============================================================
# Shared UI helpers
# ============================================================

def _chip(label):
    """Inline HTML for a small rounded stat chip used in the hero card."""
    return (
        f'<div style="padding: 0.35rem 0.85rem; '
        f'background-color: rgba(28, 131, 225, 0.08); '
        f'border-radius: 999px; font-size: 0.85rem; font-weight: 500; '
        f'border: 1px solid rgba(28, 131, 225, 0.18); '
        f'white-space: nowrap; line-height: 1.2;">{label}</div>'
    )


def _section_label(text):
    """Small uppercase section label used to anchor each major section."""
    st.markdown(
        f'<p style="opacity:0.45; font-size:0.75rem; '
        f'text-transform:uppercase; letter-spacing:0.08em; '
        f'margin: 0.4rem 0 0.6rem; font-weight:600;">{text}</p>',
        unsafe_allow_html=True,
    )


def _checklist_html(*items):
    """Render a list of (label, done) tuples as a small inline checklist.

    Filled coral ✓ for done, hollow ○ for pending. Done items get reduced
    opacity and a strikethrough so the user can see at a glance what's
    been crossed off.
    """
    parts = []
    for label, done in items:
        if done:
            icon_html = (
                '<span style="display:inline-block; width:1.4rem; '
                'font-weight:700; color:#ef4444;">✓</span>'
            )
            row_style = "opacity: 0.55; text-decoration: line-through;"
        else:
            icon_html = (
                '<span style="display:inline-block; width:1.4rem; '
                'font-weight:600; color:#9ca3af;">○</span>'
            )
            row_style = "opacity: 0.92;"

        parts.append(
            f'<div style="margin-bottom: 0.25rem; font-size: 0.92rem; '
            f'line-height: 1.5; {row_style}">{icon_html}{label}</div>'
        )
    return "".join(parts)


# ============================================================
# Hero card + pill tab nav (top region, visible on every page)
# ============================================================

def _render_hero_card():
    """Bordered hero card. Brand block on the left, stat chips on the right.
    Bigger title, descriptive tagline that names the curriculum topics, and
    the four key stats inline as compact chips."""
    goal_count, goal_target = daily_goal_progress()
    goal_display = min(goal_count, goal_target)

    streak = st.session_state.streak
    best = st.session_state.best_streak

    acc = current_accuracy()
    acc_display = f"{acc:.0%}" if acc is not None else "—"

    attempted = [
        c for c in CHAPTERS_LIST
        if st.session_state.stats[c.key]["_overall"]["attempts"] > 0
    ]
    if attempted:
        avg_m = round(sum(chapter_mastery(c.key) for c in attempted) / len(attempted))
        mastery_display = str(avg_m)
    else:
        mastery_display = "—"

    chips_html = (
        _chip(f"🎯 Session goal: {goal_display} / {goal_target}")
        + _chip(f"🔥 Streak: {streak} · Best {best}")
        + _chip(f"✓ Accuracy: {acc_display}")
        + _chip(f"📊 Mastery: {mastery_display}")
    )

    with st.container(border=True):
        st.markdown(
            f'<div style="display:flex; justify-content:space-between; '
            f'align-items:center; gap: 1.5rem; flex-wrap: wrap; '
            f'padding: 0.5rem 0.25rem;">'
            f'<div style="flex: 1; min-width: 320px;">'
            f'<div style="font-size: 2.1rem; font-weight: 700; line-height: 1.1; '
            f'margin-bottom: 0.35rem;">💊 DoseDrill</div>'
            f'<div style="opacity: 0.78; font-size: 1rem; line-height: 1.45; '
            f'max-width: 580px;">'
            f'Adaptive pharmacy math practice for dosage calculations, '
            f'dilutions, IV rates, and labels.</div>'
            f'<div style="opacity: 0.5; font-size: 0.78rem; font-style: italic; '
            f'margin-top: 0.5rem;">Built by Donny Phi</div>'
            f'</div>'
            f'<div style="display:flex; gap: 0.4rem; flex-wrap: wrap; '
            f'align-items:center; justify-content: flex-end;">{chips_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_pill_tab_nav():
    """Three page buttons styled as pill tabs (active = primary coral,
    inactive = secondary outline). Difficulty radio sits to the right.

    Implemented as buttons rather than st.radio so the visual treatment
    matches the user's spec ('Do not use radio circles visually') and so
    programmatic page switches from other parts of the UI work cleanly."""
    current = st.session_state.current_page

    # 5 columns: 3 narrow ones for the pill tabs, a small spacer, and a
    # wider one for the difficulty horizontal radio.
    t1, t2, t3, _spacer, diff = st.columns([1, 1, 1, 0.3, 2.4])

    tab_slots = (t1, t2, t3)
    for col, page_name in zip(tab_slots, _VALID_PAGES):
        with col:
            is_active = current == page_name
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                page_name,
                key=f"tab_{page_name}",
                type=btn_type,
                use_container_width=True,
            ):
                if not is_active:
                    st.session_state.current_page = page_name
                    st.rerun()

    with diff:
        st.radio(
            "Difficulty",
            ["Beginner", "Standard", "Challenge"],
            key="difficulty",
            horizontal=True,
            label_visibility="collapsed",
        )


# Render the always-visible top region.
_render_hero_card()
st.write("")
_render_pill_tab_nav()
st.write("")


# ============================================================
# Dashboard
# ============================================================

def render_dashboard():
    """v8 dashboard. Three major sections (action card, Today's Focus,
    Study Report), then a compact Learning Path and a Browse Chapters
    expander at the bottom."""
    _render_main_action_card()
    st.write("")
    _render_todays_focus_section()
    _render_review_expander()
    st.write("")
    _render_study_report_card()
    st.write("")
    _render_learning_path_compact()
    st.write("")
    _render_browse_chapters()


def _render_main_action_card():
    """The 'Ready to practice?' card. Three primary CTAs in a row, with a
    tinted session checklist box at the bottom (the simplified Today's
    Plan absorbed into this card)."""
    queue_size = review_queue_size()
    attempts = total_attempts()

    with st.container(border=True):
        st.markdown(
            '<div style="padding: 0.5rem 0.25rem 0.25rem;">'
            '<div style="font-size: 1.4rem; font-weight: 600; line-height: 1.2;">'
            'Ready to practice?</div>'
            '<div style="opacity: 0.75; font-size: 0.98rem; '
            'margin-top: 0.35rem; line-height: 1.5;">'
            'Start with adaptive mixed practice or jump into a timed sprint.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.write("")

        # Three CTAs. The Review button is disabled (secondary) when the
        # queue is empty so the row keeps three slots visually.
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button(
                "🎯 Start Mixed Practice",
                key="main_action_mixed",
                type="primary",
                use_container_width=True,
            ):
                start_mixed()
                st.rerun()
        with b2:
            if st.button(
                "⏱ Timed Sprint",
                key="main_action_timed",
                type="primary",
                use_container_width=True,
            ):
                # Default to the 5-question sprint. The Timed Practice
                # card below has the other options.
                start_timed_sprint("5q")
                st.rerun()
        with b3:
            review_label = (
                f"🔁 Review Missed ({queue_size})"
                if queue_size > 0
                else "🔁 Review Missed"
            )
            if st.button(
                review_label,
                key="main_action_review",
                type="primary" if queue_size > 0 else "secondary",
                use_container_width=True,
                disabled=queue_size == 0,
            ):
                practice_from_review(0)
                st.rerun()

        # Compact session checklist (the simplified Today's Plan).
        focus_attempted = any(
            st.session_state.stats[c.key]["_overall"]["attempts"] >= 3
            for c in CHAPTERS_LIST
        )
        review_done = attempts >= 1 and queue_size == 0

        checklist_html = _checklist_html(
            ("Answer 5 mixed practice problems", attempts >= 5),
            ("Focus on one chapter (3+ attempts)", focus_attempted),
            ("Clear your review queue", review_done),
        )

        st.markdown(
            '<div style="margin-top: 1rem; padding: 0.85rem 1.1rem; '
            'background-color: rgba(0,0,0,0.025); border-radius: 10px; '
            'border: 1px solid rgba(0,0,0,0.06);">'
            '<div style="opacity: 0.55; font-size: 0.72rem; '
            'text-transform: uppercase; letter-spacing: 0.08em; '
            "margin-bottom: 0.55rem; font-weight: 600;\">Today's session</div>"
            + checklist_html
            + '</div>',
            unsafe_allow_html=True,
        )


def _render_todays_focus_section():
    """Section B: Recommended Focus + Timed Practice, side by side."""
    _section_label("Today's focus")
    fc_col, tp_col = st.columns(2, gap="medium")
    with fc_col:
        _render_focus_card()
    with tp_col:
        _render_timed_practice_card()


def _render_focus_card():
    """Recommended Focus card. Same five-row structure across all three
    states (has-focus / no-data / all-mastered) for height parity with
    the Timed Practice card next to it."""
    focus_key = recommended_focus_chapter()
    with st.container(border=True):
        st.markdown("### ⭐  Recommended Focus")
        if focus_key:
            ch = get_chapter(focus_key)
            emoji, status_label = chapter_status(focus_key)
            mastery = chapter_mastery(focus_key)
            st.caption("Your weakest attempted chapter.")
            st.markdown(f"**Ch. {ch.number} — {ch.title}**")
            st.markdown(f"{emoji} {status_label}  •  Mastery: {mastery}")
            if st.button(
                "Practice this →",
                key="focus_card_practice",
                type="primary",
                use_container_width=True,
            ):
                start_chapter(focus_key)
                st.rerun()
        elif total_attempts() == 0:
            st.caption("Complete 5 problems so the app can find your weak topics.")
            st.write("")
            st.write("")
            if st.button(
                "Start Mixed Practice",
                key="focus_card_no_data",
                type="primary",
                use_container_width=True,
            ):
                start_mixed()
                st.rerun()
        else:
            st.caption("Nothing weak right now. Mixed practice will surface new gaps as you go.")
            st.write("")
            st.write("")
            if st.button(
                "Start Mixed Practice",
                key="focus_card_all_mastered",
                type="primary",
                use_container_width=True,
            ):
                start_mixed()
                st.rerun()


def _render_timed_practice_card():
    """Sprint picker with grouped sub-labels. Two distinct rows: a
    'Question-based' group with 5q/10q sprints, and a 'Time-based' group
    with 2min/5min sprints. Shorter button text with arrows to read as
    actions, not labels."""
    with st.container(border=True):
        st.markdown("### ⏱  Timed Practice")
        st.caption("Sprint through problems to build speed under time pressure.")
        st.write("")

        # Question-based row
        st.markdown(
            '<div style="opacity: 0.55; font-size: 0.7rem; '
            'text-transform: uppercase; letter-spacing: 0.08em; '
            'margin-bottom: 0.4rem; font-weight: 600;">Question-based</div>',
            unsafe_allow_html=True,
        )
        q1, q2 = st.columns(2)
        with q1:
            if st.button(
                "5 questions →",
                key="timed_pick_5q",
                use_container_width=True,
            ):
                start_timed_sprint("5q")
                st.rerun()
        with q2:
            if st.button(
                "10 questions →",
                key="timed_pick_10q",
                use_container_width=True,
            ):
                start_timed_sprint("10q")
                st.rerun()

        st.write("")

        # Time-based row
        st.markdown(
            '<div style="opacity: 0.55; font-size: 0.7rem; '
            'text-transform: uppercase; letter-spacing: 0.08em; '
            'margin-bottom: 0.4rem; font-weight: 600;">Time-based</div>',
            unsafe_allow_html=True,
        )
        t1, t2 = st.columns(2)
        with t1:
            if st.button(
                "2 minutes →",
                key="timed_pick_2min",
                use_container_width=True,
            ):
                start_timed_sprint("2min")
                st.rerun()
        with t2:
            if st.button(
                "5 minutes →",
                key="timed_pick_5min",
                use_container_width=True,
            ):
                start_timed_sprint("5min")
                st.rerun()


def _render_review_expander():
    """Per-item queue list. Only renders when queue is non-empty."""
    queue_size = review_queue_size()
    if queue_size == 0:
        return

    st.write("")
    with st.expander(f"View all missed problems ({queue_size})"):
        st.caption(
            "Each entry generates a fresh problem of the same type. "
            "The original is removed from the queue once you start."
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
                    "Practice →",
                    key=f"review_expander_{i}",
                    use_container_width=True,
                ):
                    practice_from_review(i)
                    st.rerun()
        st.write("")
        if st.button("Clear review queue", key="review_expander_clear"):
            clear_review_queue()
            st.rerun()


def _render_study_report_card():
    """Full-width Study Report preview + download CTA. Locked until the
    user has attempted at least one question."""
    attempts = total_attempts()
    _section_label("Study report")
    with st.container(border=True):
        if attempts == 0:
            st.markdown("### 📄  Study Report — locked")
            st.caption(
                "Answer at least one problem to generate a printable study "
                "report. The report will summarize attempts, accuracy, "
                "mastery, missed chapters, and recent missed problems with explanations."
            )
            st.write("")
            st.button(
                "Download Study Report",
                key="report_card_locked",
                use_container_width=True,
                disabled=True,
                help="Answer at least one question to unlock your study report.",
            )
        else:
            acc = current_accuracy()
            acc_display = f"{acc:.0%}" if acc is not None else "—"
            queue_size = review_queue_size()
            st.markdown("### 📄  Study Report")
            st.caption(
                "A printable summary of your session that you can keep, share, or review later."
            )
            st.markdown(
                f"**Covers:** {attempts} attempts &nbsp;·&nbsp; "
                f"{acc_display} accuracy &nbsp;·&nbsp; "
                f"streak {st.session_state.streak} (best {st.session_state.best_streak}) &nbsp;·&nbsp; "
                f"{queue_size} missed in queue"
            )
            st.write("")
            report_md = generate_study_report_markdown()
            st.download_button(
                "📄 Download Study Report (.md)",
                data=report_md,
                file_name="dosedrill_study_report.md",
                mime="text/markdown",
                key="report_card_download",
                type="primary",
                use_container_width=True,
            )


def _render_learning_path_compact():
    """Compact 3-tier curriculum preview. Smaller fonts and less padding
    than v7 so this section reads as supporting context rather than
    competing with the main action card for attention."""
    _section_label("The full curriculum")

    tiers = [
        ("Foundation", "Ch. 1–4",
         "Parenteral doses · Powdered drugs · Percents · Solutions"),
        ("Applications", "Ch. 5–7",
         "Body weight · BSA · Infusion rates"),
        ("Advanced", "Ch. 8–10",
         "Dilutions · Parenteral nutrition · Medication labels"),
    ]

    cols = st.columns(3, gap="small")
    for col, (tier_name, ch_range, topics) in zip(cols, tiers):
        with col:
            with st.container(border=True):
                st.markdown(
                    f'<div style="padding:0.35rem 0.25rem;">'
                    f'<div style="font-weight:600; font-size:0.98rem; '
                    f'margin-bottom:0.1rem;">{tier_name}</div>'
                    f'<div style="opacity:0.5; font-size:0.7rem; '
                    f'text-transform:uppercase; letter-spacing:0.07em; '
                    f'margin-bottom:0.55rem;">{ch_range}</div>'
                    f'<div style="font-size:0.83rem; opacity:0.72; '
                    f'line-height:1.55;">{topics}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


def _render_browse_chapters():
    """Chapter list as a collapsed expander at the bottom of the dashboard.
    Replaces the v6 sidebar chapter list and the v7 always-visible section.
    Practice page's diagnostic empty state still has chapter access too."""
    with st.expander("Browse all chapters", expanded=False):
        for chapter in CHAPTERS_LIST:
            emoji, status_label = chapter_status(chapter.key)
            mastery = chapter_mastery(chapter.key)
            attempts = st.session_state.stats[chapter.key]["_overall"]["attempts"]

            c_label, c_status, c_btn = st.columns([4, 3, 1])
            with c_label:
                st.markdown(f"{emoji} **Ch. {chapter.number}.** {chapter.title}")
            with c_status:
                if attempts > 0:
                    st.caption(f"{status_label}  ·  Mastery {mastery}  ·  {attempts} attempts")
                else:
                    st.caption(status_label)
            with c_btn:
                if st.button(
                    "Practice",
                    key=f"browse_practice_{chapter.key}",
                    use_container_width=True,
                ):
                    start_chapter(chapter.key)
                    st.rerun()


# ============================================================
# Practice page (preserved from v7)
# ============================================================

def render_practice_view():
    """Practice page entry point.

    Three sub-states:
      1. Timed sprint completed → render summary, then route back.
      2. No chapter selected   → render the diagnostic empty state.
      3. Chapter selected      → render the active coach-mode problem flow,
         wrapped in a timed strip if a sprint is active.
    """
    ts = st.session_state.timed_session

    # Server-side time-up check for time-based sprints.
    if ts is not None and not ts["completed"] and ts["target_seconds"]:
        if (time.time() - ts["started_at"]) >= ts["target_seconds"]:
            end_timed_sprint("time_up")
            ts = st.session_state.timed_session

    if ts is not None and ts["completed"]:
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

    if ts is not None:
        _render_timed_strip()

    problem = st.session_state.current_problem
    chapter = get_chapter(problem["chapter_key"])

    top_back, top_title = st.columns([1, 5])
    with top_back:
        if st.button("← Dashboard", key="practice_back", use_container_width=True):
            go_to_dashboard()
            st.rerun()
    with top_title:
        if st.session_state.mixed_mode:
            st.markdown("### 🎯  Mixed practice")
            st.caption(f"Currently on: Ch. {chapter.number} — {chapter.title}")
        else:
            st.markdown(f"### Ch. {chapter.number}. {chapter.title}")
            st.caption(chapter.summary)

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


def _render_timed_strip():
    """Sprint header strip: mode label, progress, timer, End sprint button."""
    ts = st.session_state.timed_session
    cfg = _TIMED_MODES[ts["mode"]]
    mode_label = cfg["label"]

    elapsed = time.time() - ts["started_at"]

    if ts["target_questions"]:
        target = ts["target_questions"]
        answered_so_far = ts["answered"]
        current_q = min(answered_so_far + 1, target)
        progress_text = f"Question {current_q} of {target}"
        time_label = "Elapsed"
        time_display_html = (
            f'{int(elapsed // 60)}:{int(elapsed % 60):02d}'
        )
    else:
        target = ts["target_seconds"]
        remaining = max(0, int(target - elapsed))
        progress_text = f"Answered: {ts['answered']}  ·  Correct: {ts['correct']}"
        time_label = "Remaining"
        timer_id = f"dd-timer-{int(ts['started_at'])}"
        ms_remaining = remaining * 1000
        time_display_html = (
            f'<span id="{timer_id}">{int(remaining // 60)}:{int(remaining % 60):02d}</span>'
            f'<script>(function(){{'
            f'  var endTime = Date.now() + {ms_remaining};'
            f'  var el = document.getElementById("{timer_id}");'
            f'  if (!el) return;'
            f'  function tick() {{'
            f'    var r = Math.max(0, endTime - Date.now());'
            f'    var m = Math.floor(r / 60000);'
            f'    var s = Math.floor((r % 60000) / 1000);'
            f'    el.innerText = m + ":" + (s < 10 ? "0" + s : s);'
            f'    if (r > 0) setTimeout(tick, 250);'
            f'  }}'
            f'  tick();'
            f'}})();</script>'
        )

    st.markdown(
        f'<div style="background-color: rgba(245, 158, 11, 0.12); '
        f'padding: 0.6rem 1rem; border-radius: 6px; '
        f'border-left: 4px solid #f59e0b; margin-bottom: 1rem; '
        f'display: flex; align-items: center; justify-content: space-between; '
        f'gap: 1rem; flex-wrap: wrap;">'
        f'<div style="font-size: 0.95rem;">'
        f'<strong>⏱ {mode_label}</strong> &nbsp;·&nbsp; {progress_text}'
        f'</div>'
        f'<div style="font-family: ui-monospace, SFMono-Regular, Menlo, monospace; '
        f'font-size: 1.05rem; font-weight: 600;">'
        f'{time_label}: {time_display_html}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    end_col, _ = st.columns([1, 5])
    with end_col:
        if st.button("End sprint", key="end_sprint_btn", use_container_width=True):
            end_timed_sprint("abandoned")
            st.rerun()


def render_timed_summary():
    """Post-sprint results view."""
    ts = st.session_state.timed_session
    cfg = _TIMED_MODES.get(ts["mode"], {"label": ts["mode"]})
    mode_label = cfg["label"]

    end_emoji = {
        "target": "🏁",
        "time_up": "⏱",
        "abandoned": "👋",
    }.get(ts["end_reason"], "🏁")
    end_heading = {
        "target": "Sprint complete",
        "time_up": "Time's up",
        "abandoned": "Sprint ended",
    }.get(ts["end_reason"], "Done")

    answered = ts["answered"]
    correct = ts["correct"]
    accuracy = (correct / answered) if answered > 0 else 0.0
    total_time = sum(ts["per_question_seconds"])
    avg_time = (total_time / answered) if answered > 0 else 0.0

    st.markdown(f"### {end_emoji}  {end_heading}")
    st.caption(mode_label)
    st.write("")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Answered", answered)
    m2.metric("First-try correct", f"{correct} of {answered}" if answered else "—")
    m3.metric("Accuracy", f"{accuracy:.0%}" if answered else "—")
    m4.metric("Avg time/Q", f"{avg_time:.1f}s" if answered else "—")

    if answered == 0:
        st.info("No questions answered in this sprint. Start another one when you're ready.")
    elif ts["end_reason"] == "target":
        st.success("Sprint target reached. Mastery and streak stats are updated.")
    elif ts["end_reason"] == "time_up":
        st.info("Time ran out. The questions you completed counted toward your stats.")
    else:
        st.info("Sprint ended early. The questions you completed counted toward your stats.")

    st.write("")
    b1, b2 = st.columns(2)
    with b1:
        if st.button(
            "Try another sprint →",
            key="ts_another",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.timed_session = None
            st.session_state.current_page = "Dashboard"
            st.rerun()
    with b2:
        if st.button(
            "Back to Dashboard",
            key="ts_back",
            use_container_width=True,
        ):
            st.session_state.timed_session = None
            go_to_dashboard()
            st.rerun()


def render_practice_empty_state():
    """Diagnostic view when no chapter is active. Houses the content that
    used to live on the old Progress page."""
    st.title("Practice")
    st.caption("Pick a chapter from Browse Chapters on the Dashboard, or jump into mixed practice below.")
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
    with st.container(border=True):
        if not st.session_state.mixed_mode:
            render_skill_picker(chapter)

        render_helper_buttons(chapter, problem)
        render_helper_content(chapter, problem)

        st.divider()

        st.caption(problem["problem_type_label"])
        st.markdown(f"#### {problem['question']}")
        st.write("")

        phase = st.session_state.problem_phase
        if phase == "answering":
            render_answer_input(problem)
        elif phase == "first_wrong":
            render_coach_intervention(problem)
        else:
            render_revealed_result()


def render_answer_input(problem):
    """Number input + Check button."""
    user_answer = st.number_input(
        f"Your answer ({problem['unit']})",
        value=0.0,
        step=0.1,
        format="%.2f",
        key=f"answer_input_{st.session_state.input_version}",
    )
    if st.button("Check answer", type="primary", use_container_width=True):
        check_answer(problem, user_answer)
        st.rerun()


def render_coach_intervention(problem):
    """First-wrong screen: gentle message + Hint / Try again / Show solution."""
    result = st.session_state.last_result
    st.warning(
        f"That's not it. You entered {result['user_answer']} {result['unit']}. "
        "Take another look. Want a hint, another try, or the full solution?"
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(
            "💡 Get a hint",
            type="secondary",
            use_container_width=True,
            key="coach_hint",
        ):
            coach_retry(open_hint=True)
            st.rerun()
    with c2:
        if st.button(
            "🔄 Try again",
            type="primary",
            use_container_width=True,
            key="coach_retry",
        ):
            coach_retry(open_hint=False)
            st.rerun()
    with c3:
        if st.button(
            "📖 Show solution",
            type="secondary",
            use_container_width=True,
            key="coach_show",
        ):
            coach_reveal()
            st.rerun()


def render_revealed_result():
    """Terminal state: result + step-by-step + Next problem."""
    result = st.session_state.last_result
    attempt_number = result.get("attempt_number", 1)

    if result["correct"] and attempt_number == 1:
        st.success(
            f"✅ Correct! You entered {result['user_answer']} {result['unit']}."
        )
    elif result["correct"] and attempt_number > 1:
        st.info(
            "Nice correction — you got it on retry. This won't count toward your streak, "
            "but it helps your review progress."
        )
    else:
        st.error(
            f"The correct answer is {result['correct_answer']} {result['unit']}."
        )

    with st.expander("Step-by-step solution", expanded=not result["correct"]):
        for step in result["steps"]:
            st.write(f"• {step}")

    if st.button("Next problem →", type="primary", use_container_width=True):
        _maybe_finalize_timed_question()
        if (
            st.session_state.timed_session is None
            or not st.session_state.timed_session["completed"]
        ):
            new_problem()
        st.rerun()


def render_skill_picker(chapter):
    """Horizontal radio to switch problem type within a chapter."""
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
    """Three toggle buttons across the top of the problem card."""
    b1, b2, b3 = st.columns(3)
    with b1:
        ex_type = "primary" if st.session_state.show_example else "secondary"
        if st.button(
            "📘 Learn with an example",
            type=ex_type,
            use_container_width=True,
            key="btn_example",
        ):
            st.session_state.show_example = not st.session_state.show_example
            if st.session_state.show_example and st.session_state.example_problem is None:
                pt = get_problem_type(problem["chapter_key"], problem["problem_type_key"])
                st.session_state.example_problem = pt.generator()
            st.rerun()
    with b2:
        fm_type = "primary" if st.session_state.show_formula else "secondary"
        if st.button(
            "📐 Show formula",
            type=fm_type,
            use_container_width=True,
            key="btn_formula",
        ):
            st.session_state.show_formula = not st.session_state.show_formula
            st.rerun()
    with b3:
        hint_type = "primary" if st.session_state.show_hint else "secondary"
        if st.button(
            "💡 Get a hint",
            type=hint_type,
            use_container_width=True,
            key="btn_hint",
        ):
            st.session_state.show_hint = not st.session_state.show_hint
            st.rerun()


def render_helper_content(chapter, problem):
    """Show the panels for whichever helper toggles are on."""
    if st.session_state.show_formula:
        st.info(f"**Formula / setup**\n\n{chapter.formula}")

    if st.session_state.show_hint:
        first_steps = problem["steps"][:2]
        body = "\n\n".join(first_steps)
        st.info(f"**Hint — how to start**\n\n{body}")

    if st.session_state.show_example and st.session_state.example_problem:
        ex = st.session_state.example_problem
        with st.container(border=True):
            st.markdown("**📘 Worked example (same problem type)**")
            st.markdown(f"_Question:_ {ex['question']}")
            st.markdown("_Solution:_")
            for step in ex["steps"]:
                st.write(f"• {step}")
            st.success(f"Answer: {ex['answer']} {ex['unit']}")


def render_work_it_out(chapter):
    """Recommend the prerequisite chapter after a wrong answer."""
    prereq = get_chapter(chapter.prerequisite_chapter)
    with st.container(border=True):
        st.markdown("#### 🔧 Work it out")
        st.markdown(
            f"This topic builds on a more foundational skill: "
            f"**Ch. {prereq.number} — {prereq.title}**."
        )
        st.caption(
            "Practicing the foundational chapter for a few problems often makes this one click."
        )
        if st.button(
            f"Practice Ch. {prereq.number} first →",
            key="prereq_jump",
            use_container_width=True,
        ):
            start_chapter(prereq.key)
            st.rerun()


# ============================================================
# Page routing
# ============================================================

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
