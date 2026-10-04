# crop_metadata.py
# Static reference info per crop — icons + illustrative stats.
# NOT model output. These are reasonable general ranges used only to make
# results more readable, same idea as the "rule-based layer" concept.


CROP_INFO = {
    "rice":        {"icon": "🌾", "display": "Rice / Palay",      "growth": "110-130 days", "water": "High",     "profit": "Moderate"},
    "maize":       {"icon": "🌽", "display": "Maize / Mais",      "growth": "90-120 days",  "water": "Moderate", "profit": "Moderate"},
    "chickpea":    {"icon": "🌱", "display": "Chickpea",          "growth": "90-100 days",  "water": "Low",      "profit": "Moderate"},
    "kidneybeans": {"icon": "🌱", "display": "Kidney Beans",      "growth": "90-120 days",  "water": "Moderate", "profit": "Moderate"},
    "pigeonpeas":  {"icon": "🌱", "display": "Pigeon Peas",       "growth": "150-180 days", "water": "Low",      "profit": "Moderate"},
    "mothbeans":   {"icon": "🌱", "display": "Moth Beans",        "growth": "60-90 days",   "water": "Low",      "profit": "Variable"},
    "mungbean":    {"icon": "🌱", "display": "Mung Bean / Munggo", "growth": "60-75 days",   "water": "Low",      "profit": "Variable"},
    "blackgram":   {"icon": "🌱", "display": "Black Gram",        "growth": "90-120 days",  "water": "Low",      "profit": "Variable"},
    "lentil":      {"icon": "🌰", "display": "Lentil",            "growth": "100-110 days", "water": "Low",      "profit": "Moderate"},
    "pomegranate": {"icon": "🔴", "display": "Pomegranate",       "growth": "6-7 months*",  "water": "Moderate", "profit": "High"},
    "banana":      {"icon": "🍌", "display": "Banana / Saging",   "growth": "9-12 months*", "water": "High",     "profit": "High"},
    "mango":       {"icon": "🥭", "display": "Mango / Mangga",    "growth": "Seasonal*",    "water": "Moderate", "profit": "High"},
    "grapes":      {"icon": "🍇", "display": "Grapes",            "growth": "Seasonal*",    "water": "Moderate", "profit": "High"},
    "watermelon":  {"icon": "🍉", "display": "Watermelon",        "growth": "80-90 days",   "water": "Moderate", "profit": "Moderate"},
    "muskmelon":   {"icon": "🍈", "display": "Muskmelon",         "growth": "80-90 days",   "water": "Moderate", "profit": "Moderate"},
    "apple":       {"icon": "🍎", "display": "Apple",             "growth": "Seasonal*",    "water": "Moderate", "profit": "High"},
    "orange":      {"icon": "🍊", "display": "Orange / Dalandan", "growth": "Seasonal*",    "water": "Moderate", "profit": "High"},
    "papaya":      {"icon": "🌳", "display": "Papaya",            "growth": "9-11 months*", "water": "Moderate", "profit": "Moderate"},
    "coconut":     {"icon": "🥥", "display": "Coconut / Niyog",   "growth": "Perennial*",   "water": "Moderate", "profit": "High"},
    "cotton":      {"icon": "🌿", "display": "Cotton",            "growth": "150-180 days", "water": "Moderate", "profit": "Moderate"},
    "jute":        {"icon": "🌿", "display": "Jute",              "growth": "120-150 days", "water": "High",     "profit": "Moderate"},
    "coffee":      {"icon": "☕", "display": "Coffee",            "growth": "Perennial*",   "water": "Moderate", "profit": "High"},
}


def get_crop_info(crop_label: str) -> dict:
    """Returns display metadata for a crop label, with a safe fallback
    for any label not in the table (e.g. future dataset changes)."""
    return CROP_INFO.get(
        crop_label,
        {"icon": "🌱", "display": crop_label.title(), "growth": "—",
         "water": "—", "profit": "—"},
    )


# Typical agronomic ranges per crop, used only to generate a contextual
# sentence (rule-based, not model output). Approximate values.
CROP_RANGES = {
    "rice":     {"rainfall": (180, 300), "humidity": (75, 90), "temp": (20, 27)},
    "maize":    {"rainfall": (60, 110),  "humidity": (55, 75), "temp": (18, 26)},
    "jute":     {"rainfall": (150, 250), "humidity": (70, 90), "temp": (24, 35)},
    "papaya":   {"rainfall": (100, 180), "humidity": (60, 85), "temp": (22, 32)},
    # ... idagdag mo yung iba kung meron kang time; may safe fallback naman sa baba
}


