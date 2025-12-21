# -*- coding: utf-8 -*-
"""
Add Test Invoices - הוספת 20 חשבוניות בדיקה
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database_manager import DatabaseManager
from datetime import datetime, timedelta
import random

# בתי מלאכה לבחירה אקראית
WORKSHOPS = [
    "גראז' המרכז",
    "שירות אקספרס",
    "מוסך דוד",
    "תיקונים מהירים",
    "Auto Service Plus"
]

# תיאורי שירות אפשריים
DESCRIPTIONS = [
    "החלפת שמן ופילטרים",
    "בדיקת טסט שנתי",
    "תיקון מערכת בלמים",
    "החלפת צמיגים",
    "טיפול 10,000 ק\"מ",
    "תיקון מזגן",
    "החלפת מצבר",
    "תיקון מערכת חשמל",
    "יישור מרכב",
    "החלפת נורות"
]

def add_test_invoices(num_invoices=20):
    """
    הוספת חשבוניות בדיקה
    """
    print(f"\n[*] Adding {num_invoices} test invoices to database...")

    db = DatabaseManager()

    # קבלת רשימת רכבים קיימים עם current_km
    vehicles = db.get_fleet_overview()
    print(f"[+] Found {len(vehicles)} vehicles in database")

    if len(vehicles) == 0:
        print("[ERROR] No vehicles found - cannot add invoices")
        return

    # קבלת מספר החשבונית האחרונה
    invoices = db.get_all_invoices()

    # מספר חשבונית הוא מחרוזת בפורמט 'INV-XXXXXXXX'
    # נחלץ את המספר הגבוה ביותר
    if len(invoices) > 0:
        invoice_numbers = invoices['invoice_no'].str.extract(r'INV-(\d+)', expand=False).astype(float)
        max_num = int(invoice_numbers.max())
    else:
        max_num = 99990000

    next_invoice_no = f"INV-{max_num + 1}"
    print(f"[+] Starting from invoice number: {next_invoice_no}")

    added_count = 0

    for i in range(num_invoices):
        # בחירת רכב אקראי
        vehicle = vehicles.sample(1).iloc[0]
        vehicle_id = vehicle['vehicle_id']
        current_km = vehicle['current_km']
        plate = vehicle['plate']
        make_model = vehicle['make_model']

        # תאריך אקראי - 30-180 ימים אחורה
        days_ago = random.randint(30, 180)
        invoice_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

        # בית מלאכה אקראי
        workshop = random.choice(WORKSHOPS)

        # קילומטראז' - קצת יותר נמוך מהנוכחי
        km_decrease = random.randint(500, 3000)
        odometer_km = max(current_km - km_decrease, vehicle.get('initial_km', 10000))

        # עלות אקראית
        subtotal = round(random.uniform(150, 700), 2)
        vat = round(subtotal * 0.17, 2)
        total = round(subtotal + vat, 2)

        # סוג טיפול
        kind = random.choice(['טיפול שוטף', 'תיקון', 'טסט'])

        # הוספה ל-DB
        invoice_no = f"INV-{max_num + i + 1}"

        try:
            db.cursor.execute("""
                INSERT INTO invoices
                (invoice_no, vehicle_id, plate, make_model, date, workshop, kind, subtotal, vat, total, odometer_km)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (invoice_no, vehicle_id, plate, make_model, invoice_date, workshop, kind, subtotal, vat, total, odometer_km))

            added_count += 1

            if (i + 1) % 5 == 0:
                print(f"[+] Added {i + 1}/{num_invoices} invoices...")

        except Exception as e:
            print(f"[!] Error adding invoice {invoice_no}: {e}")

    # שמירת השינויים
    db.conn.commit()

    print(f"\n[+] Successfully added {added_count} invoices")

    # עדכון total_services ו-total_cost לרכבים
    print("\n[*] Updating vehicle statistics...")

    for _, vehicle in vehicles.iterrows():
        vehicle_id = vehicle['vehicle_id']

        # חישוב מחדש
        vehicle_invoices = db.get_vehicle_history(vehicle_id)

        if len(vehicle_invoices) > 0:
            total_services = len(vehicle_invoices)
            total_cost = vehicle_invoices['total'].sum()
            last_service_date = vehicle_invoices['date'].max()

            db.cursor.execute("""
                UPDATE vehicles
                SET total_services = ?, total_cost = ?, last_service_date = ?
                WHERE vehicle_id = ?
            """, (total_services, float(total_cost), last_service_date, vehicle_id))

    db.conn.commit()
    print("[+] Vehicle statistics updated")

    # סיכום
    print("\n" + "="*70)
    print("TEST DATA ADDED SUCCESSFULLY")
    print("="*70)

    invoices_after = db.get_all_invoices()
    print(f"Total invoices in database: {len(invoices_after)}")
    print(f"New invoices added: {added_count}")

    return added_count


if __name__ == "__main__":
    print("\n" + "#"*70)
    print("# FleetGuard AI - Add Test Invoices")
    print("#"*70)

    count = add_test_invoices(20)

    if count > 0:
        print("\n[SUCCESS] Test invoices added - ready for testing!")
        exit(0)
    else:
        print("\n[FAILED] No invoices were added")
        exit(1)
