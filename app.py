"""
Pharmacy Tech Math Practice — Streamlit app.

Run with:
    streamlit run app.py
"""

import streamlit as st

from chapters import CHAPTERS, CHAPTERS_LIST, get_chapter, get_problem_type
from tracker import (
    init_tracker,
    record_attempt,
    pick_adaptive_chapter,
    pick_adaptive_problem_type,
    get_weak_chapters,
)

st.set_page_config(page_title="Pharmacy Tech Math Practice", page_icon="💊")
init_tracker()


MIXED_LABEL = "Mixed — adaptive across all chapters"
ADAPTIVE_TYPE_LABEL = "Adaptive (recommended)"


def chapter_label(chapter):
    """How a chapter is shown in the UI dropdown."""
    return f"Ch. {chapter.number}. {chapter.title}"


def find_chapter_by_label(label):
    return next(c for c in CHAPTERS_LIST if chapter_label(c) == label)


def new_problem(chapter_choice, problem_type_choice):
    """Resolve user selections into a concrete problem and store it in session state."""
    if chapter_choice == MIXED_LABEL:
        chapter_key = pick_adaptive_chapter()
        chapter = get_chapter(chapter_key)
        pt_key = pick_adaptive_problem_type(chapter)
    else:
        chapter = find_chapter_by_label(chapter_choice)
        if problem_type_choice == ADAPTIVE_TYPE_LABEL:
            pt_key = pick_adaptive_problem_type(chapter)
        else:
            pt_key = next(pt.key for pt in chapter.problem_types if pt.label == problem_type_choice)

    problem_type = get_problem_type(chapter.key, pt_key)
    problem = problem_type.generator()

    # Attach routing/tracking metadata for the app to use later.
    problem["chapter_key"] = chapter.key
    problem["problem_type_key"] = pt_key
    problem["chapter_title"] = chapter.title
    problem["chapter_number"] = chapter.number
    problem["problem_type_label"] = problem_type.label

    st.session_state.current_problem = problem
    st.session_state.last_result = None
    st.session_state.input_version += 1


# -------- Sidebar --------
st.sidebar.title("💊 Pharmacy Math")
st.sidebar.metric("Current streak", st.session_state.streak)
st.sidebar.metric("Best streak", st.session_state.best_streak)
page = st.sidebar.radio("Mode", ["Practice", "Dose-to-Volume", "Progress"])


# -------- Practice page --------
if page == "Practice":
    st.title("Practice problems")

    chapter_options = [MIXED_LABEL] + [chapter_label(c) for c in CHAPTERS_LIST]
    chapter_choice = st.selectbox("Chapter", chapter_options)

    # Show the problem-type selector only when a specific chapter is picked.
    problem_type_choice = ADAPTIVE_TYPE_LABEL
    if chapter_choice != MIXED_LABEL:
        chapter = find_chapter_by_label(chapter_choice)
        with st.expander(chapter.summary, expanded=False):
            st.caption("Learn and Guided Examples for this chapter are coming soon.")
        type_options = [ADAPTIVE_TYPE_LABEL] + [pt.label for pt in chapter.problem_types]
        problem_type_choice = st.selectbox("Problem type", type_options)

    # Generate the first problem on initial load.
    if st.session_state.current_problem is None:
        new_problem(chapter_choice, problem_type_choice)

    problem = st.session_state.current_problem
    st.caption(
        f"Ch. {problem['chapter_number']} · {problem['chapter_title']} · "
        f"{problem['problem_type_label']}"
    )
    st.write(problem["question"])

    # Two display states: answering vs. reviewing feedback.
    if st.session_state.last_result is None:
        user_answer = st.number_input(
            f"Your answer ({problem['unit']})",
            value=0.0, step=0.1, format="%.2f",
            key=f"answer_input_{st.session_state.input_version}",
        )
        if st.button("Check answer", type="primary"):
            correct_value = problem["answer"]
            tolerance = max(abs(correct_value) * 0.01, problem["tolerance"])
            is_correct = abs(user_answer - correct_value) <= tolerance
            record_attempt(problem["chapter_key"], problem["problem_type_key"], is_correct)
            st.session_state.last_result = {
                "correct": is_correct,
                "user_answer": user_answer,
                "correct_answer": correct_value,
                "steps": problem["steps"],
                "unit": problem["unit"],
            }
            st.rerun()
    else:
        result = st.session_state.last_result
        if result["correct"]:
            st.success(
                f"✅ Correct. You entered {result['user_answer']} {result['unit']}."
            )
        else:
            st.error(
                f"❌ Not quite. You entered {result['user_answer']} {result['unit']}. "
                f"Correct answer: {result['correct_answer']} {result['unit']}."
            )
        with st.expander("Step-by-step solution", expanded=not result["correct"]):
            for step in result["steps"]:
                st.write(f"• {step}")
        if st.button("Next problem", type="primary"):
            new_problem(chapter_choice, problem_type_choice)
            st.rerun()


# -------- Dose-to-Volume calculator --------
elif page == "Dose-to-Volume":
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


# -------- Progress page --------
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
