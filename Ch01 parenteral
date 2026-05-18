"""Chapter 1: Parenteral Doses Using Ratio and Proportion Calculations.

Follows the textbook's universal solution format:
  1. Convert units if needed.
  2. Set up a ratio and proportion problem.
  3. Cross multiply.
  4. Divide both sides and cancel out the units.
  5. State the answer.
"""

import random
from .base import Chapter, ProblemType


def gen_mg_dose_mg_per_ml():
    """Order in mg, stock in mg/mL. Same units, no conversion needed."""
    options = [
        ("Garamycin", 40),
        ("methotrexate", 25),
        ("aminophyllin", 25),
        ("Cleocin IV (clindamycin)", 150),
        ("doxorubicin", 2),
        ("phenytoin", 50),
        ("morphine sulfate", 15),
        ("tobramycin", 40),
        ("cimetidine", 150),
    ]
    drug, conc = random.choice(options)
    multipliers = [0.5, 1, 1.5, 2, 2.5, 3]
    ordered = round(conc * random.choice(multipliers), 2)
    answer = round(ordered / conc, 2)

    return {
        "question": (
            f"A physician orders {ordered} mg of {drug}. "
            f"The injection solution is available as {conc} mg/mL. "
            f"How many mL are needed?"
        ),
        "answer": answer,
        "unit": "mL",
        "tolerance": 0.01,
        "steps": [
            "Set up a ratio and proportion problem:",
            f"   {conc} mg / 1 mL  =  {ordered} mg / X",
            f"Cross multiply:  X × {conc} mg  =  1 mL × {ordered} mg",
            f"Divide both sides by {conc} mg and cancel out the milligrams:",
            f"   X  =  (1 mL × {ordered} mg) / {conc} mg",
            f"X = {answer} mL  answer",
        ],
    }


def gen_dose_with_unit_conversion():
    """Order and stock are in different units. Convert before solving."""
    case = random.choice(["g_to_mg", "mcg_to_mg", "mg_to_mcg"])

    if case == "g_to_mg":
        options = [
            ("methicillin", 1, 2),
            ("Cleocin IV (clindamycin)", 1, 6),
            ("vancomycin", 1, 10),
            ("ceftriaxone", 2, 10),
        ]
        drug, stock_g, stock_mL = random.choice(options)
        stock_mg = stock_g * 1000
        ordered_g = round(stock_g * random.choice([0.5, 1, 1.5, 2]), 2)
        ordered_mg = ordered_g * 1000
        answer = round((ordered_mg * stock_mL) / stock_mg, 2)
        return {
            "question": (
                f"A doctor orders {ordered_g} g of {drug}. "
                f"The medication is available as {stock_g} g per {stock_mL} mL. "
                f"How many mL are needed?"
            ),
            "answer": answer,
            "unit": "mL",
            "tolerance": 0.01,
            "steps": [
                "Change the grams to milligrams so the units of measurement are the same:",
                f"   Available: {stock_g} g / {stock_mL} mL  =  {stock_mg} mg / {stock_mL} mL",
                f"   Ordered: {ordered_g} g  =  {int(ordered_mg)} mg",
                "Set up a ratio and proportion problem:",
                f"   {stock_mg} mg / {stock_mL} mL  =  {int(ordered_mg)} mg / X",
                f"Cross multiply:  X × {stock_mg} mg  =  {stock_mL} mL × {int(ordered_mg)} mg",
                f"Divide both sides by {stock_mg} mg and cancel out the milligrams:",
                f"   X  =  ({stock_mL} mL × {int(ordered_mg)} mg) / {stock_mg} mg",
                f"X = {answer} mL  answer",
            ],
        }

    if case == "mcg_to_mg":
        options = [
            ("scopolamine", 0.4),
            ("digoxin", 0.25),
        ]
        drug, conc_mg = random.choice(options)
        ordered_mcg = random.choice([100, 150, 200, 300, 400, 500])
        ordered_mg = ordered_mcg / 1000
        answer = round(ordered_mg / conc_mg, 2)
        return {
            "question": (
                f"A physician orders {ordered_mcg} mcg of {drug}. "
                f"The label on the vial states the concentration is {conc_mg} mg/mL. "
                f"How many mL should be dispensed?"
            ),
            "answer": answer,
            "unit": "mL",
            "tolerance": 0.01,
            "steps": [
                "Change the micrograms to milligrams so the units of measurement are the same:",
                f"   Ordered: {ordered_mcg} mcg  =  {ordered_mg} mg",
                "Set up a ratio and proportion problem:",
                f"   {conc_mg} mg / 1 mL  =  {ordered_mg} mg / X",
                f"Cross multiply:  X × {conc_mg} mg  =  1 mL × {ordered_mg} mg",
                f"Divide both sides by {conc_mg} mg and cancel out the milligrams:",
                f"   X  =  (1 mL × {ordered_mg} mg) / {conc_mg} mg",
                f"X = {answer} mL  answer",
            ],
        }

    # mg_to_mcg case
    options = [
        ("digoxin elixir", 50),
        ("clonidine", 100),
        ("vitamin B12", 1000),
    ]
    drug, conc_mcg = random.choice(options)
    ordered_mg = random.choice([0.05, 0.1, 0.15, 0.2, 0.25, 0.5])
    ordered_mcg = ordered_mg * 1000
    answer = round(ordered_mcg / conc_mcg, 2)
    return {
        "question": (
            f"How many mL of {drug} ({conc_mcg} mcg/mL) "
            f"are needed to provide a dose of {ordered_mg} mg?"
        ),
        "answer": answer,
        "unit": "mL",
        "tolerance": 0.01,
        "steps": [
            "Change the milligrams to micrograms so the units of measurement are the same:",
            f"   Ordered: {ordered_mg} mg  =  {int(ordered_mcg)} mcg",
            "Set up a ratio and proportion problem:",
            f"   {conc_mcg} mcg / 1 mL  =  {int(ordered_mcg)} mcg / X",
            f"Cross multiply:  X × {conc_mcg} mcg  =  1 mL × {int(ordered_mcg)} mcg",
            f"Divide both sides by {conc_mcg} mcg and cancel out the micrograms:",
            f"   X  =  (1 mL × {int(ordered_mcg)} mcg) / {conc_mcg} mcg",
            f"X = {answer} mL  answer",
        ],
    }


