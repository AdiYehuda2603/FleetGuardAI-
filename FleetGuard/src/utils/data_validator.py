"""
Data Validator - Agent A Logic
Enforces dataset_contract.json schema validation with strict DROP_ROW policy
"""

import json
import pandas as pd
import os
from datetime import datetime
import re


class DataValidator:
    """
    Validates fleet data against the dataset_contract.json schema.
    Drops rows with missing critical fields and logs specific alerts.
    """

    def __init__(self, contract_path=None):
        """
        Initialize validator with schema contract

        Args:
            contract_path: Path to dataset_contract.json (auto-detects if None)
        """
        if contract_path is None:
            # Auto-detect contract path
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            contract_path = os.path.join(base_dir, "config", "dataset_contract.json")

        if not os.path.exists(contract_path):
            raise FileNotFoundError(f"❌ Dataset contract not found at: {contract_path}")

        with open(contract_path, 'r', encoding='utf-8') as f:
            self.contract = json.load(f)

        self.critical_fields = self.contract['critical_fields']
        self.optional_fields = self.contract['optional_fields']
        self.field_types = self.contract['field_types']
        self.validation_rules = self.contract['validation_rules']

        self.alerts = []
        self.dropped_count = 0

    def validate_dataframe(self, df):
        """
        Main validation method - checks DataFrame against contract

        Args:
            df: pandas DataFrame to validate

        Returns:
            tuple: (clean_df, alerts_list)
        """
        self.alerts = []
        self.dropped_count = 0

        if df is None or df.empty:
            self.alerts.append("⚠️ Empty dataset received - nothing to validate")
            return df, self.alerts

        # Track original size
        original_size = len(df)

        # Validate each row
        valid_indices = []

        for idx, row in df.iterrows():
            violations = self._validate_row(row, idx)

            if violations:
                # Log violations and drop row
                vehicle_id = row.get('vehicle_id', 'UNKNOWN')
                self.alerts.append(
                    f"⚠️ Vehicle {vehicle_id} data ignored due to missing/invalid fields: {', '.join(violations)}"
                )
                self.dropped_count += 1
            else:
                valid_indices.append(idx)

        # Create clean DataFrame
        clean_df = df.loc[valid_indices].copy()

        # Summary alert
        if self.dropped_count > 0:
            self.alerts.insert(0, f"🔴 VALIDATION SUMMARY: {self.dropped_count}/{original_size} rows dropped")
        else:
            self.alerts.insert(0, f"✅ VALIDATION SUMMARY: All {original_size} rows passed validation")

        return clean_df, self.alerts

    def _validate_row(self, row, idx):
        """
        Validate a single row against contract rules

        Args:
            row: pandas Series (single row)
            idx: row index

        Returns:
            list: violations found (empty if valid)
        """
        violations = []

        # 1. Check critical fields exist and are not null
        for field in self.critical_fields:
            if field not in row or pd.isna(row[field]) or str(row[field]).strip() == '':
                violations.append(f"{field} (missing)")

        # 2. Validate field types and rules (only if field exists)
        for field, rules in self.validation_rules.items():
            if field in row and pd.notna(row[field]):
                # Type-specific validation
                if field == 'odometer_km':
                    try:
                        km = int(row[field])
                        if km < rules.get('min', 0) or km > rules.get('max', 999999):
                            violations.append(f"{field} (out of range: {km})")
                    except (ValueError, TypeError):
                        violations.append(f"{field} (invalid type)")

                elif field == 'total':
                    try:
                        total = float(row[field])
                        if total < rules.get('min', 0) or total > rules.get('max', 999999):
                            violations.append(f"{field} (out of range: {total})")
                    except (ValueError, TypeError):
                        violations.append(f"{field} (invalid type)")

                elif field == 'date':
                    try:
                        # Try to parse date
                        pd.to_datetime(row[field])
                    except:
                        violations.append(f"{field} (invalid date format)")

                elif field == 'vehicle_id':
                    pattern = rules.get('pattern', '')
                    if pattern and not re.match(pattern, str(row[field])):
                        violations.append(f"{field} (invalid pattern)")

        return violations

    def get_validation_report(self):
        """
        Generate a formatted validation report

        Returns:
            str: Formatted report with all alerts
        """
        report = "\n".join(self.alerts)
        return report

    def save_validation_log(self, output_path=None):
        """
        Save validation alerts to a log file

        Args:
            output_path: Path to save log file (auto-generates if None)
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            output_path = os.path.join(base_dir, "data", "reports", f"validation_log_{timestamp}.txt")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("FleetGuard Data Validation Log\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            for alert in self.alerts:
                f.write(alert + "\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write(f"Total Violations: {self.dropped_count}\n")

        return output_path


# --- Testing ---
if __name__ == "__main__":
    # Test with sample data
    test_data = pd.DataFrame([
        {
            'vehicle_id': 'VH-01',
            'date': '2024-01-15',
            'odometer_km': 50000,
            'workshop': 'Yossi Garage',
            'total': 1500.0
        },
        {
            'vehicle_id': 'VH-02',
            'date': '2024-01-16',
            'odometer_km': None,  # Missing critical field!
            'workshop': 'Yoav Garage',
            'total': 2000.0
        },
        {
            'vehicle_id': 'VH-03',
            'date': 'invalid-date',  # Invalid date!
            'odometer_km': 75000,
            'workshop': 'Menashe Garage',
            'total': 3000.0
        },
        {
            'vehicle_id': 'BAD-ID',  # Invalid pattern!
            'date': '2024-01-17',
            'odometer_km': 60000,
            'workshop': 'Yossi Garage',
            'total': 1800.0
        }
    ])

    validator = DataValidator()
    clean_df, alerts = validator.validate_dataframe(test_data)

    print("\n" + "=" * 80)
    print("VALIDATION TEST RESULTS")
    print("=" * 80)
    print(f"\nOriginal rows: {len(test_data)}")
    print(f"Clean rows: {len(clean_df)}")
    print(f"Dropped rows: {validator.dropped_count}")
    print("\nAlerts:")
    for alert in alerts:
        print(f"  {alert}")
    print("\n" + "=" * 80)
