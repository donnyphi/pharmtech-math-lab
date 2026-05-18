"""Chapter 4: Using Ratio and Proportion when Preparing Solutions.

Core definition for ratio strengths:
  1:N w/v  =  1 g in N mL of solution    (solid in liquid)
  1:N v/v  =  1 mL in N mL of solution   (liquid in liquid)
  1:N w/w  =  1 g in N g of compound     (solid in solid)
"""

import random
from .base import Chapter, ProblemType


def gen_grams_for_ratio_solution():
    """How many grams to make X mL of a 1:N w/v solution."""
    options = [
        # (drug, ratio_denom_N, volume_mL)
        ("Neosporin", 1000, 2000),
        ("sodium hypochlorite", 10, 1000),
        ("potassium permanganate", 500, 750),
        ("gentian violet", 10000, 500),
        ("a drug", 4000, 750),
        ("Neosporin", 1000, 1000),
    ]
    drug, ratio_n, volume_mL = random.choice(options)
    # 1 g / N mL = X g / volume_mL  →  X = volume/N
    grams = round(volume_mL / ratio_n, 4)

    return {
        "question": (
            f"You are to prepare {volume_mL} mL of a 1:{ratio_n:,} w/v {drug} solution. "
            f"How many grams of {drug} are required?"
        ),
        "answer": grams,
        "unit": "g",
        "tolerance": 0.01,
        "steps": [
            f"Recall: 1:{ratio_n:,} w/v means 1 g in {ratio_n:,} mL.",
            "Set up a ratio and proportion problem:",
            f"   1 g / {ratio_n:,} mL  =  X / {volume_mL} mL",
            f"Cross multiply:  X × {ratio_n:,} mL  =  1 g × {volume_mL} mL",
            f"Divide both sides by {ratio_n:,} mL and cancel out the milliliters:",
            f"   X  =  (1 g × {volume_mL} mL) / {ratio_n:,} mL",
            f"X = {grams} g  answer",
        ],
    }


def gen_volume_for_dose_from_ratio():
    """Given a 1:N w/v solution and a dose in mg, find the volume needed."""
    options = [
        # (drug, ratio_denom_N, dose_mg)
        ("epinephrine (adrenalin)", 1000, 0.4),       # 1:1000 = 1 mg/mL → 0.4 mL
        ("epinephrine (adrenalin)", 1000, 0.1),       # 1:1000 = 1 mg/mL → 0.1 mL
        ("cocaine", 40, 80),                          # 1:40 = 25 mg/mL → 3.2 mL
        ("neostigmine", 1000, 12.5),                  # 1:1000 = 1 mg/mL → 12.5 mL
        ("bupivacaine", 400, 25),                     # 1:400 = 2.5 mg/mL → 10 mL
        ("a drug", 1000, 0.5),                        # 0.5 mL
        ("a drug", 5000, 4),                          # 1:5000 = 0.2 mg/mL → 20 mL
    ]
    drug, ratio_n, dose_mg = random.choice(options)
    # 1 g per N mL = 1000 mg per N mL → mg/mL = 1000/N
    mg_per_mL = 1000 / ratio_n
    volume = round(dose_mg / mg_per_mL, 2)

    return {
        "question": (
            f"{drug.capitalize()} is available as a 1:{ratio_n:,} w/v solution. "
            f"A patient is to receive {dose_mg} mg. How many mL are needed?"
        ),
        "answer": volume,
        "unit": "mL",
        "tolerance": 0.02,
        "steps": [
            f"Recall: 1:{ratio_n:,} w/v means 1 g in {ratio_n:,} mL.",
            f"Convert to milligrams: 1 g = 1,000 mg, so 1:{ratio_n:,}  =  1,000 mg / {ratio_n:,} mL.",
            "Set up a ratio and proportion problem:",
            f"   1,000 mg / {ratio_n:,} mL  =  {dose_mg} mg / X",
            f"Cross multiply:  X × 1,000 mg  =  {ratio_n:,} mL × {dose_mg} mg",
            f"Divide both sides by 1,000 mg and cancel out the milligrams:",
            f"   X  =  ({ratio_n:,} mL × {dose_mg} mg) / 1,000 mg",
            f"X = {volume} mL  answer",
        ],
    }


def gen_ratio_to_percent():
    """Convert a 1:N w/v ratio to percentage strength."""
    options = [2000, 5000, 50, 60, 250, 100000, 100, 400, 2500]
    ratio_n = random.choice(options)
    # 1 g per N mL → grams per 100 mL = 100/N
    percent = round(100 / ratio_n, 4)

    return {
        "question": (
            f"Express 1:{ratio_n:,} w/v as a percentage strength."
        ),
        "answer": percent,
        "unit": "%",
        "tolerance": 0.001,
        "steps": [
            f"Recall: 1:{ratio_n:,} w/v means 1 g in {ratio_n:,} mL.",
            "Recall: percentage strength means grams in 100 mL.",
            "Set up a ratio and proportion to find grams in 100 mL:",
            f"   1 g / {ratio_n:,} mL  =  X / 100 mL",
            f"Cross multiply:  X × {ratio_n:,} mL  =  1 g × 100 mL",
            f"Divide both sides by {ratio_n:,} mL and cancel out the milliliters:",
            f"   X  =  (1 g × 100 mL) / {ratio_n:,} mL",
            f"   X  =  {percent} g  in 100 mL",
            f"Percentage strength = {percent}%  answer",
        ],
    }


CHAPTER = Chapter(
    key="solutions_ratio",
    number=4,
    title="Using Ratio and Proportion when Preparing Solutions",
    summary="Work with ratio-strength solutions (1:N w/v): find grams, volume for a dose, or convert to %.",
    problem_types=[
        ProblemType(
            "grams_for_solution",
            "Grams needed to prepare a 1:N w/v solution",
            gen_grams_for_ratio_solution,
        ),
        ProblemType(
            "volume_for_dose",
            "Volume needed for a dose from a 1:N solution",
            gen_volume_for_dose_from_ratio,
        ),
        ProblemType(
            "ratio_to_percent",
            "Convert a 1:N ratio strength to percentage",
            gen_ratio_to_percent,
        ),
    ],
)
