
"""Chapter 9: Parenteral Nutrition Calculations.

TPN problems use ratio and proportion with these common concentrations:
  Potassium chloride       2 mEq/mL
  Sodium chloride 14.6%    2.5 mEq/mL
  Calcium gluconate 10%    4.65 mEq/10 mL
  Magnesium sulfate 50%    40.6 mEq/10 mL
  Sodium acetate           2 mEq/mL
  Potassium phosphate      4.4 mEq/mL
  Sodium phosphate         60 mEq/15 mL
  Humulin R insulin        100 units/mL
  Vitamin C                250 mg/2 mL

Base solutions: dextrose (10-70%), amino acids/Travasol (3.5-15%), fat emulsions.
"""

import random
from .base import Chapter, ProblemType


def gen_additive_volume_from_mEq():
    """Find mL of an additive needed from an mEq order."""
    options = [
        # (additive_name, conc_mEq_per_mL)
        ("potassium chloride (KCl)", 2),
        ("sodium chloride 14.6%", 2.5),
        ("sodium acetate", 2),
        ("potassium acetate 19.6%", 2),
        ("potassium phosphate", 4.4),
    ]
    drug, conc = random.choice(options)
    # Pick a clean mEq order
    ordered = random.choice([10, 15, 20, 25, 30, 33, 40, 50])
    answer = round(ordered / conc, 2)

    return {
        "question": (
            f"A TPN order requires {ordered} mEq of {drug}. "
            f"The pharmacy stocks the drug in a concentration of {conc} mEq/mL. "
            f"How many mL should be added to the TPN bag?"
        ),
        "answer": answer,
        "unit": "mL",
        "tolerance": 0.05,
        "steps": [
            f"Concentration available: {conc} mEq/mL.",
            "Set up a ratio and proportion problem:",
            f"   {conc} mEq / 1 mL  =  {ordered} mEq / X",
            f"Cross multiply:  X × {conc} mEq  =  1 mL × {ordered} mEq",
            f"Divide both sides by {conc} mEq and cancel out the milliequivalents:",
            f"   X  =  (1 mL × {ordered} mEq) / {conc} mEq",
            f"X = {answer} mL  answer",
        ],
    }


def gen_grams_in_base_solution():
    """Calculate grams of dextrose (or amino acid) in a TPN base solution."""
    case = random.choice(["dextrose", "amino_acid"])

    if case == "dextrose":
        # Dextrose concentrations 10-70%, common: 50%, 70%
        percent = random.choice([10, 25, 50, 70])
        volume = random.choice([250, 500, 900, 1000])
        component = "dextrose"
    else:
        # Travasol/amino acid: 3.5-15%
        percent = random.choice([3.5, 5, 8.5, 10, 15])
        volume = random.choice([250, 500, 1000])
        component = "amino acid (Travasol)"

    grams = round((percent / 100) * volume, 2)

    return {
        "question": (
            f"A TPN base solution contains {volume} mL of {percent}% {component}. "
            f"How many grams of {component} are in the base solution?"
        ),
        "answer": grams,
        "unit": "g",
        "tolerance": 0.1,
        "steps": [
            f"Recall: percentage strength means grams in 100 mL.",
            f"   {percent}%  =  {percent} g / 100 mL",
            "Set up a ratio and proportion problem:",
            f"   {percent} g / 100 mL  =  X / {volume} mL",
            f"Cross multiply:  X × 100 mL  =  {percent} g × {volume} mL",
            f"Divide both sides by 100 mL and cancel out the milliliters:",
            f"   X  =  ({percent} g × {volume} mL) / 100 mL",
            f"X = {grams} g {component}  answer",
        ],
    }


CHAPTER = Chapter(
    key="parenteral_nutrition",
    number=9,
    title="Parenteral Nutrition Calculations",
    summary="TPN calculations: additive volumes from mEq orders, and grams of dextrose or amino acids in base solutions.",
    problem_types=[
        ProblemType(
            "additive_volume",
            "mL of additive from an mEq order",
            gen_additive_volume_from_mEq,
        ),
        ProblemType(
            "grams_in_base",
            "Grams of dextrose or amino acid in a base solution",
            gen_grams_in_base_solution,
        ),
    ],
)
