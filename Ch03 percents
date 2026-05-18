"""Chapter 3: Calculations with Percents.

Core definition:  % w/v  =  grams of solute per 100 mL of solution
Examples from the textbook:
  - D5W: 5 g dextrose / 100 mL  (5%)
  - Normal saline: 0.9 g NaCl / 100 mL  (0.9%)
  - 23.4% NaCl: 23.4 g NaCl / 100 mL
"""

import random
from .base import Chapter, ProblemType


def gen_grams_from_percent():
    """Given % w/v and volume, find grams of solute."""
    options = [
        # (drug name, percent, volumes)
        ("amino acid", 8.5, [250, 500, 1000]),
        ("dextrose", 5, [250, 500, 1000, 1500]),
        ("glucose", 10, [500, 1000, 1500]),
        ("dextrose", 50, [50, 100, 250]),
        ("sodium chloride", 0.9, [250, 500, 1000]),
        ("mannitol", 25, [50, 100, 250]),
        ("calcium gluconate", 10, [10, 50, 100]),
        ("magnesium sulfate", 50, [10, 20, 50]),
    ]
    drug, percent, volumes = random.choice(options)
    volume = random.choice(volumes)
    grams = round((percent / 100) * volume, 2)

    return {
        "question": (
            f"How many grams of {drug} are in {volume} mL of a {percent}% w/v solution?"
        ),
        "answer": grams,
        "unit": "g",
        "tolerance": 0.05,
        "steps": [
            f"Recall: percentage strength means grams in 100 mL.",
            f"   {percent}%  =  {percent} g / 100 mL",
            "Set up a ratio and proportion problem:",
            f"   {percent} g / 100 mL  =  X / {volume} mL",
            f"Cross multiply:  X × 100 mL  =  {percent} g × {volume} mL",
            f"Divide both sides by 100 mL and cancel out the milliliters:",
            f"   X  =  ({percent} g × {volume} mL) / 100 mL",
            f"X = {grams} g  answer",
        ],
    }


def gen_percent_from_grams_and_volume():
    """Given grams of solute and volume, find % w/v."""
    options = [
        # (drug, grams, volume in mL)
        ("NaCl", 3, 25),
        ("a powdered drug", 170, 1000),
        ("a powdered drug", 13.5, 500),
        ("ampicillin", 25, 100),
        ("a powder", 8.8, 160),
        ("dextrose", 450, 1000),
        ("an antibiotic", 2.4, 6),
        ("a drug", 80, 600),
    ]
    drug, grams, volume = random.choice(options)
    # Calculate % = grams in 100 mL
    percent = round((grams / volume) * 100, 2)

    return {
        "question": (
            f"You have dissolved {grams} g of {drug} in {volume} mL of solvent. "
            f"What is the percentage strength of the solution?"
        ),
        "answer": percent,
        "unit": "%",
        "tolerance": 0.1,
        "steps": [
            "Recall: percentage strength means grams per 100 mL.",
            "Set up a ratio and proportion to find grams in 100 mL:",
            f"   {grams} g / {volume} mL  =  X / 100 mL",
            f"Cross multiply:  X × {volume} mL  =  {grams} g × 100 mL",
            f"Divide both sides by {volume} mL and cancel out the milliliters:",
            f"   X  =  ({grams} g × 100 mL) / {volume} mL",
            f"   X  =  {percent} g  in 100 mL",
            f"Percentage strength = {percent}%  answer",
        ],
    }


def gen_volume_for_dose_from_percent():
    """Given a % strength and a dose in g (or mg), find the volume needed."""
    options = [
        # (drug, percent, dose_grams)
        ("magnesium sulfate (Mag Sulf)", 50, 2),     # 50%, 2 g → 4 mL
        ("calcium gluconate", 10, 1.5),               # 10%, 1.5 g → 15 mL
        ("mannitol", 25, 3.5),                        # 25%, 3.5 g → 14 mL
        ("a drug", 18, 3.6),                          # 18%, 3.6 g → 20 mL
        ("dextrose", 50, 12.5),                       # 50%, 12.5 g → 25 mL
    ]
    drug, percent, dose_g = random.choice(options)
    # volume = dose / (percent/100)
    volume = round(dose_g / (percent / 100), 2)

    return {
        "question": (
            f"A patient is to be given {dose_g} g of {drug}. "
            f"A vial of {percent}% solution is on the shelf. "
            f"How many mL will you need?"
        ),
        "answer": volume,
        "unit": "mL",
        "tolerance": 0.05,
        "steps": [
            "Recall: percentage strength means grams in 100 mL.",
            f"   {percent}%  =  {percent} g / 100 mL",
            "Set up a ratio and proportion problem:",
            f"   {percent} g / 100 mL  =  {dose_g} g / X",
            f"Cross multiply:  X × {percent} g  =  100 mL × {dose_g} g",
            f"Divide both sides by {percent} g and cancel out the grams:",
            f"   X  =  (100 mL × {dose_g} g) / {percent} g",
            f"X = {volume} mL  answer",
        ],
    }


CHAPTER = Chapter(
    key="percents",
    number=3,
    title="Calculations with Percents",
    summary="Percentage strength means grams of solute per 100 mL: find solute, find percent, or find volume for a dose.",
    problem_types=[
        ProblemType(
            "grams_from_percent",
            "Grams of solute from % w/v and volume",
            gen_grams_from_percent,
        ),
        ProblemType(
            "percent_from_grams",
            "Percentage strength from grams and volume",
            gen_percent_from_grams_and_volume,
        ),
        ProblemType(
            "volume_for_dose",
            "Volume needed for a given dose from a % solution",
            gen_volume_for_dose_from_percent,
        ),
    ],
)
