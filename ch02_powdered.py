"""Chapter 2: Powdered Drug Preparations.

Core formula:  Final Volume = Diluent Volume + Powder Volume   (FV = DV + PV)

The textbook covers three patterns:
  1. Find powder volume given diluent, drug amount, and target concentration.
  2. Find concentration after reconstitution given drug amount, diluent, and PV.
  3. Find diluent needed to obtain a target concentration given drug amount and PV.
"""

import random
from .base import Chapter, ProblemType


# (drug name, drug strength in mg, powder volume in mL, target conc in mg/mL,
#  resulting diluent in mL — pre-computed for clean textbook values)
_RECONST_DATA = [
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
    drug, drug_mg, true_pv, conc_mg_per_mL, true_dv = random.choice(_RECONST_DATA)
    # Final volume should match drug_mg / conc_mg_per_mL
    final_volume = round(drug_mg / conc_mg_per_mL, 2)
    # Powder volume = final volume - diluent added
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
        # (drug, drug_mg, diluent_mL, pv_mL)
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
        # (drug, drug_mg, pv_mL, target_conc_mg_per_mL)
        ("a 10 g bulk powder", 10000, 5, 100),       # final = 100, diluent = 95
        ("a 20 g vial", 20000, 4, 500),               # final = 40, diluent = 36
        ("a 5 g antibiotic", 5000, 1.6, 250),         # final = 20, diluent = 18.4
        ("a 2 g vial", 2000, 1.5, 125),               # final = 16, diluent = 14.5
        ("a 10 g vial", 10000, 2.4, 250),             # final = 40, diluent = 37.6
        ("a 9 g vial", 9000, 1.3, 300),               # final = 30, diluent = 28.7
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


CHAPTER = Chapter(
    key="powdered_drug",
    number=2,
    title="Powdered Drug Preparations",
    summary="Reconstitution problems using FV = DV + PV: find powder volume, concentration, or required diluent.",
    problem_types=[
        ProblemType(
            "powder_volume",
            "Find the powder volume",
            gen_powder_volume,
        ),
        ProblemType(
            "concentration",
            "Find concentration after reconstitution",
            gen_concentration_after_reconstitution,
        ),
        ProblemType(
            "diluent_volume",
            "Find diluent needed for target concentration",
            gen_diluent_for_concentration,
        ),
    ],
)
