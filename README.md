# Pharmacy Tech Math Practice

Adaptive practice app for pharmacy technician math, organized around
curriculum chapters. Solution steps follow the textbook's universal
ratio-and-proportion format. Built with Streamlit and plain Python. No
database, no external APIs, no patient data.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

## File layout

```
app.py              Streamlit UI. Practice, Dose-to-Volume, Progress.
tracker.py          Session state, stats, streak, adaptive selection.
chapters/
  __init__.py       Imports each chapter, exposes CHAPTERS_LIST / CHAPTERS.
  base.py           Chapter and ProblemType dataclasses.
  ch01_parenteral.py through ch10_labels.py
                    One file per curriculum chapter.
requirements.txt    Just streamlit.
```

## Solution format

Every chapter follows the textbook's universal method:

1. Convert units if necessary.
2. Set up a ratio and proportion problem.
3. Cross multiply.
4. Divide both sides and cancel out the units.
5. State the answer.

Example (Chapter 1, mg per mL dosing):

```
Set up a ratio and proportion problem:
   40 mg / 1 mL  =  70 mg / X
Cross multiply:  X × 40 mg  =  1 mL × 70 mg
Divide both sides by 40 mg and cancel out the milligrams:
   X  =  (1 mL × 70 mg) / 40 mg
X = 1.75 mL  answer
```

This matches the pharmacy certification exam format.

## Chapters

| # | Title | Problem types |
|---|-------|---------------|
| 1 | Parenteral Doses Using Ratio and Proportion | mg/mL same units · unit conversion · units/mEq |
| 2 | Powdered Drug Preparations | powder volume · concentration · diluent needed |
| 3 | Calculations with Percents | grams from % · % from grams · volume for dose |
| 4 | Using Ratio and Proportion when Preparing Solutions | grams for solution · volume for dose · ratio to % |
| 5 | Dosage Calculations Based on Body Weight | kg given · lb to kg · find mL |
| 6 | Dosage Calculations Based on Body Surface Area | dose from BSA · find mL |
| 7 | Infusion Rates and Drip Rates | mL/hr · gtt/min · time to finish |
| 8 | Dilutions | new % after dilution · water to add (grams method, not C1V1=C2V2) |
| 9 | Parenteral Nutrition Calculations | additive volume from mEq · grams in base solution |
| 10 | Dosage Calculations from Medication Labels | same units · different units |

## Architecture (unchanged from v2)

`Chapter` contains a list of `ProblemType` objects. Each ProblemType has a
zero-argument generator that returns a problem dict with `question`, `answer`,
`unit`, `tolerance`, and `steps` (a list of strings shown to the student).
Stats are nested: `stats[chapter_key][problem_type_key]`, with an `_overall`
rollup per chapter. The tracker has separate adaptive pickers for cross-chapter
and within-chapter selection.

The `Chapter` dataclass has reserved fields for `learn_content` and
`guided_examples`, currently `None`. These hooks are ready for future Learn
and Guided Examples tabs.

## Reserved for future work

1. **Learn tab.** Per-chapter intro markdown explaining concepts.
2. **Guided Examples tab.** Worked problems the student clicks through.
3. **Persistence.** Save stats to a JSON file so progress survives a refresh.
4. **More problem types.** Add by writing one function per chapter file.
5. **Daily goal / XP / badges.** All doable on top of the existing stats.
