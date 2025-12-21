# -*- coding: utf-8 -*-
"""
FleetGuard Large Scale Generator
--------------------------------
Creates ~1000 invoices (85 vehicles, ~12 invoices each) with Hebrew PDF generation + Logic Biases.
Output goes directly into the FleetGuard project structure.
"""

import os
import random
import string
import sqlite3
import csv
import datetime as dt
import platform

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- הגדרת נתיבים לפרויקט ---
BASE_DIR = os.getcwd()
PROJECT_ROOT = os.path.join(BASE_DIR, "FleetGuard")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PDF_OUTPUT_DIR = os.path.join(DATA_DIR, "raw_invoices")
DB_OUTPUT_DIR = os.path.join(DATA_DIR, "database")

# יצירת תיקיות אם לא קיימות
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
os.makedirs(DB_OUTPUT_DIR, exist_ok=True)

# --- טיפול בעברית (RTL) ---
use_bidi = False
try:
    from bidi.algorithm import get_display
    use_bidi = True
except ImportError:
    pass

def rtl(s: str) -> str:
    if not s: return s
    if use_bidi: return get_display(s)
    return s[::-1] # Fallback

def register_hebrew_font() -> str:
    """
    מנסה לטעון פונט עברי בהתאם למערכת ההפעלה
    """
    system = platform.system()
    font_name = "HebrewFont"
    font_path = None

    if system == "Windows":
        # נתיב נפוץ ב-Windows
        possible_paths = ["C:\\Windows\\Fonts\\arial.ttf", "C:\\Windows\\Fonts\\tahoma.ttf"]
    elif system == "Linux":
        # נתיב נפוץ ב-Linux
        possible_paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]
    elif system == "Darwin": # Mac
        possible_paths = ["/Library/Fonts/Arial Unicode.ttf"]
    else:
        possible_paths = []

    # חיפוש הפונט הראשון שקיים
    for path in possible_paths:
        if os.path.exists(path):
            font_path = path
            break
    
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            return font_name
        except:
            return "Helvetica" # Fallback לאנגלית אם נכשל
    return "Helvetica"

BASE_FONT = register_hebrew_font()

# --- עזרים ---
def rand_id(prefix="INV-", n=8) -> str:
    """יוצר מספר חשבונית אוניברסלי (8 ספרות למניעת כפילויות)"""
    return prefix + "".join(random.choice(string.digits) for _ in range(n))

def rand_date(start: dt.date, end: dt.date) -> dt.date:
    delta = end - start
    return start + dt.timedelta(days=random.randint(0, delta.days))

def watermark(c: canvas.Canvas, text="SAMPLE / TEST DATA") -> None:
    c.saveState()
    c.setFillColorRGB(0.85, 0.85, 0.85)
    c.setFont(BASE_FONT, 36)
    w, h = A4
    c.translate(w / 2, h / 2)
    c.rotate(35)
    c.drawCentredString(0, 0, text)
    c.restoreState()

