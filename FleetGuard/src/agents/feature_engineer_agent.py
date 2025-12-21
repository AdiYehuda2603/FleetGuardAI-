# -*- coding: utf-8 -*-
"""
Agent D: Feature Engineer
תפקיד: יצירת פיצ'רים (features) מנתונים גולמיים לצורך אימון מודל ML
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
import os
import sys

# הוספת נתיב לייבוא מודולים
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database_manager import DatabaseManager
except ImportError:
    from src.database_manager import DatabaseManager


class FeatureEngineer:
    """
    סוכן D - Feature Engineer
    אחראי על יצירת פיצ'רים איכוותיים ממערך הנתונים
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.label_encoders = {}

    def load_data(self):
        """
        טעינת נתונים מהמסד
        """
        print("[*] Agent D: Loading data from database...")

        # נתוני צי מלאים
        fleet_df = self.db.get_fleet_overview()

        # חשבוניות מלאות
        invoices_df = self.db.get_all_invoices()

        print(f"[+] Loaded {len(fleet_df)} vehicles, {len(invoices_df)} invoices")

        return fleet_df, invoices_df

    def engineer_vehicle_features(self, fleet_df):
        """
        יצירת פיצ'רים ברמת רכב
        """
        print("[*] Agent D: Engineering vehicle-level features...")

        features_df = fleet_df.copy()

        # 1. גיל רכב (בשנים)
        current_date = pd.Timestamp.now()
        features_df['purchase_date'] = pd.to_datetime(features_df['purchase_date'], errors='coerce')
        features_df['vehicle_age_years'] = (
            (current_date - features_df['purchase_date']).dt.days / 365.25
        ).round(2)

        # 2. ממוצע עלות לטיפול
        features_df['avg_cost_per_service'] = (
            features_df['total_cost'] / features_df['total_services']
        ).replace([np.inf, -np.inf], 0).fillna(0).round(2)

        # 3. תדירות טיפולים (טיפולים לשנה)
        features_df['service_frequency_rate'] = (
            features_df['total_services'] / features_df['vehicle_age_years']
        ).replace([np.inf, -np.inf], 0).fillna(0).round(2)

        # 4. קילומטרים שנסעו (current - initial)
        if 'current_km' in features_df.columns and 'initial_km' in features_df.columns:
            features_df['total_km_driven'] = (features_df['current_km'] - features_df['initial_km']).fillna(0).clip(lower=0)
        else:
            features_df['total_km_driven'] = features_df.get('current_km', 0)

        # 5. קילומטראז' לחודש
        features_df['km_per_month'] = (
            features_df['total_km_driven'] / (features_df['vehicle_age_years'] * 12)
        ).replace([np.inf, -np.inf], 0).fillna(0).round(0)

        # 5. עלות שנתית (לשימוש כ-target variable)
        features_df['annual_cost'] = (
            features_df['total_cost'] / features_df['vehicle_age_years']
        ).replace([np.inf, -np.inf], 0).fillna(0).round(2)

        # 6. עלות חודשית ממוצעת - TARGET VARIABLE
        features_df['monthly_maintenance_cost'] = (
            features_df['annual_cost'] / 12
        ).round(2)

        print(f"[+] Created basic numerical features")

        return features_df

    def engineer_temporal_features(self, features_df, invoices_df):
        """
        יצירת פיצ'רים זמניים מחשבוניות
        """
        print("[*] Agent D: Engineering temporal features...")

        if invoices_df.empty:
            print("[!] No invoices data - skipping temporal features")
            features_df['days_since_last_service'] = 0
            features_df['months_since_purchase'] = features_df['vehicle_age_years'] * 12
            return features_df

        # המרת תאריכים
        invoices_df['date'] = pd.to_datetime(invoices_df['date'], errors='coerce')

        # חישוב ימים מאז טיפול אחרון
        last_service = invoices_df.groupby('vehicle_id')['date'].max().reset_index()
        last_service.columns = ['vehicle_id', 'last_service_date_calc']

        features_df = features_df.merge(last_service, on='vehicle_id', how='left')

        current_date = pd.Timestamp.now()
        features_df['days_since_last_service'] = (
            (current_date - features_df['last_service_date_calc']).dt.days
        ).fillna(0).astype(int)

        # חודשים מאז רכישה
        features_df['months_since_purchase'] = (features_df['vehicle_age_years'] * 12).round(0)

        # ניקוי
        features_df = features_df.drop('last_service_date_calc', axis=1, errors='ignore')

        print(f"[+] Created temporal features")

        return features_df

    def encode_categorical_features(self, features_df):
        """
        קידוד פיצ'רים קטגוריים (Categorical Encoding)
        """
        print("[*] Agent D: Encoding categorical features...")

        categorical_columns = ['make_model', 'assigned_to']

        for col in categorical_columns:
            if col in features_df.columns:
                # שמירת encoder לשימוש עתידי
                le = LabelEncoder()

                # טיפול ב-NaN
                features_df[col] = features_df[col].fillna('Unknown')

                features_df[f'{col}_encoded'] = le.fit_transform(features_df[col])
                self.label_encoders[col] = le

                print(f"   [+] Encoded {col}: {len(le.classes_)} unique values")

        print(f"[+] Encoded {len(categorical_columns)} categorical features")

        return features_df

    def select_final_features(self, features_df):
        """
        בחירת פיצ'רים סופיים למודל
        """
        print("[*] Agent D: Selecting final features for model...")

        # עמודות שנרצה לשמור
        feature_columns = [
            'vehicle_id',
            'plate',
            'vehicle_age_years',
            'current_km',
            'total_km_driven',
            'total_services',
            'avg_cost_per_service',
            'service_frequency_rate',
            'km_per_month',
            'days_since_last_service',
            'months_since_purchase',
            'make_model_encoded',
            'assigned_to_encoded',
            'monthly_maintenance_cost',  # TARGET
            'annual_cost'  # מידע נוסף
        ]

        # בחירת עמודות קיימות בלבד
        available_columns = [col for col in feature_columns if col in features_df.columns]

        final_df = features_df[available_columns].copy()

        # הסרת שורות עם NaN ב-target
        initial_rows = len(final_df)
        final_df = final_df.dropna(subset=['monthly_maintenance_cost'])

        # הסרת outliers קיצוניים (עלות חודשית > 10,000)
        final_df = final_df[final_df['monthly_maintenance_cost'] < 10000]
        final_df = final_df[final_df['monthly_maintenance_cost'] > 0]

        print(f"[+] Selected {len(available_columns)} features")
        print(f"[+] Clean records: {len(final_df)} (removed {initial_rows - len(final_df)} invalid/outlier rows)")

        return final_df

    def save_features(self, features_df, output_path='data/processed/features.csv'):
        """
        שמירת פיצ'רים לקובץ CSV
        """
        print(f"[*] Agent D: Saving features to {output_path}...")

        # יצירת תיקייה אם לא קיימת
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # שמירה
        features_df.to_csv(output_path, index=False, encoding='utf-8')

        print(f"[+] Saved {len(features_df)} records with {len(features_df.columns)} features")

        # סטטיסטיקות
        print("\n[*] Feature Statistics:")
        print(features_df.describe().round(2))

        return output_path

    def run(self):
        """
        הרצת התהליך המלא
        """
        print("\n" + "="*60)
        print("AGENT D: FEATURE ENGINEER - STARTING")
        print("="*60 + "\n")

        try:
            # 1. טעינת נתונים
            fleet_df, invoices_df = self.load_data()

            # 2. יצירת פיצ'רים ברמת רכב
            features_df = self.engineer_vehicle_features(fleet_df)

            # 3. יצירת פיצ'רים זמניים
            features_df = self.engineer_temporal_features(features_df, invoices_df)

            # 4. קידוד קטגוריות
            features_df = self.encode_categorical_features(features_df)

            # 5. בחירת פיצ'רים סופיים
            final_features = self.select_final_features(features_df)

            # 6. שמירה
            output_path = self.save_features(final_features)

            print("\n" + "="*60)
            print("AGENT D: FEATURE ENGINEERING COMPLETED SUCCESSFULLY")
            print("="*60 + "\n")

            return {
                'success': True,
                'output_file': output_path,
                'num_records': len(final_features),
                'num_features': len(final_features.columns),
                'target_variable': 'monthly_maintenance_cost'
            }

        except Exception as e:
            print(f"\n[ERROR] AGENT D ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }


# =============================================
# הרצה עצמאית לבדיקה
# =============================================
if __name__ == "__main__":
    agent = FeatureEngineer()
    result = agent.run()

    if result['success']:
        print(f"\n[SUCCESS] Feature engineering completed!")
        print(f"[+] Output: {result['output_file']}")
        print(f"[+] Records: {result['num_records']}")
        print(f"[+] Features: {result['num_features']}")
    else:
        print(f"\n[FAILED] {result['error']}")
