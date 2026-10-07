def normalize_feature(feature_name: str, value: float, feature_profiles: dict) -> float:
    minimum = feature_profiles["global_min"][feature_name]
    maximum = feature_profiles["global_max"][feature_name]
    if maximum == minimum:
        return 0.0
    return (value - minimum) / (maximum - minimum)


def calculate_compatibility(crop_label: str, inputs: dict, crop_iqr_ranges: dict) -> list:
    if crop_label not in crop_iqr_ranges:
        raise ValueError(
            f"Training-data IQR ranges are not available for {crop_label!r}.")

    advice = {
        "Nitrogen": "checking a soil test before adjusting fertilizer",
        "Phosphorus": "checking a soil test before adjusting fertilizer",
        "Potassium": "checking a soil test before adjusting fertilizer",
        "Temperature": "considering a different planting window",
        "Humidity": "checking local seasonal conditions before planting",
        "Soil pH": "checking with a local adviser before changing soil pH",
        "Rainfall": (
            "planning supplemental irrigation"
            if inputs["Rainfall"] < crop_iqr_ranges[crop_label]["Rainfall"][0]
            else "checking drainage and water management"
        ),
    }

    scored_factors = []
    for factor, value in inputs.items():
        low, high = crop_iqr_ranges[crop_label][factor]
        center = (low + high) / 2
        iqr_width = high - low
        if low <= value <= high:
            normalized_distance = abs(
                value - center) / max(iqr_width / 2, 0.001)
            compatibility = 100 - 30 * normalized_distance
        elif iqr_width == 0:
            compatibility = 0
        elif value < low:
            compatibility = max(0, 70 - 70 * (low - value) / iqr_width)
        else:
            compatibility = max(0, 70 - 70 * (value - high) / iqr_width)

        scored_factors.append({
            "name": factor,
            "value": value,
            "range": (low, high),
            "compatibility": round(compatibility),
            "advice": advice[factor],
        })

    return scored_factors


def build_farmer_interpretation(
    crop: dict, compatibility: list, results: list, crop_iqr_ranges: dict
) -> str:
    strongest = max(compatibility, key=lambda factor: factor["compatibility"])
    weak_factors = sorted(
        (factor for factor in compatibility if factor["compatibility"] < 70),
        key=lambda factor: factor["compatibility"],
    )[:2]
    factor_names = {
        "Nitrogen": "nitrogen level",
        "Phosphorus": "phosphorus level",
        "Potassium": "potassium level",
        "Temperature": "temperature",
        "Humidity": "humidity",
        "Soil pH": "soil pH",
        "Rainfall": "rainfall",
    }

    if weak_factors:
        if strongest["compatibility"] >= 70:
            text = (
                f"Your {factor_names[strongest['name']]} is a strong match for "
                f"{crop['display']} ({strongest['compatibility']}% compatible)."
            )
        else:
            text = (
                f"Your {factor_names[strongest['name']]} is the closest fit for "
                f"{crop['display']} ({strongest['compatibility']}% compatible)."
            )
        for factor in weak_factors:
            qualifier = (
                "slightly outside the usual range"
                if factor["compatibility"] >= 50
                else "further from the usual range"
            )
            text += (
                f" Your {factor_names[factor['name']]} is {qualifier} for "
                f"{crop['display']} ({factor['compatibility']}% compatible); "
                f"consider {factor['advice']}."
            )
    else:
        text = (
            f"All measured conditions closely match what {crop['display']} "
            "typically needs, making it a strong, low-risk recommendation."
        )

    if len(results) > 1 and crop["confidence"] - results[1]["confidence"] <= 15:
        runner_up = results[1]
        runner_up_factors = calculate_compatibility(
            runner_up["label"],
            {factor["name"]: factor["value"] for factor in compatibility},
            crop_iqr_ranges,
        )
        top_scores = {factor["name"]: factor["compatibility"]
                      for factor in compatibility}
        runner_up_improvement = max(
            (
                (factor["compatibility"] -
                 top_scores[factor["name"]], factor["name"])
                for factor in runner_up_factors
            ),
            default=(0, ""),
        )
        if runner_up_improvement[0] >= 10:
            runner_up_reason = (
                f"it is a better fit for your "
                f"{factor_names[runner_up_improvement[1]]}."
            )
        else:
            runner_up_reason = "your field conditions or plans change."
        text += f" {runner_up['display']} is also a reasonable alternative if {runner_up_reason}"
    return text
