# Critical Scientific Audit: Data Leakage via Pre-Split Augmentation

**Manuscript Reference:** Submitted to *Measurement* (Elsevier)  
**Deliverable File:** `revision_work/reports/leakage_audit.md`  
**Associated Implementation:** `revision_work/src/01_leakage_safe_pipeline.py`  
**Output Results:** `revision_work/results/leakage_comparison_metrics.csv`  

---

## 1. Executive Summary

Data leakage represents the most critical methodological error identified in the original research manuscript. 

The original pipeline performed synthetic data augmentation (generating two noisy descendants per observation via proportional Gaussian perturbation) **across the entire dataset before conducting the train/test split**. 

When a standard random split (`train_test_split(..., test_size=0.2, random_state=42)`) was subsequently applied to the 3x-augmented dataset, synthetic twins of virtually every test observation were routed into the training partition. 

As a consequence:
- **90.9% to 96.9% of all test samples had a near-identical twin in the training set.**
- The models were tested on predicting samples that differed from training samples by only $\sim 1\%$ random noise.
- The reported high performance metrics (e.g., $R^2 > 0.95$ in High, $R^2 > 0.85$ in Room) were **severely inflated artifacts of data leakage**.
- When evaluated under a methodologically strict, leakage-safe pipeline, performance in the Room Temperature regime collapsed to $R^2 = 0.31$ (Random Forest) and $R^2 = 0.02$ (XGBoost).

---

## 2. Mathematical Demonstration of Leakage

Let the original non-augmented dataset be $\mathcal{D}_0 = \{(\mathbf{x}_i, y_i)\}_{i=1}^N$, where $\mathbf{x}_i$ is the feature vector and $y_i$ is the composite thermal conductivity.

### 2.1 The Original (Flawed) Augmentation Procedure
In `336 Data Augmentation.ipynb`, the dataset was expanded threefold:
$$\mathcal{D}_{\text{aug}} = \mathcal{D}_0 \cup \mathcal{D}_1 \cup \mathcal{D}_2$$
where for each copy $k \in \{1, 2\}$ and each observation $i \in \{1, \dots, N\}$:
$$\mathbf{x}_{i}^{(k)} = \mathbf{x}_i \odot \left( \mathbf{1} + \eta \boldsymbol{\epsilon}_{i, x}^{(k)} \right), \quad y_{i}^{(k)} = y_i \left( 1 + \eta \epsilon_{i, y}^{(k)} \right)$$
with noise scale $\eta = 0.01$ and standard Gaussian perturbations $\boldsymbol{\epsilon} \sim \mathcal{N}(0, \mathbf{I})$.

The full augmented set $\mathcal{D}_{\text{aug}}$ ($|\mathcal{D}_{\text{aug}}| = 3N$) was then partitioned randomly:
$$\mathcal{D}_{\text{aug}} = \mathcal{T}_{\text{train}} \cup \mathcal{T}_{\text{test}}, \quad |\mathcal{T}_{\text{test}}| = 0.2 \times 3N = 0.6N$$

### 2.2 Probability of Twin Leakage
For any given original observation $i$, there are 3 instances in $\mathcal{D}_{\text{aug}}$: $\{\mathbf{z}_i^{(0)}, \mathbf{z}_i^{(1)}, \mathbf{z}_i^{(2)}\}$.
Under random uniform partitioning with test probability $p = 0.20$ and train probability $q = 0.80$, the probability that at least one instance enters the test set AND at least one instance enters the training set is:
$$P(\text{Leakage for observation } i) = 1 - p^3 - q^3 = 1 - (0.2)^3 - (0.8)^3 = 1 - 0.008 - 0.512 = 0.480$$
More critically, given that an instance enters the test set, the conditional probability that its twin exists in the training set is:
$$P(\text{Twin in Train} \mid \text{Sample in Test}) = 1 - p^2 = 1 - (0.2)^2 = 0.960 \quad (96.0\%)$$

### 2.3 Empirical Verification of Leakage in the Supplied Files
Tracking the parent index $i = (\text{row\_idx} \pmod N)$ through the original split code confirms the mathematical prediction:

| Regime | Augmented Total ($3N$) | Train Samples ($0.8 \times 3N$) | Test Samples ($0.2 \times 3N$) | Unique Parent IDs in Test | Parent IDs with Twin in Train | Empirical Leakage Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cryogenic** | 162 | 129 | 33 | 26 | 25 | **90.9%** (30 of 33 test rows) |
| **High** | 126 | 100 | 26 | 21 | 20 | **88.5%** (23 of 26 test rows) |
| **Room** | 480 | 384 | 96 | 75 | 74 | **96.9%** (93 of 96 test rows) |

---

## 3. The Corrected Leakage-Safe Pipeline Architecture

To eliminate data leakage, the pipeline in `revision_work/src/01_leakage_safe_pipeline.py` implements the following protocol:

