"""
Pharmacy Tech Math Practice — Streamlit app (v6.5, polished dashboard).

Layout overview:
    Sidebar    : session metrics, session-goal progress, page nav,
                 difficulty selector, chapter list. UNCHANGED from v6.4.
    Dashboard  : redesigned as a learning-platform landing page. Top
                 announcement strip → hero with title/subtitle/CTAs →
                 three-column "How it works" feature highlights →
                 Personalized action cards (focus + review) with optional
                 queue expander → Learning Path Preview with topic hints.
    Practice   : dual purpose. When a chapter is active, runs the coach-mode
                 problem flow. When no chapter is active, surfaces the
                 diagnostic content (recommended focus, mastery by chapter,
                 accuracy by chapter, weak-chapter list). UNCHANGED from v6.4.
    Calculator : dose-to-volume reference. UNCHANGED.

Run with:
    streamlit run app.py
"""

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


# ============================================================
# Core actions
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


def go_to_dashboard():
    """Clear practice state and return to the dashboard."""
    st.session_state.selected_chapter_key = None
    st.session_state.mixed_mode = False
    st.session_state.current_problem = None
    st.session_state.last_result = None
    st.session_state.problem_type_choice = "_adaptive"
    st.session_state.current_page = "Dashboard"
    reset_helpers()


def start_chapter(chapter_key, problem_type_key="_adaptive"):
    """Enter practice mode for a specific chapter and route to Practice."""
    st.session_state.selected_chapter_key = chapter_key
    st.session_state.mixed_mode = False
    st.session_state.problem_type_choice = problem_type_key
    st.session_state.current_page = "Practice"
    new_problem()


def start_mixed():
    """Enter mixed-practice mode across all chapters."""
    st.session_state.mixed_mode = True
    st.session_state.selected_chapter_key = None
    st.session_state.problem_type_choice = "_adaptive"
    st.session_state.current_page = "Practice"
    new_problem()


def practice_from_review(index):
    """Pop an entry from the review queue and start practicing that type."""
    entry = pop_review_queue_at(index)
    if entry:
        start_chapter(entry["chapter_key"], entry["problem_type_key"])


