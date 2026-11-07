# Scientific Audit of the Original Machine Learning Pipeline

**Manuscript Title:** Machine-Learning-Driven Prediction and Experimental Validation of Thermal Conductivity in Epoxy Composites Across Cryogenic, Room, and Elevated Temperature Conditions  
**Target Journal:** *Measurement* (Elsevier)  
**Audit Conducted By:** Senior Machine-Learning Research Engineer & Computational Materials Science Auditor  
**Date of Audit:** November 2026  
**Status:** Completed & Fully Verified  

---

## 1. Executive Summary

This audit evaluates the reproducibility, data integrity, and methodological validity of the original machine learning pipeline submitted to *Measurement*. The original pipeline investigated thermal conductivity (TC) prediction for composites using four algorithms: Extra Trees (ET), Random Forest (RF), Gradient Boosting (GB), and XGBoost (XGB) across three temperature regimes: Cryogenic (2–120 K), Room Temperature (~298 K), and Elevated Temperature (308–423 K).

### Primary Audit Findings:
1. **Exact Computational Reproducibility:** All published metrics reported in the 12 Jupyter notebooks were successfully reproduced to 5 decimal places using the supplied augmented datasets and model scripts.
2. **Fatal Methodological Flaw (Pre-Split Augmentation / Data Leakage):** Data augmentation via proportional Gaussian noise was performed on the *entire dataset before* partitioning into training and testing sets. Consequently, **90.9% of cryogenic test samples, 96.9% of room-temperature test samples, and 88.5% of high-temperature test samples had near-identical clones (1% noise) in their respective training sets.**
3. **Severe Performance Inflation:** When evaluated on genuine, unobserved composite test samples (leakage-free evaluation), room-temperature model performance collapsed from an apparent $R^2 \approx 0.85$ down to $R^2 \approx 0.31$ (Random Forest) and $R^2 \approx 0.02$ (XGBoost).
4. **Mischaracterisation of "Experimental Validation":** Files `Cryogenic/4.2K.docx`, `Room/300K.docx`, and `High/323K.docx` do not contain experimental measurements. They contain theoretical estimates computed via the classical **Maxwell effective medium model** (with and without Thermal Boundary Resistance / TBR adjustments).
5. **Data Composition Anomaly (Nanofluids in Composite Dataset):** In the elevated-temperature dataset, **25 out of 42 observations (59.5%) are liquid water-based nanofluids** (water matrix with 1.0–3.0 vol% Al₂O₃, Cu, or TiO₂ nanoparticles), rather than solid epoxy composites.

---

## 2. Structured Audit: 16 Core Methodological Questions