```
[Original Observations D0] (N=256)
             │
             ▼
   [Stratified / Stable Train/Test Split] (80/20 on D0)
             ├──────────────────────────────────────────┐
             ▼                                          ▼
   [Clean Train Set D_train]                  [Clean Test Set D_test]
        (80% of D0)                                (20% of D0)
             │                                          │
    (Optional Augmentation)                             │
   [Augment TRAIN ONLY: D_train_aug]                    │  (STRICTLY UNTOUCHED)
             │                                          │  (NO CLONES IN TRAIN)
             ▼                                          │
   [Model Fitting & 5-Fold CV]                          │
   (Hyperparameters selected on D_train only)           │
             │                                          │
             ▼                                          ▼
      [Trained Model] ──────── Evaluate ────────► [True Generalisation Metrics]
```

### Protocol Guarantees:
1. **Partition Integrity:** Train/test splitting occurs strictly on parent observation IDs *before* any transformation. Partition membership is saved in `revision_work/data/*_train_test_split.csv`.
2. **Zero Contamination:** No synthetic descendant of any test observation ever enters the training split ($0.0\%$ leakage rate).
3. **Pristine Test Set:** The final test set consists exclusively of untouched, non-augmented physical observations.

---

## 4. Empirical Performance Comparison: Leaked vs. Corrected

The table below contrasts the original leaked results against:
1. **Clean Original:** Models trained on clean, non-augmented original training data and evaluated on untouched test observations.
2. **Leakage-Safe Augmented:** Models trained on training data augmented 3x (within-fold), evaluated on untouched test observations.
3. **Mean Prediction Baseline:** The naive baseline predicting the training set mean.

| Regime | Model | Published / Leaked Test $R^2$ | Corrected Clean Test $R^2$ | Safe-Augmented Test $R^2$ | Mean Baseline $R^2$ | Absolute Performance Drop ($\Delta R^2$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Cryogenic** | **Extra Trees** | 0.9095 | **0.8296** | **0.9308** | -0.0022 | -0.0799 |
| **Cryogenic** | **Gradient Boosting**| 0.9810 | **0.9741** | **0.9636** | -0.0022 | -0.0069 |
| **Cryogenic** | **Random Forest** | 0.9233 | **0.8799** | **0.9446** | -0.0022 | -0.0434 |
| **Cryogenic** | **XGBoost** | 0.9371 | **0.9344** | **0.9507** | -0.0022 | -0.0027 |
| **High** | **Extra Trees** | 0.9566 | **0.7141** | **0.8446** | -0.0053 | -0.2425 |
| **High** | **Gradient Boosting**| 0.8742 | **0.9014** | **0.8794** | -0.0053 | +0.0272 |
| **High** | **Random Forest** | 0.9429 | **0.8545** | **0.9691** | -0.0053 | -0.0884 |
| **High** | **XGBoost** | 0.9140 | **0.8340** | **0.8624** | -0.0053 | -0.0800 |
| **Room** | **Extra Trees** | 0.8681 | **0.3608** | **0.3777** | -0.0103 | **-0.5073** |
| **Room** | **Gradient Boosting**| 0.8166 | **0.1921** | **0.1804** | -0.0103 | **-0.6245** |
| **Room** | **Random Forest** | 0.8525 | **0.3108** | **0.2065** | -0.0103 | **-0.5417** |
| **Room** | **XGBoost** | 0.8203 | **0.0230** | **-0.0179** | -0.0103 | **-0.7973** |

---

## 5. Scientific Analysis of Performance Collapse

### 5.1 Why Room Temperature Collapsed Completely ($R^2: 0.85 \to 0.31$)
In the Room Temperature dataset ($N=160$), 72 distinct filler/matrix material combinations exist. Many systems have only 1 to 3 data points. 
- In the **leaked pipeline**, each unique material had 3 nearly identical copies. The random split placed 1 or 2 copies in the training set and 1 in the test set. Tree-based regressors easily memorized the exact $(k_m, k_f)$ coordinate and predicted the target accurately.
- In the **corrected pipeline**, holdout observations frequently belong to material formulations never seen during training. Decision trees without microstructural features cannot extrapolate accurately across diverse filler chemistries, resulting in $R^2 \approx 0.31\text{--}0.36$.
- XGBoost in Room Temperature completely failed ($R^2 = 0.023$), demonstrating that extreme gradient boosting overfit the sparse training samples and failed on independent test data.

### 5.2 Why Cryogenic Remained Resilient ($R^2 \approx 0.83\text{--}0.97$)
In Cryogenic conditions, thermal conductivity behavior is dominated by temperature dependence ($T \in [2, 120]\text{ K}$). Cryogenic thermal conductivity follows strong power-law relations ($k \propto T^3$ at very low $T$, transitioning to a phonon mean-free-path peak). The smooth functional relationship between temperature and thermal conductivity allowed interpolation across temperatures even when split cleanly.

---

## 6. Reviewer Response Summary

When responding to reviewers regarding data leakage:
1. **Full Transparency:** Acknowledge the pre-split augmentation as a methodological error in the initial submission.
2. **Defensible Correction:** Present the corrected, leakage-safe pipeline results alongside the leaked comparison in the revised manuscript.
3. **Scientific Value:** Explain that unmasking this error enhances the scientific integrity of the work and provides genuine, trustworthy baseline benchmarks for the thermal composite community.
