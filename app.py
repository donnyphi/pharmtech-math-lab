@@ -1,27 +1,25 @@
"""
Pharmacy Tech Math Practice — Streamlit app (v6, coach mode).
Pharmacy Tech Math Practice — Streamlit app (v6.4, simplified navigation).

Layout overview:
    Sidebar    : session metrics, today's-goal progress, difficulty selector,
                 page nav, chapter list.
    Dashboard  : Mixed Practice + Recommended Focus, session stats, today's
                 goal, mastery bars by chapter, review queue.
    Practice   : coach-mode problem flow with a three-state machine
                 (answering → first_wrong → revealed). Wrong-first answers
                 trigger a gentle intervention with Hint / Try again /
                 Show solution. The full solution only renders in `revealed`.
    Sidebar    : session metrics, session-goal progress, page nav,
                 difficulty selector, chapter list.
    Dashboard  : action-oriented launchpad. Hero CTAs, Recommended Focus +
                 Missed Problem Review cards, optional queue expander,
                 Learning Path Preview.
    Practice   : dual purpose. When a chapter is active, runs the coach-mode
                 problem flow (answering → first_wrong → revealed). When no
                 chapter is active, surfaces the diagnostic content that
                 used to live on the old Progress page: recommended focus,
                 mastery by chapter, accuracy by chapter, weak-chapter list.
                 The empty state IS the diagnostic page.
    Calculator : dose-to-volume reference.
    Progress   : per-chapter accuracy breakdown.

Routing note:
    The internal page state is `st.session_state.current_page`. The sidebar
    nav radio uses a SEPARATE widget key `nav_choice`. This split is
    deliberate: Streamlit raises StreamlitAPIException if you mutate a
    widget's session_state key after the widget has been instantiated on
    the current run. The chapter buttons in the sidebar render AFTER the
    nav radio, so they cannot touch `nav_choice` directly. They update
    `current_page` (which is not a widget key) and a pre-render sync block
    mirrors it into `nav_choice` on the next rerun.
    nav radio uses a SEPARATE widget key `nav_choice`. Setting current_page
    is always safe (not a widget key). The pre-render sync block mirrors
    current_page → nav_choice before the radio is instantiated.

Run with:
    streamlit run app.py
@@ -59,13 +57,21 @@
)
init_tracker()

# Valid pages after the v6.4 nav simplification. Progress is gone; its
# content lives on the Practice page's empty state.
_VALID_PAGES = ["Dashboard", "Practice", "Calculator"]

# Internal routing key. Kept separate from any widget key so it can be
# updated safely from anywhere in the script (including after widgets
# have rendered). tracker.init_tracker() still initializes an unused
# `page` key from v6.0; harmless and can be removed in a follow-up.
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
@@ -185,15 +191,7 @@ def check_answer(problem, user_answer):


def coach_retry(open_hint=False):
    """Transition first_wrong → answering for a second attempt.

    Keeps attempt_count at 1 so the next Check is recognized as the second
    submission. Clears last_result so the input widget renders again, and
    bumps input_version so the number_input clears to 0.

    open_hint=True also flips on show_hint (the existing helper panel),
    which is what the 'Get a hint' button on the intervention screen uses.
    """
    """Transition first_wrong → answering for a second attempt."""
    st.session_state.problem_phase = "answering"
    st.session_state.last_result = None
    st.session_state.input_version += 1
@@ -207,15 +205,11 @@ def coach_reveal():


# ============================================================
# Sidebar (metrics, today's goal, difficulty, nav, chapter list)
# Sidebar (metrics, session goal, nav, difficulty, chapter list)
# ============================================================

def _on_nav_change():
    """Sync current_page when the user clicks the navigation radio.

    Runs DURING widget processing (before the script reruns), so we can
    safely write to current_page here. Triggered by the radio's on_change.
    """
    """Sync current_page when the user clicks the navigation radio."""
    st.session_state.current_page = st.session_state.nav_choice


@@ -238,58 +232,53 @@ def _on_nav_change():

    st.divider()

    st.markdown("**🎚️ Difficulty**")
    st.radio(
        "Difficulty",
        ["Beginner", "Standard", "Challenge"],
        key="difficulty",
        label_visibility="collapsed",
    )

    st.divider()

    # Nav now sits above Difficulty per v6.4. Progress is no longer an
    # option; its content lives on the Practice page's empty state.
    st.markdown("**Navigate**")

    # Mirror current_page → nav_choice BEFORE the radio is instantiated.
    # Handles the chapter-button case: that handler updates current_page,
    # this block resyncs the radio's display on the next rerun. Safe to
    # write to a widget's key here because the widget does not exist yet
    # on this run.
    if st.session_state.get("nav_choice") != st.session_state.current_page:
        st.session_state.nav_choice = st.session_state.current_page

    st.radio(
        "Page",
        ["Dashboard", "Practice", "Calculator", "Progress"],
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
            # start_chapter writes current_page (not nav_choice) — safe even
            # though the nav radio has already been instantiated this run.
            start_chapter(chapter.key)
            st.rerun()


# ============================================================
# Dashboard
# Dashboard (action-oriented launchpad)
# ============================================================

def render_dashboard():
    """Action-oriented launchpad. Answers: 'What should I do next?'
    """Answers 'What should I do next?'

    Status detail (mastery bars, accuracy breakdown, weak chapters) lives on
    the Progress page. Glanceable session metrics (answered, accuracy,
    streak, best, session goal) live in the sidebar. This page is for
    decisions, not measurement.
    Section order: hero → action cards → optional queue expander →
    learning path. No status duplication of the sidebar; mastery and
    accuracy detail live on the Practice page.
    """
    _render_hero()
    st.write("")
