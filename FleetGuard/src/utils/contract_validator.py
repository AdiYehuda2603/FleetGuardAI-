# -*- coding: utf-8 -*-
"""
Dataset Contract Validator
מאמת שנתונים תואמים ל-dataset_contract.json
"""

import json
import pandas as pd
import os
from datetime import datetime


class ContractValidator:
    """
    מאמת נתונים מול Dataset Contract
    """

    def __init__(self, contract_path='data/processed/dataset_contract.json'):
        self.contract_path = contract_path
        self.contract = None
        self.validation_results = {
            'passed': True,
            'errors': [],
            'warnings': [],
            'checks_performed': 0
        }

    def load_contract(self):
        """
        טעינת Dataset Contract
        """
        if not os.path.exists(self.contract_path):
            raise FileNotFoundError(f"Dataset contract not found: {self.contract_path}")

        with open(self.contract_path, 'r', encoding='utf-8') as f:
            self.contract = json.load(f)

        print(f"[+] Loaded dataset contract v{self.contract['contract_version']}")
        return self.contract

    def validate_features_file(self, features_path='data/processed/features.csv'):
        """
        אימות קובץ הפיצ'רים מול החוזה
        """
        print(f"\n[*] Validating features file: {features_path}")

        if not os.path.exists(features_path):
            self._add_error(f"Features file not found: {features_path}")
            return self.validation_results

        df = pd.read_csv(features_path)
        schema = self.contract['schemas']['features']

        # בדיקה 1: מספר רשומות
        expected_count = schema.get('record_count_expected')
        if expected_count and len(df) != expected_count:
            self._add_warning(
                f"Record count mismatch: expected {expected_count}, got {len(df)}"
            )
        self.validation_results['checks_performed'] += 1

        # בדיקה 2: שדות חובה
        required_fields = schema.get('required_fields', [])
        missing_fields = [f for f in required_fields if f not in df.columns]
        if missing_fields:
            self._add_error(f"Missing required fields: {missing_fields}")
        self.validation_results['checks_performed'] += 1

        # בדיקה 3: אילוצי ערכים
        for field_name, field_spec in schema['fields'].items():
            if field_name not in df.columns:
                continue

            constraints = field_spec.get('constraints', {})

            # בדיקת min/max
            if 'min' in constraints:
                min_val = constraints['min']
                invalid = df[df[field_name] < min_val]
                if len(invalid) > 0:
                    self._add_error(
                        f"{field_name}: {len(invalid)} values below min ({min_val})"
                    )
            self.validation_results['checks_performed'] += 1

            if 'max' in constraints:
                max_val = constraints['max']
                invalid = df[df[field_name] > max_val]
                if len(invalid) > 0:
                    self._add_error(
                        f"{field_name}: {len(invalid)} values above max ({max_val})"
                    )
            self.validation_results['checks_performed'] += 1

            # בדיקת nulls בשדות חובה
            if constraints.get('required', False):
                null_count = df[field_name].isnull().sum()
                if null_count > 0:
                    self._add_error(
                        f"{field_name}: {null_count} null values in required field"
                    )
            self.validation_results['checks_performed'] += 1

        # בדיקה 4: Business Rules
        business_rules = schema.get('business_rules', [])
        self._validate_business_rules(df, business_rules)

        # סיכום
        if self.validation_results['passed']:
            print(f"[+] Validation PASSED: {self.validation_results['checks_performed']} checks")
        else:
            print(f"[ERROR] Validation FAILED: {len(self.validation_results['errors'])} errors")

        return self.validation_results

    def _validate_business_rules(self, df, rules):
        """
        אימות business rules
        """
        for rule in rules:
            if 'monthly_maintenance_cost = annual_cost / 12' in rule:
                # בדיקת חישוב
                calculated = df['annual_cost'] / 12
                diff = (df['monthly_maintenance_cost'] - calculated).abs()
                if diff.max() > 0.1:  # tolerance of 0.1
                    self._add_warning(
                        f"Business rule violation: {rule} (max diff: {diff.max():.2f})"
                    )
                self.validation_results['checks_performed'] += 1

            elif 'Outlier removal' in rule:
                # בדיקה שאין outliers
                outliers = df[
                    (df['monthly_maintenance_cost'] >= 10000) |
                    (df['monthly_maintenance_cost'] <= 0)
                ]
                if len(outliers) > 0:
                    self._add_error(f"Found {len(outliers)} outliers violating: {rule}")
                self.validation_results['checks_performed'] += 1

    def validate_model_performance(self, metrics):
        """
        אימות ביצועי מודל מול סף מינימום
        """
        print("\n[*] Validating model performance...")

        thresholds = self.contract['validation_rules']['model_performance']['minimum_thresholds']

        for metric, min_val in thresholds.items():
            actual_val = metrics.get(metric)

            if actual_val is None:
                self._add_warning(f"Metric {metric} not provided")
                continue

            # R2 צריך להיות גבוה מהסף
            if metric == 'r2_score':
                if actual_val < min_val:
                    self._add_error(f"{metric}: {actual_val:.4f} < {min_val} (threshold)")
                else:
                    print(f"  [+] {metric}: {actual_val:.4f} >= {min_val} (PASS)")

            # RMSE, MAE, MAPE צריכים להיות נמוכים מהסף
            else:
                if actual_val > min_val:
                    self._add_error(f"{metric}: {actual_val:.2f} > {min_val} (threshold)")
                else:
                    print(f"  [+] {metric}: {actual_val:.2f} <= {min_val} (PASS)")

            self.validation_results['checks_performed'] += 1

        return self.validation_results

    def generate_validation_report(self, output_path='reports/contract_validation_report.json'):
        """
        יצירת דוח אימות
        """
        report = {
            'validation_date': datetime.now().isoformat(),
            'contract_version': self.contract.get('contract_version'),
            'results': self.validation_results,
            'summary': {
                'status': 'PASSED' if self.validation_results['passed'] else 'FAILED',
                'total_checks': self.validation_results['checks_performed'],
                'total_errors': len(self.validation_results['errors']),
                'total_warnings': len(self.validation_results['warnings'])
            }
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n[+] Validation report saved: {output_path}")
        return output_path

    def _add_error(self, message):
        """
        הוספת שגיאה
        """
        self.validation_results['errors'].append(message)
        self.validation_results['passed'] = False
        print(f"  [ERROR] {message}")

    def _add_warning(self, message):
        """
        הוספת אזהרה
        """
        self.validation_results['warnings'].append(message)
        print(f"  [!] {message}")


# =============================================
# הרצה עצמאית לבדיקה
# =============================================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("DATASET CONTRACT VALIDATION")
    print("="*70)

    validator = ContractValidator()

    # טעינת החוזה
    validator.load_contract()

    # אימות features file
    validator.validate_features_file()

    # אימות ביצועי מודל
    # קריאת metadata של המודל
    try:
        with open('models/model_metadata.json', 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            metrics = {
                'r2_score': metadata.get('test_r2'),
                'rmse': metadata.get('rmse'),
                'mae': metadata.get('mae')
            }
            validator.validate_model_performance(metrics)
    except FileNotFoundError:
        print("\n[!] Model metadata not found - skipping model validation")

    # יצירת דוח
    validator.generate_validation_report()

    # סיכום
    print("\n" + "="*70)
    if validator.validation_results['passed']:
        print("FINAL STATUS: PASSED")
        print(f"Total checks: {validator.validation_results['checks_performed']}")
        print(f"Warnings: {len(validator.validation_results['warnings'])}")
        exit(0)
    else:
        print("FINAL STATUS: FAILED")
        print(f"Errors: {len(validator.validation_results['errors'])}")
        print(f"Warnings: {len(validator.validation_results['warnings'])}")
        exit(1)
