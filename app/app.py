import streamlit as st
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime
from io import BytesIO
from fpdf import FPDF

from crop_metadata import get_crop_info, generate_description

st.set_page_config(page_title="AniWise", page_icon="🌱", layout="wide")

# ---------- Load CSS ----------
css_path = Path(__file__).parent / "styles.css"
st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ---------- Load model artifacts (cached so it only loads once) ----------


@st.cache_resource
def load_artifacts():
    models_dir = Path(__file__).parent.parent / "models"
    model = joblib.load(models_dir / "crop_recommendation_model.pkl")
    feature_names = joblib.load(models_dir / "feature_names.pkl")
    class_labels = joblib.load(models_dir / "class_labels.pkl")
    return model, feature_names, class_labels


model, FEATURES, CLASS_LABELS = load_artifacts()

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
    leaf_svg = (
        '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" '
        'stroke="#1b5e20" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 1.5 3.5 1 8-.5 4.5-3.5 6.5-9 7-1.1.1-2 0-2-.4z"/>'
        '<path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>'
        '</svg>'
    )
    st.markdown(
        f'<div class="brand-header">'
        f'<div class="brand-icon-chip">{leaf_svg}</div>'
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
    st.markdown('<div class="section-header">👤 Farmer Context <span style="color:#94a3b8; font-weight:400; font-size:12px;">(optional)</span></div>', unsafe_allow_html=True)

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
            rainfall=rainfall, humidity=humidity, temperature=temperature
        )
        recommended_tag = '<p class="crop-recommended-tag">Recommended for your farm</p>' if i == 0 else ""

        # Built as ONE continuous string (no real newlines inside the HTML)
        # so Streamlit/Markdown never mistakes indented lines for a code block.
        card_html = (
            f'<div class="{card_class}">'
            f'<div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">'
            f'<div style="display:flex; gap:14px; align-items:flex-start;">'
            f'<div class="crop-icon-box">{r["icon"]}</div>'
            f'<div>'
            f'<span class="crop-rank-badge">{i+1}</span>'
            f'&nbsp;<strong style="font-size:18px;">{r["display"]}</strong>'
            f'{recommended_tag}'
            f'<p style="margin:6px 0 4px 0; color:#334155; font-size:14px;">{description}</p>'
            f'<p style="margin:0; color:#64748b; font-size:13px;">'
            f'📅 {r["growth"]} &nbsp;&nbsp;💧 {r["water"]} water need'
            f'</p>'
            f'<span style="display:inline-block; margin-top:8px; background:#f1f5f9; color:#334155; '
            f'padding:4px 10px; border-radius:8px; font-size:12px; font-weight:600;">'
            f'Profit potential: {r["profit"].lower()}'
            f'</span>'
            f'</div>'
            f'</div>'
            f'<span class="confidence-badge">{r["confidence"]:.1f}%<br>confidence</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

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
