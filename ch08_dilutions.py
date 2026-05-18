"""Chapter 8: Dilutions.

The textbook does NOT use C1V1 = C2V2. It uses the grams-based method:
  1. Calculate the grams of solute in the original solution.
  2. Determine the final volume (or use target % to find it).
  3. Set up grams/new_volume to find the new percentage (or solve for diluent).

Two problem types from the textbook:
  - Final % after diluting a solution to a new volume or by adding diluent.
  - Water to add to obtain a target % from a stronger stock solution.
"""

import random
from .base import Chapter, ProblemType


def gen_final_percent_after_dilution():
    """Given a starting % solution diluted to a new volume, find the new %."""
    options = [
        # (start_percent, start_volume_mL, final_volume_mL)
        (30, 500, 500),    # If diluted to 500 mL total — wait, that's same volume
        (35, 350, 550),    # 200 mL added → final 550
        (30, 500, 600),    # 100 mL added
        (50, 200, 500),
        (40, 250, 1000),
        (20, 300, 600),
        (25, 400, 800),
    ]
    start_percent, start_volume, final_volume = random.choice(options)
    # Grams in starting solution
    grams = round((start_percent / 100) * start_volume, 2)
    # New % = grams in 100 mL
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
        # (stock_percent, stock_volume_mL, target_percent)
        (70, 200, 40),     # 350 - 200 = 150 mL water
        (50, 100, 20),     # 250 - 100 = 150 mL water
        (40, 250, 10),     # 1000 - 250 = 750 mL water
        (25, 200, 5),      # 1000 - 200 = 800 mL water
        (50, 300, 15),     # 1000 - 300 = 700 mL water
        (40, 200, 8),      # 1000 - 200 = 800 mL water
    ]
    stock_percent, stock_volume, target_percent = random.choice(options)
    # Grams in stock
    grams = round((stock_percent / 100) * stock_volume, 2)
    # Final volume to give target_percent
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


CHAPTER = Chapter(
    key="dilutions",
    number=8,
    title="Dilutions",
    summary="Dilution problems using the grams method: find new % after dilution, or water needed to reach a target %.",
    problem_types=[
        ProblemType(
            "final_percent",
            "Final % after dilution to a new total volume",
            gen_final_percent_after_dilution,
        ),
        ProblemType(
            "water_to_add",
            "Water to add to reach a target %",
            gen_water_to_add_for_target_percent,
        ),
    ],
)
