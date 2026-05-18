"""
Pharmacy Tech Math Practice — Streamlit app.

Layout overview:
    Sidebar      : streak metrics + page navigation (Practice / Calculator / Progress).
    Practice     : chapter grid OR practice view with helper buttons + stats panel.
    Calculator   : dose-to-volume reference (unchanged from v3).
    Progress     : per-chapter accuracy breakdown (unchanged from v3).

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
)

st.set_page_config(
    page_title="Pharmacy Tech Math Practice",
    page_icon="💊",
    layout="wide",
)
init_tracker()


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

    # Attach metadata so the renderer knows what to display and track.
    problem["chapter_key"] = chapter.key
    problem["problem_type_key"] = pt_key
    problem["chapter_title"] = chapter.title
    problem["chapter_number"] = chapter.number
    problem["problem_type_label"] = problem_type.label

    st.session_state.current_problem = problem
    st.session_state.last_result = None
    st.session_state.input_version += 1
    reset_helpers()


def go_to_chapter_grid():
    """Clear selection so the chapter grid renders."""
    st.session_state.selected_chapter_key = None
    st.session_state.mixed_mode = False
    st.session_state.current_problem = None
    st.session_state.last_result = None
    st.session_state.problem_type_choice = "_adaptive"
    reset_helpers()


def start_chapter(chapter_key):
    """Enter practice mode for a specific chapter."""
    st.session_state.selected_chapter_key = chapter_key
    st.session_state.mixed_mode = False
    st.session_state.problem_type_choice = "_adaptive"
    new_problem()


def start_mixed():
    """Enter mixed-practice mode across all chapters."""
    st.session_state.mixed_mode = True
    st.session_state.selected_chapter_key = None
    st.session_state.problem_type_choice = "_adaptive"
    new_problem()


def check_answer(problem, user_answer):
    """Verify the answer and store the result. Math preserved from v3,
    with the difficulty multiplier added on top of the textbook tolerance."""
    correct_value = problem["answer"]
    base_tolerance = max(abs(correct_value) * 0.01, problem["tolerance"])
    tolerance = base_tolerance * difficulty_tolerance_multiplier()
    is_correct = abs(user_answer - correct_value) <= tolerance
    record_attempt(problem["chapter_key"], problem["problem_type_key"], is_correct)
    st.session_state.last_result = {
        "correct": is_correct,
        "user_answer": user_answer,
        "correct_answer": correct_value,
        "steps": problem["steps"],
        "unit": problem["unit"],
    }


# ============================================================
# Sidebar dashboard (session metrics + difficulty + nav)
# ============================================================

with st.sidebar:
    st.title("💊 Pharmacy Math")

    # Session metrics — 2x2 grid of compact metrics
    st.markdown("**📊 This session**")
    row1 = st.columns(2)
    row1[0].metric("Answered", total_attempts())
    acc = current_accuracy()
    row1[1].metric("Accuracy", f"{acc:.0%}" if acc is not None else "—")
    row2 = st.columns(2)
    row2[0].metric("Streak", st.session_state.streak)
    row2[1].metric("Best", st.session_state.best_streak)

    st.divider()

    # Recommended focus — short hint at the weakest chapter
    st.markdown("**⭐ Recommended focus**")
    weak = recommend_weak_topic()
    if weak:
        st.markdown(f"_{weak}_")
    else:
        st.caption("Practice more to see recommendations.")

    st.divider()

    # Difficulty selector — bound directly to session state via key.
    st.markdown("**🎯 Difficulty**")
    st.radio(
        "Difficulty",
        ["Beginner", "Standard", "Challenge"],
        key="difficulty",
        label_visibility="collapsed",
    )

    st.divider()

    page = st.radio(
        "Navigate",
        ["Practice", "Calculator", "Progress"],
        label_visibility="collapsed",
    )


# ============================================================
# Practice — chapter grid view
# ============================================================

def render_chapter_grid():
    st.title("Choose a chapter")
    st.caption("Pick mixed practice, jump to a recommended focus, or browse the chapter list.")
    st.write("")

    # Recommended Focus + Mixed Practice cards. Side-by-side if there's data
    # to recommend from, otherwise Mixed Practice goes full width.
    focus_key = recommended_focus_chapter()
    if focus_key:
        focus_chapter = get_chapter(focus_key)
        focus_emoji, focus_status = chapter_status(focus_key)
        focus_mastery = chapter_mastery(focus_key)

        col_focus, col_mixed = st.columns(2)
        with col_focus:
            with st.container(border=True):
                st.markdown("### ⭐  Recommended focus")
                st.caption("Your weakest attempted chapter. Practice here to level up fast.")
                st.markdown(f"**Ch. {focus_chapter.number} — {focus_chapter.title}**")
                st.markdown(f"{focus_emoji} {focus_status}  •  Mastery: {focus_mastery}")
                if st.button(
                    "Practice this →",
                    key="start_focus",
                    type="primary",
                    use_container_width=True,
                ):
                    start_chapter(focus_key)
                    st.rerun()
        with col_mixed:
            with st.container(border=True):
                st.markdown("### 🎯  Mixed practice")
                st.caption("Adaptive across all chapters. Drills your weakest topics first.")
                st.write("")
                st.write("")
                if st.button(
                    "Start mixed",
                    key="start_mixed",
                    type="primary",
                    use_container_width=True,
                ):
                    start_mixed()
                    st.rerun()
    else:
        # No attempts yet — single full-width Mixed practice card.
        with st.container(border=True):
            c_text, c_btn = st.columns([4, 1])
            with c_text:
                st.markdown("### 🎯  Mixed practice")
                st.caption("Adaptive across all chapters. Focuses on your weakest topics first.")
            with c_btn:
                st.write("")
                if st.button(
                    "Start",
                    key="start_mixed",
                    type="primary",
                    use_container_width=True,
                ):
                    start_mixed()
                    st.rerun()

    st.write("")
    st.markdown("##### Or pick a specific chapter")
    st.write("")

    # 2-column grid of chapter cards, each showing status + mastery
    for row_start in range(0, len(CHAPTERS_LIST), 2):
        row = CHAPTERS_LIST[row_start:row_start + 2]
        cols = st.columns(2)
        for col, chapter in zip(cols, row):
            with col:
                with st.container(border=True):
                    st.caption(f"Chapter {chapter.number}")
                    st.markdown(f"#### {chapter.title}")
                    st.caption(chapter.summary)

                    emoji, status_label = chapter_status(chapter.key)
                    mastery = chapter_mastery(chapter.key)
                    overall = st.session_state.stats[chapter.key]["_overall"]

                    if overall["attempts"] == 0:
                        st.markdown(f"{emoji} **{status_label}**")
                    else:
                        st.markdown(
                            f"{emoji} **{status_label}**  •  Mastery: {mastery}"
                        )
                        st.progress(mastery / 100)

                    if st.button(
                        "Practice →",
                        key=f"start_{chapter.key}",
                        type="primary",
                        use_container_width=True,
                    ):
                        start_chapter(chapter.key)
                        st.rerun()


# ============================================================
# Practice — main view (problem card + stats panel)
# ============================================================

def render_practice_view():
    problem = st.session_state.current_problem
    chapter = get_chapter(problem["chapter_key"])

    # Top bar: back button + chapter header
    top_back, top_title = st.columns([1, 5])
    with top_back:
        if st.button("← Back", use_container_width=True):
            go_to_chapter_grid()
            st.rerun()
    with top_title:
        if st.session_state.mixed_mode:
            st.markdown("### 🎯  Mixed practice")
            st.caption(f"Currently on: Ch. {chapter.number} — {chapter.title}")
        else:
            st.markdown(f"### Ch. {chapter.number}. {chapter.title}")
            st.caption(chapter.summary)

    st.write("")

    # Single-column main area. Stats now live in the sidebar dashboard.
    render_problem_card(chapter, problem)
    result = st.session_state.last_result
    if result is not None and not result["correct"] and chapter.prerequisite_chapter:
        st.write("")
        render_work_it_out(chapter)


def render_problem_card(chapter, problem):
    with st.container(border=True):
        # Skill picker (single-chapter mode only)
        if not st.session_state.mixed_mode:
            render_skill_picker(chapter)

        # Three helper buttons across the top of the card
        render_helper_buttons(chapter, problem)

        # Conditional helper content (only what's toggled on)
        render_helper_content(chapter, problem)

        st.divider()

        # The actual problem
        st.caption(problem["problem_type_label"])
        st.markdown(f"#### {problem['question']}")
        st.write("")

        # Two states: answering vs reviewing
        if st.session_state.last_result is None:
            user_answer = st.number_input(
                f"Your answer ({problem['unit']})",
                value=0.0, step=0.1, format="%.2f",
                key=f"answer_input_{st.session_state.input_version}",
            )
            if st.button("Check answer", type="primary", use_container_width=True):
                check_answer(problem, user_answer)
                st.rerun()
        else:
            result = st.session_state.last_result
            if result["correct"]:
                st.success(
                    f"✅ Correct! You entered {result['user_answer']} {result['unit']}."
                )
            else:
                st.error(
                    f"❌ Not quite. You entered {result['user_answer']} {result['unit']}. "
                    f"Correct answer: {result['correct_answer']} {result['unit']}."
                )
            with st.expander("Step-by-step solution", expanded=not result["correct"]):
                for step in result["steps"]:
                    st.write(f"• {step}")
            if st.button("Next problem →", type="primary", use_container_width=True):
                new_problem()
                st.rerun()


def render_skill_picker(chapter):
    """Horizontal radio to switch problem type within a chapter.

    Includes 'Adaptive' as the default. Selecting a different option
    triggers a fresh problem from that type.
    """
    options = [("_adaptive", "Adaptive")] + [(pt.key, pt.label) for pt in chapter.problem_types]
    keys = [k for k, _ in options]
    labels = [lbl for _, lbl in options]

    current = st.session_state.problem_type_choice
    if current not in keys:
        # Defensive: if state has a key not valid for this chapter, reset.
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
            # Lazy-generate a worked example the first time it's shown
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
        # Reveal the first two steps — enough to set up the proportion.
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

if page == "Practice":
    if st.session_state.selected_chapter_key is None and not st.session_state.mixed_mode:
        render_chapter_grid()
    else:
        # Edge case: somehow landed here without a problem (e.g., direct page switch).
        if st.session_state.current_problem is None:
            new_problem()
        render_practice_view()


# ============================================================
# Calculator (dose-to-volume) — unchanged from v3
# ============================================================

elif page == "Calculator":
    st.title("Dose-to-Volume calculator")
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


# ============================================================
# Progress — unchanged from v3
# ============================================================

elif page == "Progress":
    st.title("Your progress")

    cols = st.columns(2)
    cols[0].metric("Current streak", st.session_state.streak)
    cols[1].metric("Best streak", st.session_state.best_streak)

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
