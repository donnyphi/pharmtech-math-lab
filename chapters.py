"""
Pharmacy Tech Math — all chapters in one module.

This is the single-file version. The same content was previously split across
chapters/base.py, chapters/__init__.py, and chapters/ch01-ch10. Combined here
so it works in deployment environments (like Streamlit Community Cloud) that
sometimes mishandle package subdirectories.

Layout of this file:
    1. Base dataclasses (ProblemType, Chapter)
    2. Generator functions, one section per chapter (1-10)
    3. CHAPTER instances built from the generators
    4. Registry: CHAPTERS_LIST, CHAPTERS, get_chapter, get_problem_type

To add a new chapter:
    a) Write generator function(s) in a new section below.
    b) Build a Chapter(...) instance in the "Chapter instances" section.
    c) Append it to CHAPTERS_LIST at the bottom.
"""

import math
import random
from dataclasses import dataclass
from typing import Callable, List, Optional


# ============================================================================
# 1. Base dataclasses
# ============================================================================

@dataclass
class ProblemType:
    """A specific problem type within a chapter."""
    key: str               # unique within its chapter, e.g., "single_dose"
    label: str             # display label, e.g., "Single dose (mg/kg)"
    generator: Callable    # zero-arg function returning a problem dict


@dataclass
class Chapter:
    """A curriculum chapter."""
    key: str                                       # globally unique, e.g., "body_weight"
    number: int                                    # curriculum order
    title: str                                     # full title shown in the UI
    summary: str                                   # one-line description
    problem_types: List[ProblemType]               # one or more problem types

    # Future hooks. Leave as None until implemented.
    learn_content: Optional[str] = None
    guided_examples: Optional[List[dict]] = None


# ============================================================================
# 2a. Chapter 1: Parenteral Doses Using Ratio and Proportion
# ============================================================================

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


# ============================================================================
# 2b. Chapter 2: Powdered Drug Preparations
# ============================================================================

_RECONST_DATA = [
    # (drug, drug_mg, true_pv, target_conc_mg_per_mL, true_dv)
    ("Unasyn", 3000, 0.6, 375, 7.4),
    ("Claforan", 2000, 1.0, 180, 10.11),
    ("Rocephin", 500, 0.2, 250, 1.8),
    ("Mefoxin", 1000, 0.5, 100, 9.5),
    ("Fortaz", 6000, 4.0, 200, 26.0),
    ("nafcillin", 1000, 0.6, 250, 3.4),
    ("Zithromax", 500, 0.2, 100, 4.8),
]


def gen_powder_volume():
    """Find the powder volume given total drug, diluent, and resulting concentration."""
    drug, drug_mg, _true_pv, conc_mg_per_mL, true_dv = random.choice(_RECONST_DATA)
    final_volume = round(drug_mg / conc_mg_per_mL, 2)
    pv = round(final_volume - true_dv, 2)

    return {
        "question": (
            f"A vial contains {drug_mg} mg of {drug}. "
            f"The directions state to add {true_dv} mL of sterile water for injection "
            f"to obtain a concentration of {conc_mg_per_mL} mg/mL. "
            f"What is the powder volume of the drug?"
        ),
        "answer": pv,
        "unit": "mL",
        "tolerance": 0.05,
        "steps": [
            "First find the final volume after reconstitution using ratio and proportion:",
            f"   {conc_mg_per_mL} mg / 1 mL  =  {drug_mg} mg / X",
            f"Cross multiply:  X × {conc_mg_per_mL} mg  =  1 mL × {drug_mg} mg",
            f"Divide both sides by {conc_mg_per_mL} mg and cancel out the milligrams:",
            f"   X  =  (1 mL × {drug_mg} mg) / {conc_mg_per_mL} mg  =  {final_volume} mL",
            "Use the formula:  Powder volume = Final volume − Diluent added",
            f"   Powder volume  =  {final_volume} mL − {true_dv} mL",
            f"Powder volume = {pv} mL  answer",
        ],
    }