def check_answer(problem, user_answer):
    """Verify the answer and drive the coach state machine.

    Stats math preserved: record_attempt fires only on the FIRST submission,
    so retries and self-corrections don't affect mastery or streak.
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
# Sidebar (UNCHANGED from v6.4)
# ============================================================

def _on_nav_change():
    """Sync current_page when the user clicks the navigation radio."""
    st.session_state.current_page = st.session_state.nav_choice


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
# Dashboard (REDESIGNED for v6.5 — landing-page feel)
# ============================================================

def _section_label(text):
    """Small uppercase section label. Used above each Dashboard section
    that contains multiple cards, to anchor the eye and create rhythm
    without taking much vertical space."""
    st.markdown(
        f'<p style="opacity:0.55; font-size:0.8rem; '
        f'text-transform:uppercase; letter-spacing:0.06em; '
        f'margin: 0 0 0.6rem; font-weight:600;">{text}</p>',
        unsafe_allow_html=True,
    )


def render_dashboard():
    """Action-oriented learning-platform landing page.

    Section order: announcement → hero → feature highlights → action cards
    (+ optional queue expander) → learning path. Status metrics and mastery
    detail live elsewhere (sidebar and Practice page respectively) to keep
    this page focused on decisions and motivation rather than measurement.
    """
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
    """Thin notification banner at the top of the dashboard. Context-aware:
    flips to a review-focused message when the user has missed problems
    queued, otherwise highlights the coach-mode feature.
    """
    if review_queue_size() > 0:
        message = "<strong>New:</strong> Missed problems are saved for review."
    else:
        message = "<strong>New:</strong> Coach Mode now gives hints before showing solutions."

    st.markdown(
        f'<div style="background-color: rgba(28, 131, 225, 0.08); '
        f'padding: 0.55rem 1rem; border-radius: 6px; '
        f'border-left: 3px solid #1c83e1; margin-bottom: 1.25rem; '
        f'font-size: 0.92rem;">'
        f'🆕 &nbsp;{message}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_hero():
    """Landing-page hero: large title, descriptive subtitle, two primary CTAs.

    Title and subtitle render via inline HTML inside a bordered container
    so the entire hero reads as one block. The CTAs are native Streamlit
    buttons in a column row directly below the title block.
    """
    queue_size = review_queue_size()
    with st.container(border=True):
        st.markdown(
            '<div style="padding: 1rem 0.25rem 0.5rem;">'
            '<h1 style="margin:0; font-size:2.1rem; line-height:1.2; font-weight:700;">'
            'DoseDrill: pharmacy math, practiced with purpose.'
            '</h1>'
            '<p style="margin:1rem 0 0; font-size:1.05rem; line-height:1.55; opacity:0.78;">'
'Build accuracy with 500+ randomized pharmacy math question variants across '
'dosage calculations, reconstitution, dilutions, IV rates, and more — with hints, review queues, and mastery tracking.'
'</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.write("")
        b1, b2 = st.columns(2)
        with b1:
            if st.button(
                "🎯 Start Mixed Practice",
                key="hero_start_mixed",
                type="primary",
                use_container_width=True,
            ):
                start_mixed()
                st.rerun()
        with b2:
            review_label = (
                f"🔁 Review Missed Problems ({queue_size})"
                if queue_size > 0
                else "🔁 Review Missed Problems"
            )
            if st.button(
                review_label,
                key="hero_start_review",
                type="primary",
                use_container_width=True,
                disabled=queue_size == 0,
            ):
                practice_from_review(0)
                st.rerun()


def _render_feature_highlights():
    """Three-column 'How it works' section. Each card centers a large icon
    above a bold title and a one-paragraph description. No buttons — these
    are explanatory cards, not CTAs.
    """
    _section_label("How it works")

    features = [
        ("🔁", "Unlimited Practice",
 "Randomized pharmacy math problems help you build speed and confidence."),
        ("💡", "Hints Before Answers",
         "Wrong answers trigger hints and retry chances before the full "
         "solution is revealed."),
        ("🎯", "Adaptive Review",
         "Missed problems are saved into a review queue so you know exactly "
         "what to practice next."),
    ]

    cols = st.columns(3, gap="medium")
    for col, (icon, title, body) in zip(cols, features):
        with col:
            with st.container(border=True):
                st.markdown(
                    f'<div style="text-align:center; padding:0.75rem 0.5rem;">'
                    f'<div style="font-size:2.4rem; line-height:1; margin-bottom:0.6rem;">{icon}</div>'
                    f'<div style="font-weight:600; font-size:1.05rem; margin-bottom:0.45rem;">{title}</div>'
                    f'<div style="opacity:0.75; font-size:0.92rem; line-height:1.55;">{body}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


def _render_action_cards():
    """Side-by-side Recommended Focus and Missed Problem Review.

    The cards themselves (and their height-parity structure) are unchanged
    from v6.4. The wrapping section label positions them visually as
    'personalized actions' beneath the explanatory feature highlights above.
    """
    _section_label("Personalized for you")
    col_focus, col_review = st.columns(2, gap="medium")
    with col_focus:
        _render_focus_card()
    with col_review:
        _render_review_card()


def _render_focus_card():
    """Action card A: Recommended Focus.

    Three states (has-focus / no-data / all-mastered) share a uniform
    five-element structure (heading + 3 content rows + button) so the
    card matches the visual height of _render_review_card across states.
    """
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


def _render_review_card():
    """Action card B: Missed Problem Review.

    Mirrors _render_focus_card's five-element structure for height parity.
    The empty-queue state uses a disabled Start review button rather than
    going button-less, so the visual weight matches the focus card.
    """
    queue_size = review_queue_size()
    with st.container(border=True):
        st.markdown("### 🔁  Missed Problem Review")
        if queue_size > 0:
            plural = "problem" if queue_size == 1 else "problems"
            st.caption("Practice these again to lock the concept in.")
            st.markdown(f"**{queue_size} missed {plural}** waiting for another look.")
            st.write("")
            if st.button(
                "Start review →",
                key="review_card_start",
                type="primary",
                use_container_width=True,
            ):
                practice_from_review(0)
                st.rerun()
        else:
            st.caption("Problems you miss on the first try will land here for review.")
            st.write("")
            st.write("")
            st.button(
                "Start review →",
                key="review_card_disabled",
                type="primary",
                use_container_width=True,
                disabled=True,
            )


def _render_review_expander():
    """Compact per-item queue list. Renders only when queue is non-empty."""
    queue_size = review_queue_size()
    if queue_size == 0:
        return

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


def _render_learning_path():
    """Three-tier curriculum preview with chapter topic hints below each
    tier's description. Informational only — no buttons. Topic lines use
    middle-dot separators to keep the rhythm visual rather than rhetorical.
    """
    _section_label("The full curriculum")

    tiers = [
        ("Foundation", "Ch. 1–4",
         "Build the universal ratio-and-proportion method.",
         "Parenteral doses · Powdered drugs · Percents · Solutions"),
        ("Applications", "Ch. 5–7",
         "Apply the method to body-based and infusion dosing.",
         "Body weight · BSA · Infusion rates"),
        ("Advanced", "Ch. 8–10",
         "Specialized dosing techniques beyond the standard ratio.",
         "Dilutions · Parenteral nutrition · Medication labels"),
    ]

    cols = st.columns(3, gap="medium")
    for col, (tier_name, ch_range, description, topics) in zip(cols, tiers):
        with col:
            with st.container(border=True):
                st.markdown(
                    f'<div style="padding:0.5rem 0.25rem;">'
                    f'<div style="font-weight:600; font-size:1.05rem; margin-bottom:0.2rem;">{tier_name}</div>'
                    f'<div style="opacity:0.55; font-size:0.78rem; '
                    f'text-transform:uppercase; letter-spacing:0.06em; '
                    f'margin-bottom:0.75rem;">{ch_range}</div>'
                    f'<div style="font-size:0.95rem; opacity:0.85; margin-bottom:0.6rem; line-height:1.5;">{description}</div>'
                    f'<div style="font-size:0.85rem; opacity:0.7; line-height:1.6;">{topics}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ============================================================
# Practice (UNCHANGED from v6.4)
# ============================================================

def render_practice_view():
    """Practice page entry point.

    Dual mode:
      - No chapter selected → render_practice_empty_state (diagnostic view)
      - Chapter selected   → active practice flow
    """
    if (
        st.session_state.selected_chapter_key is None
        and not st.session_state.mixed_mode
    ):
        render_practice_empty_state()
        return

    if st.session_state.current_problem is None:
        new_problem()

    problem = st.session_state.current_problem
    chapter = get_chapter(problem["chapter_key"])

    top_back, top_title = st.columns([1, 5])
    with top_back:
        if st.button("← Dashboard", use_container_width=True):
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


def render_practice_empty_state():
    """Practice page when no chapter is active. Houses the diagnostic content
    that used to live on the Progress page.
    """
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
    """Number input + Check button. Used for both first attempt and retry."""
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
    """Terminal state: full result + step-by-step + Next problem."""
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
