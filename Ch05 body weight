"""Chapter 5: Dosage Calculations Based on Body Weight.

Core conversion: 1 kg = 2.2 lb
Doses are expressed as mg/kg, mcg/kg, or mg/lb.

Standard textbook approach:
  1. Convert weight to kg if given in pounds.
  2. Multiply by dose per kg using ratio and proportion.
  3. (Optional) Convert to volume using the available concentration.
"""

import random
from .base import Chapter, ProblemType


def gen_dose_in_kg():
    """Patient weight in kg, find total dose in mg from mg/kg order."""
    options = [
        # (drug, dose_per_kg_in_mg)
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
            f"Divide both sides by 1 kg and cancel out the kilograms:",
            f"   X  =  ({dose_per_kg} mg × {weight_kg} kg) / 1 kg",
            f"X = {answer} mg  answer",
        ],
    }


def gen_dose_with_lb_to_kg_conversion():
    """Patient weight in lb. Convert to kg first, then calculate dose."""
    options = [
        # (drug, dose_per_kg_in_mg)
        ("zidovudine", 2),
        ("amphotericin B", 0.25),
        ("acyclovir", 7.5),
        ("gentamicin", 3),
        ("ampicillin", 100),
        ("theophylline", 0.5),
        ("a medication", 5),
    ]
    drug, dose_per_kg = random.choice(options)
    # Pick weights that convert cleanly: multiples of 2.2 or 11
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
            f"Convert pounds to kilograms.  Conversion factor: 1 kg = 2.2 lb.",
            "Set up a ratio and proportion problem:",
            f"   1 kg / 2.2 lb  =  X / {weight_lb} lb",
            f"Cross multiply:  X × 2.2 lb  =  1 kg × {weight_lb} lb",
            f"Divide both sides by 2.2 lb and cancel out the pounds:",
            f"   X  =  (1 kg × {weight_lb} lb) / 2.2 lb  =  {weight_kg} kg",
            f"Now apply the dose: {dose_per_kg} mg / 1 kg  =  Y / {weight_kg} kg",
            f"   Y  =  ({dose_per_kg} mg × {weight_kg} kg) / 1 kg",
            f"Y = {answer} mg  answer",
        ],
    }


def gen_volume_from_body_weight_dose():
    """Body-weight dose then convert mg to mL using available concentration."""
    options = [
        # (drug, dose_per_kg_mg, concentration_mg_per_mL)
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


CHAPTER = Chapter(
    key="body_weight",
    number=5,
    title="Dosage Calculations Based on Body Weight",
    summary="Calculate doses from mg/kg orders. Convert lb to kg using 1 kg = 2.2 lb when needed.",
    problem_types=[
        ProblemType(
            "weight_in_kg",
            "Patient weight in kg (no conversion needed)",
            gen_dose_in_kg,
        ),
        ProblemType(
            "weight_in_lb",
            "Patient weight in lb (convert to kg first)",
            gen_dose_with_lb_to_kg_conversion,
        ),
        ProblemType(
            "find_volume",
            "Find mL needed for a body-weight dose",
            gen_volume_from_body_weight_dose,
        ),
    ],
)