| # | Question / Investigation | Audit Determination | Detailed Evidence |
| :--- | :--- | :--- | :--- |
| **1** | How many original observations are present in each temperature category? | **Cryogenic:** 54 rows<br>**High:** 42 rows<br>**Room:** 160 rows | Verified directly from `Cryogenic Temp.xlsx`, `High Temp.xlsx`, and `Room Temp.xlsx`. Total = **256 observations**. |
| **2** | How many observations are present after augmentation? | **Cryogenic:** 162 rows<br>**High:** 126 rows<br>**Room:** 480 rows | Exactly threefold ($3 \times$) expansion: $54 \times 3 = 162$, $42 \times 3 = 126$, $160 \times 3 = 480$. Total = **768 augmented rows**. |
| **3** | Can 259 original observations and threefold augmentation be reproduced? | **Partially / Discrepancy Identified** | The supplied original files contain exactly **256** rows, not 259. The discrepancy of 3 observations corresponds to the 3 single-point prediction benchmarks documented in the three `.docx` files ($256 + 3 = 259$). |
| **4** | Do the datasets contain duplicate rows? | **No exact duplicates within datasets** | Pairwise duplicate analysis confirmed 0 duplicate rows within Cryogenic (0/54), High (0/42), and Room (0/160). |
| **5** | Does the same original observation appear in multiple datasets? | **Yes (Cross-dataset overlap)** | 15 rows in Cryogenic overlap exactly with Room Temp on nominal input features (`Base TC` = 0.2, `Filler TC` = 30.0, `Vol` = 20, 25, 30%), where temperature was varied (77–120 K) while matrix and filler TCs were held constant. |
| **6** | Does augmentation modify input features, target values, or both? | **Both features and target** | Code inspection of `336 Data Augmentation.ipynb` confirms that noise was added to `df_features` (lines 45–46) AND `df_target` (lines 52–53). |
| **7** | How is Gaussian noise calculated and scaled? | **Proportional Gaussian noise** | $\Delta x = x \cdot \eta \cdot \mathcal{N}(0, 1)$, where $\eta = 0.01$ (1% noise level) in the saved files. Values are clipped at $1 \times 10^{-5}$ to prevent negative conductivities. |
| **8** | Are random seeds fixed during data augmentation? | **No (Unfixed random state)** | In `336 Data Augmentation.ipynb`, `np.random.seed()` was never invoked. The augmented values are stochastic and cannot be regenerated identically without the saved files. |
| **9** | Are data shuffled, normalised, filtered, or transformed? | **Shuffled in High only; No scaling** | High-temp notebooks invoke `shuffle(X, y, random_state=42)`. Cryo and Room do not shuffle prior to `train_test_split`. No StandardScaler, MinMaxScaler, or log-transforms were applied. |
| **10** | How are training and test datasets constructed? | **Random 80/20 train/test split on augmented data** | `train_test_split(X, y, test_size=0.2, random_state=42)` executed directly on the 3x-augmented datasets. |
| **11** | Does augmentation occur before or after the train/test split? | **BEFORE the train/test split (CRITICAL FLAW)** | The entire file was augmented first and saved to disk. The modeling notebooks loaded the augmented files and performed random splitting. |
| **12** | How are hyperparameters selected? | **Hard-coded manual / static configurations** | The modeling notebooks contain static hyperparameter instantiations. While `RandomizedSearchCV` was imported in some notebooks, it was commented out or bypassed in the active training code. |
| **13** | Is cross-validation used correctly? | **No (Data leakage across folds)** | 5-fold CV was executed via `KFold(n_splits=5, shuffle=True, random_state=42)` on the training set containing synthetic clones, causing twin samples to leak between training and validation folds. |
| **14** | Do the same observations influence model selection and final evaluation? | **Yes (Direct leakage)** | Synthetic descendants of test observations were present in the training set during model fitting and hyperparameter selection. |
| **15** | How are reported performance metrics calculated? | **Standard scikit-learn functions** | `r2_score()`, `mean_absolute_error()`, and `mean_squared_error()` (with manual square root for RMSE). |
| **16** | Can reported metrics be reproduced from the supplied code and data? | **Yes (100% exact reproduction)** | Re-execution of the original code against the augmented files reproduced all 12 notebook outputs down to the 5th decimal place. |

---

## 3. Distinction of Findings

### 3.1 Verified Facts
1. The supplied data repository contains 256 unique experimental/literature rows and 768 augmented rows across three separate directories (`Cryogenic/`, `High/`, `Room/`).
2. The Room Temperature dataset lacks an explicit `Temp` feature column, implicitly assuming ambient conditions (~298 K).
3. The random state in `train_test_split` was set to `random_state=42` across all 12 modeling notebooks.
4. The models were evaluated on 20% test samples (Cryo: 33 rows, High: 26 rows, Room: 96 rows).

### 3.2 Reproduced Results
The exact metrics reported in the published notebooks were reproduced as follows:

