"""
Pharmacy Tech Math Practice — Streamlit app (v6, coach mode).

Layout overview:
    Sidebar    : session metrics, today's-goal progress, difficulty selector,
                 page nav, chapter list.
    Dashboard  : Mixed Practice + Recommended Focus, session stats, today's
                 goal, mastery bars by chapter, review queue.
    Practice   : coach-mode problem flow with a three-state machine
                 (answering → first_wrong → revealed). Wrong-first answers
                 trigger a gentle intervention with Hint / Try again /
                 Show solution. The full solution only renders in `revealed`.
    Calculator : dose-to-volume reference.
    Progress   : per-chapter accuracy breakdown.

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
    st.session_state.page = "Dashboard"
    reset_helpers()


def start_chapter(chapter_key, problem_type_key="_adaptive"):
    """Enter practice mode for a specific chapter and route to Practice."""
    st.session_state.selected_chapter_key = chapter_key
    st.session_state.mixed_mode = False
    st.session_state.problem_type_choice = problem_type_key
    st.session_state.page = "Practice"
    new_problem()


def start_mixed():
    """Enter mixed-practice mode across all chapters."""
    st.session_state.mixed_mode = True
    st.session_state.selected_chapter_key = None
    st.session_state.problem_type_choice = "_adaptive"
    st.session_state.page = "Practice"
    new_problem()


def practice_from_review(index):
    """Pop an entry from the review queue and start practicing that type."""
    entry = pop_review_queue_at(index)
    if entry:
        start_chapter(entry["chapter_key"], entry["problem_type_key"])


def check_answer(problem, user_answer):
    """Verify the answer and drive the coach state machine.

    Stats math preserved: record_attempt fires only on the FIRST submission,
    so retries and self-corrections don't affect mastery or streak. The
    first wrong submission also adds the problem to the review queue.

    Phase transitions:
        answering   + correct  →  revealed
        answering   + wrong    →  first_wrong   (record_attempt + push to queue)
        first_wrong + correct  →  revealed      (late-correct, no stats update)
        first_wrong + wrong    →  revealed      (full solution forced)
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
        # Second wrong submission → reveal the full solution.
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
    """Transition first_wrong → answering for a second attempt.

    Keeps attempt_count at 1 so the next Check is recognized as the second
    submission. Clears last_result so the input widget renders again, and
    bumps input_version so the number_input clears to 0.

    open_hint=True also flips on show_hint (the existing helper panel),
    which is what the 'Get a hint' button on the intervention screen uses.
    """
    st.session_state.problem_phase = "answering"
    st.session_state.last_result = None
    st.session_state.input_version += 1
    if open_hint:
        st.session_state.show_hint = True


def coach_reveal():
    """User clicked Show solution from the first_wrong intervention."""
    st.session_state.problem_phase = "revealed"


# ============================================================
# Sidebar (metrics, today's goal, difficulty, nav, chapter list)
# ============================================================