def gen_concentration_after_reconstitution():
    """Find concentration given drug amount, diluent volume, and powder volume."""
    options = [
        ("a powdered antibiotic", 2000, 18, 2),
        ("ampicillin", 1000, 9.2, 0.8),
        ("a 4 g vial", 4000, 19.8, 0.2),
        ("a 3 g antibiotic", 3000, 23, 3),
        ("Fortaz", 6000, 26, 4),
        ("a 2 g vial", 2000, 17, 3),
    ]
    drug, drug_mg, diluent, pv = random.choice(options)
    final_volume = round(diluent + pv, 2)
    conc = round(drug_mg / final_volume, 2)

    return {
        "question": (
            f"You add {diluent} mL of sterile water for injection to a vial of {drug} "
            f"that contains {drug_mg:,} mg of drug. The powder volume is {pv} mL. "
            f"What is the concentration of the drug in mg/mL after reconstitution?"
        ),
        "answer": conc,
        "unit": "mg/mL",
        "tolerance": 0.5,
        "steps": [
            "First find the final volume:  Final volume = Diluent volume + Powder volume",
            f"   Final volume  =  {diluent} mL + {pv} mL  =  {final_volume} mL",
            "Set up a ratio and proportion to find concentration (mg per 1 mL):",
            f"   {drug_mg:,} mg / {final_volume} mL  =  X / 1 mL",
            f"Cross multiply:  X × {final_volume} mL  =  1 mL × {drug_mg:,} mg",
            f"Divide both sides by {final_volume} mL and cancel out the milliliters:",
            f"   X  =  (1 mL × {drug_mg:,} mg) / {final_volume} mL",
            f"X = {conc} mg/mL  answer",
        ],
    }


def gen_diluent_for_concentration():
    """Find the diluent needed to obtain a target concentration given drug and PV."""
    options = [
        ("a 10 g bulk powder", 10000, 5, 100),
        ("a 20 g vial", 20000, 4, 500),
        ("a 5 g antibiotic", 5000, 1.6, 250),
        ("a 2 g vial", 2000, 1.5, 125),
        ("a 10 g vial", 10000, 2.4, 250),
        ("a 9 g vial", 9000, 1.3, 300),
    ]
    drug, drug_mg, pv, target_conc = random.choice(options)
    final_volume = round(drug_mg / target_conc, 2)
    diluent = round(final_volume - pv, 2)

    return {
        "question": (
            f"You have {drug} containing {drug_mg:,} mg of drug with a powder volume of {pv} mL. "
            f"How many mL of sterile water for injection should you add to obtain "
            f"a concentration of {target_conc} mg/mL?"
        ),
        "answer": diluent,
        "unit": "mL",
        "tolerance": 0.05,
        "steps": [
            "First find the final volume needed using ratio and proportion:",
            f"   {target_conc} mg / 1 mL  =  {drug_mg:,} mg / X",
            f"Cross multiply:  X × {target_conc} mg  =  1 mL × {drug_mg:,} mg",
            f"Divide both sides by {target_conc} mg and cancel out the milligrams:",
            f"   X  =  (1 mL × {drug_mg:,} mg) / {target_conc} mg  =  {final_volume} mL",
            "Use the formula:  Diluent volume = Final volume − Powder volume",
            f"   Diluent  =  {final_volume} mL − {pv} mL",
            f"Diluent = {diluent} mL  answer",
        ],
    }


# ============================================================================
# 2c. Chapter 3: Calculations with Percents
# ============================================================================

def gen_grams_from_percent():
    """Given % w/v and volume, find grams of solute."""
    options = [
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
            "Recall: percentage strength means grams in 100 mL.",
            f"   {percent}%  =  {percent} g / 100 mL",
            "Set up a ratio and proportion problem:",
            f"   {percent} g / 100 mL  =  X / {volume} mL",
            f"Cross multiply:  X × 100 mL  =  {percent} g × {volume} mL",
            "Divide both sides by 100 mL and cancel out the milliliters:",
            f"   X  =  ({percent} g × {volume} mL) / 100 mL",
            f"X = {grams} g  answer",
        ],
    }