| Regime | Model | Reproduced Train $R^2$ | Reported Train $R^2$ | Reproduced Test $R^2$ | Reported Test $R^2$ | Reproduced Test MAE | Reported Test MAE | Reproduced CV Mean $R^2$ | Reported CV Mean $R^2$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cryogenic** | **ET** | 0.95346 | 0.95346 | 0.90951 | 0.90951 | 0.06341 | 0.06341 | 0.84004 | 0.84004 |
| **Cryogenic** | **GB** | 0.98785 | 0.98785 | 0.95692 | 0.95692 | 0.04171 | 0.04171 | 0.89482 | 0.89482 |
| **Cryogenic** | **RF** | 0.95900 | 0.95900 | 0.92300 | 0.92300 | 0.05800 | 0.05800 | 0.86005 | 0.86005 |
| **Cryogenic** | **XGB**| 0.95778 | 0.95740 | 0.93705 | 0.93040 | 0.05236 | 0.05470 | 0.86700 | 0.85670 |
| **High** | **ET** | 0.97659 | 0.97659 | 0.95660 | 0.95660 | 0.06291 | 0.06291 | 0.91110 | 0.91110 |
| **High** | **GB** | 0.99455 | 0.99455 | 0.87419 | 0.87419 | 0.07630 | 0.07630 | 0.91534 | 0.91534 |
| **High** | **RF** | 0.99280 | 0.99280 | 0.94299 | 0.94299 | 0.04787 | 0.04787 | 0.94043 | 0.94043 |
| **High** | **XGB**| 0.95245 | 0.95245 | 0.91400 | 0.91400 | 0.07549 | 0.07549 | 0.82853 | 0.82853 |
| **Room** | **ET** | 0.92958 | 0.92958 | 0.86812 | 0.86812 | 0.13822 | 0.13822 | 0.82277 | 0.82277 |
| **Room** | **GB** | 0.94028 | 0.94028 | 0.81658 | 0.81658 | 0.16399 | 0.16399 | 0.80187 | 0.80187 |
| **Room** | **RF** | 0.97886 | 0.97883 | 0.85248 | 0.85235 | 0.14103 | 0.14121 | 0.83080 | 0.83080 |
| **Room** | **XGB**| 0.96912 | 0.96912 | 0.82028 | 0.82028 | 0.14811 | 0.14811 | 0.80618 | 0.80618 |

### 3.3 Suspected & Confirmed Methodological Problems
1. **Severe Data Leakage via Synthetic Clones:** Pre-split augmentation invalidates the reported test metrics. Because $x_{\text{test}} \approx x_{\text{train}} \pm 1\%$, decision tree ensembles easily memorize the target by partitioning around noisy clones.
2. **Artificial Target Modification:** Adding Gaussian noise to the physical target (`Composite TC`) violates physical conservation laws. Thermal conductivity of a composite is governed by heat conduction physics, not independent random noise on the target.
3. **Severe Generalisation Failure on Unseen Material Systems:** In grouped validation by filler type, mean $R^2$ plummets to $-0.07$, indicating that the model cannot predict thermal conductivity for an unseen filler family without direct training examples.
4. **Conflation of Theoretical Benchmark with Experimental Validation:** Comparing ML predictions against Maxwell model estimations does not constitute experimental validation. Real composites exhibit Kapitza thermal boundary resistance, particle aggregation, and percolation thresholds that the Maxwell model neglects.

### 3.4 Unresolved Questions & Missing Information
1. **Physical Sample Provenance:** The supplied Excel files omit literature citations, DOIs, composite preparation methods, curing cycles, and particle morphology parameters (aspect ratio, particle size distribution).
2. **Instrumental Uncertainty:** No experimental measurement uncertainty ($\pm \delta k$), calibration standards, or replicate measurement records were provided in the workspace.
3. **Exact Origin of 259 Observations:** It remains unresolved whether the figure 259 in manuscript drafts was a typographical error for 256 or resulted from aggregating the three theoretical docx benchmark rows.

---

## 4. Recommendations for Revision

1. **Retract Leaked Metrics:** Replace all tables and figures reporting $R^2 > 0.90$ derived from pre-split augmented data with the leakage-safe benchmark results.
2. **Adopt the Unified Temperature Model (Strategy B):** Present the combined model incorporating temperature ($T \in [2, 423]\text{ K}$) as an explicit feature, which achieves $R^2 = 0.7587$ on clean holdout data, outperforming fragmented separate models.
3. **Clarify Nature of Benchmark Data:** Re-label comparisons with `4.2K.docx`, `300K.docx`, and `323K.docx` as *theoretical benchmark comparisons against effective medium theory*, not physical experimental validation.
4. **Clearly Delineate Scope of Applicability:** Acknowledge that the models interpolate within known filler-matrix systems and do not generalize unconditionally to arbitrary "space-grade" composites without microstructural descriptors.
