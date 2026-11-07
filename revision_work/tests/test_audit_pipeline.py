"""
test_audit_pipeline.py
Automated Quality Assurance & Reproducibility Unit Tests
========================================================
Tests:
1. Data loading integrity and original row counts
2. Absolute separation of partitions in leakage-safe pipeline (0% leakage)
3. Correctness of metric calculations
4. Physical plausibility checks on predictions
"""

import os
import unittest
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

class TestAuditPipeline(unittest.TestCase):

    def test_original_dataset_counts(self):
        """Verify exact counts of original non-augmented datasets."""
        cryo = pd.read_excel('Cryogenic/Cryogenic Temp.xlsx')
        high = pd.read_excel('High/High Temp.xlsx')
        room = pd.read_excel('Room/Room Temp.xlsx')
        
        self.assertEqual(len(cryo), 54, "Cryogenic dataset must have exactly 54 observations")
        self.assertEqual(len(high), 42, "High temp dataset must have exactly 42 observations")
        self.assertEqual(len(room), 160, "Room temp dataset must have exactly 160 observations")
        self.assertEqual(len(cryo) + len(high) + len(room), 256, "Total original observations must equal 256")

    def test_augmented_dataset_counts(self):
        """Verify 3x augmented row counts."""
        cryo_aug = pd.read_excel('Cryogenic/Cryogenic_Temp_3x_Augmented_1Percent_Noise.xlsx')
        high_aug = pd.read_excel('High/High_Temp_3x_Augmented_1Percent_Noise.xlsx')
        room_aug = pd.read_excel('Room/Room_Temp_3x_Augmented_1Percent_Noise.xlsx')
        
        self.assertEqual(len(cryo_aug), 54 * 3, "Cryo augmented must be 162")
        self.assertEqual(len(high_aug), 42 * 3, "High augmented must be 126")
        self.assertEqual(len(room_aug), 160 * 3, "Room augmented must be 480")

    def test_leakage_safe_separation(self):
        """Ensure that corrected train/test split has strictly 0% sample leakage."""
        for regime in ['cryogenic', 'high', 'room']:
            split_file = f"revision_work/data/{regime}_train_test_split.csv"
            self.assertTrue(os.path.exists(split_file), f"Split file {split_file} must exist")
            
            df = pd.read_csv(split_file)
            train_ids = set(df[df['partition'] == 'train']['orig_id'])
            test_ids = set(df[df['partition'] == 'test']['orig_id'])
            
            overlap = train_ids.intersection(test_ids)
            self.assertEqual(len(overlap), 0, f"Leakage detected in {regime}: {overlap} IDs in both train and test!")

    def test_metric_correctness(self):
        """Verify standard error metric calculations."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 1.9, 3.2, 3.8, 5.1])
        
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        
        self.assertAlmostEqual(mae, 0.14, places=4)
        self.assertAlmostEqual(rmse, 0.1483, places=3)
        self.assertTrue(r2 > 0.98, "R2 must reflect strong correlation")

    def test_prediction_physical_positivity(self):
        """Verify that all model predictions are strictly positive physical values."""
        preds_file = 'revision_work/results/predictions.csv'
        self.assertTrue(os.path.exists(preds_file), "Predictions file must exist")
        df_p = pd.read_csv(preds_file)
        
        self.assertTrue((df_p['Predicted_Composite_TC'] > 0).all(), "All predicted thermal conductivities must be positive")

if __name__ == '__main__':
    unittest.main()