def gen_percent_from_grams_and_volume():
    """Given grams of solute and volume, find % w/v."""
    options = [
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
    """Given a % strength and a dose in g, find the volume needed."""
    options = [
        ("magnesium sulfate (Mag Sulf)", 50, 2),
        ("calcium gluconate", 10, 1.5),
        ("mannitol", 25, 3.5),
        ("a drug", 18, 3.6),
        ("dextrose", 50, 12.5),
    ]
    drug, percent, dose_g = random.choice(options)
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


# ============================================================================
# 2d. Chapter 4: Using Ratio and Proportion when Preparing Solutions
# ============================================================================

def gen_grams_for_ratio_solution():
    """How many grams to make X mL of a 1:N w/v solution."""
    options = [
        ("Neosporin", 1000, 2000),
        ("sodium hypochlorite", 10, 1000),
        ("potassium permanganate", 500, 750),
        ("gentian violet", 10000, 500),
        ("a drug", 4000, 750),
        ("Neosporin", 1000, 1000),
    ]
    drug, ratio_n, volume_mL = random.choice(options)
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
        ("epinephrine (adrenalin)", 1000, 0.4),
        ("epinephrine (adrenalin)", 1000, 0.1),
        ("cocaine", 40, 80),
        ("neostigmine", 1000, 12.5),
        ("bupivacaine", 400, 25),
        ("a drug", 1000, 0.5),
        ("a drug", 5000, 4),
    ]
    drug, ratio_n, dose_mg = random.choice(options)
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
            "Divide both sides by 1,000 mg and cancel out the milligrams:",
            f"   X  =  ({ratio_n:,} mL × {dose_mg} mg) / 1,000 mg",
            f"X = {volume} mL  answer",
        ],
    }


def gen_ratio_to_percent():
    """Convert a 1:N w/v ratio to percentage strength."""
    options = [2000, 5000, 50, 60, 250, 100000, 100, 400, 2500]
    ratio_n = random.choice(options)
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


# ============================================================================
# 2e. Chapter 5: Dosage Calculations Based on Body Weight
# ============================================================================

def gen_dose_in_kg():
    """Patient weight in kg, find total dose in mg from mg/kg order."""
    options = [
        ("cefuroxime", 20),
        ("vancomycin", 10),
        ("acyclovir", 7.5),
        ("ampicillin", 50),
        ("cyclophosphamide", 5),
        ("a chemotherapy drug", 2),
    ]
    drug, dose_per_kg = random.choice(options)
    weight_kg = random.choice([20, 30, 40, 50, 60, 70, 75, 80])
    answer = round(dose_per_kg * weight_kg, 2)

    return {
        "question": (
            f"A patient weighs {weight_kg} kg. The physician orders {drug} at {dose_per_kg} mg/kg. "
            f"How many mg should the patient receive per dose?"
        ),
        "answer": answer,
        "unit": "mg",
        "tolerance": 0.5,
        "steps": [
            f"The dose is {dose_per_kg} mg per kg of body weight.",
            "Set up a ratio and proportion problem:",
            f"   {dose_per_kg} mg / 1 kg  =  X / {weight_kg} kg",
            f"Cross multiply:  X × 1 kg  =  {dose_per_kg} mg × {weight_kg} kg",
            "Divide both sides by 1 kg and cancel out the kilograms:",
            f"   X  =  ({dose_per_kg} mg × {weight_kg} kg) / 1 kg",
            f"X = {answer} mg  answer",
        ],
    }


def gen_dose_with_lb_to_kg_conversion():
    """Patient weight in lb. Convert to kg first, then calculate dose."""
    options = [
        ("zidovudine", 2),
        ("amphotericin B", 0.25),
        ("acyclovir", 7.5),
        ("gentamicin", 3),
        ("ampicillin", 100),
        ("theophylline", 0.5),
        ("a medication", 5),
    ]
    drug, dose_per_kg = random.choice(options)
    weight_lb = random.choice([22, 44, 66, 110, 132, 154, 176, 198, 220])
    weight_kg = round(weight_lb / 2.2, 2)
    answer = round(dose_per_kg * weight_kg, 2)

    return {
        "question": (
            f"A patient weighs {weight_lb} pounds. The physician orders {drug} at {dose_per_kg} mg/kg. "
            f"How many mg should the patient receive per dose?"
        ),
        "answer": answer,
        "unit": "mg",
        "tolerance": 0.5,
        "steps": [
            "Convert pounds to kilograms.  Conversion factor: 1 kg = 2.2 lb.",
            "Set up a ratio and proportion problem:",
            f"   1 kg / 2.2 lb  =  X / {weight_lb} lb",
            f"Cross multiply:  X × 2.2 lb  =  1 kg × {weight_lb} lb",
            "Divide both sides by 2.2 lb and cancel out the pounds:",
            f"   X  =  (1 kg × {weight_lb} lb) / 2.2 lb  =  {weight_kg} kg",
            f"Now apply the dose: {dose_per_kg} mg / 1 kg  =  Y / {weight_kg} kg",
            f"   Y  =  ({dose_per_kg} mg × {weight_kg} kg) / 1 kg",
            f"Y = {answer} mg  answer",
        ],
    }


