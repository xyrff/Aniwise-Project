from io import BytesIO
from pathlib import Path

from fpdf import FPDF
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from crop_analysis import (
    build_farmer_interpretation,
    calculate_compatibility,
    normalize_feature,
)


GREEN = (46, 125, 50)
DARK_GREEN = (27, 94, 32)
TEXT = (30, 30, 30)
MUTED = (90, 90, 90)
INPUT_FEATURES = (
    ("N", "Nitrogen"),
    ("P", "Phosphorus"),
    ("K", "Potassium"),
    ("temperature", "Temperature"),
    ("humidity", "Humidity"),
    ("ph", "Soil pH"),
    ("rainfall", "Rainfall"),
)


def _probability_chart(results: list[dict]) -> BytesIO:
    ranked_results = list(reversed(results))
    figure = Figure(figsize=(7.2, 1.9), dpi=160, layout="constrained")
    axes = figure.subplots()
    colors = ["#a5d6a7"] * len(ranked_results)
    if colors:
        colors[-1] = "#2e7d32"

    bars = axes.barh(
        [result["display"] for result in ranked_results],
        [result["confidence"] for result in ranked_results],
        color=colors,
        height=0.58,
    )
    axes.set_xlim(0, 110)
    axes.set_xlabel("Probability (%)", fontsize=8)
    axes.tick_params(axis="y", labelsize=8, length=0)
    axes.tick_params(axis="x", labelsize=7)
    axes.grid(axis="x", color="#e5e7eb", linewidth=0.7)
    axes.set_axisbelow(True)
    axes.spines[["top", "right", "left"]].set_visible(False)
    axes.spines["bottom"].set_color("#cbd5e1")
    axes.bar_label(
        bars,
        labels=[f"{result['confidence']:.1f}%" for result in ranked_results],
        padding=3,
        fontsize=8,
        color="#334155",
    )

    image = BytesIO()
    FigureCanvasAgg(figure).print_png(image)
    image.seek(0)
    return image


def _radar_chart(
    top_crop: dict, model_inputs: dict, feature_profiles: dict
) -> BytesIO:
    crop_medians = feature_profiles["crop_medians"][top_crop["label"]]

    labels = [label for _, label in INPUT_FEATURES]
    input_values = [
        normalize_feature(feature, model_inputs[label], feature_profiles)
        for feature, label in INPUT_FEATURES
    ]
    typical_values = [
        normalize_feature(feature, crop_medians[feature], feature_profiles)
        for feature, _ in INPUT_FEATURES
    ]
    angles = [index * 2 * 3.141592653589793 / len(labels) for index in range(len(labels))]

    closed_angles = [*angles, angles[0]]
    closed_inputs = [*input_values, input_values[0]]
    closed_typical = [*typical_values, typical_values[0]]
    figure = Figure(figsize=(7.2, 2.5), dpi=160, layout="constrained")
    axes = figure.subplots(subplot_kw={"polar": True})
    axes.set_theta_offset(3.141592653589793 / 2)
    axes.set_theta_direction(-1)
    axes.set_xticks(angles, labels, fontsize=7)
    axes.set_ylim(0, 1)
    axes.set_yticks([0.25, 0.5, 0.75, 1.0], labels=["25", "50", "75", "100"], fontsize=6)
    axes.grid(color="#dbe3dc", linewidth=0.65)
    axes.set_title(
        f"Your Input vs. Typical {top_crop['display']} Profile",
        fontsize=10,
        color="#1b5e20",
        pad=12,
    )
    axes.plot(
        closed_angles,
        closed_typical,
        color="#94a3b8",
        linewidth=1.5,
        label=f"Typical {top_crop['display']}",
    )
    axes.fill(closed_angles, closed_typical, color="#94a3b8", alpha=0.2)
    axes.plot(
        closed_angles,
        closed_inputs,
        color="#2e7d32",
        linewidth=1.7,
        label="Your Input",
    )
    axes.fill(closed_angles, closed_inputs, color="#2e7d32", alpha=0.22)
    axes.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, -0.2),
        ncol=2,
        frameon=False,
        fontsize=7,
    )

    image = BytesIO()
    FigureCanvasAgg(figure).print_png(image)
    image.seek(0)
    return image


def _section_heading(pdf: FPDF, title: str) -> None:
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*GREEN)
    pdf.cell(0, 8, title, ln=True)


def _input_table(pdf: FPDF, rows: list[tuple[str, str]]) -> None:
    page_width = pdf.epw
    parameter_width = 53
    value_width = page_width - parameter_width
    row_height = 6.5

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*DARK_GREEN)
    pdf.set_fill_color(220, 252, 231)
    pdf.cell(parameter_width, row_height, "Parameter", border=1, fill=True)
    pdf.cell(value_width, row_height, "Value", border=1, fill=True, ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*TEXT)
    for index, (parameter, value) in enumerate(rows):
        pdf.set_fill_color(*(248, 250, 248) if index % 2 == 0 else (255, 255, 255))
        pdf.cell(parameter_width, row_height, parameter, border="LRB", fill=True)
        pdf.cell(value_width, row_height, value, border="LRB", fill=True, ln=True)