with st.sidebar:
    st.title("💊 Pharmacy Math")

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
    st.markdown(f"**🎯 Today's goal:** {min(goal_count, goal_target)} / {goal_target}")
    st.progress(goal_pct)

    st.divider()

    st.markdown("**🎚️ Difficulty**")
    st.radio(
        "Difficulty",
        ["Beginner", "Standard", "Challenge"],
        key="difficulty",
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("**Navigate**")
    st.radio(
        "Page",
        ["Dashboard", "Practice", "Calculator", "Progress"],
        key="page",
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

def render_dashboard():
    st.title("Dashboard")
    st.caption("Pick up where you left off, or jump into mixed practice.")
    st.write("")

    # Quick-start row
    focus_key = recommended_focus_chapter()
    if focus_key:
        focus_chapter = get_chapter(focus_key)
        focus_emoji, focus_status_label = chapter_status(focus_key)
        focus_mastery = chapter_mastery(focus_key)

        col_focus, col_mixed = st.columns(2)
        with col_focus:
            with st.container(border=True):
                st.markdown("### ⭐  Recommended focus")
                st.caption("Your weakest attempted chapter. Practice here to level up.")
                st.markdown(f"**Ch. {focus_chapter.number} — {focus_chapter.title}**")
                st.markdown(f"{focus_emoji} {focus_status_label}  •  Mastery: {focus_mastery}")
                if st.button(
                    "Practice this →",
                    key="dash_start_focus",
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
                    key="dash_start_mixed",
                    type="primary",
                    use_container_width=True,
                ):
                    start_mixed()
                    st.rerun()
    else:
        with st.container(border=True):
            c_text, c_btn = st.columns([4, 1])
            with c_text:
                st.markdown("### 🎯  Mixed practice")
                st.caption("Adaptive across all chapters. Focuses on your weakest topics first.")
            with c_btn:
                st.write("")
                if st.button(
                    "Start",
                    key="dash_start_mixed_solo",
                    type="primary",
                    use_container_width=True,
                ):
                    start_mixed()
                    st.rerun()

    st.write("")

    # Session stats row
    st.markdown("### 📊  Session stats")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Answered", total_attempts())
    accuracy_now = current_accuracy()
    s2.metric("Accuracy", f"{accuracy_now:.0%}" if accuracy_now is not None else "—")
    s3.metric("Streak", st.session_state.streak)
    s4.metric("Best streak", st.session_state.best_streak)

    # Today's goal
    goal_count, goal_target = daily_goal_progress()
    goal_display = min(goal_count, goal_target)
    st.markdown(f"**🎯 Today's goal:** {goal_display} / {goal_target} problems")
    st.progress(min(goal_count / goal_target, 1.0) if goal_target > 0 else 0.0)
    if goal_count == 0:
        st.caption("Resets when the browser session ends.")

    st.write("")

    # Mastery bars
    st.markdown("### 📈  Mastery by chapter")
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
            if st.button("Practice", key=f"dash_practice_{chapter.key}", use_container_width=True):
                start_chapter(chapter.key)
                st.rerun()

    st.write("")

    # Review queue
    queue_size = review_queue_size()
    st.markdown(f"### 🔁  Review queue  ({queue_size})")
    if queue_size == 0:
        st.caption("Problems you miss on the first try will land here so you can revisit the topic.")
    else:
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
                    "Practice this →",
                    key=f"review_start_{i}",
                    use_container_width=True,
                ):
                    practice_from_review(i)
                    st.rerun()
        st.write("")
        if st.button("Clear review queue", key="review_clear"):
            clear_review_queue()
            st.rerun()


# ============================================================
# Practice (coach-mode problem view)
# ============================================================

def render_practice_view():
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

    # Work-it-out fires only when the FIRST attempt was wrong and the answer
    # has been revealed (second wrong or Show solution). Late-correct leaves
    # last_result["correct"]=True, so this won't fire there.
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
    st.title("Practice")
    st.caption("Pick a chapter from the sidebar, or jump into mixed practice.")
    st.write("")
    with st.container(border=True):
        c_text, c_btn = st.columns([4, 1])
        with c_text:
            st.markdown("### 🎯  Mixed practice")
            st.caption("Adaptive across all ten chapters.")
        with c_btn:
            st.write("")
            if st.button(
                "Start",
                key="practice_empty_mixed",
                type="primary",
                use_container_width=True,
            ):
                start_mixed()
                st.rerun()


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
    """First-wrong screen: gentle message + Hint / Try again / Show solution.

    The correct answer and the full steps are NOT shown here. record_attempt
    has already fired for the first wrong submission, the streak is reset to
    zero, and the problem has been pushed to the review queue.
    """
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
        # Late-correct. Streak stays broken (already reset on the first wrong).
        st.info(
            "Nice correction — you got it on retry. This won't count toward your streak, "
            "but it helps your review progress."
        )
    else:
        # Either two wrong submissions or Show solution clicked.
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

page = st.session_state.page

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
