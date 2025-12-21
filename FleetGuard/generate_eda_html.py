# -*- coding: utf-8 -*-
"""
Generate HTML EDA Report
יצירת דוח EDA בפורמט HTML עבור פרויקט הגמר
"""

import pandas as pd
from ydata_profiling import ProfileReport
import os

def generate_html_eda():
    """
    יוצר דוח HTML EDA מקובץ הנתונים המנוקה
    """
    print("[*] Starting HTML EDA Report Generation...")

    # טעינת הנתונים המנוקים
    data_path = "data/processed/fleet_data_cleaned.csv"

    if not os.path.exists(data_path):
        print(f"[ERROR] Data file not found: {data_path}")
        return False

    print(f"[*] Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"[+] Loaded {len(df)} records with {len(df.columns)} columns")

    # יצירת דוח ProfileReport
    print("[*] Generating EDA profile report (this may take a minute)...")

    profile = ProfileReport(
        df,
        title="FleetGuard AI - Exploratory Data Analysis",
        explorative=True,
        minimal=False
    )

    # שמירת הדוח
    output_path = "reports/eda_report.html"
    os.makedirs("reports", exist_ok=True)

    print(f"[*] Saving HTML report to: {output_path}")
    profile.to_file(output_path)

    print("[+] HTML EDA Report generated successfully!")
    print(f"[+] File size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
    print(f"[+] Open in browser: file:///{os.path.abspath(output_path)}")

    return True


if __name__ == "__main__":
    print("=" * 70)
    print("FleetGuard AI - HTML EDA Report Generator")
    print("=" * 70)
    print()

    success = generate_html_eda()

    if success:
        print()
        print("[SUCCESS] EDA Report ready for Final Project submission!")
    else:
        print()
        print("[FAILED] Please check the error messages above")
