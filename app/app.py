import base64
from html import escape

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
from io import BytesIO
from fpdf import FPDF

from crop_metadata import (
    compute_crop_iqr_ranges,
    get_crop_info,
    generate_description,
)

st.set_page_config(page_title="AniWise", page_icon="🌱", layout="wide")

# ---------- Load CSS ----------
css_path = Path(__file__).parent / "styles.css"
st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

icon_dir = Path(__file__).parent.parent / "images"


def image_data_uri(filename: str) -> str:
    encoded_image = base64.b64encode((icon_dir / filename).read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


farmhouse_icon = image_data_uri("farmhouse.png")
farmer_icon = image_data_uri("farmer.png")
calendar_icon = image_data_uri("forest.png")
water_icon = image_data_uri("watering-plants.png")


def calculate_compatibility(crop_label: str, inputs: dict, crop_iqr_ranges: dict) -> list:
    if crop_label not in crop_iqr_ranges:
        raise ValueError(f"Training-data IQR ranges are not available for {crop_label!r}.")

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
            normalized_distance = abs(value - center) / max(iqr_width / 2, 0.001)
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
            "typically needs — this is a strong, low-risk recommendation."
        )

    if len(results) > 1 and crop["confidence"] - results[1]["confidence"] <= 15:
        runner_up = results[1]
        runner_up_factors = calculate_compatibility(
            runner_up["label"],
            {factor["name"]: factor["value"] for factor in compatibility},
            crop_iqr_ranges,
        )
        top_scores = {factor["name"]: factor["compatibility"] for factor in compatibility}
        runner_up_improvement = max(
            (
                (factor["compatibility"] - top_scores[factor["name"]], factor["name"])
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


# ---------- Load model artifacts (cached so it only loads once) ----------


@st.cache_resource
def load_artifacts():
    models_dir = Path(__file__).parent.parent / "models"
    model = joblib.load(models_dir / "crop_recommendation_model.pkl")
    feature_names = joblib.load(models_dir / "feature_names.pkl")
    class_labels = joblib.load(models_dir / "class_labels.pkl")
    dataset_path = Path(__file__).parent.parent / "data" / "Crop_recommendation.csv"
    training_data = pd.read_csv(dataset_path)
    crop_iqr_ranges = compute_crop_iqr_ranges(training_data)
    feature_profiles = {
        "global_min": training_data[list(feature_names)].min().to_dict(),
        "global_max": training_data[list(feature_names)].max().to_dict(),
        "crop_medians": training_data.groupby("label")[list(feature_names)].median().to_dict(
            orient="index"
        ),
    }

    dataset_labels = set(crop_iqr_ranges)
    model_labels = set(model.classes_)
    if dataset_labels != model_labels or set(class_labels) != model_labels:
        raise ValueError(
            "Training dataset crop labels do not match the loaded model classes."
        )
    expected_feature_names = ("N", "P", "K", "temperature", "humidity", "ph", "rainfall")
    if tuple(feature_names) != expected_feature_names:
        raise ValueError("Loaded model feature names do not match the training dataset.")

    return model, feature_names, class_labels, crop_iqr_ranges, feature_profiles


model, FEATURES, CLASS_LABELS, CROP_IQR_RANGES, FEATURE_PROFILES = load_artifacts()

# ---------- Session state setup ----------
if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts, newest first
if "latest_result" not in st.session_state:
    st.session_state.latest_result = None


# ---------- PDF generation ----------
def build_pdf(inputs: dict, context: dict, results: list, timestamp: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(27, 94, 32)  # agri-800
    pdf.cell(0, 10, "AniWise - Crop Recommendation Summary", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Generated {timestamp}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 8, "Soil & Climate Inputs", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)
    for key, val in inputs.items():
        pdf.cell(0, 6, f"{key}: {val}", ln=True)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 8, "Farmer Context", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)
    for key, val in context.items():
        pdf.cell(0, 6, f"{key}: {val}", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 8, "Recommended Crops", ln=True)
    for i, r in enumerate(results, start=1):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(
            0, 7, f"{i}. {r['display']}  -  {r['confidence']:.1f}% confidence", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(90, 90, 90)
        pdf.cell(
            0, 6, f"   Growth: {r['growth']} | Water: {r['water']} | Profit: {r['profit']}", ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(130, 130, 130)
    pdf.multi_cell(0, 5, "Illustrative ML results. Confidence is a model score, not a yield guarantee. "
                         "Consult your local agricultural adviser before planting.")

    return bytes(pdf.output(dest="S"))


# ---------- Sidebar: Inputs ----------
with st.sidebar:
    st.markdown(
        f'<div class="brand-header">'
        f'<div class="brand-icon-chip"><img src="{farmhouse_icon}" alt="Farmhouse" '
        f'style="width:26px; height:26px; object-fit:contain;"></div>'
        f'<p class="brand-title">AniWise</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.caption("Smarter choices. Better harvests.")
    st.markdown("---")

    st.markdown('<div class="section-header">🌱 Soil & Climate Inputs</div>',
                unsafe_allow_html=True)
    st.caption("Use your latest soil test and local averages.")

    nitrogen = st.number_input(
        "Nitrogen (N)", min_value=0, max_value=200, value=90)
    st.markdown('<p class="field-caption">Available nitrogen · mg/kg</p>',
                unsafe_allow_html=True)

    phosphorus = st.number_input(
        "Phosphorus (P)", min_value=0, max_value=200, value=42)
    st.markdown('<p class="field-caption">Available phosphorus · mg/kg</p>',
                unsafe_allow_html=True)

    potassium = st.number_input(
        "Potassium (K)", min_value=0, max_value=250, value=43)
    st.markdown('<p class="field-caption">Available potassium · mg/kg</p>',
                unsafe_allow_html=True)

    temperature = st.number_input(
        "Temperature (°C)", min_value=0.0, max_value=55.0, value=26.0)
    st.markdown('<p class="field-caption">Average air temperature · °C</p>',
                unsafe_allow_html=True)

    humidity = st.number_input(
        "Humidity (%)", min_value=0.0, max_value=100.0, value=82.0)
    st.markdown('<p class="field-caption">Relative humidity · %</p>',
                unsafe_allow_html=True)

    ph = st.number_input("Soil pH", min_value=0.0, max_value=14.0, value=6.5)
    st.markdown('<p class="field-caption">Soil acidity · scale of 0-14</p>',
                unsafe_allow_html=True)

    rainfall = st.number_input(
        "Rainfall (mm)", min_value=0.0, max_value=400.0, value=203.0)
    st.markdown('<p class="field-caption">Average monthly rainfall · mm</p>',
                unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        f'<div class="section-header"><img src="{farmer_icon}" alt="Farmer" '
        f'style="width:18px; height:18px; object-fit:contain;"> Farmer Context '
        f'<span style="color:#94a3b8; font-weight:400; font-size:12px;">(optional)</span></div>',
        unsafe_allow_html=True,
    )

    farm_size = st.number_input("Farm Size (ha)", min_value=0.0, value=1.5)
    water_avail = st.selectbox("Water Availability", [
                               "Reliable irrigation", "Seasonal / rain-fed", "Limited"])
    experience = st.selectbox("Farming Experience", [
                              "Less than 1 year", "1-3 years", "3-5 years", "5+ years"])
    market_pref = st.selectbox("Market Preference", [
                               "Local market", "Export", "No preference"])

    st.markdown("---")
    predict_clicked = st.button("Predict Crop", use_container_width=True)


# ---------- Run prediction ----------
if predict_clicked:
    input_row = pd.DataFrame([[nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall]],
                             columns=FEATURES)
    probabilities = model.predict_proba(input_row)[0]
    top_idx = np.argsort(probabilities)[::-1][:3]

    results = []
    for idx in top_idx:
        crop_label = model.classes_[idx]
        info = get_crop_info(crop_label)
        results.append({
            "label": crop_label,
            "display": info["display"],
            "icon": info["icon"],
            "growth": info["growth"],
            "water": info["water"],
            "profit": info["profit"],
            "confidence": probabilities[idx] * 100,
        })

    timestamp = datetime.now().strftime("%d %b %Y · %I:%M %p")

    result_record = {
        "timestamp": timestamp,
        "inputs": {
            "Nitrogen": f"{nitrogen} mg/kg", "Phosphorus": f"{phosphorus} mg/kg",
            "Potassium": f"{potassium} mg/kg", "Temperature": f"{temperature} °C",
            "Humidity": f"{humidity} %", "Soil pH": f"{ph}", "Rainfall": f"{rainfall} mm",
        },
        "context": {
            "Farm size": f"{farm_size} ha", "Water": water_avail,
            "Experience": experience, "Market": market_pref,
        },
        "model_inputs": {
            "Nitrogen": nitrogen,
            "Phosphorus": phosphorus,
            "Potassium": potassium,
            "Temperature": temperature,
            "Humidity": humidity,
            "Soil pH": ph,
            "Rainfall": rainfall,
        },
        "results": results,
    }

    st.session_state.latest_result = result_record
    st.session_state.history.insert(0, result_record)  # newest first


# ---------- Main content ----------
st.markdown("##### 🌿 GROW WITH CONFIDENCE")
st.title("Your Crop Recommendation")
st.caption("The best-fit crops for your soil, climate, and farm context.")

if st.session_state.latest_result is None:
    st.info("Fill in your soil and climate data in the sidebar, then click **Predict Crop** to get started.")
else:
    record = st.session_state.latest_result

    col_status, col_save = st.columns([3, 1])
    with col_status:
        st.success(f"Prediction complete · {record['timestamp']}")
    with col_save:
        with st.popover("⬇ Save Result", use_container_width=True):
            pdf_bytes = build_pdf(
                record["inputs"], record["context"], record["results"], record["timestamp"])
            st.download_button("Download as PDF", data=pdf_bytes,
                               file_name="aniwise_result.pdf", mime="application/pdf",
                               use_container_width=True)

            csv_lines = ["Crop,Confidence(%),Growth,Water,Profit"]
            for r in record["results"]:
                csv_lines.append(
                    f"{r['display']},{r['confidence']:.1f},{r['growth']},{r['water']},{r['profit']}")
            st.download_button("Download as CSV", data="\n".join(csv_lines),
                               file_name="aniwise_result.csv", mime="text/csv",
                               use_container_width=True)

    # NOTE: this header row must be OUTSIDE/AFTER the col_status/col_save
    # block above, not indented inside "with col_save:" — that was the bug.
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown(f"**Your top {len(record['results'])} crops**")
    with header_col2:
        st.markdown(f"<p style='text-align:right; color:#94a3b8; font-size:13px;'>{record['timestamp']}</p>",
                    unsafe_allow_html=True)

    for i, r in enumerate(record["results"]):
        card_class = "crop-card crop-card-top" if i == 0 else "crop-card"
        description = generate_description(
            r["label"], confidence=r["confidence"],
            rainfall=rainfall, humidity=humidity, temperature=temperature,
            crop_iqr_ranges=CROP_IQR_RANGES,
        )
        recommended_tag = '<p class="crop-recommended-tag">Recommended for your farm</p>' if i == 0 else ""

        # Built as ONE continuous string (no real newlines inside the HTML)
        # so Streamlit/Markdown never mistakes indented lines for a code block.
        card_html = (
            f'<div class="{card_class}">'
            f'<div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem;">'
            f'<div style="display:flex; gap:1rem; align-items:flex-start;">'
            f'<div class="crop-icon-box">{r["icon"]}</div>'
            f'<div>'
            f'<span class="crop-rank-badge">{i+1}</span>'
            f'&nbsp;<strong style="font-size:18px;">{r["display"]}</strong>'
            f'{recommended_tag}'
            f'<p style="margin:0.5rem 0; color:#334155; font-size:14px;">{description}</p>'
            f'<p style="margin:0; color:#64748b; font-size:13px;">'
            f'<img src="{calendar_icon}" alt="Planting calendar" '
            f'style="width:18px; height:18px; object-fit:contain; vertical-align:middle;"> '
            f'{r["growth"]} &nbsp;&nbsp;'
            f'<img src="{water_icon}" alt="Watering plants" '
            f'style="width:18px; height:18px; object-fit:contain; vertical-align:middle;"> '
            f'{r["water"]} water need'
            f'</p>'
            f'<span style="display:inline-block; margin-top:8px; background:#f1f5f9; color:#334155; '
            f'padding:0.5rem 1rem; border-radius:8px; font-size:12px; font-weight:600;">'
            f'Profit potential: {r["profit"].lower()}'
            f'</span>'
            f'</div>'
            f'</div>'
            f'<span class="confidence-badge">{r["confidence"]:.1f}%<br>confidence</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("#### Top 3 Candidate Crops")
    probabilities_chart = pd.DataFrame({
        "Crop": [result["display"] for result in record["results"]],
        "Probability": [result["confidence"] for result in record["results"]],
    })
    st.bar_chart(
        probabilities_chart,
        x="Crop",
        y="Probability",
        horizontal=True,
        color="#2e7d32",
        x_label="Crop",
        y_label="Probability (%)",
    )

    model_inputs = record.get("model_inputs")
    if model_inputs is None:
        saved_inputs = record["inputs"]
        model_inputs = {
            "Nitrogen": float(saved_inputs["Nitrogen"].split()[0]),
            "Phosphorus": float(saved_inputs["Phosphorus"].split()[0]),
            "Potassium": float(saved_inputs["Potassium"].split()[0]),
            "Temperature": float(saved_inputs["Temperature"].split()[0]),
            "Humidity": float(saved_inputs["Humidity"].split()[0]),
            "Soil pH": float(saved_inputs["Soil pH"].split()[0]),
            "Rainfall": float(saved_inputs["Rainfall"].split()[0]),
        }

    top_crop = record["results"][0]
    compatibility = calculate_compatibility(
        top_crop["label"], model_inputs, CROP_IQR_RANGES)
    crop_water = get_crop_info(top_crop["label"])["water"]

    with st.container(border=True):
        st.markdown("### Environmental Compatibility Analysis")
        st.caption(
            "Ideal bounds are the 25th–75th percentile (IQR) of each crop's "
            "training-data values. These describe the dataset, not guaranteed field outcomes."
        )
        compatibility_html = '<div class="compatibility-grid">'
        for factor in compatibility:
            low, high = factor["range"]
            if factor["name"] == "Soil pH":
                ph_class = (
                    "acidic" if model_inputs["Soil pH"] < 6
                    else "slightly acidic" if model_inputs["Soil pH"] < 6.5
                    else "near neutral" if model_inputs["Soil pH"] <= 7.5
                    else "alkaline"
                )
                detail = f'pH class: {ph_class} · training IQR: {low:g}–{high:g}'
            elif factor["name"] == "Nitrogen":
                fit = (
                    "within the usual range" if low <= factor["value"] <= high
                    else "below the usual range" if factor["value"] < low
                    else "above the usual range"
                )
                detail = f'N fit: {fit} · training IQR: {low:g}–{high:g} mg/kg'
            else:
                detail = f'Training IQR: {low:g}–{high:g}'
            unit = {
                "Nitrogen": " mg/kg",
                "Phosphorus": " mg/kg",
                "Potassium": " mg/kg",
                "Temperature": " °C",
                "Humidity": "%",
                "Soil pH": "",
                "Rainfall": " mm",
            }[factor["name"]]
            score_class = "compatibility-score" if factor["compatibility"] >= 70 else "compatibility-score compatibility-score-low"
            compatibility_html += (
                '<div class="compatibility-item">'
                f'<strong>{escape(factor["name"])}</strong>'
                f'<span>{factor["value"]:g}{unit} · {detail}</span>'
                f'<b class="{score_class}">{factor["compatibility"]}% match</b>'
                '</div>'
            )
        compatibility_html += (
            '<div class="compatibility-summary">'
            f'<strong>Crop water demand: {escape(crop_water)}</strong>'
            '<span>IQR bounds are computed from the crop-specific training rows; '
            'they are descriptive, not a guarantee of yield.</span>'
            '</div></div>'
        )
        st.markdown(compatibility_html, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### Visualization")
        forest = getattr(model, "named_steps", {}).get("classifier", model)
        tree_count = forest.n_estimators
        pipeline_steps = [
            ("Your Inputs", "7 soil & climate values"),
            ("Random Forest", f"{tree_count} decision trees"),
            ("Probabilities", f"Scored across {len(model.classes_)} crops"),
            ("Top 3 Crops", "Ranked by confidence"),
        ]
        pipeline_html = '<div class="pipeline-diagram">'
        for index, (title, subtitle) in enumerate(pipeline_steps):
            pipeline_html += (
                '<div class="pipeline-step">'
                f'<strong>{escape(title)}</strong>'
                f'<span>{escape(subtitle)}</span>'
                '</div>'
            )
            if index < len(pipeline_steps) - 1:
                pipeline_html += '<span class="pipeline-arrow" aria-hidden="true">→</span>'
        pipeline_html += '</div>'
        st.markdown(pipeline_html, unsafe_allow_html=True)

        radar_features = [
            ("N", "Nitrogen"),
            ("P", "Phosphorus"),
            ("K", "Potassium"),
            ("temperature", "Temperature"),
            ("humidity", "Humidity"),
            ("ph", "Soil pH"),
            ("rainfall", "Rainfall"),
        ]

        def normalize_feature(feature_name: str, value: float) -> float:
            minimum = FEATURE_PROFILES["global_min"][feature_name]
            maximum = FEATURE_PROFILES["global_max"][feature_name]
            if maximum == minimum:
                return 0.0
            return (value - minimum) / (maximum - minimum)

        radar_labels = [label for _, label in radar_features]
        input_values = [
            normalize_feature(feature, model_inputs[label])
            for feature, label in radar_features
        ]
        crop_medians = FEATURE_PROFILES["crop_medians"][top_crop["label"]]
        typical_values = [
            normalize_feature(feature, crop_medians[feature])
            for feature, _ in radar_features
        ]
        radar_labels.append(radar_labels[0])
        input_values.append(input_values[0])
        typical_values.append(typical_values[0])

        radar_figure = go.Figure()
        radar_figure.add_trace(go.Scatterpolar(
            r=typical_values,
            theta=radar_labels,
            fill="toself",
            name=f"Typical {top_crop['display']}",
            line={"color": "#94a3b8"},
            fillcolor="rgba(148, 163, 184, 0.22)",
        ))
        radar_figure.add_trace(go.Scatterpolar(
            r=input_values,
            theta=radar_labels,
            fill="toself",
            name="Your Input",
            line={"color": "#2e7d32"},
            fillcolor="rgba(46, 125, 50, 0.28)",
        ))
        radar_figure.update_layout(
            title=f"Your Input vs. Typical {top_crop['display']} Profile",
            polar={
                "radialaxis": {"visible": True, "range": [0, 1]},
                "bgcolor": "rgba(0,0,0,0)",
            },
            paper_bgcolor="rgba(0,0,0,0)",
            margin={"l": 45, "r": 45, "t": 65, "b": 35},
            legend={"orientation": "h", "yanchor": "bottom", "y": -0.15},
        )
        st.plotly_chart(radar_figure, use_container_width=True)

        sorted_compatibility = sorted(
            compatibility, key=lambda factor: factor["compatibility"], reverse=True
        )
        compatibility_colors = [
            "#2e7d32" if factor["compatibility"] >= 80
            else "#f59e0b" if factor["compatibility"] >= 50
            else "#dc2626"
            for factor in sorted_compatibility
        ]
        compatibility_figure = go.Figure(go.Bar(
            x=[factor["compatibility"] for factor in sorted_compatibility],
            y=[factor["name"] for factor in sorted_compatibility],
            orientation="h",
            marker_color=compatibility_colors,
            text=[f"{factor['compatibility']}%" for factor in sorted_compatibility],
            textposition="outside",
            hovertemplate="%{y}: %{x}% compatible<extra></extra>",
        ))
        compatibility_figure.update_layout(
            title="Compatibility by Factor",
            xaxis={"title": "Compatibility (%)", "range": [0, 110]},
            yaxis={
                "title": None,
                "categoryorder": "array",
                "categoryarray": [factor["name"] for factor in sorted_compatibility],
                "autorange": "reversed",
            },
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin={"l": 100, "r": 45, "t": 65, "b": 45},
            showlegend=False,
        )
        st.plotly_chart(compatibility_figure, use_container_width=True)

        interpretation = build_farmer_interpretation(
            top_crop, compatibility, record["results"], CROP_IQR_RANGES)
        st.markdown(
            '<div class="farmer-insight">'
            '<span aria-hidden="true">💡</span>'
            f'<p>{escape(interpretation)}</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.caption("Illustrative ML results. Confidence is a model score, not a yield guarantee. "
               "Profit potential varies with local prices, costs, and growing conditions.")

    with st.expander("📋 Submitted input values"):
        st.json({**record["inputs"], **record["context"]})

    with st.expander(f"🕓 Session history ({len(st.session_state.history)} predictions)"):
        st.markdown('<div class="session-tag">🛡 This session only — not saved to an account.</div>',
                    unsafe_allow_html=True)
        st.markdown("")
        for h in st.session_state.history:
            top = h["results"][0]
            st.markdown(
                f"**{h['timestamp']}** — {top['icon']} {top['display']} ({top['confidence']:.1f}% confidence)")
        st.caption(
            "History clears when this session ends. Download any results you want to keep.")
