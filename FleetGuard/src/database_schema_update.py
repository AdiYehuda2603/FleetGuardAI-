# -*- coding: utf-8 -*-
"""
Database Schema Update - Adding Fleet Management Fields
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

class DatabaseSchemaUpdater:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            self.db_path = os.path.join(base_dir, "data", "database", "fleet.db")
        else:
            self.db_path = db_path

    def update_schema(self):
        """מוסיף עמודות חדשות לטבלת vehicles"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # בדיקה אם העמודות כבר קיימות
        cursor.execute("PRAGMA table_info(vehicles)")
        existing_columns = [col[1] for col in cursor.fetchall()]

        new_columns = {
            'purchase_date': 'TEXT',  # תאריך רכישה
            'assigned_to': 'TEXT',  # משוייך ל (נהג/מחלקה)
            'last_test_date': 'TEXT',  # תאריך טסט אחרון
            'next_test_date': 'TEXT',  # תאריך טסט הבא
            'estimated_retirement_date': 'TEXT',  # תאריך גריטה משוער
            'status': 'TEXT DEFAULT "active"'  # סטטוס: active, maintenance, retired
        }

        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE vehicles ADD COLUMN {col_name} {col_type}")
                    print(f"[OK] Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ Column {col_name} might already exist: {e}")

        conn.commit()
        conn.close()
        print("[SUCCESS] Schema update completed!")

    def populate_sample_data(self):
        """ממלא נתוני דמו בשדות החדשים"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # שליפת כל הרכבים
        cursor.execute("SELECT vehicle_id, year FROM vehicles")
        vehicles = cursor.fetchall()

        departments = ['משלוחים', 'מכירות', 'שירות', 'ניהול', 'טכני']
        drivers = [
            'דוד כהן', 'שרה לוי', 'מיכאל אברהם', 'רחל ישראלי', 'יוסף מזרחי',
            'דנה גולן', 'אבי שמעון', 'תמר ברק', 'עמית רוזנברג', 'נועה פרידמן'
        ]

        for vehicle_id, year in vehicles:
            # תאריך רכישה - לפי שנת הרכב
            vehicle_year = int(year) if year else 2020
            purchase_month = random.randint(1, 12)
            purchase_day = random.randint(1, 28)
            purchase_date = f"{vehicle_year}-{purchase_month:02d}-{purchase_day:02d}"

            # שיוך לנהג/מחלקה
            assigned_to = f"{random.choice(drivers)} ({random.choice(departments)})"

            # תאריך טסט אחרון (בשנה האחרונה)
            last_test_date = (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")

            # תאריך טסט הבא (שנה מהטסט האחרון)
            next_test = datetime.strptime(last_test_date, "%Y-%m-%d") + timedelta(days=365)
            next_test_date = next_test.strftime("%Y-%m-%d")

            # גריטה משוערת (15 שנים מהרכישה או 300,000 ק"מ)
            retirement_year = vehicle_year + 15
            estimated_retirement_date = f"{retirement_year}-{purchase_month:02d}-01"

            # סטטוס
            status = 'active'

            # עדכון הרכב
            cursor.execute("""
                UPDATE vehicles
                SET purchase_date = ?,
                    assigned_to = ?,
                    last_test_date = ?,
                    next_test_date = ?,
                    estimated_retirement_date = ?,
                    status = ?
                WHERE vehicle_id = ?
            """, (purchase_date, assigned_to, last_test_date, next_test_date,
                  estimated_retirement_date, status, vehicle_id))

        conn.commit()
        conn.close()
        print(f"[SUCCESS] Updated {len(vehicles)} vehicles with sample fleet management data!")


if __name__ == "__main__":
    updater = DatabaseSchemaUpdater()
    updater.update_schema()
    updater.populate_sample_data()
