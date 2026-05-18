"""
Session-state tracker for practice stats, streaks, and adaptive topic selection.

State lives in st.session_state, so it resets when the user refreshes the
browser. Persistence (JSON file or SQLite) would be a v2 enhancement.
"""

import random
import streamlit as st

from problems import TOPICS


def init_tracker():
    """Set up all session-state keys if they don't exist yet."""
    if "stats" not in st.session_state:
        st.session_state.stats = {
            topic: {"attempts": 0, "correct": 0} for topic in TOPICS
        }
    if "streak" not in st.session_state:
        st.session_state.streak = 0
    if "best_streak" not in st.session_state:
        st.session_state.best_streak = 0
    if "current_problem" not in st.session_state:
        st.session_state.current_problem = None
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "input_version" not in st.session_state:
        # Bumped each time we generate a new problem so the answer input resets.
        st.session_state.input_version = 0


def record_attempt(topic_key, is_correct):
    """Update stats and streak after the user submits an answer."""
    st.session_state.stats[topic_key]["attempts"] += 1
    if is_correct:
        st.session_state.stats[topic_key]["correct"] += 1
        st.session_state.streak += 1
        if st.session_state.streak > st.session_state.best_streak:
            st.session_state.best_streak = st.session_state.streak
    else:
        st.session_state.streak = 0


def pick_adaptive_topic():
    """
    Pick a topic with weight inversely proportional to accuracy.

    Topics with fewer than 3 attempts get a flat baseline weight so the
    student explores all topics before adaptive logic kicks in fully.
    """
    topics = list(TOPICS.keys())
    weights = []
    for topic in topics:
        stats = st.session_state.stats[topic]
        if stats["attempts"] < 3:
            weight = 1.0
        else:
            accuracy = stats["correct"] / stats["attempts"]
            # Lower accuracy gets higher weight, clamped so even strong topics still appear.
            weight = max(1.0 - accuracy, 0.1) * 2
        weights.append(weight)
    return random.choices(topics, weights=weights, k=1)[0]


def get_weak_topics(threshold=0.7, min_attempts=3):
    """Return topics with accuracy below threshold, sorted weakest first."""
    weak = []
    for topic_key in TOPICS:
        stats = st.session_state.stats[topic_key]
        if stats["attempts"] >= min_attempts:
            accuracy = stats["correct"] / stats["attempts"]
            if accuracy < threshold:
                weak.append((topic_key, accuracy))
    return sorted(weak, key=lambda pair: pair[1])
