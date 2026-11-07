# Data Directory Documentation & File Inventory

## 1. Overview
This directory contains the cleaned, partitioned, and audited dataset files generated during the scientific reproducibility audit of thermal conductivity prediction models for polymer composites.

The original datasets supplied in the root directory were preserved as read-only inputs and never overwritten.

---

## 2. File Inventory of Supplied Project Workspace

| Relative File Path | File Type | File Size (Bytes) | Likely Purpose | Content Classification | Role Uncertainty / Methodological Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `336 Data Augmentation.ipynb` | Jupyter Notebook | 10,198 | Data Augmentation script | Source code / Preprocessing | Generates synthetic data with proportional Gaussian noise. No random seed set. Augmentation executed prior to any train/test split. |
| `Cryogenic/Cryogenic Temp.xlsx` | Excel Spreadsheet | 10,302 | Original cryogenic dataset | Original observations | 54 rows, 5 columns (`Base TC`, `Filler TC`, `Vol`, `Temp`, `Composite TC`). Temperatures 2.0 K to 120.0 K. |
| `Cryogenic/Cryogenic_Temp_3x_Augmented_1Percent_Noise.xlsx` | Excel Spreadsheet | 18,531 | Augmented cryogenic dataset | Augmented observations | 162 rows (3x 54). First 54 rows are exact copies; remaining 108 are ~1% Gaussian noise descendants. |
| `Cryogenic/371 ET.ipynb` | Jupyter Notebook | 1,313,935 | Extra Trees model for cryogenic regime | Model training & evaluation | Trained on augmented file. Leaked test R² = 0.9095. Manual prediction for Maxwell benchmark at 4.2 K. |
| `Cryogenic/372 GB.ipynb` | Jupyter Notebook | 1,379,009 | Gradient Boosting model for cryogenic regime | Model training & evaluation | Trained on augmented file. Leaked test R² = 0.9569. |
| `Cryogenic/373 RF.ipynb` | Jupyter Notebook | 1,350,663 | Random Forest model for cryogenic regime | Model training & evaluation | Trained on augmented file. Leaked test R² = 0.9230. |
| `Cryogenic/374 XGBoost.ipynb` | Jupyter Notebook | 2,482,267 | XGBoost model for cryogenic regime | Model training & evaluation | Trained on augmented file. Leaked test R² = 0.9304. |
| `Cryogenic/4.2K.docx` | Word Document | 17,453 | Validation data at 4.2 K | Theoretical Maxwell model calculation | Titled "Thermal Conductivity Estimation at 4.2 K Using Maxwell Model". Not physical experimental measurements. |
| `High/High Temp.xlsx` | Excel Spreadsheet | 9,980 | Original elevated temperature dataset | Original observations | 42 rows, 5 columns. Temperatures 308 K to 423 K. 25 of 42 rows (59.5%) are liquid nanofluids (water matrix), not solid composites. |
| `High/High_Temp_3x_Augmented_1Percent_Noise.xlsx` | Excel Spreadsheet | 16,175 | Augmented high-temp dataset | Augmented observations | 126 rows (3x 42). Part 1 exact match; Parts 2-3 are 1% noisy clones. |
| `High/381 ET.ipynb` | Jupyter Notebook | 1,915,255 | Extra Trees model for high-temp regime | Model training & evaluation | Trained on augmented file with pre-split shuffle. Leaked test R² = 0.9566. |
| `High/382 GB.ipynb` | Jupyter Notebook | 2,058,876 | Gradient Boosting model for high-temp regime | Model training & evaluation | Trained on augmented file. Leaked test R² = 0.8742. |
| `High/383 RF.ipynb` | Jupyter Notebook | 1,851,156 | Random Forest model for high-temp regime | Model training & evaluation | Trained on augmented file. Leaked test R² = 0.9430. |
| `High/384 XGB.ipynb` | Jupyter Notebook | 1,285,449 | XGBoost model for high-temp regime | Model training & evaluation | Trained on augmented file. Leaked test R² = 0.9140. |
| `High/323K.docx` | Word Document | 17,319 | Validation data at 323 K | Theoretical Maxwell model calculation | Titled "Thermal Conductivity of Epoxy Composites at 323 K". Explicitly states "Maxwell model is used for calculation". |
| `Room/Room Temp.xlsx` | Excel Spreadsheet | 12,208 | Original room temperature dataset | Original observations | 160 rows, 4 columns (`Base TC`, `Filler TC`, `Vol`, `Composite TC`). Missing `Temp` column (implicitly 298.15 K). |
| `Room/Room_Temp_3x_Augmented_1Percent_Noise.xlsx` | Excel Spreadsheet | 32,324 | Augmented room-temp dataset | Augmented observations | 480 rows (3x 160). Part 1 exact match; Parts 2-3 are 1% noisy clones. |
| `Room/375 ET.ipynb` | Jupyter Notebook | 1,817,074 | Extra Trees model for room regime | Model training & evaluation | Trained on augmented file. Leaked test R² = 0.8681. |
| `Room/376 GB.ipynb` | Jupyter Notebook | 1,891,787 | Gradient Boosting model for room regime | Model training & evaluation | Trained on augmented file. Leaked test R² = 0.8166. |
| `Room/377 RF.ipynb` | Jupyter Notebook | 1,893,521 | Random Forest model for room regime | Model training & evaluation | Trained on augmented file. Leaked test R² = 0.8524. |
| `Room/378 XGBoost.ipynb` | Jupyter Notebook | 1,365,458 | XGBoost model for room regime | Model training & evaluation | Trained on augmented file. Leaked test R² = 0.8203. |
| `Room/300K.docx` | Word Document | 17,400 | Validation data at 300 K | Theoretical Maxwell model calculation | Titled "Thermal Conductivity Estimation at 300 K Using Maxwell Model". |

---

## 3. Generated Clean Datasets in `revision_work/data/`

1. **`provenance_audit.csv`**:
   - Master dataset containing all 256 unique physical observations across all three regimes.
   - Includes stable observation identifiers (`CRYO_000` to `CRYO_053`, `HIG_000` to `HIG_041`, `ROO_000` to `ROO_159`).
   - Contains classified matrix and filler material identities, material classification (solid composite vs. liquid nanofluid), and provenance status.

2. **`cryogenic_clean_original.csv`, `high_clean_original.csv`, `room_clean_original.csv`**:
   - Clean, non-augmented versions of the original datasets with verified numeric types and stable IDs.

3. **`cryogenic_train_test_split.csv`, `high_train_test_split.csv`, `room_train_test_split.csv`**:
   - Explicit partition assignment records (`train` vs. `test`) established on original observations before any augmentation.
   - Confirms strictly 0% sample or twin leakage between training and testing sets.
