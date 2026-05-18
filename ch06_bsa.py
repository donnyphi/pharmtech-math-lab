"""Chapter 6: Dosage Calculations Based on Body Surface Area.

BSA is expressed in m² and obtained from a nomogram using patient height and weight.
For practice, BSA is given directly. Doses are typically expressed as mg/m² or mcg/m².

The textbook uses ratio and proportion: dose/m² to known BSA.
"""

import random
from .base import Chapter, ProblemType


def gen_dose_from_bsa():
    """Given BSA in m² and dose in mg/m², find total dose."""
    options = [
        # (drug, dose_per_m2_mg)
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
            f"Divide both sides by 1 m² and cancel out the square meters:",
            f"   X  =  ({dose_per_m2} mg × {bsa} m²) / 1 m²",
            f"X = {answer} mg  answer",
        ],
    }


def gen_volume_from_bsa_dose():
    """BSA dose then convert mg to mL using available concentration."""
    options = [
        # (drug, dose_per_m2_mg, conc_mg_per_mL)
        ("doxorubicin", 25, 4),
        ("methotrexate", 40, 2.5),
        ("methotrexate", 900, 25),
        ("paclitaxel", 45, 6),
        ("CISplatin", 15, 1),
        ("Taxotere", 55, 20),
        ("etoposide", 100, 21),     # 525 mg/25 mL = 21 mg/mL
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


CHAPTER = Chapter(
    key="bsa",
    number=6,
    title="Dosage Calculations Based on Body Surface Area",
    summary="Use BSA (m²) with mg/m² orders. BSA is obtained from a nomogram and given in the problem.",
    problem_types=[
        ProblemType(
            "dose_from_bsa",
            "Dose in mg from BSA and mg/m²",
            gen_dose_from_bsa,
        ),
        ProblemType(
            "volume_from_bsa",
            "Find mL needed for a BSA dose",
            gen_volume_from_bsa_dose,
        ),
    ],
)
