# -*- coding: utf-8 -*-
"""
Replace Vehicle - הוצאת רכב והחלפה ברכב חדש
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database_manager import DatabaseManager
from datetime import datetime, timedelta
import random
import sqlite3
import pandas as pd

def retire_vehicle_and_add_new():
    """
    מוציא רכב מהפול ומוסיף רכב חדש
    """
    print("\n" + "="*70)
    print("VEHICLE REPLACEMENT PROCESS")
    print("="*70)

    db = DatabaseManager()

    # שלב 1: בחירת רכב להוצאה מהפול
    print("\n[STEP 1] Selecting vehicle to retire...")

    vehicles = db.get_fleet_overview()

    # סינון רק רכבים פעילים
    active_vehicles = vehicles[vehicles['status'] == 'active'].copy()

    # חישוב גיל הרכב
    from datetime import datetime
    active_vehicles['vehicle_age_years'] = (
        (datetime.now() - pd.to_datetime(active_vehicles['purchase_date'])).dt.days / 365.25
    )

    # נבחר רכב עם הרבה קילומטרים או גיל גבוה
    candidate = active_vehicles.nlargest(5, 'vehicle_age_years').sample(1).iloc[0]

    old_vehicle_id = candidate['vehicle_id']
    old_plate = candidate['plate']
    old_make_model = candidate['make_model']
    old_age = candidate['vehicle_age_years']
    old_km = candidate['current_km']
    old_cost = candidate['total_cost']

    print(f"\n[+] Selected vehicle to retire:")
    print(f"    ID: {old_vehicle_id}")
    print(f"    Plate: {old_plate}")
    print(f"    Model: {old_make_model}")
    print(f"    Age: {old_age:.2f} years")
    print(f"    Mileage: {old_km:,} km")
    print(f"    Total cost: ₪{old_cost:,.2f}")

    # שלב 2: סימון הרכב כ-retired
    print("\n[STEP 2] Marking vehicle as retired...")

    try:
        conn = sqlite3.connect('data/database/fleet.db')
        cursor = conn.cursor()

        retirement_date = datetime.now().strftime('%Y-%m-%d')

        cursor.execute("""
            UPDATE vehicles
            SET status = 'retired'
            WHERE vehicle_id = ?
        """, (old_vehicle_id,))

        conn.commit()
        print(f"[+] Vehicle {old_plate} marked as retired on {retirement_date}")

    except Exception as e:
        print(f"[ERROR] Failed to retire vehicle: {e}")
        conn.rollback()
        return False

    # שלב 3: הוספת רכב חדש
    print("\n[STEP 3] Adding new vehicle to fleet...")

    # רכבים אפשריים
    new_models = [
        "Toyota Corolla",
        "Honda Civic",
        "Mazda 3",
        "Hyundai i30",
        "Kia Picanto"
    ]

    # יצירת פרטי רכב חדש
    new_make_model = random.choice(new_models)
    new_year = 2024
    new_plate = f"{random.randint(10,99)}-{random.randint(100,999)}-{random.randint(10,99)}"

    # תאריך כניסה לצי - חודש אחרון
    entry_date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')

    initial_km = random.randint(5, 500)  # רכב כמעט חדש

    # בחירת נהג אקראי מהרשימה הקיימת
    existing_drivers = vehicles['assigned_to'].unique()
    assigned_to = random.choice(existing_drivers)

    # מציאת vehicle_id הבא
    # vehicle_id הוא מחרוזת בפורמט 'VH-XX'
    vehicle_ids = vehicles['vehicle_id'].str.extract(r'VH-(\d+)', expand=False).astype(int)
    max_num = vehicle_ids.max()
    new_vehicle_id = f"VH-{max_num + 1}"

    try:
        cursor.execute("""
            INSERT INTO vehicles
            (vehicle_id, plate, make_model, year, fleet_entry_date, purchase_date, initial_km, status, assigned_to)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
        """, (new_vehicle_id, new_plate, new_make_model, new_year, entry_date, entry_date, initial_km, assigned_to))

        conn.commit()

        print(f"\n[+] New vehicle added:")
        print(f"    ID: {new_vehicle_id}")
        print(f"    Plate: {new_plate}")
        print(f"    Model: {new_make_model}")
        print(f"    Year: {new_year}")
        print(f"    Entry date: {entry_date}")
        print(f"    Initial km: {initial_km}")
        print(f"    Assigned to: {assigned_to}")

    except Exception as e:
        print(f"[ERROR] Failed to add new vehicle: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

    # שלב 4: הוספת חשבונית ראשונה לרכב החדש
    print("\n[STEP 4] Adding initial service invoice for new vehicle...")

    try:
        conn = sqlite3.connect('data/database/fleet.db')
        cursor = conn.cursor()

        # קבלת מספר חשבונית הבא
        cursor.execute("SELECT MAX(CAST(SUBSTR(invoice_no, 5) AS INTEGER)) FROM invoices")
        max_inv = cursor.fetchone()[0]
        new_invoice_no = f"INV-{max_inv + 1}"

        # חשבונית ראשונה - טיפול קבלה
        service_date = (datetime.strptime(entry_date, '%Y-%m-%d') + timedelta(days=3)).strftime('%Y-%m-%d')
        workshop = "מוסך דוד"
        kind = "טיפול קבלה"
        subtotal = round(random.uniform(300, 500), 2)
        vat = round(subtotal * 0.17, 2)
        total = round(subtotal + vat, 2)
        odometer = initial_km + random.randint(10, 50)

        cursor.execute("""
            INSERT INTO invoices
            (invoice_no, vehicle_id, plate, make_model, date, workshop, kind, subtotal, vat, total, odometer_km)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (new_invoice_no, new_vehicle_id, new_plate, new_make_model, service_date,
              workshop, kind, subtotal, vat, total, odometer))

        conn.commit()
        conn.close()

        print(f"[+] Initial service invoice added: {new_invoice_no}")
        print(f"    Date: {service_date}")
        print(f"    Workshop: {workshop}")
        print(f"    Total: ₪{total:.2f}")

    except Exception as e:
        print(f"[ERROR] Failed to add invoice: {e}")
        return False

    # סיכום
    print("\n" + "="*70)
    print("REPLACEMENT COMPLETED SUCCESSFULLY")
    print("="*70)
    print(f"\n[RETIRED] {old_plate} ({old_make_model})")
    print(f"[ADDED] {new_plate} ({new_make_model}, {new_year})")
    print("\n[+] Fleet updated - ready for testing!")

    return True


if __name__ == "__main__":
    print("\n" + "#"*70)
    print("# FleetGuard AI - Vehicle Replacement")
    print("# Retire old vehicle and add new one")
    print("#"*70)

    success = retire_vehicle_and_add_new()

    if success:
        print("\n" + "="*70)
        print("Next: Run full system test to verify everything works")
        print("Command: python src/crew_flow.py")
        print("="*70)
        exit(0)
    else:
        print("\n[FAILED] Vehicle replacement failed")
        exit(1)