def gen_units_or_mEq_dose():
    """Order in units or mEq, stock in units/mL or mEq/mL."""
    case = random.choice(["units", "mEq"])

    if case == "units":
        options = [
            ("regular insulin (Humulin R)", 100, [15, 25, 40, 50, 65, 78]),
            ("heparin", 5000, [2500, 5000, 7500, 10000, 12500]),
            ("heparin", 10000, [5000, 7500, 10000, 15000]),
            ("penicillin G", 500000, [200000, 1000000, 1500000, 2000000]),
        ]
        drug, conc, doses = random.choice(options)
        ordered = random.choice(doses)
        answer = round(ordered / conc, 2)
        return {
            "question": (
                f"An order is received for {ordered:,} units of {drug}. "
                f"The available concentration is {conc:,} units/mL. "
                f"How many mL are needed?"
            ),
            "answer": answer,
            "unit": "mL",
            "tolerance": 0.01,
            "steps": [
                "Set up a ratio and proportion problem:",
                f"   {conc:,} units / 1 mL  =  {ordered:,} units / X",
                f"Cross multiply:  X × {conc:,} units  =  1 mL × {ordered:,} units",
                f"Divide both sides by {conc:,} units and cancel out the units:",
                f"   X  =  (1 mL × {ordered:,} units) / {conc:,} units",
                f"X = {answer} mL  answer",
            ],
        }

    # mEq case
    options = [
        ("potassium chloride (KCl)", 2, [10, 15, 20, 25, 30]),
        ("potassium phosphate", 4.4, [8.8, 13.2, 17.6, 22]),
        ("sodium chloride 23.4%", 4, [12, 20, 33, 40]),
        ("sodium acetate", 2, [10, 20, 30, 50]),
    ]
    drug, conc, doses = random.choice(options)
    ordered = random.choice(doses)
    answer = round(ordered / conc, 2)
    return {
        "question": (
            f"A patient requires {ordered} mEq of {drug}. "
            f"The pharmacy stocks the drug in a concentration of {conc} mEq/mL. "
            f"How many mL will be needed?"
        ),
        "answer": answer,
        "unit": "mL",
        "tolerance": 0.01,
        "steps": [
            "Set up a ratio and proportion problem:",
            f"   {conc} mEq / 1 mL  =  {ordered} mEq / X",
            f"Cross multiply:  X × {conc} mEq  =  1 mL × {ordered} mEq",
            f"Divide both sides by {conc} mEq and cancel out the milliequivalents:",
            f"   X  =  (1 mL × {ordered} mEq) / {conc} mEq",
            f"X = {answer} mL  answer",
        ],
    }


CHAPTER = Chapter(
    key="parenteral_ratio",
    number=1,
    title="Parenteral Doses Using Ratio and Proportion Calculations",
    summary="Calculate injection volumes using ratio and proportion, including unit conversions and units/mEq dosing.",
    problem_types=[
        ProblemType(
            "mg_per_ml_same_units",
            "Order in mg, stock in mg/mL (same units)",
            gen_mg_dose_mg_per_ml,
        ),
        ProblemType(
            "with_unit_conversion",
            "Different units (convert g/mg/mcg first)",
            gen_dose_with_unit_conversion,
        ),
        ProblemType(
            "units_or_mEq",
            "Doses in units (heparin, insulin) or mEq (KCl, NaCl)",
            gen_units_or_mEq_dose,
        ),
    ],
)
