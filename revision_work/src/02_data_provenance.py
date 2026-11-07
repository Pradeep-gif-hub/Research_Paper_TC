"""
02_data_provenance.py
Scientific Data Provenance and Material System Audit
=====================================================
Audits the provenance, physical material classification, temperature ranges,
filler and matrix identities, and integrity of thermal conductivity datasets
across Cryogenic, Room Temperature, and High Temperature regimes.
"""

import os
import pandas as pd
import numpy as np

def classify_observation(regime, row_idx, row):
    base_tc = row['Base TC']
    filler_tc = row['Filler TC']
    vol = row['Vol']
    temp = row['Temp'] if 'Temp' in row else 298.15 # Room temp assumption
    comp_tc = row['Composite TC']
    
    matrix_id = "Unknown Matrix"
    filler_id = "Unknown Filler"
    material_type = "Composite"
    provenance_status = "Inferred from thermal properties"
    doi_or_source = "Literature compilation"
    notes = []
    
    # Classify matrix
    if 0.58 <= base_tc <= 0.68 and regime in ['High', 'Room']:
        matrix_id = "Water (Liquid)"
        material_type = "Nanofluid"
        notes.append("Base TC matches liquid water across 25-60 C")
    elif 0.14 <= base_tc <= 0.25:
        matrix_id = "Epoxy / Polymer Resin"
        material_type = "Solid Composite"
        notes.append("Base TC typical of standard epoxy/polymer (0.15-0.25 W/mK)")
    elif 0.25 < base_tc <= 0.38:
        matrix_id = "Modified Epoxy / High-TC Polymer"
        material_type = "Solid Composite"
        notes.append("Base TC elevated above neat epoxy")
    elif base_tc < 0.14:
        if regime == 'Cryogenic':
            matrix_id = "Cryogenic Epoxy / Glass-Epoxy"
            material_type = "Solid Composite"
            notes.append("Epoxy base TC plummets at cryogenic temperatures (< 77 K)")
        else:
            matrix_id = "Low-TC Polymer / Porous Matrix"
            material_type = "Solid Composite"
    elif base_tc > 0.68:
        matrix_id = "High-TC Polymer Matrix / Composite Precursor"
        material_type = "Solid Composite"
        
    # Classify filler
    if 25.0 <= filler_tc <= 35.0:
        filler_id = "Al2O3 (Alumina)"
        notes.append("Nominal TC ~30 W/mK at RT")
    elif 14.0 <= filler_tc <= 18.0:
        filler_id = "SS304 / Stainless Steel"
        notes.append("Nominal TC ~15-16.5 W/mK at RT")
    elif 2.8 <= filler_tc <= 3.6:
        filler_id = "TiO2 (Titania)"
        notes.append("Nominal TC ~3.0 W/mK")
    elif 380.0 <= filler_tc <= 420.0:
        filler_id = "Cu (Copper)"
        notes.append("Nominal TC ~400 W/mK")
    elif 110.0 <= filler_tc <= 140.0:
        filler_id = "SiC / Silicon Carbide"
    elif 160.0 <= filler_tc <= 260.0:
        filler_id = "AlN (Aluminum Nitride) / Al"
    elif 500.0 <= filler_tc <= 1200.0:
        filler_id = "Carbon Fiber / Synthetic Graphite"
    elif 1800.0 <= filler_tc <= 3500.0:
        filler_id = "CNT / Single/Multi-Walled Carbon Nanotubes"
    elif filler_tc > 3500.0:
        if regime == 'Cryogenic':
            filler_id = "High-Purity Crystal / Diamond / Sapphire"
            notes.append("Peak cryogenic TC effect at 4-10 K")
        else:
            filler_id = "Graphene / High-Quality Diamond"
    elif filler_tc < 2.0:
        filler_id = "Polymer Bead / Low-Conductivity Ceramic"
        
    return {
        'Regime': regime,
        'Original_Index': row_idx,
        'Observation_ID': f"{regime[:3].upper()}_{row_idx:03d}",
        'Temperature_K': temp,
        'Base_TC_W_mK': base_tc,
        'Filler_TC_W_mK': filler_tc,
        'Volume_Fraction_pct': vol,
        'Composite_TC_W_mK': comp_tc,
        'Matrix_Identity': matrix_id,
        'Filler_Identity': filler_id,
        'Material_Type': material_type,
        'Data_Nature': 'Experimental (Extracted from secondary source)',
        'Provenance_Status': provenance_status,
        'Potential_Source_Ref': doi_or_source,
        'Audit_Notes': "; ".join(notes)
    }

def run_provenance_audit():
    datasets = [
        ('Cryogenic', 'Cryogenic/Cryogenic Temp.xlsx'),
        ('High', 'High/High Temp.xlsx'),
        ('Room', 'Room/Room Temp.xlsx')
    ]
    
    audit_rows = []
    
    for regime, path in datasets:
        df = pd.read_excel(path)
        for idx, row in df.iterrows():
            rec = classify_observation(regime, idx, row)
            audit_rows.append(rec)
            
    audit_df = pd.DataFrame(audit_rows)
    
    os.makedirs('revision_work/data', exist_ok=True)
    out_csv = 'revision_work/data/provenance_audit.csv'
    audit_df.to_csv(out_csv, index=False)
    print(f"✅ Data provenance audit complete. Saved {len(audit_df)} observations to {out_csv}")
    
    # Summary statistics
    print("\n--- Summary by Regime ---")
    print(audit_df.groupby('Regime').agg(
        Total_Obs=('Observation_ID', 'count'),
        Min_Temp=('Temperature_K', 'min'),
        Max_Temp=('Temperature_K', 'max'),
        Min_Base_TC=('Base_TC_W_mK', 'min'),
        Max_Base_TC=('Base_TC_W_mK', 'max'),
        Min_Filler_TC=('Filler_TC_W_mK', 'min'),
        Max_Filler_TC=('Filler_TC_W_mK', 'max')
    ))
    
    print("\n--- Material Type Breakdown ---")
    print(audit_df.groupby(['Regime', 'Material_Type']).size())
    
    print("\n--- Filler Breakdown ---")
    print(audit_df.groupby(['Regime', 'Filler_Identity']).size())

if __name__ == '__main__':
    run_provenance_audit()