# Typical agronomic ranges per crop, used only to generate a contextual
# sentence (rule-based, not model output). Approximate values.
CROP_RANGES = {
    "rice":        {"rainfall": (180, 300), "humidity": (75, 90), "temp": (20, 27)},
    "maize":       {"rainfall": (60, 110),  "humidity": (55, 75), "temp": (18, 26)},
    "jute":        {"rainfall": (150, 250), "humidity": (70, 90), "temp": (24, 35)},
    "papaya":      {"rainfall": (40, 180),  "humidity": (60, 85), "temp": (22, 32)},
    "chickpea":    {"rainfall": (65, 105),  "humidity": (14, 25), "temp": (17, 21)},
    "kidneybeans": {"rainfall": (60, 150),  "humidity": (18, 25), "temp": (15, 25)},
    "pigeonpeas":  {"rainfall": (65, 200),  "humidity": (30, 70), "temp": (18, 37)},
    "mothbeans":   {"rainfall": (25, 65),   "humidity": (40, 65), "temp": (24, 32)},
    "mungbean":    {"rainfall": (25, 65),   "humidity": (80, 90), "temp": (27, 30)},
    "blackgram":   {"rainfall": (65, 75),   "humidity": (60, 70), "temp": (25, 35)},
    "lentil":      {"rainfall": (45, 55),   "humidity": (60, 70), "temp": (18, 30)},
    "pomegranate": {"rainfall": (35, 110),  "humidity": (85, 95), "temp": (18, 25)},
    "banana":      {"rainfall": (90, 130),  "humidity": (75, 85), "temp": (25, 30)},
    "mango":       {"rainfall": (85, 105),  "humidity": (45, 55), "temp": (27, 37)},
    "grapes":      {"rainfall": (65, 75),   "humidity": (80, 85), "temp": (8, 20)},
    "watermelon":  {"rainfall": (40, 55),   "humidity": (80, 90), "temp": (24, 27)},
    "muskmelon":   {"rainfall": (20, 30),   "humidity": (90, 95), "temp": (25, 30)},
    "apple":       {"rainfall": (100, 125), "humidity": (90, 95), "temp": (21, 24)},
    "orange":      {"rainfall": (100, 110), "humidity": (90, 95), "temp": (10, 35)},
    "coconut":     {"rainfall": (140, 230), "humidity": (90, 100), "temp": (25, 30)},
    "cotton":      {"rainfall": (60, 100),  "humidity": (70, 85), "temp": (22, 26)},
    "coffee":      {"rainfall": (150, 250), "humidity": (50, 70), "temp": (22, 28)},
}


def generate_description(crop_label: str, confidence: float,
                         rainfall: float, humidity: float, temperature: float) -> str:
    """Rule-based sentence comparing user inputs to this crop's typical
    range. Tone and content depend on the actual confidence score, not
    just the rank, so low-confidence crops honestly explain the mismatch."""
    ranges = CROP_RANGES.get(crop_label)

    matched, mismatched = [], []
    if ranges:
        checks = [
            ("rainfall", rainfall, "steady rainfall",
             "low or excess rainfall for this crop"),
            ("humidity", humidity, "a suitable humidity level",
             "humidity outside this crop's typical range"),
            ("temp", temperature, "a suitable temperature",
             "temperature outside this crop's typical range"),
        ]
        for key, value, good_label, bad_label in checks:
            lo, hi = ranges[key]
            if lo <= value <= hi:
                matched.append(good_label)
            else:
                mismatched.append(bad_label)

    # Tone is driven by the model's actual confidence score.
    if confidence >= 50:
        if matched:
            joined = ", ".join(
                matched[:-1]) + (" and " + matched[-1] if len(matched) > 1 else matched[0])
            return f"A strong match for your {joined}."
        return "A strong match based on your overall soil and climate profile."

    elif confidence >= 15:
        if mismatched:
            joined = ", ".join(
                mismatched[:-1]) + (" and " + mismatched[-1] if len(mismatched) > 1 else mismatched[0])
            return f"A possible option, but your {joined} may limit how well this crop performs."
        return "A moderate match — worth considering, but not as strongly suited as the top recommendation."

    else:
        if mismatched:
            joined = ", ".join(
                mismatched[:-1]) + (" and " + mismatched[-1] if len(mismatched) > 1 else mismatched[0])
            return f"Low-confidence match. Your {joined}, making this crop less likely to perform well under your current conditions."
        return "Low-confidence match based on your current conditions — likely not well-suited for this farm setup."
