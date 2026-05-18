# Pharmacy Tech Math Practice

An adaptive practice app for pharmacy technician math. Built with Streamlit and
plain Python — no database, no external APIs, no patient data.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

The browser opens automatically at `http://localhost:8501`.

## Files

| File | What it does |
|------|--------------|
| `app.py` | Streamlit UI. Three modes: Practice, Dose-to-Volume, Progress. |
| `problems.py` | One generator function per topic. Each returns a question, answer, unit, and step-by-step solution. |
| `tracker.py` | Session-state setup, streak logic, and the adaptive topic picker. |
| `requirements.txt` | Just `streamlit`. |

## How it works

**Topics covered:** unit conversion, tablet dose calculation, percent strength
(w/v), IV flow rate, days supply.

**Adaptive mode** picks topics using weighted random selection. Topics with
under 3 attempts get a flat baseline weight (so everything gets explored
first). After that, weight scales inversely with accuracy.

**Answer checking** uses a tolerance of max(1% of the answer, 0.01) so students
aren't punished for tiny rounding differences.

**Tracking** lives in `st.session_state` — it resets when the browser refreshes.
That's intentional for v1 simplicity.

## Ideas for v2

1. **Persistence.** Save stats to a JSON file in `~/.pharmacy_practice.json` so
   progress survives page refreshes. About 15 lines of code in `tracker.py`.
2. **More topics.** Alligation, ratio strength, drops per minute, mg/kg dosing,
   business math (markup, AWP). Each is one new function in `problems.py` plus
   a line in the `TOPICS` and `GENERATORS` dicts.
3. **Difficulty levels.** Add an `"easy" | "medium" | "hard"` parameter to each
   generator that controls the range of input values.
4. **Duolingo-style features.** Daily goal counter, XP bar, badge for hitting
   a 10-streak. All doable with session state plus a small JSON persistence
   layer.
5. **Explanation depth toggle.** Short solution vs. detailed walkthrough.
6. **Topic-level review screen.** Show the last 5 missed problems per topic
   with their solutions.