# --- יצירת PDF ---
def pdf_hebrew(path: str, inv: dict) -> None:
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4

    # כותרות
    c.setFont(BASE_FONT, 18)
    c.drawString(22 * mm, h - 22 * mm, rtl("חשבונית (נתוני בדיקה)"))
    c.setFont(BASE_FONT, 9)
    c.drawString(22 * mm, h - 28 * mm, rtl("מסמך זה נוצר לצורך פרויקט FleetGuard. אינו חשבונית אמיתית."))

    # פרטים
    c.setFont(BASE_FONT, 10)
    right_x = 200 * mm 

    def draw_label_value(y, label_he, value):
        c.setFont(BASE_FONT, 10)
        c.drawRightString(right_x, y, rtl(label_he))
        c.drawString(22 * mm, y, str(value))

    draw_label_value(h - 40 * mm, "מוסך:", inv["workshop"])
    draw_label_value(h - 46 * mm, "מספר מסמך:", inv["invoice_no"])
    draw_label_value(h - 52 * mm, "תאריך:", inv["date"].strftime("%d/%m/%Y"))
    draw_label_value(h - 58 * mm, "רכב:", f'{inv["vehicle_id"]} ({inv["plate"]})')
    draw_label_value(h - 64 * mm, 'ק"מ:', inv["odometer_km"])
    draw_label_value(h - 70 * mm, "דגם:", inv["make_model"])

    # טבלה
    y = h - 85 * mm
    c.setFillColor(colors.lightgrey)
    c.rect(22 * mm, y, 176 * mm, 8 * mm, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont(BASE_FONT, 10)
    c.drawString(24 * mm, y + 2.5 * mm, rtl("תיאור"))
    c.drawString(120 * mm, y + 2.5 * mm, rtl("כמות"))
    c.drawString(140 * mm, y + 2.5 * mm, rtl("יחידה"))
    c.drawString(170 * mm, y + 2.5 * mm, rtl('סה"כ'))

    y -= 7 * mm
    for ln in inv["lines"]:
        c.drawString(24 * mm, y, rtl(ln["description"]))
        c.drawRightString(135 * mm, y, str(ln["qty"]))
        c.drawRightString(162 * mm, y, f'{ln["unit_price"]:.2f}')
        c.drawRightString(198 * mm, y, f'{ln["line_total"]:.2f}')
        y -= 6 * mm

    # סיכומים
    subtotal = round(sum(l["line_total"] for l in inv["lines"]), 2)
    vat = round(subtotal * 0.17, 2)
    total = round(subtotal + vat, 2)
    inv["subtotal"], inv["vat"], inv["total"] = subtotal, vat, total

    y -= 3 * mm
    c.line(130 * mm, y, 198 * mm, y)
    y -= 7 * mm
    c.drawRightString(175 * mm, y, rtl("סכום ביניים:"))
    c.drawRightString(198 * mm, y, f"{subtotal:.2f}")
    y -= 6 * mm
    c.drawRightString(175 * mm, y, rtl('מע"מ (17%):'))
    c.drawRightString(198 * mm, y, f"{vat:.2f}")
    y -= 7 * mm
    c.setFont(BASE_FONT, 12)
    c.drawRightString(175 * mm, y, rtl('סה"כ לתשלום:'))
    c.drawRightString(198 * mm, y, f"{total:.2f}")

    watermark(c)
    c.showPage()
    c.save()

# --- לוגיקה עסקית ---
def main():
    random.seed(42)
    print(f"[*] Starting Large Scale Generation...")
    print(f"[*] Saving PDFs to: {PDF_OUTPUT_DIR}")
    print(f"[*] Saving DB to: {DB_OUTPUT_DIR}")

    # 1. יצירת צי רכב מוגדל (85 רכבים -> ~1000 חשבוניות)
    vehicles = []
    makes = ["Toyota Corolla", "Hyundai i10", "Kia Niro", "Skoda Octavia", "Ford Transit", "Mazda 3", "Chevrolet Spark"]

    # טווח מוגדל
    for i in range(1, 86):
        year = random.choice([2019, 2020, 2021, 2022, 2023])
        # תאריך כניסה לצי - בין 3-12 חודשים אחרי שנת הייצור
        fleet_entry_date = dt.date(year, 1, 1) + dt.timedelta(days=random.randint(90, 365))
        # קילומטרז' התחלתי - רכבים חדשים עם 0-5000 ק"מ
        initial_km = random.randint(0, 5000)

        vehicles.append({
            "vehicle_id": f"VH-{i:02d}",
            "plate": f"{random.randint(10,99)}-{random.randint(100,999)}-{random.randint(10,99)}",
            "make_model": random.choice(makes),
            "year": year,
            "fleet_entry_date": fleet_entry_date,
            "initial_km": initial_km,
            "status": "active"  # כל הרכבים פעילים
        })

    # מוסכים והטיות
    WORK_YOSSI = "יוסי צמיגים ופרונט (בדיקה)"
    WORK_YOAV = "יואב חשמל ופנסים (בדיקה)"
    WORK_OVED = "עובד חלפים מקוריים (בדיקה)"
    other_workshops = ["מוסך צי צפון (בדיקה)", "מוסך העיר (בדיקה)", "מוסך המרכז (בדיקה)"]
    workshops = [WORK_YOSSI, WORK_YOAV, WORK_OVED] + other_workshops

    ITEMS = {
        "TIRES": ("צמיג 205/55R16", "part", (320, 720)),
        "ALIGN": ("כיוון פרונט", "labor", (140, 260)),
        "HEADL": ("נורת פנס קדמי (H7)", "part", (70, 220)),
        "LAMP": ("יחידת פנס אחורי", "part", (180, 520)),
        "SPARK": ("פלאגים מקוריים (סט)", "part", (220, 520)),
        "OIL": ("שמן מנוע 5W-30", "part", (180, 320)),
        "OFILT": ("פילטר שמן", "part", (35, 85)),
        "DIAG": ("אבחון/דיאגנוסטיקה", "labor", (120, 280)),
        "LAB": ("שעות עבודה", "labor", (180, 420)),
    }

    def biased_unit_price(item_key, workshop):
        lo, hi = ITEMS[item_key][2]
        base = random.uniform(lo, hi)
        # Biases
        if item_key == "TIRES" and workshop == WORK_YOSSI: base *= random.uniform(0.70, 0.85)
        if item_key in ["HEADL", "LAMP"] and workshop == WORK_YOAV: base *= random.uniform(0.70, 0.88)
        if item_key == "SPARK" and workshop == WORK_OVED: base *= random.uniform(0.68, 0.85)
        if workshop in other_workshops and item_key in ["TIRES", "SPARK", "LAMP", "HEADL"]:
            base *= random.uniform(1.05, 1.25)
        return round(base, 2)

    def make_line(item_key, qty):
        desc, typ, _ = ITEMS[item_key]
        return {"description": desc, "type": typ, "qty": qty}

    def add_prices(lines, workshop):
        priced = []
        desc_to_key = {v[0]: k for k, v in ITEMS.items()}
        for ln in lines:
            key = desc_to_key[ln["description"]]
            unit = biased_unit_price(key, workshop)
            priced.append({**ln, "unit_price": unit, "line_total": round(unit * ln["qty"], 2)})
        return priced

    start = dt.date(2023, 1, 1) # התחלנו מוקדם יותר כדי לייצר היסטוריה
    end = dt.date(2024, 12, 1)

    # אתחול מצב רכבים - מתחילים מהקילומטרז' ההתחלתי
    vehicle_state = {v["vehicle_id"]: {"odo": v["initial_km"], "km_month": random.randint(1200, 3000)} for v in vehicles}
    invoice_rows = []
    line_rows = []

    def create_invoice_entry(vehicle, workshop, date, lines, tag):
        state = vehicle_state[vehicle["vehicle_id"]]
        state["odo"] += int(state["km_month"] * random.uniform(0.5, 1.3))
        
        inv = {
            "invoice_no": rand_id(),
            "date": date,
            "workshop": workshop,
            "vehicle_id": vehicle["vehicle_id"],
            "plate": vehicle["plate"],
            "make_model": vehicle["make_model"],
            "odometer_km": state["odo"],
            "kind": tag,
            "lines": add_prices(lines, workshop)
        }
        
        filename = f'{inv["invoice_no"]}_{inv["vehicle_id"]}.pdf'
        inv["pdf_file"] = filename
        pdf_hebrew(os.path.join(PDF_OUTPUT_DIR, filename), inv)
        
        invoice_rows.append(inv)
        for i, ln in enumerate(inv["lines"], 1):
            line_rows.append({
                "invoice_no": inv["invoice_no"], "line_no": i,
                "description": ln["description"], "type": ln["type"],
                "qty": ln["qty"], "unit_price": ln["unit_price"], "line_total": ln["line_total"]
            })

    # --- מחולל הנתונים הראשי ---
    print("[*] Generating invoices (this might take a minute)...")
    
    target_categories = [
        ("tires", ["TIRES", "ALIGN"]),
        ("lights", ["HEADL"]),
        ("spark_plugs", ["SPARK", "DIAG"]),
    ]
    weights_map = {
        "tires": [(WORK_YOSSI, 0.45), (WORK_OVED, 0.25), (WORK_YOAV, 0.15), (other_workshops[0], 0.15)],
        "lights": [(WORK_YOAV, 0.45), (WORK_YOSSI, 0.20), (WORK_OVED, 0.20), (other_workshops[1], 0.15)],
        "spark_plugs": [(WORK_OVED, 0.45), (WORK_YOSSI, 0.20), (WORK_YOAV, 0.20), (other_workshops[0], 0.15)],
    }

    for idx, v in enumerate(vehicles):
        if idx % 10 == 0: print(f"   Processing vehicle {idx+1}/{len(vehicles)}...")
        
        # 1. טיפולים שוטפים (Routine) - 8-10 טיפולים לרכב (להגיע ל-1000 חשבוניות)
        for _ in range(random.randint(8, 10)):
            ws = random.choice(workshops)
            d = rand_date(start, end)
            lines = [make_line("OIL", 1), make_line("OFILT", 1), make_line("LAB", random.choice([1, 1.5, 2]))]
            create_invoice_entry(v, ws, d, lines, "routine")

        # 2. תקלות ספציפיות (Targeted) - הסתברות גבוהה
        for cat, keys in target_categories:
            if random.random() < 0.95: # כמעט לכולם יש תקלות
                ws = random.choices([w for w, _ in weights_map[cat]], weights=[p for _, p in weights_map[cat]], k=1)[0]
                d = rand_date(start, end)
                lines = [make_line(k, 4 if k == "TIRES" else 1) for k in keys]
                lines.append(make_line("LAB", 1))
                create_invoice_entry(v, ws, d, lines, cat)

    print(f"[OK] Generated {len(invoice_rows)} invoices total.")

    # --- שמירה ל-CSV ו-SQLite ---
    csv_file = os.path.join(DB_OUTPUT_DIR, "invoices.csv")
    pd = list(invoice_rows[0].keys())
    # remove lines and complex objects for CSV header
    csv_headers = ["invoice_no", "date", "workshop", "vehicle_id", "plate", "make_model", "odometer_km", "kind", "subtotal", "vat", "total", "pdf_file"]

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=csv_headers)
        w.writeheader()
        for inv in invoice_rows:
            row = {k: inv[k] for k in csv_headers}
            # המרת תאריך ל-String
            row["date"] = row["date"].isoformat()
            w.writerow(row)

    # SQLite creation
    db_path = os.path.join(DB_OUTPUT_DIR, "fleet.db")
    if os.path.exists(db_path): os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # טבלאות
    # טבלת רכבים - מידע על כל רכב בצי
    cur.execute("""CREATE TABLE vehicles (
        vehicle_id TEXT PRIMARY KEY,
        plate TEXT,
        make_model TEXT,
        year INTEGER,
        fleet_entry_date TEXT,
        initial_km INTEGER,
        status TEXT
    )""")

    cur.execute("""CREATE TABLE invoices (
        invoice_no TEXT PRIMARY KEY, date TEXT, workshop TEXT, vehicle_id TEXT,
        plate TEXT, make_model TEXT, odometer_km INTEGER, kind TEXT,
        subtotal REAL, vat REAL, total REAL, pdf_file TEXT
    )""")

    cur.execute("""CREATE TABLE invoice_lines (
        invoice_no TEXT, line_no INTEGER, description TEXT, type TEXT,
        qty REAL, unit_price REAL, line_total REAL
    )""")

    # הכנסת נתונים
    # 1. רכבים
    vehicle_data = [(v["vehicle_id"], v["plate"], v["make_model"], v["year"],
                     v["fleet_entry_date"].isoformat(), v["initial_km"], v["status"]) for v in vehicles]
    cur.executemany("INSERT INTO vehicles VALUES (?,?,?,?,?,?,?)", vehicle_data)

    # 2. חשבוניות
    inv_data = [(i["invoice_no"], i["date"].isoformat(), i["workshop"], i["vehicle_id"], i["plate"], i["make_model"],
                 i["odometer_km"], i["kind"], i["subtotal"], i["vat"], i["total"], i["pdf_file"]) for i in invoice_rows]
    cur.executemany("INSERT INTO invoices VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", inv_data)

    # 3. שורות פירוט
    line_data = [(l["invoice_no"], l["line_no"], l["description"], l["type"], l["qty"], l["unit_price"], l["line_total"]) for l in line_rows]
    cur.executemany("INSERT INTO invoice_lines VALUES (?,?,?,?,?,?,?)", line_data)
    
    conn.commit()
    conn.close()
    
    print("[SUCCESS] Finished! Data populated in FleetGuard folder.")

if __name__ == "__main__":
    main()