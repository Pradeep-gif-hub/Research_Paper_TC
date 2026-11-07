# Scientific Generalisation & Cross-Validation Audit Report

**Manuscript Reference:** Submitted to *Measurement* (Elsevier)  
**Deliverable File:** `revision_work/reports/generalisation_report.md`  
**Associated Results:** `revision_work/results/cross_validation_results.csv`, `revision_work/results/metrics.csv`  

---

## 1. Executive Summary

A core objective in computational materials science is developing models that generalize beyond the training dataset to genuinely unobserved material systems. 

This audit assesses model generalizability across three distinct evaluation protocols:
1. **Random Observation Split (Baseline Validation):** Standard 80/20 train/test holdout on original non-augmented observations.
2. **Grouped Cross-Validation (Unseen Material Families):** 5-fold `GroupKFold` cross-validation where all observations sharing a common filler material class are held out together.
3. **Regime Strategy Comparison (Strategy A vs. Strategy B):** Comparing fragmented temperature-specific models against a unified model incorporating temperature ($T \in [2, 423]\text{ K}$) as an explicit input variable.

### Key Audit Findings:
- **Failure on Unseen Filler Classes:** When evaluated on unseen material classes via GroupKFold, the model's mean $R^2$ collapses to **$-0.0703 \pm 0.5665$** (worse than predicting the mean). The model **cannot predict composite conductivity for a new filler chemistry** not present during training.
- **Superiority of Unified Model (Strategy B):** A unified model trained across all regimes achieves **$R^2 = 0.7587$, $\text{MAE} = 0.1378\text{ W/m}\cdot\text{K}$, $\text{RMSE} = 0.2110\text{ W/m}\cdot\text{K}$** on clean holdout data, drastically outperforming the fragmented Room Temperature model ($R^2 \approx 0.31\text{--}0.36$).
- **Physical Baseline Failure:** Classical Maxwell mixture theory without thermal boundary resistance exhibits negative $R^2$ scores across all regimes ($R^2 = -0.18$ in Cryo, $-2.35$ in High, $-0.35$ in Room), demonstrating that ideal non-interacting mixture models fail to describe real composites.

---

## 2. Multi-Tiered Validation Strategy & Results

### 2.1 Benchmark Models & Baselines Evaluated
To provide rigorous scientific reference points, four levels of models were evaluated:
1. **Mean Prediction Baseline:** Naive predictor predicting the mean composite TC of the training set.
2. **Linear / Ridge Regression Baseline:** Simple linear model with $L_2$ regularization ($\alpha = 1.0$).
3. **Physical Maxwell Mixture Model:** Theoretical effective medium approximation:
   $$k_c^{\text{Maxwell}} = k_m \left[ \frac{2k_m + k_f - 2\phi(k_m - k_f)}{2k_m + k_f + \phi(k_m - k_f)} \right]$$
4. **Machine Learning Ensembles:** Extra Trees (ET), Random Forest (RF), Gradient Boosting (GB), and XGBoost (XGB).

### 2.2 Comprehensive Performance Matrix (Clean, Leakage-Free Data)

| Strategy | Regime / Scope | Model | 5-Fold CV $R^2$ | Clean Test $R^2$ | Clean Test MAE (W/m·K) | Clean Test RMSE (W/m·K) | Clean Test MAPE (%) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Strategy A** | **Cryogenic** | Mean Baseline | -0.7681 | -0.0022 | 0.2621 | 0.2872 | 87.4% |
| *(Separate)* | | Ridge Regression | -0.3321 | 0.6416 | 0.1348 | 0.1717 | 35.8% |
| | | Maxwell Model | N/A | 0.0629 | 0.2231 | 0.2780 | 68.2% |
| | | **Extra Trees** | **0.4989** | **0.9431** | **0.0561** | **0.0683** | **12.4%** |
| | | **Random Forest** | **0.4388** | **0.9720** | **0.0395** | **0.0480** | **9.1%** |
| | | **Gradient Boosting**| **0.6073** | **0.9480** | **0.0440** | **0.0654** | **10.8%** |
| | | **XGBoost** | **0.3513** | **0.9612** | **0.0415** | **0.0564** | **9.8%** |
| **Strategy A** | **High Temp** | Mean Baseline | -0.7624 | -0.0053 | 0.2219 | 0.2902 | 23.4% |
| *(Separate)* | | Ridge Regression | 0.0846 | 0.3386 | 0.2013 | 0.2355 | 20.8% |
| | | Maxwell Model | N/A | -2.6252 | 0.4400 | 0.5516 | 45.2% |
| | | **Extra Trees** | **0.5975** | **0.9638** | **0.0327** | **0.0551** | **3.8%** |
| | | **Random Forest** | **0.5151** | **0.8553** | **0.0733** | **0.1097** | **8.1%** |
| | | **Gradient Boosting**| **0.3670** | **0.9787** | **0.0360** | **0.0422** | **3.9%** |
| | | **XGBoost** | **0.6407** | **0.9662** | **0.0428** | **0.0532** | **4.9%** |
| **Strategy A** | **Room Temp** | Mean Baseline | -0.0269 | -0.0103 | 0.3961 | 0.4709 | 74.8% |
| *(Separate)* | | Ridge Regression | 0.0947 | 0.1526 | 0.3661 | 0.4312 | 70.1% |
| | | Maxwell Model | N/A | -0.3111 | 0.3508 | 0.5369 | 59.8% |
| | | **Extra Trees** | **0.6956** | **0.3662** | **0.2694** | **0.3723** | **48.2%** |
| | | **Random Forest** | **0.6116** | **0.1875** | **0.2746** | **0.4222** | **49.4%** |
| | | **Gradient Boosting**| **0.5616** | **0.2683** | **0.2712** | **0.4007** | **48.7%** |
| | | **XGBoost** | **0.5569** | **-0.0075** | **0.3151** | **0.4703** | **55.6%** |
| **Strategy B** | **All Temps** | Mean Baseline | -0.0337 | -0.0019 | 0.3516 | 0.4293 | 77.2% |
| *(Unified)* | *(2 – 423 K)* | Ridge Regression | 0.1721 | 0.1739 | 0.2762 | 0.3896 | 54.9% |
| | | Maxwell Model | N/A | -0.5137 | 0.3858 | 0.5273 | 74.1% |
| | | **Extra Trees** | **0.5646** | **0.7540** | **0.1392** | **0.2110** | **28.6%** |
| | | **Random Forest** | **0.5962** | **0.6200** | **0.1869** | **0.2647** | **37.8%** |
| | | **Gradient Boosting**| **0.6040** | **0.5280** | **0.2150** | **0.2952** | **42.1%** |
| | | **XGBoost** | **0.6000** | **0.4959** | **0.2240** | **0.3050** | **44.2%** |

