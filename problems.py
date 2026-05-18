"""
Problem generators for pharmacy tech math practice.

Each generator returns a dict shaped like:
    {
        "topic": "<topic_key>",
        "question": "<question text shown to the user>",
        "answer": <numeric answer>,
        "unit": "<unit string>",
        "tolerance": <absolute tolerance floor>,
        "steps": [<list of solution step strings>],
    }
"""

import random

# Topic key -> human-readable label
TOPICS = {
    "unit_conversion": "Unit Conversion",
    "dose_calculation": "Dose Calculation (Tablets)",
    "percent_strength": "Percent Strength (w/v)",
    "iv_flow_rate": "IV Flow Rate",
    "days_supply": "Days Supply",
}


def gen_unit_conversion():
    """Convert between metric units commonly used in pharmacy."""
    conversions = [
        ("g", "mg", 1000),
        ("mg", "mcg", 1000),
        ("L", "mL", 1000),
        ("kg", "g", 1000),
    ]
    from_unit, to_unit, factor = random.choice(conversions)
    value = round(random.uniform(0.1, 10), 2)
    answer = round(value * factor, 2)

    return {
        "topic": "unit_conversion",
        "question": f"Convert {value} {from_unit} to {to_unit}.",
        "answer": answer,
        "unit": to_unit,
        "tolerance": 0.01,
        "steps": [
            f"Conversion factor: 1 {from_unit} = {factor} {to_unit}.",
            f"Multiply: {value} {from_unit} x {factor} = {answer} {to_unit}.",
        ],
    }


def gen_dose_calculation():
    """Tablets to dispense = ordered dose / stock strength."""
    stock_strengths = [125, 250, 500]
    multipliers = [1, 1.5, 2, 3, 4]
    stock = random.choice(stock_strengths)
    multiplier = random.choice(multipliers)
    ordered = stock * multiplier
    quantity = round(ordered / stock, 2)

    return {
        "topic": "dose_calculation",
        "question": (
            f"A medication is ordered as {ordered} mg. "
            f"Available stock is {stock} mg tablets. "
            f"How many tablets should be dispensed?"
        ),
        "answer": quantity,
        "unit": "tablets",
        "tolerance": 0.01,
        "steps": [
            "Formula: tablets = ordered dose / stock strength.",
            f"Plug in values: {ordered} mg / {stock} mg = {quantity} tablets.",
        ],
    }


def gen_percent_strength():
    """Grams of drug in a volume of w/v solution."""
    percent = random.choice([1, 2, 5, 10, 20])
    volume = random.choice([100, 250, 500, 1000])
    grams = round((percent / 100) * volume, 2)

    return {
        "topic": "percent_strength",
        "question": (
            f"How many grams of drug are in {volume} mL "
            f"of a {percent}% w/v solution?"
        ),
        "answer": grams,
        "unit": "g",
        "tolerance": 0.01,
        "steps": [
            f"A {percent}% w/v solution contains {percent} g of drug per 100 mL.",
            f"Set up proportion: {percent} g / 100 mL = x g / {volume} mL.",
            f"Solve for x: ({percent} x {volume}) / 100 = {grams} g.",
        ],
    }


def gen_iv_flow_rate():
    """Flow rate (mL/hr) = total volume / total time."""
    volume = random.choice([500, 1000, 1500, 2000])
    hours = random.choice([2, 4, 6, 8, 10, 12])
    rate = round(volume / hours, 2)

    return {
        "topic": "iv_flow_rate",
        "question": (
            f"An IV is ordered to infuse {volume} mL over {hours} hours. "
            f"What is the flow rate in mL/hour?"
        ),
        "answer": rate,
        "unit": "mL/hr",
        "tolerance": 0.01,
        "steps": [
            "Formula: flow rate (mL/hr) = total volume (mL) / total time (hr).",
            f"Plug in values: {volume} mL / {hours} hr = {rate} mL/hr.",
        ],
    }


def gen_days_supply():
    """Days supply = total quantity / quantity used per day. Clean integer answers only."""
    # (quantity, doses_per_day, tablets_per_dose) chosen to divide cleanly
    options = [
        (30, 1, 1),
        (30, 2, 1),
        (60, 2, 1),
        (60, 3, 1),
        (60, 4, 1),
        (90, 3, 1),
        (90, 1, 1),
        (100, 4, 1),
        (100, 2, 1),
        (60, 1, 2),
        (120, 2, 2),
    ]
    quantity, doses_per_day, tabs_per_dose = random.choice(options)
    total_daily = doses_per_day * tabs_per_dose
    days = quantity / total_daily

    freq_map = {
        1: "once daily",
        2: "twice daily",
        3: "three times daily",
        4: "four times daily",
    }
    tab_word = "tablet" if tabs_per_dose == 1 else "tablets"
    sig = f"{tabs_per_dose} {tab_word} {freq_map[doses_per_day]}"

    return {
        "topic": "days_supply",
        "question": (
            f"A prescription is for {quantity} tablets with the sig: '{sig}'. "
            f"What is the days supply?"
        ),
        "answer": days,
        "unit": "days",
        "tolerance": 0.01,
        "steps": [
            f"Tablets used per day: {tabs_per_dose} x {doses_per_day} = {total_daily} tablets/day.",
            f"Days supply: {quantity} tablets / {total_daily} tablets per day = {days} days.",
        ],
    }


# Topic key -> generator function
GENERATORS = {
    "unit_conversion": gen_unit_conversion,
    "dose_calculation": gen_dose_calculation,
    "percent_strength": gen_percent_strength,
    "iv_flow_rate": gen_iv_flow_rate,
    "days_supply": gen_days_supply,
}


def generate_problem(topic_key):
    """Generate a problem for the given topic key."""
    return GENERATORS[topic_key]()
