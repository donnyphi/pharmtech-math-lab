
"""Chapter 7: Infusion Rates and Drip Rates.

Core formula:  Volume / Time = Rate

Three calculation types from the textbook:
  1. Flow rate in mL/hr (simple division).
  2. Drip rate in gtt/min — two-step ratio and proportion using drop factor.
  3. Time to finish a bag from rate and volume.

Common drop factors: 10, 15, 20 gtt/mL (macrodrip) and 60 gtt/mL (microdrip).
"""

import random
from .base import Chapter, ProblemType


def gen_flow_rate_mlhr():
    """Flow rate in mL/hr from volume and time."""
    options = [
        (1000, 8),    # 125
        (1000, 10),   # 100
        (1000, 12),   # 83.3
        (500, 4),     # 125
        (500, 2),     # 250
        (250, 1),     # 250
        (2000, 12),   # 166.7
        (1500, 12),   # 125
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
        # (volume_mL, hours, drop_factor_gtt_per_mL)
        (1000, 8, 10),
        (1000, 8, 15),
        (1000, 12, 15),
        (500, 4, 15),
        (500, 4, 10),
        (1000, 10, 20),
        (1500, 12, 15),
        (250, 2, 60),
        (500, 4, 60),
    ]
    volume, hours, drop_factor = random.choice(options)
    # Step 1: mL/hr
    rate_mlhr = volume / hours
    # Step 2: mL/min
    minutes = hours * 60
    rate_mlmin = round(rate_mlhr / 60, 2)
    # Step 3: gtt/min (rounded to whole drop)
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
            f"Divide both sides by 1 mL and cancel out the milliliters:",
            f"   Y  =  ({drop_factor} gtt × {rate_mlmin} mL) / 1 mL  =  {round(rate_mlmin * drop_factor, 2)} gtt/min",
            f"Round to a whole drop:  Y = {rate_gttmin} gtt/min  answer",
        ],
    }


def gen_time_to_finish():
    """How long will a bag take to finish, given volume and rate?"""
    options = [
        # (volume_mL, rate_mlhr)
        (1000, 100),
        (1000, 125),
        (1000, 50),
        (500, 100),
        (500, 50),
        (2000, 125),
        (250, 50),
    ]
    volume, rate = random.choice(options)
    hours = round(volume / rate, 2)

    return {
        "question": (
            f"A 1 liter bag containing {volume} mL is running at {rate} mL/hr. "
            f"How many hours will the bag take to finish?"
            if volume == 1000 else
            f"A bag of {volume} mL is running at {rate} mL/hr. "
            f"How many hours will the bag take to finish?"
        ),
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


CHAPTER = Chapter(
    key="infusion_drip",
    number=7,
    title="Infusion Rates and Drip Rates",
    summary="Calculate flow rates (mL/hr), drip rates (gtt/min) using a two-step proportion, and infusion times.",
    problem_types=[
        ProblemType(
            "flow_rate_mlhr",
            "Flow rate in mL/hr",
            gen_flow_rate_mlhr,
        ),
        ProblemType(
            "drip_rate_gttmin",
            "Drip rate in gtt/min (two-step calculation)",
            gen_drip_rate_gttmin,
        ),
        ProblemType(
            "time_to_finish",
            "Hours to finish a bag",
            gen_time_to_finish,
        ),
    ],
)