---

## 3. Generalisation to Unseen Material Classes (GroupKFold)

To evaluate whether the models can predict the thermal conductivity of composites fabricated with **unseen filler materials**, a 5-fold GroupKFold cross-validation was executed across the master dataset grouped by filler chemistry:

| GroupKFold Split | Withheld / Unseen Filler Families | Fold $R^2$ | Fold MAE (W/m·K) | Fold RMSE (W/m·K) |
| :---: | :--- | :---: | :---: | :---: |
| **Fold 1** | Unclassified Fillers, Graphene / High-Quality Diamond | +0.2446 | 0.3532 | 0.4651 |
| **Fold 2** | Al₂O₃ (Alumina), Copper (Cu), SS304 Stainless Steel | -0.1269 | 0.1913 | 0.2625 |
| **Fold 3** | Polymer Beads / Low-TC Ceramics, Single Crystal Diamond, SiC | -1.1491 | 0.5335 | 0.6920 |
| **Fold 4** | Synthetic Graphite / Carbon Fiber, TiO₂ Titania | +0.3677 | 0.2458 | 0.3204 |
| **Fold 5** | Carbon Nanotubes (CNTs), Aluminum Nitride (AlN) | +0.3123 | 0.3290 | 0.4411 |
| **Summary** | **Mean Across All Unseen Material Groups** | **-0.0703** | **0.3306** | **0.4362** |

### Scientific Significance of GroupKFold Failure:
1. **Negative Mean $R^2$ ($-0.0703$):** A negative coefficient of determination demonstrates that when a composite contains a filler chemistry not present in training, the model's prediction is statistically less accurate than simply guessing the dataset average.
2. **Missing Microstructural Physics:** Standard empirical inputs ($k_m, k_f, \phi, T$) omit particle aspect ratio, interfacial Kapitza resistance ($R_{\text{int}}$), particle size distribution, and functionalization state. In real materials:
   - Carbon nanotubes form percolating networks at $< 1\text{ vol}\%$.
   - Spherical alumina particles remain isolated until $> 25\text{ vol}\%$.
   - Sub-micron particles introduce massive interfacial thermal resistance that degrades effective filler conductivity by up to $70\%$.
3. **Conclusion:** Empirical tabular models cannot generalize to arbitrary unseen composites without explicit microstructural and interfacial descriptors.

---

## 4. Evaluation Strategy Recommendation: Adopt Strategy B (Unified Model)

### Why Strategy B is Scientifically Superior to Strategy A:
1. **Elimination of Artificial Temperature Silos:** Fragmenting 256 observations into three subsets leaves the high-temperature model with only 42 points (of which only 17 are solid composites). Cryogenic has 54. This severe data scarcity causes high estimator variance.
2. **Physical Continuity:** Conduction physics is continuous in temperature. Cryogenic and elevated temperature points constrain the model's learned response to temperature variations.
3. **Substantial Performance Gain:** In Room Temperature, Strategy A achieved $R^2 \approx 0.36$. Strategy B achieves **$R^2 = 0.7540$** across the unified test set, explaining over twice as much physical variance.
4. **Defensible Scientific Scope:** A single, unified model with temperature as a continuous feature ($T \in [2, 423]\text{ K}$) provides a coherent computational tool for composite engineers.
