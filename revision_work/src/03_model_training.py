"""
03_model_training.py
Systematic Model Training, Hyperparameter Tuning & Baseline Comparison
======================================================================
Trains:
1. Baseline models: Mean predictor, Ridge regression, Physical Maxwell model
2. Clean unaugmented ML models (ET, RF, GB, XGB) for each temperature regime (Strategy A)
3. Unified combined ML model across all regimes (Strategy B)
4. Grouped CV across material systems

Saves models to `revision_work/models/` and CV metrics to `revision_work/results/`.
"""

import os
import pickle
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import KFold, GroupKFold, cross_validate, train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

SEED = 42

def maxwell_tc(km, kf, phi):
    phi_dec = phi / 100.0
    num = 2 * km + kf - 2 * phi_dec * (km - kf)
    den = 2 * km + kf + phi_dec * (km - kf)
    return km * (num / den)

def main():
    os.makedirs('revision_work/models', exist_ok=True)
    os.makedirs('revision_work/results', exist_ok=True)
    
    prov = pd.read_csv('revision_work/data/provenance_audit.csv')
    
    cv_records = []
    
    # -------------------------------------------------------------
    # 1. TEMPERATURE-SPECIFIC MODELS (STRATEGY A)
    # -------------------------------------------------------------
    for regime in ['Cryogenic', 'High', 'Room']:
        sub = prov[prov['Regime'] == regime].copy()
        features = ['Base_TC_W_mK', 'Filler_TC_W_mK', 'Volume_Fraction_pct']
        if regime != 'Room':
            features.append('Temperature_K')
            
        X = sub[features]
        y = sub['Composite_TC_W_mK']
        
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=SEED)
        
        models = {
            'Mean_Baseline': DummyRegressor(strategy='mean'),
            'Ridge_Baseline': Ridge(alpha=1.0, random_state=SEED),
            'Extra_Trees': ExtraTreesRegressor(n_estimators=200, random_state=SEED, n_jobs=-1),
            'Random_Forest': RandomForestRegressor(n_estimators=200, random_state=SEED, n_jobs=-1),
            'Gradient_Boosting': GradientBoostingRegressor(n_estimators=200, random_state=SEED),
            'XGBoost': XGBRegressor(n_estimators=200, learning_rate=0.05, random_state=SEED, n_jobs=-1)
        }
        
        cv = KFold(n_splits=5, shuffle=True, random_state=SEED)
        
        for name, m in models.items():
            cv_res = cross_validate(m, X_tr, y_tr, cv=cv, scoring=['r2', 'neg_mean_absolute_error', 'neg_root_mean_squared_error'])
            
            # Fit on full training set
            m.fit(X_tr, y_tr)
            y_pred = m.predict(X_te)
            
            # Save model
            model_file = f"revision_work/models/{regime.lower()}_{name.lower()}.pkl"
            with open(model_file, 'wb') as f:
                pickle.dump(m, f)
                
            cv_records.append({
                'Strategy': 'Separate_Regime',
                'Regime': regime,
                'Model': name,
                'CV_R2_Mean': cv_res['test_r2'].mean(),
                'CV_R2_Std': cv_res['test_r2'].std(),
                'CV_MAE_Mean': -cv_res['test_neg_mean_absolute_error'].mean(),
                'CV_MAE_Std': cv_res['test_neg_mean_absolute_error'].std(),
                'CV_RMSE_Mean': -cv_res['test_neg_root_mean_squared_error'].mean(),
                'CV_RMSE_Std': cv_res['test_neg_root_mean_squared_error'].std(),
                'Test_R2': r2_score(y_te, y_pred),
                'Test_MAE': mean_absolute_error(y_te, y_pred),
                'Test_RMSE': np.sqrt(mean_squared_error(y_te, y_pred))
            })
            
        # Maxwell Physical Baseline
        pred_maxwell_te = maxwell_tc(X_te['Base_TC_W_mK'], X_te['Filler_TC_W_mK'], X_te['Volume_Fraction_pct'])
        cv_records.append({
            'Strategy': 'Separate_Regime',
            'Regime': regime,
            'Model': 'Maxwell_Physical_Baseline',
            'CV_R2_Mean': np.nan,
            'CV_R2_Std': np.nan,
            'CV_MAE_Mean': np.nan,
            'CV_MAE_Std': np.nan,
            'CV_RMSE_Mean': np.nan,
            'CV_RMSE_Std': np.nan,
            'Test_R2': r2_score(y_te, pred_maxwell_te),
            'Test_MAE': mean_absolute_error(y_te, pred_maxwell_te),
            'Test_RMSE': np.sqrt(mean_squared_error(y_te, pred_maxwell_te))
        })

    # -------------------------------------------------------------
    # 2. COMBINED TEMPERATURE MODEL (STRATEGY B)
    # -------------------------------------------------------------
    comb_features = ['Base_TC_W_mK', 'Filler_TC_W_mK', 'Volume_Fraction_pct', 'Temperature_K']
    X_comb = prov[comb_features]
    y_comb = prov['Composite_TC_W_mK']
    groups_comb = prov['Filler_Identity']
    
    X_tr_c, X_te_c, y_tr_c, y_te_c = train_test_split(X_comb, y_comb, test_size=0.2, random_state=SEED)
    
    comb_models = {
        'Mean_Baseline': DummyRegressor(strategy='mean'),
        'Ridge_Baseline': Ridge(alpha=1.0, random_state=SEED),
        'Extra_Trees': ExtraTreesRegressor(n_estimators=300, random_state=SEED, n_jobs=-1),
        'Random_Forest': RandomForestRegressor(n_estimators=300, random_state=SEED, n_jobs=-1),
        'Gradient_Boosting': GradientBoostingRegressor(n_estimators=300, random_state=SEED),
        'XGBoost': XGBRegressor(n_estimators=300, learning_rate=0.03, max_depth=4, random_state=SEED, n_jobs=-1)
    }
    
    cv_comb = KFold(n_splits=5, shuffle=True, random_state=SEED)
    
    for name, m in comb_models.items():
        cv_res = cross_validate(m, X_tr_c, y_tr_c, cv=cv_comb, scoring=['r2', 'neg_mean_absolute_error', 'neg_root_mean_squared_error'])
        m.fit(X_tr_c, y_tr_c)
        y_pred_c = m.predict(X_te_c)
        
        # Save model
        with open(f"revision_work/models/combined_{name.lower()}.pkl", 'wb') as f:
            pickle.dump(m, f)
            
        cv_records.append({
            'Strategy': 'Combined_Unified',
            'Regime': 'All_Temperatures',
            'Model': name,
            'CV_R2_Mean': cv_res['test_r2'].mean(),
            'CV_R2_Std': cv_res['test_r2'].std(),
            'CV_MAE_Mean': -cv_res['test_neg_mean_absolute_error'].mean(),
            'CV_MAE_Std': cv_res['test_neg_mean_absolute_error'].std(),
            'CV_RMSE_Mean': -cv_res['test_neg_root_mean_squared_error'].mean(),
            'CV_RMSE_Std': cv_res['test_neg_root_mean_squared_error'].std(),
            'Test_R2': r2_score(y_te_c, y_pred_c),
            'Test_MAE': mean_absolute_error(y_te_c, y_pred_c),
            'Test_RMSE': np.sqrt(mean_squared_error(y_te_c, y_pred_c))
        })
        
    # Maxwell Physical Baseline on Combined
    pred_maxwell_comb = maxwell_tc(X_te_c['Base_TC_W_mK'], X_te_c['Filler_TC_W_mK'], X_te_c['Volume_Fraction_pct'])
    cv_records.append({
        'Strategy': 'Combined_Unified',
        'Regime': 'All_Temperatures',
        'Model': 'Maxwell_Physical_Baseline',
        'CV_R2_Mean': np.nan,
        'CV_R2_Std': np.nan,
        'CV_MAE_Mean': np.nan,
        'CV_MAE_Std': np.nan,
        'CV_RMSE_Mean': np.nan,
        'CV_RMSE_Std': np.nan,
        'Test_R2': r2_score(y_te_c, pred_maxwell_comb),
        'Test_MAE': mean_absolute_error(y_te_c, pred_maxwell_comb),
        'Test_RMSE': np.sqrt(mean_squared_error(y_te_c, pred_maxwell_comb))
    })

    # -------------------------------------------------------------
    # 3. GROUPED GENERALISATION CROSS-VALIDATION
    # -------------------------------------------------------------
    gkf = GroupKFold(n_splits=5)
    for name, m in [('Extra_Trees_Grouped', ExtraTreesRegressor(n_estimators=300, random_state=SEED, n_jobs=-1)),
                    ('Random_Forest_Grouped', RandomForestRegressor(n_estimators=300, random_state=SEED, n_jobs=-1))]:
        cv_res = cross_validate(m, X_comb, y_comb, groups=groups_comb, cv=gkf, scoring=['r2', 'neg_mean_absolute_error', 'neg_root_mean_squared_error'])
        cv_records.append({
            'Strategy': 'Grouped_Generalisation_CV',
            'Regime': 'All_Temperatures',
            'Model': name,
            'CV_R2_Mean': cv_res['test_r2'].mean(),
            'CV_R2_Std': cv_res['test_r2'].std(),
            'CV_MAE_Mean': -cv_res['test_neg_mean_absolute_error'].mean(),
            'CV_MAE_Std': cv_res['test_neg_mean_absolute_error'].std(),
            'CV_RMSE_Mean': -cv_res['test_neg_root_mean_squared_error'].mean(),
            'CV_RMSE_Std': cv_res['test_neg_root_mean_squared_error'].std(),
            'Test_R2': np.nan,
            'Test_MAE': np.nan,
            'Test_RMSE': np.nan
        })

    cv_df = pd.DataFrame(cv_records)
    out_csv = 'revision_work/results/cross_validation_results.csv'
    cv_df.to_csv(out_csv, index=False)
    print(f"✅ Training and cross-validation complete. Results saved to {out_csv}")
    print(cv_df[['Strategy', 'Regime', 'Model', 'CV_R2_Mean', 'Test_R2', 'Test_MAE']].to_string())

if __name__ == '__main__':
    main()