def gen_volume_from_body_weight_dose():
    """Body-weight dose then convert mg to mL using available concentration."""
    options = [
        ("cyclophosphamide", 5, 50),
        ("gentamicin", 2, 10),
        ("vancomycin", 10, 50),
        ("a drug", 1.5, 40),
        ("ampicillin", 25, 125),
    ]
    drug, dose_per_kg, conc = random.choice(options)
    weight_lb = random.choice([44, 66, 88, 110, 132, 154, 176])
    weight_kg = round(weight_lb / 2.2, 2)
    dose_mg = round(dose_per_kg * weight_kg, 2)
    volume = round(dose_mg / conc, 2)

    return {
        "question": (
            f"A patient weighs {weight_lb} pounds. The physician orders {drug} at {dose_per_kg} mg/kg. "
            f"The drug is available as {conc} mg/mL. How many mL are needed for the dose?"
        ),
        "answer": volume,
        "unit": "mL",
        "tolerance": 0.05,
        "steps": [
            "Step 1: Convert pounds to kilograms.  Conversion factor: 1 kg = 2.2 lb.",
            f"   1 kg / 2.2 lb  =  X / {weight_lb} lb",
            f"   X  =  (1 kg × {weight_lb} lb) / 2.2 lb  =  {weight_kg} kg",
            f"Step 2: Find total dose in mg.  {dose_per_kg} mg/kg × {weight_kg} kg = {dose_mg} mg.",
            "Step 3: Convert mg to mL using the available concentration:",
            f"   {conc} mg / 1 mL  =  {dose_mg} mg / X",
            f"Cross multiply:  X × {conc} mg  =  1 mL × {dose_mg} mg",
            f"Divide both sides by {conc} mg and cancel out the milligrams:",
            f"   X  =  (1 mL × {dose_mg} mg) / {conc} mg",
            f"X = {volume} mL  answer",
        ],
    }


# ============================================================================
# 2f. Chapter 6: Dosage Calculations Based on Body Surface Area
# ============================================================================

def gen_dose_from_bsa():
    """Given BSA in m² and dose in mg/m², find total dose."""
    options = [
        ("doxorubicin", 75),
        ("doxorubicin (Adriamycin)", 25),
        ("vincristine", 1.4),
        ("vinblastine", 1.6),
        ("methotrexate", 900),
        ("fluorouracil (5-FU)", 400),
        ("paclitaxel (Taxol)", 175),
        ("cisplatin (CISplatin)", 15),
        ("bleomycin", 20),
        ("a chemotherapy drug", 5),
    ]
    drug, dose_per_m2 = random.choice(options)
    bsa = random.choice([0.96, 1.10, 1.24, 1.40, 1.52, 1.60, 1.80, 1.93, 2.10])
    answer = round(dose_per_m2 * bsa, 2)

    return {
        "question": (
            f"A patient has a BSA of {bsa} m². The physician orders {drug} at {dose_per_m2} mg/m². "
            f"What is the dose in mg?"
        ),
        "answer": answer,
        "unit": "mg",
        "tolerance": 0.5,
        "steps": [
            f"The dose is {dose_per_m2} mg per 1 m² of BSA.",
            "Set up a ratio and proportion problem:",
            f"   {dose_per_m2} mg / 1 m²  =  X / {bsa} m²",
            f"Cross multiply:  X × 1 m²  =  {dose_per_m2} mg × {bsa} m²",
            "Divide both sides by 1 m² and cancel out the square meters:",
            f"   X  =  ({dose_per_m2} mg × {bsa} m²) / 1 m²",
            f"X = {answer} mg  answer",
        ],
    }


