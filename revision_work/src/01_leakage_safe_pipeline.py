"""
01_leakage_safe_pipeline.py
Leakage-Safe Machine Learning Pipeline & Comparative Audit
==========================================================
Implements both:
1. The original published pipeline (with pre-split augmentation causing data leakage)
2. The methodologically corrected pipeline:
   - Split performed strictly on original physical observations
   - Augmentation (if applied) performed ONLY on the training split
   - Final evaluation exclusively on untouched original test observations
   - K-fold Cross-Validation strictly grouped or partition-safe

Outputs metrics comparison, split memberships, and verified leakage metrics.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.utils import shuffle

# Fixed seeds for exact scientific reproducibility
SEED = 42

def load_datasets():
    datasets = {
        'Cryogenic': {
            'orig_path': 'Cryogenic/Cryogenic Temp.xlsx',
            'aug_path': 'Cryogenic/Cryogenic_Temp_3x_Augmented_1Percent_Noise.xlsx',
            'features': ['Base TC', 'Filler TC', 'Vol', 'Temp'],
            'target': 'Composite TC',
            'shuffle_first': False
        },
        'High': {
            'orig_path': 'High/High Temp.xlsx',
            'aug_path': 'High/High_Temp_3x_Augmented_1Percent_Noise.xlsx',
            'features': ['Base TC', 'Filler TC', 'Vol', 'Temp'],
            'target': 'Composite TC',
            'shuffle_first': True
        },
        'Room': {
            'orig_path': 'Room/Room Temp.xlsx',
            'aug_path': 'Room/Room_Temp_3x_Augmented_1Percent_Noise.xlsx',
            'features': ['Base TC', 'Filler TC', 'Vol'],
            'target': 'Composite TC',
            'shuffle_first': False
        }
    }
    return datasets

def get_original_model(regime, algo):
    """
    Instantiates models with the exact hyperparameters used in the published notebooks.
    """
    if regime == 'Cryogenic':
        if algo == 'ET':
            return ExtraTreesRegressor(n_estimators=200, max_depth=12, min_samples_split=5, min_samples_leaf=3, max_features='sqrt', random_state=SEED, n_jobs=-1)
        elif algo == 'GB':
            return GradientBoostingRegressor(n_estimators=600, learning_rate=0.03, max_depth=4, subsample=0.6, max_features='sqrt', min_samples_split=5, min_samples_leaf=3, random_state=SEED)
        elif algo == 'RF':
            return RandomForestRegressor(n_estimators=400, max_depth=15, min_samples_split=4, min_samples_leaf=3, max_features='sqrt', random_state=SEED, n_jobs=-1)
        elif algo == 'XGB':
            return XGBRegressor(subsample=0.5, reg_lambda=5, reg_alpha=0.1, n_estimators=250, max_depth=3, learning_rate=0.03, colsample_bytree=0.8, random_state=SEED, verbosity=0, n_jobs=-1)
            
    elif regime == 'High':
        if algo == 'ET':
            return ExtraTreesRegressor(n_estimators=150, min_samples_split=5, min_samples_leaf=2, max_features=0.8, max_depth=5, random_state=SEED, n_jobs=-1)
        elif algo == 'GB':
            return GradientBoostingRegressor(subsample=0.8, n_estimators=150, min_samples_split=15, min_samples_leaf=2, max_features='sqrt', max_depth=3, learning_rate=0.05, random_state=SEED)
        elif algo == 'RF':
            return RandomForestRegressor(n_estimators=100, min_samples_split=2, min_samples_leaf=1, max_features=1.0, max_depth=25, random_state=SEED, n_jobs=-1)
        elif algo == 'XGB':
            return XGBRegressor(subsample=0.6, reg_lambda=1, reg_alpha=1, n_estimators=400, max_depth=8, learning_rate=0.1, gamma=0, colsample_bytree=1.0, objective='reg:squarederror', random_state=SEED, n_jobs=-1)
            
    elif regime == 'Room':
        if algo == 'ET':
            return ExtraTreesRegressor(n_estimators=150, min_samples_split=2, min_samples_leaf=1, max_features=0.8, max_depth=10, bootstrap=False, random_state=SEED, n_jobs=-1)
        elif algo == 'GB':
            return GradientBoostingRegressor(subsample=0.7, n_estimators=300, min_samples_split=15, min_samples_leaf=5, max_features='sqrt', max_depth=4, learning_rate=0.03, random_state=SEED)
        elif algo == 'RF':
            return RandomForestRegressor(n_estimators=250, min_samples_split=2, min_samples_leaf=1, max_features=0.6, max_depth=15, random_state=SEED, n_jobs=-1)
        elif algo == 'XGB':
            return XGBRegressor(subsample=0.6, reg_lambda=1, reg_alpha=1, n_estimators=400, max_depth=8, learning_rate=0.1, gamma=0, colsample_bytree=1.0, objective='reg:squarederror', random_state=SEED, n_jobs=-1)

    raise ValueError(f"Unknown config: {regime}, {algo}")

def run_pipeline_audit():
    datasets = load_datasets()
    algorithms = ['ET', 'GB', 'RF', 'XGB']
    
    records = []
    
    os.makedirs('revision_work/results', exist_ok=True)
    os.makedirs('revision_work/data', exist_ok=True)
    
    for regime, meta in datasets.items():
        print(f"\n=======================================================")
        print(f"PROCESSING REGIME: {regime}")
        print(f"=======================================================")
        
        # Load datasets
        df_orig = pd.read_excel(meta['orig_path'])
        df_aug = pd.read_excel(meta['aug_path'])
        n_orig = len(df_orig)
        
        # Assign stable original IDs
        df_orig['orig_id'] = [f"{regime[:3].upper()}_{i:03d}" for i in range(n_orig)]
        df_aug['orig_id'] = [f"{regime[:3].upper()}_{(i % n_orig):03d}" for i in range(len(df_aug))]
        
        # Save clean original dataset with stable IDs
        df_orig.to_csv(f"revision_work/data/{regime.lower()}_clean_original.csv", index=False)
        
        # -------------------------------------------------------------
        # PIPELINE 1: PUBLISHED / REPRODUCED PIPELINE (LEAKED)
        # -------------------------------------------------------------
        X_aug = df_aug[meta['features']]
        y_aug = df_aug[meta['target']]
        aug_orig_ids = df_aug['orig_id']
        
        if meta['shuffle_first']:
            X_aug, y_aug, aug_orig_ids = shuffle(X_aug, y_aug, aug_orig_ids, random_state=SEED)
            
        X_tr_leak, X_te_leak, y_tr_leak, y_te_leak, ids_tr_leak, ids_te_leak = train_test_split(
            X_aug, y_aug, aug_orig_ids, test_size=0.2, random_state=SEED
        )
        
        # Quantify Leakage in Test Set
        train_id_set = set(ids_tr_leak)
        leaked_count = sum(1 for test_id in ids_te_leak if test_id in train_id_set)
        leakage_rate = (leaked_count / len(ids_te_leak)) * 100.0
        
        # -------------------------------------------------------------
        # PIPELINE 2: CORRECTED LEAKAGE-FREE (Original Data Only)
        # -------------------------------------------------------------
        X_orig = df_orig[meta['features']]
        y_orig = df_orig[meta['target']]
        orig_ids = df_orig['orig_id']
        
        X_tr_clean, X_te_clean, y_tr_clean, y_te_clean, ids_tr_clean, ids_te_clean = train_test_split(
            X_orig, y_orig, orig_ids, test_size=0.2, random_state=SEED
        )
        
        # Record partition membership
        split_df = pd.DataFrame({
            'orig_id': list(ids_tr_clean) + list(ids_te_clean),
            'partition': ['train'] * len(ids_tr_clean) + ['test'] * len(ids_te_clean)
        })
        split_df.to_csv(f"revision_work/data/{regime.lower()}_train_test_split.csv", index=False)
        
        # -------------------------------------------------------------
        # PIPELINE 3: LEAKAGE-SAFE AUGMENTED (Train-Only Augmentation)
        # -------------------------------------------------------------
        np.random.seed(SEED)
        aug_X_tr = [X_tr_clean]
        aug_y_tr = [y_tr_clean]
        for _ in range(2):
            noise_X = X_tr_clean * 0.01 * np.random.randn(*X_tr_clean.shape)
            new_X = (X_tr_clean + noise_X).clip(lower=1e-5)
            noise_y = y_tr_clean * 0.01 * np.random.randn(*y_tr_clean.shape)
            new_y = (y_tr_clean + noise_y).clip(lower=1e-5)
            aug_X_tr.append(new_X)
            aug_y_tr.append(new_y)
        X_tr_safe_aug = pd.concat(aug_X_tr, ignore_index=True)
        y_tr_safe_aug = pd.concat(aug_y_tr, ignore_index=True)
        
        # Evaluate All Algorithms
        for algo in algorithms:
            # Model 1: Leaked
            m_leak = get_original_model(regime, algo)
            m_leak.fit(X_tr_leak, y_tr_leak)
            y_pred_tr_leak = m_leak.predict(X_tr_leak)
            y_pred_te_leak = m_leak.predict(X_te_leak)
            
            # Cross-validation on leaked training set
            cv_leak = KFold(n_splits=5, shuffle=True, random_state=SEED)
            cv_scores_leak = cross_val_score(m_leak, X_tr_leak, y_tr_leak, cv=cv_leak, scoring='r2', n_jobs=-1)
            
            # Model 2: Clean Unaugmented
            m_clean = get_original_model(regime, algo)
            m_clean.fit(X_tr_clean, y_tr_clean)
            y_pred_tr_clean = m_clean.predict(X_tr_clean)
            y_pred_te_clean = m_clean.predict(X_te_clean)
            
            cv_clean = KFold(n_splits=5, shuffle=True, random_state=SEED)
            cv_scores_clean = cross_val_score(m_clean, X_tr_clean, y_tr_clean, cv=cv_clean, scoring='r2', n_jobs=-1)
            
            # Model 3: Leakage-Safe Train Augmentation
            m_safe = get_original_model(regime, algo)
            m_safe.fit(X_tr_safe_aug, y_tr_safe_aug)
            y_pred_tr_safe = m_safe.predict(X_tr_safe_aug)
            y_pred_te_safe = m_safe.predict(X_te_clean)
            
            # Mean Baseline on Clean Test Set
            y_pred_mean = np.full_like(y_te_clean, y_tr_clean.mean())
            r2_mean = r2_score(y_te_clean, y_pred_mean)
            mae_mean = mean_absolute_error(y_te_clean, y_pred_mean)
            rmse_mean = np.sqrt(mean_squared_error(y_te_clean, y_pred_mean))
            
            record = {
                'Regime': regime,
                'Algorithm': algo,
                # Leaked metrics
                'Leaked_Train_R2': r2_score(y_tr_leak, y_pred_tr_leak),
                'Leaked_Test_R2': r2_score(y_te_leak, y_pred_te_leak),
                'Leaked_Test_MAE': mean_absolute_error(y_te_leak, y_pred_te_leak),
                'Leaked_Test_RMSE': np.sqrt(mean_squared_error(y_te_leak, y_pred_te_leak)),
                'Leaked_CV_Mean_R2': cv_scores_leak.mean(),
                'Leaked_CV_Std_R2': cv_scores_leak.std(),
                'Leakage_Rate_pct': leakage_rate,
                # Clean unaugmented metrics
                'Clean_Train_R2': r2_score(y_tr_clean, y_pred_tr_clean),
                'Clean_Test_R2': r2_score(y_te_clean, y_pred_te_clean),
                'Clean_Test_MAE': mean_absolute_error(y_te_clean, y_pred_te_clean),
                'Clean_Test_RMSE': np.sqrt(mean_squared_error(y_te_clean, y_pred_te_clean)),
                'Clean_CV_Mean_R2': cv_scores_clean.mean(),
                'Clean_CV_Std_R2': cv_scores_clean.std(),
                # Safe augmented metrics
                'SafeAug_Test_R2': r2_score(y_te_clean, y_pred_te_safe),
                'SafeAug_Test_MAE': mean_absolute_error(y_te_clean, y_pred_te_safe),
                'SafeAug_Test_RMSE': np.sqrt(mean_squared_error(y_te_clean, y_pred_te_safe)),
                # Baseline
                'Mean_Baseline_R2': r2_mean,
                'Mean_Baseline_MAE': mae_mean,
                'Mean_Baseline_RMSE': rmse_mean,
            }
            records.append(record)
            
            print(f"[{regime} {algo:3s}] "
                  f"Leaked Test R2={record['Leaked_Test_R2']:.4f} (CV={record['Leaked_CV_Mean_R2']:.4f}) | "
                  f"Clean Test R2={record['Clean_Test_R2']:.4f} (CV={record['Clean_CV_Mean_R2']:.4f}) | "
                  f"SafeAug Test R2={record['SafeAug_Test_R2']:.4f} | "
                  f"Mean Baseline R2={r2_mean:.4f}")

    df_out = pd.DataFrame(records)
    out_path = 'revision_work/results/leakage_comparison_metrics.csv'
    df_out.to_csv(out_path, index=False)
    print(f"\n✅ All leakage audit models evaluated. Metrics saved to {out_path}")
    
    return df_out

if __name__ == '__main__':
    run_pipeline_audit()
