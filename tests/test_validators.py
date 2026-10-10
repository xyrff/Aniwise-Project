import math

from app.validators import validate_inputs


VALID_INPUTS = {
    "N": 90,
    "P": 42,
    "K": 43,
    "temperature": 26.0,
    "humidity": 82.0,
    "ph": 6.5,
    "rainfall": 203.0,
}


def test_valid_input():
    assert validate_inputs(VALID_INPUTS) == ([], [], [])


def test_all_hard_minimum_boundaries_are_accepted():
    values = {
        "N": 0,
        "P": 0,
        "K": 0,
        "temperature": -10,
        "humidity": 0,
        "ph": 0,
        "rainfall": 0,
    }

    errors, warnings, notes = validate_inputs(values)

    assert errors == []
    assert len(warnings) == 6
    assert any("Nitrogen" in note for note in notes)


def test_physical_maximums_are_accepted_but_warned():
    values = {**VALID_INPUTS, "humidity": 100, "ph": 14}

    errors, warnings, notes = validate_inputs(values)

    assert errors == []
    assert len(warnings) == 2
    assert any("Humidity" in warning for warning in warnings)
    assert any("Soil pH" in warning for warning in warnings)
    assert notes == []


def test_potassium_outside_training_range_warns():
    errors, warnings, notes = validate_inputs({**VALID_INPUTS, "K": 250})

    assert errors == []
    assert len(warnings) == 1
    assert "Potassium" in warnings[0]
    assert notes == []


def test_humidity_above_hard_maximum_is_error():
    errors, warnings, notes = validate_inputs({**VALID_INPUTS, "humidity": 120})

    assert any("Humidity" in error for error in errors)
    assert warnings == []
    assert notes == []


def test_negative_nitrogen_is_error():
    errors, warnings, notes = validate_inputs({**VALID_INPUTS, "N": -5})

    assert any("Nitrogen" in error for error in errors)
    assert warnings == []
    assert notes == []


def test_ph_above_hard_maximum_is_error():
    errors, warnings, notes = validate_inputs({**VALID_INPUTS, "ph": 15})

    assert any("Soil pH" in error for error in errors)
    assert warnings == []
    assert notes == []


def test_empty_rainfall_is_error():
    errors, warnings, notes = validate_inputs({**VALID_INPUTS, "rainfall": ""})

    assert any("Rainfall" in error and "required" in error for error in errors)
    assert warnings == []
    assert notes == []


def test_text_temperature_is_error():
    errors, warnings, notes = validate_inputs(
        {**VALID_INPUTS, "temperature": "warm"}
    )

    assert any("Temperature" in error and "number" in error for error in errors)
    assert warnings == []
    assert notes == []


def test_nan_is_error():
    errors, warnings, notes = validate_inputs(
        {**VALID_INPUTS, "temperature": math.nan}
    )

    assert any("Temperature" in error and "finite" in error for error in errors)
    assert warnings == []
    assert notes == []