def gen_volume_from_bsa_dose():
    """BSA dose then convert mg to mL using available concentration."""
    options = [
        ("doxorubicin", 25, 4),
        ("methotrexate", 40, 2.5),
        ("methotrexate", 900, 25),
        ("paclitaxel", 45, 6),
        ("CISplatin", 15, 1),
        ("Taxotere", 55, 20),
        ("etoposide", 100, 21),
        ("cyclophosphamide", 600, 20),
    ]
    drug, dose_per_m2, conc = random.choice(options)
    bsa = random.choice([0.82, 0.96, 1.20, 1.39, 1.52, 1.60, 1.80, 1.93, 2.00, 2.10])
    dose_mg = round(dose_per_m2 * bsa, 2)
    volume = round(dose_mg / conc, 2)

    return {
        "question": (
            f"A patient has a BSA of {bsa} m². The physician orders {drug} at {dose_per_m2} mg/m². "
            f"The drug is available as {conc} mg/mL. How many mL are needed?"
        ),
        "answer": volume,
        "unit": "mL",
        "tolerance": 0.1,
        "steps": [
            "Step 1: Find the total dose in mg.",
            f"   {dose_per_m2} mg / 1 m²  =  X / {bsa} m²",
            f"   X  =  ({dose_per_m2} mg × {bsa} m²) / 1 m²  =  {dose_mg} mg",
            "Step 2: Convert mg to mL using the available concentration:",
            f"   {conc} mg / 1 mL  =  {dose_mg} mg / Y",
            f"Cross multiply:  Y × {conc} mg  =  1 mL × {dose_mg} mg",
            f"Divide both sides by {conc} mg and cancel out the milligrams:",
            f"   Y  =  (1 mL × {dose_mg} mg) / {conc} mg",
            f"Y = {volume} mL  answer",
        ],
    }


# ============================================================================
# 2g. Chapter 7: Infusion Rates and Drip Rates
# ============================================================================

def gen_flow_rate_mlhr():
    """Flow rate in mL/hr from volume and time."""
    options = [
        (1000, 8), (1000, 10), (1000, 12),
        (500, 4), (500, 2),
        (250, 1),
        (2000, 12), (1500, 12),
    ]
    volume, hours = random.choice(options)
    rate = round(volume / hours, 2)

    return {
        "question": (
            f"An IV is ordered to infuse {volume} mL over {hours} hours. "
            f"What is the flow rate in mL/hr?"
        ),
        "answer": rate,
        "unit": "mL/hr",
        "tolerance": 0.1,
        "steps": [
            "Use the formula:  Volume / Time = Rate",
            f"   {volume} mL / {hours} hr  =  Rate",
            f"Divide:  Rate  =  {volume} ÷ {hours}",
            f"Rate = {rate} mL/hr  answer",
        ],
    }


def gen_drip_rate_gttmin():
    """Drip rate in gtt/min using two-step ratio and proportion."""
    options = [
        (1000, 8, 10), (1000, 8, 15), (1000, 12, 15),
        (500, 4, 15), (500, 4, 10),
        (1000, 10, 20),
        (1500, 12, 15),
        (250, 2, 60), (500, 4, 60),
    ]
    volume, hours, drop_factor = random.choice(options)
    rate_mlhr = volume / hours
    rate_mlmin = round(rate_mlhr / 60, 2)
    rate_gttmin = round(rate_mlmin * drop_factor)

    return {
        "question": (
            f"An IV is ordered to infuse {volume} mL over {hours} hours. "
            f"The IV set is calibrated at {drop_factor} drops/mL. "
            f"Calculate the rate of flow in drops/min (round to a whole drop)."
        ),
        "answer": float(rate_gttmin),
        "unit": "gtt/min",
        "tolerance": 0.5,
        "steps": [
            f"Step 1: Convert the flow rate to mL/hr.  {volume} mL / {hours} hr  =  {rate_mlhr:g} mL/hr.",
            "Step 2: Convert mL/hr to mL/min.  1 hour = 60 minutes.",
            f"   {rate_mlhr:g} mL / 60 min  =  X / 1 min",
            f"   X  =  ({rate_mlhr:g} mL × 1 min) / 60 min  =  {rate_mlmin} mL/min",
            f"Step 3: Convert mL/min to gtt/min using the drop factor {drop_factor} gtt/mL.",
            f"   {drop_factor} gtt / 1 mL  =  Y / {rate_mlmin} mL",
            f"Cross multiply:  Y × 1 mL  =  {drop_factor} gtt × {rate_mlmin} mL",
            "Divide both sides by 1 mL and cancel out the milliliters:",
            f"   Y  =  ({drop_factor} gtt × {rate_mlmin} mL) / 1 mL  =  {round(rate_mlmin * drop_factor, 2)} gtt/min",
            f"Round to a whole drop:  Y = {rate_gttmin} gtt/min  answer",
        ],
    }


