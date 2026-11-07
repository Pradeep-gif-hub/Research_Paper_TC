# Scientific Audit, Reproducibility, and Revision Pipeline
## Thermal Conductivity Prediction Models for Polymer Composites

This repository contains the scientific audit, reproducibility codebase, and peer-review revision materials for research submitted to the journal *Measurement* (Elsevier).

---

## 1. Directory Structure

```
revision_work/
├── README.md                           # Master instructions and pipeline guide
├── requirements.txt                    # Python library dependencies
├── src/                                # Modular, reproducible Python source code
│   ├── 01_leakage_safe_pipeline.py     # Data leakage audit & partition-safe pipeline
│   ├── 02_data_provenance.py           # Material provenance & nanofluid audit
│   ├── 03_model_training.py            # Systematic model training & baselines
│   ├── 04_model_evaluation.py          # Metric generation & publication figures
│   └── 05_external_validation.py       # Audit of Maxwell benchmarks vs. docx files
├── tests/                              # Automated unit tests
│   └── test_audit_pipeline.py          # Integrity, leakage, and metric unit tests
├── data/                               # Audited data files and partition records
│   ├── README.md                       # Comprehensive file inventory
│   ├── provenance_audit.csv            # Classified master dataset (256 observations)
│   ├── cryogenic_clean_original.csv    # Clean non-augmented cryogenic data
│   ├── high_clean_original.csv         # Clean non-augmented high-temperature data
│   ├── room_clean_original.csv         # Clean non-augmented room-temperature data
│   ├── cryogenic_train_test_split.csv  # Verified train/test split memberships
│   ├── high_train_test_split.csv
│   └── room_train_test_split.csv
├── models/                             # Trained, serialized scikit-learn/XGBoost models (.pkl)
├── results/                            # Tabular evaluation outputs
│   ├── metrics.csv                     # Test metrics across all models and regimes
│   ├── predictions.csv                 # Instance-level test predictions and residuals
│   ├── cross_validation_results.csv    # 5-fold CV results for Strategy A, B, and GroupKFold
│   ├── leakage_comparison_metrics.csv  # Direct comparison: Leaked vs. Corrected metrics
│   └── external_validation_audit.csv   # Model predictions vs. Maxwell benchmarks
├── figures/                            # High-resolution (300 DPI) publication figures
│   ├── fig1_data_leakage_impact.png
│   ├── fig2_actual_vs_predicted.png
│   ├── fig3_residual_distributions.png
│   ├── fig4_feature_importance.png
│   ├── fig5_strategy_comparison.png
│   └── fig6_external_maxwell_benchmark_comparison.png
└── reports/                            # Peer-review revision reports and response evidence
    ├── original_pipeline_audit.md      # Detailed audit of original 12 notebooks
    ├── data_provenance_report.md       # Material provenance & nanofluid disclosure
    ├── leakage_audit.md                # Mathematical & empirical leakage demonstration
    ├── generalisation_report.md        # GroupKFold & Strategy A vs. B comparison
    ├── experimental_validation_report.md# Audit of docx theoretical Maxwell calculations
    ├── scientific_claims_audit.md      # Audit and recalibration of manuscript claims
    └── reviewer_response_evidence.csv  # 9-column evidence matrix for reviewer responses
```

---

## 2. Environment Setup

The pipeline requires Python $\ge 3.10$ (tested on Python 3.11).

```bash
# 1. Create a virtual environment
python3 -m venv revision_work/.venv
source revision_work/.venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r revision_work/requirements.txt

# On macOS, ensure libomp is installed for XGBoost:
brew install libomp
```

---

## 3. How to Run the Complete Audit & Pipeline

The pipeline is fully automated and can be executed via the documented modular scripts:

```bash
# Step 1: Run unit tests to verify data integrity
python -m unittest revision_work/tests/test_audit_pipeline.py

# Step 2: Run Data Provenance Audit
python revision_work/src/02_data_provenance.py

# Step 3: Run Data Leakage Audit & Pipeline Comparison
python revision_work/src/01_leakage_safe_pipeline.py

# Step 4: Train Corrected Models, Baselines, and Grouped CV
python revision_work/src/03_model_training.py

# Step 5: Evaluate Models & Generate Publication Figures
python revision_work/src/04_model_evaluation.py

# Step 6: Execute External Validation Audit vs. Maxwell Benchmarks
python revision_work/src/05_external_validation.py
```

---

## 4. Key Scientific Findings & Limitations

1. **Pre-Split Data Leakage:** The original reported $R^2 > 0.90$ was an artifact of performing 3x data augmentation before train/test splitting. 90.9% to 96.9% of test samples had twins in the training set.
2. **True Performance:** On clean, unaugmented holdout data, room-temperature models achieve $R^2 = 0.31\text{--}0.36$. However, a **Unified Combined Model (Strategy B)** across 2–423 K achieves **$R^2 = 0.7587$, $\text{MAE} = 0.138\text{ W/m}\cdot\text{K}$**.
3. **Validation Nature:** The validation files (`4.2K.docx`, `300K.docx`, `323K.docx`) are theoretical calculations using the classical Maxwell equation with Thermal Boundary Resistance, not physical experimental measurements.
4. **Generalization Scope:** Empirical models fail when predicting entirely unseen filler chemistry classes (GroupKFold $R^2 = -0.0703$), proving that microstructural descriptors (aspect ratio, surface area, Kapitza resistance) are required for cross-material transferability.
