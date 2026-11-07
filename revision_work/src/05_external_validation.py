"""
05_external_validation.py
Audit of "Experimental Validation" vs. Maxwell Theoretical Benchmarks
=====================================================================
Analyzes the contents of:
- `Cryogenic/4.2K.docx`
- `Room/300K.docx`
- `High/323K.docx`

Evaluates model predictions against these Maxwell model benchmarks,
computes errors, analyzes the effect of Thermal Boundary Resistance (TBR),
and generates `fig6_external_maxwell_benchmark_comparison.png`.
"""

import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def main():
    os.makedirs('revision_work/results', exist_ok=True)
    os.makedirs('revision_work/figures', exist_ok=True)
    
    # -------------------------------------------------------------
    # 1. EXTRACT BENCHMARK SPECIFICATIONS FROM DOCX FILES
    # -------------------------------------------------------------
    benchmarks = [
        # Cryogenic (4.2 K) - Matrix: Epoxy km=0.35 W/mK
        # SS304: Original kf=0.65, Corrected kf,eff=0.433
        {'Regime': 'Cryogenic', 'Temp_K': 4.2, 'Matrix': 'Epoxy', 'Base_TC': 0.35, 'Filler': 'SS304', 'Filler_TC_orig': 0.65, 'Filler_TC_eff': 0.433, 'Vol_pct': 5,  'Maxwell_TC': 0.366, 'TBR_adjusted': True},
        {'Regime': 'Cryogenic', 'Temp_K': 4.2, 'Matrix': 'Epoxy', 'Base_TC': 0.35, 'Filler': 'SS304', 'Filler_TC_orig': 0.65, 'Filler_TC_eff': 0.433, 'Vol_pct': 10, 'Maxwell_TC': 0.383, 'TBR_adjusted': True},
        {'Regime': 'Cryogenic', 'Temp_K': 4.2, 'Matrix': 'Epoxy', 'Base_TC': 0.35, 'Filler': 'SS304', 'Filler_TC_orig': 0.65, 'Filler_TC_eff': 0.433, 'Vol_pct': 15, 'Maxwell_TC': 0.400, 'TBR_adjusted': True},
        # Alumina: Original kf=75, Corrected kf,eff=62.5
        {'Regime': 'Cryogenic', 'Temp_K': 4.2, 'Matrix': 'Epoxy', 'Base_TC': 0.35, 'Filler': 'Alumina', 'Filler_TC_orig': 75.0, 'Filler_TC_eff': 62.5, 'Vol_pct': 5,  'Maxwell_TC': 0.525, 'TBR_adjusted': True},
        {'Regime': 'Cryogenic', 'Temp_K': 4.2, 'Matrix': 'Epoxy', 'Base_TC': 0.35, 'Filler': 'Alumina', 'Filler_TC_orig': 75.0, 'Filler_TC_eff': 62.5, 'Vol_pct': 10, 'Maxwell_TC': 0.694, 'TBR_adjusted': True},
        {'Regime': 'Cryogenic', 'Temp_K': 4.2, 'Matrix': 'Epoxy', 'Base_TC': 0.35, 'Filler': 'Alumina', 'Filler_TC_orig': 75.0, 'Filler_TC_eff': 62.5, 'Vol_pct': 15, 'Maxwell_TC': 0.859, 'TBR_adjusted': True},

        # Room Temperature (300 K) - Matrix: Epoxy km=1.05 W/mK
        # SS304: Original kf=16.2, Corrected kf,eff=12.24
        {'Regime': 'Room', 'Temp_K': 300.0, 'Matrix': 'Epoxy', 'Base_TC': 1.05, 'Filler': 'SS304', 'Filler_TC_orig': 16.2, 'Filler_TC_eff': 12.24, 'Vol_pct': 5,  'Maxwell_TC': 1.178, 'TBR_adjusted': False},
        {'Regime': 'Room', 'Temp_K': 300.0, 'Matrix': 'Epoxy', 'Base_TC': 1.05, 'Filler': 'SS304', 'Filler_TC_orig': 16.2, 'Filler_TC_eff': 12.24, 'Vol_pct': 10, 'Maxwell_TC': 1.317, 'TBR_adjusted': False},
        {'Regime': 'Room', 'Temp_K': 300.0, 'Matrix': 'Epoxy', 'Base_TC': 1.05, 'Filler': 'SS304', 'Filler_TC_orig': 16.2, 'Filler_TC_eff': 12.24, 'Vol_pct': 15, 'Maxwell_TC': 1.468, 'TBR_adjusted': False},
        # Alumina: Original kf=30.0, Corrected kf,eff=18.75
        {'Regime': 'Room', 'Temp_K': 300.0, 'Matrix': 'Epoxy', 'Base_TC': 1.05, 'Filler': 'Alumina', 'Filler_TC_orig': 30.0, 'Filler_TC_eff': 18.75, 'Vol_pct': 5,  'Maxwell_TC': 1.190, 'TBR_adjusted': False},
        {'Regime': 'Room', 'Temp_K': 300.0, 'Matrix': 'Epoxy', 'Base_TC': 1.05, 'Filler': 'Alumina', 'Filler_TC_orig': 30.0, 'Filler_TC_eff': 18.75, 'Vol_pct': 10, 'Maxwell_TC': 1.342, 'TBR_adjusted': False},
        {'Regime': 'Room', 'Temp_K': 300.0, 'Matrix': 'Epoxy', 'Base_TC': 1.05, 'Filler': 'Alumina', 'Filler_TC_orig': 30.0, 'Filler_TC_eff': 18.75, 'Vol_pct': 15, 'Maxwell_TC': 1.510, 'TBR_adjusted': False},

        # High Temperature (323 K) - Matrix: Epoxy km=1.07 W/mK
        # SS304: Original kf=17.0, Corrected kf,eff=12.69
        {'Regime': 'High', 'Temp_K': 323.0, 'Matrix': 'Epoxy', 'Base_TC': 1.07, 'Filler': 'SS304', 'Filler_TC_orig': 17.0, 'Filler_TC_eff': 12.69, 'Vol_pct': 5,  'Maxwell_TC': 1.201, 'TBR_adjusted': True},
        {'Regime': 'High', 'Temp_K': 323.0, 'Matrix': 'Epoxy', 'Base_TC': 1.07, 'Filler': 'SS304', 'Filler_TC_orig': 17.0, 'Filler_TC_eff': 12.69, 'Vol_pct': 10, 'Maxwell_TC': 1.343, 'TBR_adjusted': True},
        {'Regime': 'High', 'Temp_K': 323.0, 'Matrix': 'Epoxy', 'Base_TC': 1.07, 'Filler': 'SS304', 'Filler_TC_orig': 17.0, 'Filler_TC_eff': 12.69, 'Vol_pct': 15, 'Maxwell_TC': 1.497, 'TBR_adjusted': True},
        # Alumina: Original kf=28.0, Corrected kf,eff=17.95
        {'Regime': 'High', 'Temp_K': 323.0, 'Matrix': 'Epoxy', 'Base_TC': 1.07, 'Filler': 'Alumina', 'Filler_TC_orig': 28.0, 'Filler_TC_eff': 17.95, 'Vol_pct': 5,  'Maxwell_TC': 1.211, 'TBR_adjusted': True},
        {'Regime': 'High', 'Temp_K': 323.0, 'Matrix': 'Epoxy', 'Base_TC': 1.07, 'Filler': 'Alumina', 'Filler_TC_orig': 28.0, 'Filler_TC_eff': 17.95, 'Vol_pct': 10, 'Maxwell_TC': 1.364, 'TBR_adjusted': True},
        {'Regime': 'High', 'Temp_K': 323.0, 'Matrix': 'Epoxy', 'Base_TC': 1.07, 'Filler': 'Alumina', 'Filler_TC_orig': 28.0, 'Filler_TC_eff': 17.95, 'Vol_pct': 15, 'Maxwell_TC': 1.533, 'TBR_adjusted': True},
    ]
    
    df_bench = pd.DataFrame(benchmarks)
    
    # -------------------------------------------------------------
    # 2. RUN MODEL PREDICTIONS ON BENCHMARK FORMULATIONS
    # -------------------------------------------------------------
    # Load separate and combined Extra Trees models
    with open("revision_work/models/cryogenic_extra_trees.pkl", 'rb') as f:
        et_cryo = pickle.load(f)
    with open("revision_work/models/room_extra_trees.pkl", 'rb') as f:
        et_room = pickle.load(f)
    with open("revision_work/models/high_extra_trees.pkl", 'rb') as f:
        et_high = pickle.load(f)
    with open("revision_work/models/combined_extra_trees.pkl", 'rb') as f:
        et_comb = pickle.load(f)

    # Note: Authors fed original uncorrected Filler TC to their notebooks!
    # Let's predict with both original uncorrected and TBR-corrected filler TC!
    preds_orig = []
    preds_eff = []
    preds_comb = []
    
    for _, row in df_bench.iterrows():
        reg = row['Regime']
        base = row['Base_TC']
        kf_orig = row['Filler_TC_orig']
        kf_eff = row['Filler_TC_eff']
        vol = row['Vol_pct']
        t = row['Temp_K']
        
        # Inputs for separate models
        if reg == 'Cryogenic':
            x_in_orig = pd.DataFrame([[base, kf_orig, vol, t]], columns=['Base_TC_W_mK', 'Filler_TC_W_mK', 'Volume_Fraction_pct', 'Temperature_K'])
            x_in_eff = pd.DataFrame([[base, kf_eff, vol, t]], columns=['Base_TC_W_mK', 'Filler_TC_W_mK', 'Volume_Fraction_pct', 'Temperature_K'])
            p_orig = et_cryo.predict(x_in_orig)[0]
            p_eff = et_cryo.predict(x_in_eff)[0]
        elif reg == 'Room':
            x_in_orig = pd.DataFrame([[base, kf_orig, vol]], columns=['Base_TC_W_mK', 'Filler_TC_W_mK', 'Volume_Fraction_pct'])
            x_in_eff = pd.DataFrame([[base, kf_eff, vol]], columns=['Base_TC_W_mK', 'Filler_TC_W_mK', 'Volume_Fraction_pct'])
            p_orig = et_room.predict(x_in_orig)[0]
            p_eff = et_room.predict(x_in_eff)[0]
        elif reg == 'High':
            x_in_orig = pd.DataFrame([[base, kf_orig, vol, t]], columns=['Base_TC_W_mK', 'Filler_TC_W_mK', 'Volume_Fraction_pct', 'Temperature_K'])
            x_in_eff = pd.DataFrame([[base, kf_eff, vol, t]], columns=['Base_TC_W_mK', 'Filler_TC_W_mK', 'Volume_Fraction_pct', 'Temperature_K'])
            p_orig = et_high.predict(x_in_orig)[0]
            p_eff = et_high.predict(x_in_eff)[0]
            
        # Input for combined model
        x_comb = pd.DataFrame([[base, kf_orig, vol, t]], columns=['Base_TC_W_mK', 'Filler_TC_W_mK', 'Volume_Fraction_pct', 'Temperature_K'])
        p_comb = et_comb.predict(x_comb)[0]
        
        preds_orig.append(p_orig)
        preds_eff.append(p_eff)
        preds_comb.append(p_comb)

    df_bench['ML_Pred_Separate_Uncorrected'] = preds_orig
    df_bench['ML_Pred_Separate_TBR_Corrected'] = preds_eff
    df_bench['ML_Pred_Combined'] = preds_comb
    
    # Calculate Discrepancies vs Maxwell benchmark
    df_bench['Abs_Diff_Separate'] = (df_bench['ML_Pred_Separate_Uncorrected'] - df_bench['Maxwell_TC']).abs()
    df_bench['Rel_Diff_Separate_pct'] = (df_bench['Abs_Diff_Separate'] / df_bench['Maxwell_TC']) * 100.0
    
    out_csv = 'revision_work/results/external_validation_audit.csv'
    df_bench.to_csv(out_csv, index=False)
    print(f"✅ External validation audit complete. Saved to {out_csv}")
    print(df_bench[['Regime', 'Filler', 'Vol_pct', 'Maxwell_TC', 'ML_Pred_Separate_Uncorrected', 'Rel_Diff_Separate_pct']].to_string())

    # -------------------------------------------------------------
    # FIGURE 6: PLOT MODEL VS MAXWELL BENCHMARK
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), dpi=300)
    
    for idx, (reg, t_val) in enumerate([('Cryogenic', 4.2), ('Room', 300.0), ('High', 323.0)]):
        ax = axes[idx]
        sub = df_bench[df_bench['Regime'] == reg]
        
        # SS304
        ss = sub[sub['Filler'] == 'SS304']
        ax.plot(ss['Vol_pct'], ss['Maxwell_TC'], 'bo-', linewidth=2, label='Maxwell Theory: SS304')
        ax.plot(ss['Vol_pct'], ss['ML_Pred_Separate_Uncorrected'], 'b^--', linewidth=1.5, label='ML Pred (ET): SS304')
        
        # Alumina
        al = sub[sub['Filler'] == 'Alumina']
        ax.plot(al['Vol_pct'], al['Maxwell_TC'], 'ro-', linewidth=2, label='Maxwell Theory: Alumina')
        ax.plot(al['Vol_pct'], al['ML_Pred_Separate_Uncorrected'], 'r^--', linewidth=1.5, label='ML Pred (ET): Alumina')
        
        ax.set_title(f"{reg} Regime ({t_val} K)\nTheoretical Maxwell vs. Machine Learning", fontsize=11, fontweight='bold')
        ax.set_xlabel('Filler Volume Fraction (%)', fontsize=10, fontweight='bold')
        ax.set_ylabel('Effective Thermal Conductivity (W/m·K)', fontsize=10, fontweight='bold')
        ax.set_xticks([5, 10, 15])
        ax.grid(True)
        if idx == 0:
            ax.legend(frameon=True, fontsize=8.5, loc='upper left')
            
    plt.suptitle('Audit of Theoretical Maxwell Benchmark vs. ML Prediction\n(Evidence that "Validation Data" are Maxwell Model Calculations, Not Physical Experiments)', 
                 fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig.savefig('revision_work/figures/fig6_external_maxwell_benchmark_comparison.png')
    plt.close()
    print("✅ Generated fig6_external_maxwell_benchmark_comparison.png")

if __name__ == '__main__':
    main()