def gen_time_to_finish():
    """How long will a bag take to finish, given volume and rate?"""
    options = [
        (1000, 100), (1000, 125), (1000, 50),
        (500, 100), (500, 50),
        (2000, 125),
        (250, 50),
    ]
    volume, rate = random.choice(options)
    hours = round(volume / rate, 2)

    question = (
        f"A 1 liter bag containing {volume} mL is running at {rate} mL/hr. "
        f"How many hours will the bag take to finish?"
        if volume == 1000 else
        f"A bag of {volume} mL is running at {rate} mL/hr. "
        f"How many hours will the bag take to finish?"
    )

    return {
        "question": question,
        "answer": hours,
        "unit": "hours",
        "tolerance": 0.1,
        "steps": [
            "Use the formula:  Volume / Rate = Time",
            "Set up a ratio and proportion problem:",
            f"   {rate} mL / 1 hr  =  {volume} mL / X",
            f"Cross multiply:  X × {rate} mL  =  1 hr × {volume} mL",
            f"Divide both sides by {rate} mL and cancel out the milliliters:",
            f"   X  =  (1 hr × {volume} mL) / {rate} mL",
            f"X = {hours} hr  answer",
        ],
    }


# ============================================================================
# 2h. Chapter 8: Dilutions (grams method, not C1V1 = C2V2)
# ============================================================================

def gen_final_percent_after_dilution():
    """Given a starting % solution diluted to a new volume, find the new %."""
    options = [
        (35, 350, 550),
        (30, 500, 600),
        (50, 200, 500),
        (40, 250, 1000),
        (20, 300, 600),
        (25, 400, 800),
    ]
    start_percent, start_volume, final_volume = random.choice(options)
    grams = round((start_percent / 100) * start_volume, 2)
    new_percent = round((grams / final_volume) * 100, 2)

    return {
        "question": (
            f"You start with {start_volume} mL of a {start_percent}% solution. "
            f"Additional solvent is added to bring the total volume to {final_volume} mL. "
            f"What is the percent strength of the diluted solution?"
        ),
        "answer": new_percent,
        "unit": "%",
        "tolerance": 0.1,
        "steps": [
            "Step 1: Calculate the grams of solute in the original solution.",
            f"   {start_percent}%  =  {start_percent} g / 100 mL",
            f"   {start_percent} g / 100 mL  =  X / {start_volume} mL",
            f"   X  =  ({start_percent} g × {start_volume} mL) / 100 mL  =  {grams} g",
            f"Step 2: The {grams} g is now in a final volume of {final_volume} mL.",
            "Step 3: Calculate the new percent (grams in 100 mL):",
            f"   {grams} g / {final_volume} mL  =  Y / 100 mL",
            f"   Y  =  ({grams} g × 100 mL) / {final_volume} mL",
            f"   Y  =  {new_percent} g  in 100 mL",
            f"New percent strength = {new_percent}%  answer",
        ],
    }


def gen_water_to_add_for_target_percent():
    """Find water to add to dilute a stock solution to a target % strength."""
    options = [
        (70, 200, 40),
        (50, 100, 20),
        (40, 250, 10),
        (25, 200, 5),
        (50, 300, 15),
        (40, 200, 8),
    ]
    stock_percent, stock_volume, target_percent = random.choice(options)
    grams = round((stock_percent / 100) * stock_volume, 2)
    final_volume = round(grams / (target_percent / 100), 2)
    water_needed = round(final_volume - stock_volume, 2)

    return {
        "question": (
            f"You have {stock_volume} mL of a {stock_percent}% solution. "
            f"You want to dilute it to {target_percent}%. "
            f"How many mL of water should you add?"
        ),
        "answer": water_needed,
        "unit": "mL",
        "tolerance": 0.5,
        "steps": [
            "Step 1: Calculate the grams of solute in the original solution.",
            f"   {stock_percent}%  =  {stock_percent} g / 100 mL",
            f"   {stock_percent} g / 100 mL  =  X / {stock_volume} mL",
            f"   X  =  ({stock_percent} g × {stock_volume} mL) / 100 mL  =  {grams} g",
            f"Step 2: The {grams} g must now produce a {target_percent}% solution.",
            "Find the final volume:",
            f"   {target_percent} g / 100 mL  =  {grams} g / Y",
            f"   Y  =  (100 mL × {grams} g) / {target_percent} g  =  {final_volume} mL",
            "Step 3: Water to add = Final volume − Original volume",
            f"   Water  =  {final_volume} mL − {stock_volume} mL",
            f"Water to add = {water_needed} mL  answer",
        ],
    }


# ============================================================================
# 2i. Chapter 9: Parenteral Nutrition Calculations
# ============================================================================

