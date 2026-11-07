"""
04_model_evaluation.py
Comprehensive Model Evaluation, Prediction Generation & Visualisation
=====================================================================
Generates:
1. `revision_work/results/metrics.csv`
2. `revision_work/results/predictions.csv`
3. Publication-ready figures in `revision_work/figures/`:
   - fig1_data_leakage_impact.png
   - fig2_actual_vs_predicted.png
   - fig3_residual_distributions.png
   - fig4_feature_importance.png
   - fig5_strategy_comparison.png
"""

import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

# Styling configuration for publication quality
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 1.0
plt.rcParams['grid.color'] = '#e0e0e0'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.7

SEED = 42

def main():
    os.makedirs('revision_work/results', exist_ok=True)
    os.makedirs('revision_work/figures', exist_ok=True)
    
    prov = pd.read_csv('revision_work/data/provenance_audit.csv')
    
    # -------------------------------------------------------------
    # 1. GENERATE PREDICTIONS FOR ALL CLEAN TEST SETS
    # -------------------------------------------------------------
    pred_records = []
    metric_records = []
    
    # Separate models
    for regime in ['Cryogenic', 'High', 'Room']:
        sub = prov[prov['Regime'] == regime].copy()
        features = ['Base_TC_W_mK', 'Filler_TC_W_mK', 'Volume_Fraction_pct']
        if regime != 'Room':
            features.append('Temperature_K')
            
        X = sub[features]
        y = sub['Composite_TC_W_mK']
        ids = sub['Observation_ID']
        
        X_tr, X_te, y_tr, y_te, ids_tr, ids_te = train_test_split(
            X, y, ids, test_size=0.2, random_state=SEED
        )
        
        for algo in ['Extra_Trees', 'Random_Forest', 'Gradient_Boosting', 'XGBoost']:
            model_path = f"revision_work/models/{regime.lower()}_{algo.lower()}.pkl"
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
                
            y_pred = model.predict(X_te)
            
            for o_id, y_t, y_p in zip(ids_te, y_te, y_pred):
                pred_records.append({
                    'Regime': regime,
                    'Model_Type': 'Separate',
                    'Algorithm': algo,
                    'Observation_ID': o_id,
                    'Actual_Composite_TC': y_t,
                    'Predicted_Composite_TC': y_p,
                    'Residual': y_t - y_p,
                    'Absolute_Error': abs(y_t - y_p),
                    'Relative_Error_pct': abs(y_t - y_p) / y_t * 100.0
                })
                
            metric_records.append({
                'Regime': regime,
                'Model_Type': 'Separate',
                'Algorithm': algo,
                'Test_N': len(y_te),
                'R2': r2_score(y_te, y_pred),
                'MAE': mean_absolute_error(y_te, y_pred),
                'RMSE': np.sqrt(mean_squared_error(y_te, y_pred)),
                'MAPE_pct': np.mean(np.abs(y_te - y_pred) / y_te) * 100.0
            })
            
    # Combined model
    comb_features = ['Base_TC_W_mK', 'Filler_TC_W_mK', 'Volume_Fraction_pct', 'Temperature_K']
    X_comb = prov[comb_features]
    y_comb = prov['Composite_TC_W_mK']
    ids_comb = prov['Observation_ID']
    regimes_comb = prov['Regime']
    
    X_tr_c, X_te_c, y_tr_c, y_te_c, ids_tr_c, ids_te_c, reg_tr_c, reg_te_c = train_test_split(
        X_comb, y_comb, ids_comb, regimes_comb, test_size=0.2, random_state=SEED
    )
    
    for algo in ['Extra_Trees', 'Random_Forest', 'Gradient_Boosting', 'XGBoost']:
        with open(f"revision_work/models/combined_{algo.lower()}.pkl", 'rb') as f:
            model = pickle.load(f)
            
        y_pred = model.predict(X_te_c)
        
        for o_id, reg, y_t, y_p in zip(ids_te_c, reg_te_c, y_te_c, y_pred):
            pred_records.append({
                'Regime': reg,
                'Model_Type': 'Combined_Unified',
                'Algorithm': algo,
                'Observation_ID': o_id,
                'Actual_Composite_TC': y_t,
                'Predicted_Composite_TC': y_p,
                'Residual': y_t - y_p,
                'Absolute_Error': abs(y_t - y_p),
                'Relative_Error_pct': abs(y_t - y_p) / y_t * 100.0
            })
            
        metric_records.append({
            'Regime': 'All_Temperatures',
            'Model_Type': 'Combined_Unified',
            'Algorithm': algo,
            'Test_N': len(y_te_c),
            'R2': r2_score(y_te_c, y_pred),
            'MAE': mean_absolute_error(y_te_c, y_pred),
            'RMSE': np.sqrt(mean_squared_error(y_te_c, y_pred)),
            'MAPE_pct': np.mean(np.abs(y_te_c - y_pred) / y_te_c) * 100.0
        })

    df_preds = pd.DataFrame(pred_records)
    df_metrics = pd.DataFrame(metric_records)
    
    df_preds.to_csv('revision_work/results/predictions.csv', index=False)
    df_metrics.to_csv('revision_work/results/metrics.csv', index=False)
    print(f"✅ Saved predictions.csv ({len(df_preds)} rows) and metrics.csv ({len(df_metrics)} rows)")

    # -------------------------------------------------------------
    # FIGURE 1: IMPACT OF DATA LEAKAGE ON EVALUATION
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    leakage_df = pd.read_csv('revision_work/results/leakage_comparison_metrics.csv')
    
    # Plot Leaked vs Clean Test R2
    x = np.arange(len(leakage_df))
    width = 0.35
    
    rects1 = ax.bar(x - width/2, leakage_df['Leaked_Test_R2'], width, label='Published / Leaked Split (Pre-Split Augmentation)', color='#d9534f', alpha=0.9)
    rects2 = ax.bar(x + width/2, leakage_df['Clean_Test_R2'], width, label='Corrected Leakage-Free Split (Untouched Test Set)', color='#2e6da4', alpha=0.9)
    
    ax.set_ylabel('Test Set R² Score', fontsize=12, fontweight='bold')
    ax.set_title('Severe Performance Collapse Under Leakage-Safe Validation\n(Comparison of Reported vs. Genuine Out-of-Sample R²)', fontsize=13, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['Regime']}\n{r['Algorithm']}" for _, r in leakage_df.iterrows()], fontsize=9)
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
    ax.set_ylim(-0.15, 1.05)
    ax.legend(frameon=True, facecolor='white', edgecolor='#cccccc', loc='lower left', fontsize=10)
    ax.grid(axis='y', alpha=0.4)
    
    plt.tight_layout()
    fig.savefig('revision_work/figures/fig1_data_leakage_impact.png')
    plt.close()
    print("✅ Generated fig1_data_leakage_impact.png")

    # -------------------------------------------------------------
    # FIGURE 2: ACTUAL VS PREDICTED (PARITY PLOTS)
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), dpi=300)
    colors = {'Cryogenic': '#2b5c8f', 'High': '#d95f02', 'Room': '#7570b3'}
    
    for idx, regime in enumerate(['Cryogenic', 'High', 'Room']):
        ax = axes[idx]
        sub = df_preds[(df_preds['Regime'] == regime) & 
                       (df_preds['Model_Type'] == 'Separate') & 
                       (df_preds['Algorithm'] == 'Extra_Trees')]
        
        act = sub['Actual_Composite_TC']
        pred = sub['Predicted_Composite_TC']
        r2 = r2_score(act, pred)
        mae = mean_absolute_error(act, pred)
        
        ax.scatter(act, pred, color=colors[regime], s=60, edgecolors='black', alpha=0.8, label=f'Test Samples (N={len(act)})')
        min_v = min(act.min(), pred.min()) * 0.9
        max_v = max(act.max(), pred.max()) * 1.1
        ax.plot([min_v, max_v], [min_v, max_v], 'r--', linewidth=1.5, label='Ideal 1:1 Parity')
        
        ax.set_title(f"{regime} Regime (Extra Trees)\nR² = {r2:.3f}, MAE = {mae:.3f} W/m·K", fontsize=11, fontweight='bold')
        ax.set_xlabel('Measured Composite TC (W/m·K)', fontsize=10, fontweight='bold')
        ax.set_ylabel('Predicted Composite TC (W/m·K)', fontsize=10, fontweight='bold')
        ax.set_xlim(min_v, max_v)
        ax.set_ylim(min_v, max_v)
        ax.grid(True)
        ax.legend(loc='upper left', frameon=True, fontsize=9)
        
    plt.suptitle('Corrected Leakage-Free Parity Plots (Untouched Test Observations)', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig.savefig('revision_work/figures/fig2_actual_vs_predicted.png')
    plt.close()
    print("✅ Generated fig2_actual_vs_predicted.png")

    # -------------------------------------------------------------
    # FIGURE 3: RESIDUAL DISTRIBUTIONS
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=300)
    
    # Combined model predictions
    comb_preds = df_preds[(df_preds['Model_Type'] == 'Combined_Unified') & (df_preds['Algorithm'] == 'Extra_Trees')]
    
    # Residual vs Actual
    axes[0].scatter(comb_preds['Actual_Composite_TC'], comb_preds['Residual'], color='#1b9e77', s=50, edgecolors='black', alpha=0.8)
    axes[0].axhline(0, color='red', linestyle='--', linewidth=1.5)
    axes[0].set_title('Residuals vs. Measured TC (Combined Extra Trees)', fontsize=11, fontweight='bold')
    axes[0].set_xlabel('Measured Composite TC (W/m·K)', fontsize=10, fontweight='bold')
    axes[0].set_ylabel('Residual (Measured - Predicted, W/m·K)', fontsize=10, fontweight='bold')
    axes[0].grid(True)
    
    # Histogram of residuals
    axes[1].hist(comb_preds['Residual'], bins=15, color='#1b9e77', edgecolor='black', alpha=0.7, density=True)
    axes[1].axvline(0, color='red', linestyle='--', linewidth=1.5)
    axes[1].set_title(f"Residual Error Distribution\nMean = {comb_preds['Residual'].mean():.3f}, Std = {comb_preds['Residual'].std():.3f}", fontsize=11, fontweight='bold')
    axes[1].set_xlabel('Residual (W/m·K)', fontsize=10, fontweight='bold')
    axes[1].set_ylabel('Density', fontsize=10, fontweight='bold')
    axes[1].grid(True)
    
    plt.tight_layout()
    fig.savefig('revision_work/figures/fig3_residual_distributions.png')
    plt.close()
    print("✅ Generated fig3_residual_distributions.png")

    # -------------------------------------------------------------
    # FIGURE 4: FEATURE IMPORTANCE (COMBINED MODEL)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    with open("revision_work/models/combined_extra_trees.pkl", 'rb') as f:
        et_comb = pickle.load(f)
        
    feat_names = ['Matrix TC', 'Filler TC', 'Volume Fraction', 'Temperature']
    importances = et_comb.feature_importances_
    
    y_pos = np.arange(len(feat_names))
    ax.barh(y_pos, importances, color='#4575b4', edgecolor='black', alpha=0.85)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(feat_names, fontsize=11, fontweight='bold')
    ax.invert_yaxis()
    ax.set_xlabel('Gini Feature Importance', fontsize=11, fontweight='bold')
    ax.set_title('Empirical Feature Importance in Unified Composite TC Model\n(Model Behaviour, Not Proof of Physical Causation)', fontsize=12, fontweight='bold', pad=12)
    ax.grid(axis='x', alpha=0.4)
    
    for i, v in enumerate(importances):
        ax.text(v + 0.01, i, f"{v*100:.1f}%", va='center', fontweight='bold', fontsize=10)
        
    ax.set_xlim(0, max(importances) * 1.2)
    plt.tight_layout()
    fig.savefig('revision_work/figures/fig4_feature_importance.png')
    plt.close()
    print("✅ Generated fig4_feature_importance.png")

    # -------------------------------------------------------------
    # FIGURE 5: STRATEGY A VS STRATEGY B COMPARISON
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    cv_res = pd.read_csv('revision_work/results/cross_validation_results.csv')
    
    et_rows = cv_res[cv_res['Model'].str.contains('Extra_Trees') & ~cv_res['Model'].str.contains('Grouped')]
    
    strat_labels = ['Cryogenic\n(Strategy A)', 'High\n(Strategy A)', 'Room\n(Strategy A)', 'Combined All-Temp\n(Strategy B)']
    test_r2_vals = et_rows['Test_R2'].values
    cv_r2_vals = et_rows['CV_R2_Mean'].values
    
    x = np.arange(len(strat_labels))
    w = 0.35
    ax.bar(x - w/2, cv_r2_vals, w, label='5-Fold CV R²', color='#74add1', edgecolor='black')
    ax.bar(x + w/2, test_r2_vals, w, label='Test Set R²', color='#313695', edgecolor='black')
    
    ax.set_xticks(x)
    ax.set_xticklabels(strat_labels, fontsize=10, fontweight='bold')
    ax.set_ylabel('R² Score', fontsize=11, fontweight='bold')
    ax.set_title('Model Generalisation Comparison: Temperature-Specific vs. Unified Model', fontsize=12, fontweight='bold', pad=12)
    ax.legend(frameon=True, fontsize=10)
    ax.grid(axis='y', alpha=0.4)
    ax.set_ylim(-0.1, 1.05)
    
    plt.tight_layout()
    fig.savefig('revision_work/figures/fig5_strategy_comparison.png')
    plt.close()
    print("✅ Generated fig5_strategy_comparison.png")

if __name__ == '__main__':
    main()