def build_pdf_report(
    inputs: dict,
    context: dict,
    results: list[dict],
    timestamp: str,
    model_inputs: dict,
    crop_iqr_ranges: dict,
    feature_profiles: dict,
    logo_path: Path,
) -> bytes:
    if not results:
        raise ValueError("At least one crop result is required to build a PDF report.")

    pdf = FPDF()
    pdf.set_margins(14, 12, 14)
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    pdf.image(str(logo_path), x=14, y=10, w=10, h=10)
    pdf.set_xy(27, 10)
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(*DARK_GREEN)
    pdf.cell(0, 10, "AniWise - Crop Recommendation Summary", ln=True)
    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Generated {timestamp}", ln=True)
    pdf.ln(3)

    input_labels = {
        "Nitrogen": "Nitrogen (N)",
        "Phosphorus": "Phosphorus (P)",
        "Potassium": "Potassium (K)",
        "Temperature": "Temperature",
        "Humidity": "Humidity",
        "Soil pH": "Soil pH",
        "Rainfall": "Rainfall",
    }
    _section_heading(pdf, "Soil & Climate Inputs")
    _input_table(pdf, [(input_labels.get(key, key), str(value)) for key, value in inputs.items()])

    pdf.ln(2)
    _section_heading(pdf, "Farmer Context")
    context_labels = {
        "Farm size": "Farm size",
        "Water": "Water",
        "Experience": "Experience",
        "Market": "Market",
    }
    _input_table(pdf, [(context_labels.get(key, key), str(value)) for key, value in context.items()])

    pdf.ln(2)
    _section_heading(pdf, "Visualization")
    pdf.image(_probability_chart(results), x=pdf.l_margin, w=pdf.epw)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MUTED)
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, 5, "Top 3 crops ranked by the probabilities from this prediction.", ln=True)
    pdf.ln(1)

    top_crop = results[0]
    pdf.image(
        _radar_chart(top_crop, model_inputs, feature_profiles),
        x=pdf.l_margin,
        w=pdf.epw,
    )
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MUTED)
    pdf.set_x(pdf.l_margin)
    pdf.cell(
        0,
        5,
        f"Your field values compared with the typical {top_crop['display']} profile.",
        ln=True,
    )

    pdf.add_page()
    _section_heading(pdf, "Recommended Crops")
    for index, crop in enumerate(results, start=1):
        compatibility = calculate_compatibility(
            crop["label"], model_inputs, crop_iqr_ranges)
        interpretation = build_farmer_interpretation(
            crop, compatibility, results[index - 1:], crop_iqr_ranges)
        if all(factor["compatibility"] >= 70 for factor in compatibility):
            interpretation += (
                f" Consider whether {crop['display']}'s growing season and resource "
                "needs fit your farm plan and local conditions."
            )

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*TEXT)
        pdf.cell(
            0,
            7,
            f"{index}. {crop['display']} - {crop['confidence']:.1f}% confidence",
            ln=True,
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*MUTED)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(
            0,
            5,
            f"Growth: {crop['growth']} | Water: {crop['water']} | Profit: {crop['profit']}",
        )
        pdf.set_text_color(*TEXT)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 4.5, interpretation)
        pdf.ln(3)

    disclaimer = (
        "This report is generated by a machine learning decision-support tool and is "
        "intended to assist, not replace, your own judgment. Confidence scores reflect "
        "patterns learned from historical data, not a guarantee of yield, income, or "
        "suitability for your specific field. Please consider local conditions not "
        "captured in this analysis (pest and disease pressure, recent weather events, "
        "market access, and input costs) and consult your local agricultural extension "
        "officer, cooperative adviser, or another qualified expert before making final "
        "planting decisions."
    )
    box_height = 42
    box_y = max(pdf.get_y() + 4, pdf.h - pdf.b_margin - box_height)
    pdf.set_fill_color(240, 253, 244)
    pdf.set_draw_color(*GREEN)
    pdf.set_line_width(0.4)
    pdf.rect(pdf.l_margin, box_y, pdf.epw, box_height, style="DF")
    pdf.set_xy(pdf.l_margin + 5, box_y + 4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*DARK_GREEN)
    pdf.cell(0, 6, "Decision Support Disclaimer", ln=True)
    pdf.set_x(pdf.l_margin + 5)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*TEXT)
    pdf.multi_cell(pdf.epw - 10, 4, disclaimer)

    return bytes(pdf.output(dest="S"))