@@ -300,13 +289,8 @@ def render_dashboard():
    with col_review:
        _render_review_card()

    # Compact expander preserves access to the per-item queue without
    # cluttering the action cards above.
    _render_review_expander()

    st.write("")
    _render_session_practice_plan()

    st.write("")
    _render_learning_path()

@@ -334,7 +318,6 @@ def _render_hero():
                if queue_size > 0
                else "🔁 Review Missed Problems"
            )
            # Disabled when queue is empty so the button is visible but inert.
            if st.button(
                review_label,
                key="hero_start_review",
@@ -347,16 +330,21 @@ def _render_hero():


def _render_focus_card():
    """Action card A: recommended focus, with no-data fallback to mixed."""
    """Action card A: Recommended Focus.

    Three states (has-focus / no-data / all-mastered) share a uniform
    five-element structure (heading + 3 content rows + button) so the
    card matches the visual height of _render_review_card across states.
    Spacer rows via st.write("") pad shorter states up to the same height.
    """
    focus_key = recommended_focus_chapter()
    with st.container(border=True):
        st.markdown("### ⭐  Recommended Focus")

        if focus_key:
            ch = get_chapter(focus_key)
            emoji, status_label = chapter_status(focus_key)
            mastery = chapter_mastery(focus_key)
            st.caption("Your weakest attempted chapter. Practicing here moves the needle fastest.")
            st.caption("Your weakest attempted chapter.")
            st.markdown(f"**Ch. {ch.number} — {ch.title}**")
            st.markdown(f"{emoji} {status_label}  •  Mastery: {mastery}")
            if st.button(
@@ -368,10 +356,8 @@ def _render_focus_card():
                start_chapter(focus_key)
                st.rerun()
        elif total_attempts() == 0:
            # First-run state.
            st.caption(
                "Complete 5 problems so the app can find your weak topics."
            )
            st.caption("Complete 5 problems so the app can find your weak topics.")
            st.write("")
            st.write("")
            if st.button(
                "Start Mixed Practice",
@@ -382,10 +368,8 @@ def _render_focus_card():
                start_mixed()
                st.rerun()
        else:
            # Every attempted chapter is at or above the Mastered threshold.
            st.caption(
                "Nothing weak right now. Mixed practice will surface new gaps as you go."
            )
            st.caption("Nothing weak right now. Mixed practice will surface new gaps as you go.")
            st.write("")
            st.write("")
            if st.button(
                "Start Mixed Practice",
@@ -398,14 +382,21 @@ def _render_focus_card():


def _render_review_card():
    """Action card B: count + CTA only. Per-item list is in the expander below."""
    """Action card B: Missed Problem Review.

    Mirrors _render_focus_card's five-element structure (heading + 3 content
    rows + button) for height parity. The empty-queue state uses a disabled
    Start review button rather than going button-less, so the visual weight
    matches the focus card's empty states.
    """
    queue_size = review_queue_size()
    with st.container(border=True):
        st.markdown("### 🔁  Missed Problem Review")
        if queue_size > 0:
            plural = "problem" if queue_size == 1 else "problems"
            st.caption("Practice these again to lock the concept in.")
            st.markdown(f"**{queue_size} missed {plural}** waiting for another look.")
            st.caption("Practicing the same problem type again is how the concept locks in.")
            st.write("")
            if st.button(
                "Start review →",
                key="review_card_start",
@@ -415,18 +406,20 @@ def _render_review_card():
                practice_from_review(0)
                st.rerun()
        else:
            st.caption(
                "Problems you miss on the first try will land here. "
                "You'll come back to a fresh problem of the same type so you can prove you've got it."
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
    """Optional drill-down: per-item queue list with individual Practice buttons.

    Only renders when the queue has at least one entry. Collapsed by default
    so the dashboard stays clean.
    """
    """Compact per-item queue list. Renders only when queue is non-empty."""
    queue_size = review_queue_size()
    if queue_size == 0:
        return
@@ -459,30 +452,15 @@ def _render_review_expander():
            st.rerun()


def _render_session_practice_plan():
    """Full-width three-step plan. Start Plan kicks off mixed practice."""
    with st.container(border=True):
        st.markdown("### 📋  Session Practice Plan")
        st.caption("A simple three-step session that builds depth across mixed, focus, and review.")
        st.write("")
        st.markdown("**Step 1.** Warm up with mixed practice.")
        st.markdown("**Step 2.** Practice your recommended focus chapter.")
        st.markdown("**Step 3.** Review missed problems.")
        st.write("")
        if st.button(
            "Start Plan →",
            key="plan_start",
            type="primary",
            use_container_width=True,
        ):
            start_mixed()
            st.rerun()


def _render_learning_path():
    """Three-tier curriculum preview. View Full Progress routes to Progress."""
    """Three-tier curriculum preview. Informational only — no button.

    Removed the v6.3 'View Full Progress' button since Progress is no longer
    a page. Diagnostic detail lives on the Practice page now and is reachable
    via the Practice nav option when no chapter is active.
    """
    st.markdown("### 🗺️  Learning Path Preview")
    st.caption("The curriculum at a glance. Chapter detail and mastery live on the Progress page.")
    st.caption("The curriculum at a glance. Mastery and accuracy detail live on the Practice page.")

    tiers = [
        ("Foundation",   "Ch. 1–4",  "Build the universal ratio-and-proportion method."),
@@ -498,25 +476,18 @@ def _render_learning_path():
                st.caption(ch_range)
                st.write(description)

    st.write("")
    if st.button(
        "View Full Progress →",
        key="learning_path_view_progress",
        use_container_width=True,
    ):
        # current_page is not a widget key, so this is safe even though the
        # nav radio has already rendered this run. The pre-render sync block
        # will resync nav_choice on the next rerun.
        st.session_state.current_page = "Progress"
        st.rerun()



# ============================================================
# Practice (coach-mode problem view)
# Practice (coach-mode problem view + diagnostic empty state)
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
@@ -561,24 +532,137 @@ def render_practice_view():


def render_practice_empty_state():
    """Practice page when no chapter is active. Houses the diagnostic content
    that used to live on the Progress page: recommended-focus callout,
    mastery by chapter, accuracy by chapter, and the weak-chapters list.
    A quick-start strip at the top offers Mixed Practice plus (when relevant)
    Review Missed Problems.
    """
    st.title("Practice")
    st.caption("Pick a chapter from the sidebar, or jump into mixed practice.")
    st.caption("Pick a chapter from the sidebar, or use the quick-start options below.")
    st.write("")
    with st.container(border=True):
        c_text, c_btn = st.columns([4, 1])
        with c_text:
            st.markdown("### 🎯  Mixed practice")
            st.caption("Adaptive across all ten chapters.")
        with c_btn:
            st.write("")

    # --- Quick-start CTA strip ---
    queue_size = review_queue_size()
    if queue_size > 0:
        c1, c2 = st.columns(2)
        with c1:
            if st.button(
                "Start",
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

    # --- Recommended focus callout (moved from old Progress page) ---
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

    # --- Mastery by chapter (moved from old Progress page) ---
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

    # --- Accuracy by chapter (deeper detail, moved from old Progress page) ---
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

    # --- Weak chapters list (moved from old Progress page) ---
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
@@ -619,12 +703,7 @@ def render_answer_input(problem):


def render_coach_intervention(problem):
    """First-wrong screen: gentle message + Hint / Try again / Show solution.

    The correct answer and the full steps are NOT shown here. record_attempt
    has already fired for the first wrong submission, the streak is reset to
    zero, and the problem has been pushed to the review queue.
    """
    """First-wrong screen: gentle message + Hint / Try again / Show solution."""
    result = st.session_state.last_result
    st.warning(
        f"That's not it. You entered {result['user_answer']} {result['unit']}. "
@@ -677,7 +756,6 @@ def render_revealed_result():
            "but it helps your review progress."
        )
    else:
        # Either two wrong submissions or Show solution clicked.
        st.error(
            f"The correct answer is {result['correct_answer']} {result['unit']}."
        )
@@ -821,94 +899,3 @@ def render_work_it_out(chapter):
    st.caption(
        f"Formula: volume = dose / strength = {dose} / {strength} = {volume:.2f} mL."
    )

elif page == "Progress":
    st.title("Your progress")
    st.caption("Diagnostic detail. Use the Dashboard to decide what to practice next.")

    cols = st.columns(2)
    cols[0].metric("Current streak", st.session_state.streak)
    cols[1].metric("Best streak", st.session_state.best_streak)

    # Recommended Focus callout — moved here from the v6.1 dashboard.
    # Surfaces the weakest attempted chapter at the top of the diagnostic view.
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
                key="progress_focus_practice",
                type="primary",
                use_container_width=True,
            ):
                start_chapter(focus_key)
                st.rerun()

    # Mastery by chapter — moved here from the v6.1 dashboard.
    # Compact list showing emoji status, mastery score, and a per-chapter progress bar.
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
            if st.button("Practice", key=f"progress_practice_{chapter.key}", use_container_width=True):
                start_chapter(chapter.key)
                st.rerun()

    # Accuracy by chapter — existing detailed breakdown stays, with the
    # per-problem-type expander, as the deep-dive view below mastery.
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
