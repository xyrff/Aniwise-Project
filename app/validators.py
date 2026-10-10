import math


# (label, unit, hard_min, hard_max, train_min, train_max)
FIELDS = {
    "N": ("Nitrogen (N)", "", 0.0, 300.0, 0.0, 140.0),
    "P": ("Phosphorus (P)", "", 0.0, 300.0, 5.0, 145.0),
    "K": ("Potassium (K)", "", 0.0, 400.0, 5.0, 205.0),
    "temperature": ("Temperature", "°C", -10.0, 60.0, 8.83, 43.68),
    "humidity": ("Humidity", "%", 0.0, 100.0, 14.26, 99.98),
    "ph": ("Soil pH", "", 0.0, 14.0, 3.50, 9.94),
    "rainfall": ("Rainfall", "mm", 0.0, 1000.0, 20.21, 298.56),
}


def validate_inputs(values: dict):
    """Return (errors, warnings, notes) for crop recommendation inputs."""
    errors, warnings, notes = [], [], []
    for key, (label, unit, hmin, hmax, tmin, tmax) in FIELDS.items():
        v = values.get(key)
        u = f" {unit}" if unit else ""
        if v is None or (isinstance(v, str) and not v.strip()):
            errors.append(f"{label} is required. Please enter a value.")
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            errors.append(f"{label} must be a number (got '{values.get(key)}').")
            continue
        if math.isnan(v) or math.isinf(v):
            errors.append(f"{label} must be a finite number.")
            continue
        if v < hmin or v > hmax:
            errors.append(
                f"{label} of {v:g}{u} is not valid. "
                f"Accepted range: {hmin:g}–{hmax:g}{u}."
            )
            continue
        if v < tmin or v > tmax:
            warnings.append(
                f"{label} of {v:g}{u} is outside the range the model was trained on "
                f"({tmin:g}–{tmax:g}{u}). The prediction may be unreliable."
            )
        elif v == tmin or v == tmax:
            notes.append(
                f"{label} is exactly at the edge of the training range ({v:g}{u})."
            )
    return errors, warnings, notes
