# 🌾 AniWise — Crop Recommendation System

A machine learning system that recommends the most suitable crop to plant based on soil nutrients (Nitrogen, Phosphorus, Potassium) and climate conditions (temperature, humidity, pH, rainfall). Built as a final group project for **[Course Name — Section]**, under **[Instructor Name]**.

Three traditional machine learning algorithms — Decision Tree, Logistic Regression, and Random Forest — were trained and compared under fair experimental conditions (stratified 80/20 split, 5-fold cross-validation, `GridSearchCV` tuning). **Random Forest** was selected as the final model (99.55% test accuracy) and deployed as an interactive Streamlit web application.

> ⚠️ **Decision support disclaimer:** This tool is a machine learning decision-support aid, not a replacement for professional agricultural advice. Confidence scores reflect statistical patterns learned from historical data, not a guarantee of yield or suitability. Always consider local conditions and consult a qualified agricultural adviser before making final planting decisions.

---

## 📁 Project Structure

```
AniWise_CropRecommendation/
├── app/                        # Streamlit application
│   ├── app.py                  # Main app entry point
│   ├── crop_metadata.py        # Crop reference data (scientific names, categories, etc.)
│   ├── styles.css              # Custom styling
│   └── images/                 # Icon assets (farmhouse, farmer, forest, watering-plants)
├── data/                       # Original and processed datasets
│   └── Crop_recommendation.csv
├── models/                     # Saved trained model + supporting files
│   ├── crop_recommendation_model.pkl
│   ├── feature_names.pkl
│   └── class_labels.pkl
├── notebooks/                  # EDA and model development
│   └── Crop_Classification_Colab.ipynb
├── documentation/              # Technical docs, screenshots
├── paper/                      # IMRaD/IEEE manuscript (DOCX + PDF)
├── archive/                    # Older/deprecated files
├── .gitignore
├── README.md                   # You are here
└── requirements.txt            # Exact pinned dependencies
```

---

## 🧠 Model Summary

| Algorithm | Test Accuracy | Macro F1 | 5-Fold CV Macro-F1 |
|---|---|---|---|
| **Random Forest** ✅ *(selected)* | **99.55%** | **0.9955** | 0.9960 ± 0.0050 |
| Logistic Regression | 98.41% | 0.9840 | 0.9776 ± 0.0058 |
| Decision Tree | 98.18% | 0.9817 | 0.9858 ± 0.0067 |

- **Dataset:** [Crop Recommendation Dataset](https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset) (Kaggle, A. Ingle) — 2,200 records, 22 crop classes (100 samples each), 7 numeric features, no missing values or duplicates.
- **Full methodology, EDA findings, and evaluation details:** see `paper/` and `notebooks/Crop_Classification_Colab.ipynb`.

---

## 🚀 Getting Started (run the app on your own device)

### 1. Clone the repository

```bash
git clone <repo-url>
cd AniWise_CropRecommendation
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Important:** `requirements.txt` pins exact package versions — including `scikit-learn==1.9.0` — to match the version the model was trained with. Installing a different scikit-learn version can trigger a model-loading warning or subtly inconsistent predictions. If you hit a version warning, run `pip install -r requirements.txt --force-reinstall` to be sure.

### 4. Run the Streamlit app

```bash
cd app
streamlit run app.py
```

Your browser should open automatically to `http://localhost:8501`. If not, open that link manually.

---

## 📓 Working with the Notebook

The full EDA, preprocessing, model training, tuning, and comparison process is in [`notebooks/Crop_Classification_Colab.ipynb`](notebooks/Crop_Classification_Colab.ipynb), built for Google Colab.

To re-run it:
1. Open the notebook in [Google Colab](https://colab.research.google.com/).
2. Run the cells top to bottom.
3. When prompted, upload `data/Crop_recommendation.csv`.
4. The notebook will train and compare all three algorithms, then save the best model (`crop_recommendation_model.pkl`) for download.

If you retrain and get a new model file, replace the one in `models/` and make sure the scikit-learn version used in Colab matches the one pinned in `requirements.txt` (see the Colab setup cell at the top of the notebook).

---

## 🛠️ Tech Stack

- **Language:** Python 3
- **ML:** scikit-learn (Decision Tree, Logistic Regression, Random Forest)
- **Data analysis:** pandas, numpy
- **Visualization:** matplotlib, seaborn (notebook), Plotly (app)
- **App framework:** Streamlit
- **Model persistence:** joblib

See `requirements.txt` for exact pinned versions.

---

## 👥 Team

| Name | Role / Responsibility |
|---|---|
| [Student Name 1] | [role] |
| [Student Name 2] | [role] |
| [Student Name 3] | [role] |
| [Student Name 4] | [role] |
| [Student Name 5] | [role] |

**Course:** [Course Name — Section] · **Instructor:** [Instructor Name] · **Group:** [Group Name/Number]

---

## 📄 License & Academic Use

This project was developed for academic purposes as part of a final course requirement. Dataset usage follows the license terms of the original [Kaggle dataset](https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset). See `paper/` for the complete ownership and authorship declaration.