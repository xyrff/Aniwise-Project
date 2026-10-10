import pandas as pd


# crop_metadata.py
# Static presentation metadata per crop. This is not model output.


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


DATASET_FEATURE_NAMES = {
    "N": "Nitrogen",
    "P": "Phosphorus",
    "K": "Potassium",
    "temperature": "Temperature",
    "humidity": "Humidity",
    "ph": "Soil pH",
    "rainfall": "Rainfall",
}


def compute_crop_iqr_ranges(training_data: pd.DataFrame) -> dict:
    """Calculate per-crop Q1/Q3 bounds for all model features."""
    required_columns = [*DATASET_FEATURE_NAMES, "label"]
    missing_columns = sorted(set(required_columns) - set(training_data.columns))
    if missing_columns:
        raise ValueError(
            f"Training dataset is missing required columns: {', '.join(missing_columns)}"
        )
    if training_data[required_columns].isna().any().any():
        raise ValueError("Training dataset contains missing feature values or labels.")

    features = list(DATASET_FEATURE_NAMES)
    numeric_features = training_data[features].apply(pd.to_numeric, errors="raise")
    grouped = numeric_features.assign(label=training_data["label"]).groupby("label")
    q1 = grouped[features].quantile(0.25)
    q3 = grouped[features].quantile(0.75)

    return {
        crop_label: {
            display_name: (
                float(q1.loc[crop_label, dataset_name]),
                float(q3.loc[crop_label, dataset_name]),
            )
            for dataset_name, display_name in DATASET_FEATURE_NAMES.items()
        }
        for crop_label in q1.index
    }


def generate_description(crop_label: str, confidence: float,
                         rainfall: float, humidity: float, temperature: float,
                         crop_iqr_ranges: dict) -> str:
    """Compare user inputs with the crop's training-data IQR."""
    ranges = crop_iqr_ranges[crop_label]

    matched, mismatched = [], []
    checks = [
        ("Rainfall", rainfall, "steady rainfall", "low or excess rainfall for this crop"),
        ("Humidity", humidity, "a suitable humidity level",
         "humidity outside this crop's typical range"),
        ("Temperature", temperature, "a suitable temperature",
         "temperature outside this crop's typical range"),
    ]
    for key, value, good_label, bad_label in checks:
        low, high = ranges[key]
        if low <= value <= high:
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
        return "Low-confidence match based on your current conditions — likely not well-suited to this field."
