# Smart Agriculture AI — Irrigation Recommendation System

An intelligent, client-facing agricultural decision-support application built around a trained **Decision Tree Machine Learning Pipeline** (`models/irrigation_prediction_model.pkl`).

---

## 🌾 Features & Capabilities

- **16 Multimodal Trained Inputs**:
  - **Soil Conditions**: Soil Type, pH, Moisture (%), Organic Carbon, Electrical Conductivity.
  - **Weather Conditions**: Temperature (°C), Humidity (%), Rainfall (mm), Sunlight Hours, Wind Speed (km/h).
  - **Crop Details**: Crop Type (Wheat, Maize, Cotton, Rice, Sugarcane, Potato), Growth Stage (Sowing, Vegetative, Flowering, Harvest).
  - **Farm Setup**: Field Area (hectare), Region, Season, Mulching Used.
- **Decision Tree Model Pipeline**:
  - Predicts multi-class irrigation requirement (`LOW`, `MEDIUM`, `HIGH`).
  - Displays **Model Confidence** % and full class probability distribution.
- **Strict Input Validation**:
  - Validates numeric boundaries (e.g. non-negative rainfall/area, 0-100% moisture).
  - Friendly error banners to prevent invalid inference.
- **Decision-Support Explanation Layer**:
  - Bullet-point rule-based explanations clearly demarcated from ML prediction.
- **Farm Health Summary Dashboard**:
  - Qualitative interpretation layer (*Moderate Moisture*, *Elevated Temperature*).
- **Feature Importance Visualization**:
  - Horizontal bar chart of exact Gini feature importances extracted from the Decision Tree classifier pipeline.
- **Model Info & Disclaimer**:
  - Test-set accuracy (**98.38%**), precision/recall metrics, and operational field validation disclaimer.

---

## 📂 Project Structure

```text
Irrigation Recommendation/
│
├── app/
│   └── irrigation_app.py            # Streamlit Client Application
│
├── src/
│   └── irrigation_engine.py          # Core Inference Engine, Validation & Rules
│
├── models/
│   └── irrigation_prediction_model.pkl  # Trained Decision Tree Pipeline Artifact
│
├── data/
│   └── irrigation_prediction.csv    # Training & Evaluation Dataset
│
├── outputs/
│   └── feature_importance.csv        # Exported Gini Feature Importances
│
├── logs/
│   └── app.log                      # Technical Developer Application Logs
│
├── requirements.txt                 # Project Dependencies
└── README.md                        # Documentation
```

---

## 🚀 How to Run the Application

1. Open your terminal in the project directory:
   ```bash
   cd "c:\Users\admin\Desktop\Smart-Agriculture-AI\Irrigation Recommendation"
   ```

2. Run the Streamlit application:
   ```bash
   streamlit run app/irrigation_app.py
   ```

3. Open your browser at:
   **[http://localhost:8501](http://localhost:8501)**

---

## 📊 Model Information & Test Performance

- **Algorithm**: Decision Tree Classifier (`ColumnTransformer` with `OneHotEncoder` + `passthrough`)
- **Training Features**: 16
- **Target**: `Irrigation_Need` (`Low`, `Medium`, `High`)
- **Test-Set Accuracy**: **98.38%**

*Disclaimer: Model performance is based on the available training/test dataset and may differ under real-world field conditions. Local field validation is recommended before operational deployment.*
