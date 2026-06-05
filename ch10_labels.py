
"""Chapter 10: Dosage Calculations from Medication Labels.

The student reads the concentration from a medication label and calculates the volume
needed for the prescribed dose. The textbook emphasizes:
  1. Make sure the units match. Convert if necessary.
  2. Set up a ratio and proportion using the label concentration.
"""

import random
from .base import Chapter, ProblemType


def gen_label_same_units():
    """Label and order use the same units. Direct ratio and proportion."""
    options = [
        # (drug_name, label_amount, label_volume_mL, label_unit, doses)
        ("Adriamycin", 200, 100, "mg", [33, 50, 100, 150]),
        ("epinephrine", 1, 10, "mg", [0.3, 0.5, 0.8, 1]),
        ("gentamicin", 40, 1, "mg", [60, 80, 100, 175]),
        ("calcium gluconate", 5, 50, "g", [0.5, 1, 1.5, 2]),
        ("Heparin", 5000, 1, "units", [2500, 7500, 10000]),
    ]
    drug, label_amt, label_vol, unit, doses = random.choice(options)
    ordered = random.choice(doses)
    # volume = (ordered × label_vol) / label_amt
    answer = round((ordered * label_vol) / label_amt, 3)

    return {
        "question": (
            f"The label on a {drug} vial states '{label_amt} {unit} per {label_vol} mL'. "
            f"The order is for {ordered} {unit}. How many mL are needed?"
        ),
        "answer": answer,
        "unit": "mL",
        "tolerance": 0.05,
        "steps": [
            f"Concentration from the label: {label_amt} {unit} per {label_vol} mL.",
            "Make sure the units match (they do, both in " + unit + ").",
            "Set up a ratio and proportion problem:",
            f"   {label_amt} {unit} / {label_vol} mL  =  {ordered} {unit} / X",
            f"Cross multiply:  X × {label_amt} {unit}  =  {label_vol} mL × {ordered} {unit}",
            f"Divide both sides by {label_amt} {unit} and cancel out the {unit}:",
            f"   X  =  ({label_vol} mL × {ordered} {unit}) / {label_amt} {unit}",
            f"X = {answer} mL  answer",
        ],
    }


def gen_label_different_units():
    """Label is in %, or units don't match the order. Convert first."""
    case = random.choice(["percent_label", "g_per_mL_to_mg"])

    if case == "percent_label":
        # Label gives a % concentration, order is in mg or g
        options = [
            # (drug, percent, dose, dose_unit)
            ("magnesium sulfate", 50, 2, "g"),
            ("calcium gluconate", 10, 1.5, "g"),
            ("mannitol", 25, 3.5, "g"),
            ("lidocaine", 1, 40, "mg"),       # 1% = 10 mg/mL → 40 mg in 4 mL
            ("calcium gluconate", 10, 500, "mg"),  # 10% = 100 mg/mL → 500 mg in 5 mL
        ]
        drug, percent, dose, dose_unit = random.choice(options)
        # Convert to grams for calculation
        dose_g = dose if dose_unit == "g" else dose / 1000
        # percent g per 100 mL: volume = dose_g / (percent/100) × 1 (actually dose_g * 100 / percent)
        volume = round((dose_g * 100) / percent, 2)

        if dose_unit == "g":
            conversion_step = f"   The dose is {dose} g (no conversion needed; percentage gives grams)."
        else:
            conversion_step = f"   Convert dose to grams: {dose} mg  =  {dose_g} g (because 1,000 mg = 1 g)."

        return {
            "question": (
                f"The label on a {drug} vial reads '{percent}%'. "
                f"A patient is to be given {dose} {dose_unit}. How many mL are needed?"
            ),
            "answer": volume,
            "unit": "mL",
            "tolerance": 0.05,
            "steps": [
                f"Recall: percentage strength means grams in 100 mL.",
                f"   {percent}%  =  {percent} g / 100 mL",
                conversion_step,
                "Set up a ratio and proportion problem:",
                f"   {percent} g / 100 mL  =  {dose_g} g / X",
                f"Cross multiply:  X × {percent} g  =  100 mL × {dose_g} g",
                f"Divide both sides by {percent} g and cancel out the grams:",
                f"   X  =  (100 mL × {dose_g} g) / {percent} g",
                f"X = {volume} mL  answer",
            ],
        }

    # g_per_mL_to_mg case: label in g, order in mg
    options = [
        # (drug, label_g, label_mL, dose_mg)
        ("a drug", 1, 10, 400),       # 1 g/10 mL = 100 mg/mL → 4 mL
        ("ampicillin", 1, 5, 250),    # 200 mg/mL → 1.25 mL
        ("a drug", 0.5, 5, 50),       # 100 mg/mL → 0.5 mL
        ("a drug", 2, 5, 500),        # 400 mg/mL → 1.25 mL
    ]
    drug, label_g, label_mL, dose_mg = random.choice(options)
    label_mg = label_g * 1000
    answer = round((dose_mg * label_mL) / label_mg, 3)

    return {
        "question": (
            f"The label on a {drug} vial reads '{label_g} g per {label_mL} mL'. "
            f"The order is for {dose_mg} mg. How many mL are needed?"
        ),
        "answer": answer,
        "unit": "mL",
        "tolerance": 0.02,
        "steps": [
            "Change the grams to milligrams so the units of measurement are the same:",
            f"   Label: {label_g} g per {label_mL} mL  =  {int(label_mg)} mg per {label_mL} mL",
            "Set up a ratio and proportion problem:",
            f"   {int(label_mg)} mg / {label_mL} mL  =  {dose_mg} mg / X",
            f"Cross multiply:  X × {int(label_mg)} mg  =  {label_mL} mL × {dose_mg} mg",
            f"Divide both sides by {int(label_mg)} mg and cancel out the milligrams:",
            f"   X  =  ({label_mL} mL × {dose_mg} mg) / {int(label_mg)} mg",
            f"X = {answer} mL  answer",
        ],
    }


CHAPTER = Chapter(
    key="med_labels",
    number=10,
    title="Dosage Calculations from Medication Labels",
    summary="Read concentration from a label and calculate the volume needed. Convert units when label and order disagree.",
    problem_types=[
        ProblemType(
            "same_units",
            "Label and order use the same units",
            gen_label_same_units,
        ),
        ProblemType(
            "different_units",
            "Label and order use different units (convert first)",
            gen_label_different_units,
        ),
    ],
)