def gen_additive_volume_from_mEq():
    """Find mL of an additive needed from an mEq order."""
    options = [
        ("potassium chloride (KCl)", 2),
        ("sodium chloride 14.6%", 2.5),
        ("sodium acetate", 2),
        ("potassium acetate 19.6%", 2),
        ("potassium phosphate", 4.4),
    ]
    drug, conc = random.choice(options)
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
        percent = random.choice([10, 25, 50, 70])
        volume = random.choice([250, 500, 900, 1000])
        component = "dextrose"
    else:
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
            "Recall: percentage strength means grams in 100 mL.",
            f"   {percent}%  =  {percent} g / 100 mL",
            "Set up a ratio and proportion problem:",
            f"   {percent} g / 100 mL  =  X / {volume} mL",
            f"Cross multiply:  X × 100 mL  =  {percent} g × {volume} mL",
            "Divide both sides by 100 mL and cancel out the milliliters:",
            f"   X  =  ({percent} g × {volume} mL) / 100 mL",
            f"X = {grams} g {component}  answer",
        ],
    }


# ============================================================================
# 2j. Chapter 10: Dosage Calculations from Medication Labels
# ============================================================================

def gen_label_same_units():
    """Label and order use the same units. Direct ratio and proportion."""
    options = [
        ("Adriamycin", 200, 100, "mg", [33, 50, 100, 150]),
        ("epinephrine", 1, 10, "mg", [0.3, 0.5, 0.8, 1]),
        ("gentamicin", 40, 1, "mg", [60, 80, 100, 175]),
        ("calcium gluconate", 5, 50, "g", [0.5, 1, 1.5, 2]),
        ("Heparin", 5000, 1, "units", [2500, 7500, 10000]),
    ]
    drug, label_amt, label_vol, unit, doses = random.choice(options)
    ordered = random.choice(doses)
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
            f"Make sure the units match (they do, both in {unit}).",
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
        options = [
            ("magnesium sulfate", 50, 2, "g"),
            ("calcium gluconate", 10, 1.5, "g"),
            ("mannitol", 25, 3.5, "g"),
            ("lidocaine", 1, 40, "mg"),
            ("calcium gluconate", 10, 500, "mg"),
        ]
        drug, percent, dose, dose_unit = random.choice(options)
        dose_g = dose if dose_unit == "g" else dose / 1000
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
                "Recall: percentage strength means grams in 100 mL.",
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

    # g_per_mL_to_mg case
    options = [
        ("a drug", 1, 10, 400),
        ("ampicillin", 1, 5, 250),
        ("a drug", 0.5, 5, 50),
        ("a drug", 2, 5, 500),
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


# ============================================================================
# 3. Chapter instances
# ============================================================================

_CH01 = Chapter(
    key="parenteral_ratio",
    number=1,
    title="Parenteral Doses Using Ratio and Proportion Calculations",
    summary="Calculate injection volumes using ratio and proportion, including unit conversions and units/mEq dosing.",
    problem_types=[
        ProblemType("mg_per_ml_same_units", "Order in mg, stock in mg/mL (same units)", gen_mg_dose_mg_per_ml),
        ProblemType("with_unit_conversion", "Different units (convert g/mg/mcg first)", gen_dose_with_unit_conversion),
        ProblemType("units_or_mEq", "Doses in units (heparin, insulin) or mEq (KCl, NaCl)", gen_units_or_mEq_dose),
    ],
)

_CH02 = Chapter(
    key="powdered_drug",
    number=2,
    title="Powdered Drug Preparations",
    summary="Reconstitution problems using FV = DV + PV: find powder volume, concentration, or required diluent.",
    problem_types=[
        ProblemType("powder_volume", "Find the powder volume", gen_powder_volume),
        ProblemType("concentration", "Find concentration after reconstitution", gen_concentration_after_reconstitution),
        ProblemType("diluent_volume", "Find diluent needed for target concentration", gen_diluent_for_concentration),
    ],
)

_CH03 = Chapter(
    key="percents",
    number=3,
    title="Calculations with Percents",
    summary="Percentage strength means grams of solute per 100 mL: find solute, find percent, or find volume for a dose.",
    problem_types=[
        ProblemType("grams_from_percent", "Grams of solute from % w/v and volume", gen_grams_from_percent),
        ProblemType("percent_from_grams", "Percentage strength from grams and volume", gen_percent_from_grams_and_volume),
        ProblemType("volume_for_dose", "Volume needed for a given dose from a % solution", gen_volume_for_dose_from_percent),
    ],
)

_CH04 = Chapter(
    key="solutions_ratio",
    number=4,
    title="Using Ratio and Proportion when Preparing Solutions",
    summary="Work with ratio-strength solutions (1:N w/v): find grams, volume for a dose, or convert to %.",
    problem_types=[
        ProblemType("grams_for_solution", "Grams needed to prepare a 1:N w/v solution", gen_grams_for_ratio_solution),
        ProblemType("volume_for_dose", "Volume needed for a dose from a 1:N solution", gen_volume_for_dose_from_ratio),
        ProblemType("ratio_to_percent", "Convert a 1:N ratio strength to percentage", gen_ratio_to_percent),
    ],
)

_CH05 = Chapter(
    key="body_weight",
    number=5,
    title="Dosage Calculations Based on Body Weight",
    summary="Calculate doses from mg/kg orders. Convert lb to kg using 1 kg = 2.2 lb when needed.",
    problem_types=[
        ProblemType("weight_in_kg", "Patient weight in kg (no conversion needed)", gen_dose_in_kg),
        ProblemType("weight_in_lb", "Patient weight in lb (convert to kg first)", gen_dose_with_lb_to_kg_conversion),
        ProblemType("find_volume", "Find mL needed for a body-weight dose", gen_volume_from_body_weight_dose),
    ],
)

_CH06 = Chapter(
    key="bsa",
    number=6,
    title="Dosage Calculations Based on Body Surface Area",
    summary="Use BSA (m²) with mg/m² orders. BSA is obtained from a nomogram and given in the problem.",
    problem_types=[
        ProblemType("dose_from_bsa", "Dose in mg from BSA and mg/m²", gen_dose_from_bsa),
        ProblemType("volume_from_bsa", "Find mL needed for a BSA dose", gen_volume_from_bsa_dose),
    ],
)

_CH07 = Chapter(
    key="infusion_drip",
    number=7,
    title="Infusion Rates and Drip Rates",
    summary="Calculate flow rates (mL/hr), drip rates (gtt/min) using a two-step proportion, and infusion times.",
    problem_types=[
        ProblemType("flow_rate_mlhr", "Flow rate in mL/hr", gen_flow_rate_mlhr),
        ProblemType("drip_rate_gttmin", "Drip rate in gtt/min (two-step calculation)", gen_drip_rate_gttmin),
        ProblemType("time_to_finish", "Hours to finish a bag", gen_time_to_finish),
    ],
)

_CH08 = Chapter(
    key="dilutions",
    number=8,
    title="Dilutions",
    summary="Dilution problems using the grams method: find new % after dilution, or water needed to reach a target %.",
    problem_types=[
        ProblemType("final_percent", "Final % after dilution to a new total volume", gen_final_percent_after_dilution),
        ProblemType("water_to_add", "Water to add to reach a target %", gen_water_to_add_for_target_percent),
    ],
)

_CH09 = Chapter(
    key="parenteral_nutrition",
    number=9,
    title="Parenteral Nutrition Calculations",
    summary="TPN calculations: additive volumes from mEq orders, and grams of dextrose or amino acids in base solutions.",
    problem_types=[
        ProblemType("additive_volume", "mL of additive from an mEq order", gen_additive_volume_from_mEq),
        ProblemType("grams_in_base", "Grams of dextrose or amino acid in a base solution", gen_grams_in_base_solution),
    ],
)

_CH10 = Chapter(
    key="med_labels",
    number=10,
    title="Dosage Calculations from Medication Labels",
    summary="Read concentration from a label and calculate the volume needed. Convert units when label and order disagree.",
    problem_types=[
        ProblemType("same_units", "Label and order use the same units", gen_label_same_units),
        ProblemType("different_units", "Label and order use different units (convert first)", gen_label_different_units),
    ],
)


# ============================================================================
# 4. Registry
# ============================================================================

CHAPTERS_LIST = [_CH01, _CH02, _CH03, _CH04, _CH05, _CH06, _CH07, _CH08, _CH09, _CH10]
CHAPTERS = {chapter.key: chapter for chapter in CHAPTERS_LIST}


def get_chapter(key: str) -> Chapter:
    return CHAPTERS[key]


def get_problem_type(chapter_key: str, problem_type_key: str) -> ProblemType:
    chapter = CHAPTERS[chapter_key]
    return next(pt for pt in chapter.problem_types if pt.key == problem_type_key)


__all__ = [
    "Chapter",
    "ProblemType",
    "CHAPTERS_LIST",
    "CHAPTERS",
    "get_chapter",
    "get_problem_type",
]
