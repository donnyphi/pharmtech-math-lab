"""
Pharmacy Tech Math Practice — Streamlit app.

Run with:
    streamlit run app.py
"""

import streamlit as st

from problems import TOPICS, generate_problem
from tracker import (
    init_tracker,
    record_attempt,
    pick_adaptive_topic,
    get_weak_topics,
)

st.set_page_config(page_title="Pharmacy Tech Math Practice", page_icon="💊")
init_tracker()


def new_problem(topic_label):
    """Generate a new problem based on the user's topic selection."""
    if topic_label == "Adaptive (recommended)":
        topic_key = pick_adaptive_topic()
    else:
        topic_key = next(key for key, label in TOPICS.items() if label == topic_label)
    st.session_state.current_problem = generate_problem(topic_key)
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

    topic_label = st.selectbox(
        "Topic",
        ["Adaptive (recommended)"] + list(TOPICS.values()),
        help="Adaptive mode picks weaker topics more often.",
    )

    # Generate the first problem on initial load.
    if st.session_state.current_problem is None:
        new_problem(topic_label)

    problem = st.session_state.current_problem
    st.subheader(TOPICS[problem["topic"]])
    st.write(problem["question"])

    # Two states: answering vs. reviewing feedback.
    if st.session_state.last_result is None:
        user_answer = st.number_input(
            f"Your answer ({problem['unit']})",
            value=0.0,
            step=0.1,
            format="%.2f",
            key=f"answer_input_{st.session_state.input_version}",
        )
        if st.button("Check answer", type="primary"):
            correct_value = problem["answer"]
            # Tolerance: 1% of the answer with an absolute floor.
            tolerance = max(abs(correct_value) * 0.01, problem["tolerance"])
            is_correct = abs(user_answer - correct_value) <= tolerance
            record_attempt(problem["topic"], is_correct)
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
            new_problem(topic_label)
            st.rerun()


# -------- Dose-to-Volume page --------
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

    st.subheader("Accuracy by topic")
    for topic_key, label in TOPICS.items():
        stats = st.session_state.stats[topic_key]
        if stats["attempts"] == 0:
            st.write(f"**{label}** — not attempted yet")
        else:
            accuracy = stats["correct"] / stats["attempts"]
            st.write(
                f"**{label}** — {stats['correct']}/{stats['attempts']} "
                f"correct ({accuracy:.0%})"
            )
            st.progress(accuracy)

    weak = get_weak_topics()
    if weak:
        st.subheader("Topics to focus on")
        for topic_key, accuracy in weak:
            st.write(f"• {TOPICS[topic_key]} — {accuracy:.0%} accuracy")
    else:
        st.caption(
            "Attempt at least 3 problems in a topic to see weak-topic recommendations."
        )
