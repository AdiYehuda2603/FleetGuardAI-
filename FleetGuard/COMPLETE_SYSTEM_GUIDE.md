# 📚 מדריך מלא - FleetGuard System

## 📊 מה יש במערכת?

### 1. נתונים במערכת

#### טבלת `vehicles` (רכבים)
- ✅ `vehicle_id` - מזהה ייחודי
- ✅ `plate` - מספר לוחית
- ✅ `make_model` - דגם רכב
- ✅ `year` - שנת ייצור
- ✅ `fleet_entry_date` - תאריך כניסה לצי
- ✅ `initial_km` - קילומטראז' התחלתי
- ✅ `status` - סטטוס (active/inactive)

#### טבלת `invoices` (חשבוניות)
- ✅ `invoice_no` - מספר חשבונית
- ✅ `date` - תאריך
- ✅ `workshop` - מוסך
- ✅ `vehicle_id` - מזהה רכב
- ✅ `odometer_km` - קילומטראז' בחשבונית
- ✅ `kind` - סוג טיפול
- ✅ `total` - סכום כולל

#### טבלת `invoice_lines` (שורות פירוט)
- ✅ פריטים מפורטים מכל חשבונית

---

## 🆕 מה נוסף עכשיו?

### 1. ✅ פונקציות CRUD (הוספה, מחיקה, עדכון)

**מיקום:** `src/database_manager.py`

**פונקציות חדשות:**
- `add_invoice()` - הוספת חשבונית חדשה
- `delete_invoice()` - מחיקת חשבונית
- `update_vehicle_odometer()` - עדכון קילומטראז' ידני
- `get_invoice_by_no()` - חיפוש חשבונית לפי מספר
- `search_invoices()` - חיפוש מתקדם

### 2. ✅ לשונית ניהול נתונים

**מיקום:** לשונית 4 ב-`main.py`

**תת-לשוניות:**
- **📤 העלאת חשבונית** - העלאת PDF/CSV לעיבוד
- **🗑️ מחיקת חשבונית** - חיפוש ומחיקה
- **📊 עדכון קילומטראז'** - עדכון ידני

### 3. ✅ סוכן AI לזיהוי דפוסי תקלות

**מיקום:** `src/maintenance_pattern_agent.py`

**מה הוא עושה:**
- 🔍 מזהה דפוסי החלפת צמיגים (כל כמה ק"מ)
- 🔍 מזהה דפוסי טיפול שוטף
- 🔍 מנתח מגמות עלויות לפי קילומטראז'
- 🔍 נותן המלצות תחזוקה

**דוגמה:**
```
"החלף צמיגים כל 2,500 ק"מ או כל שנתיים (לפי מה שמגיע קודם)"
```

### 4. ✅ לשונית דפוסי תחזוקה

**מיקום:** לשונית 5 ב-`main.py`

**מה יש שם:**
- בחירת רכב לניתוח
- ניתוח דפוסי תקלות
- המלצות תחזוקה
- גרפים של מגמות עלויות

---

## 🎯 איפה כל דבר?

### העלאת חשבונית
1. פתח את הדשבורד
2. לך ללשונית **"⚙️ ניהול נתונים"**
3. תת-לשונית **"📤 העלאת חשבונית"**
4. גרור קובץ PDF או CSV
5. הקובץ יעובד אוטומטית

### מחיקת חשבונית
1. לך ללשונית **"⚙️ ניהול נתונים"**
2. תת-לשונית **"🗑️ מחיקת חשבונית"**
3. הזן מספר חשבונית
4. לחץ "מחק"

### עדכון קילומטראז'
1. לך ללשונית **"⚙️ ניהול נתונים"**
2. תת-לשונית **"📊 עדכון קילומטראז'"**
3. בחר רכב
4. הזן קילומטראז' חדש
5. לחץ "עדכן"

### ניתוח דפוסי תקלות
1. לך ללשונית **"🔍 דפוסי תחזוקה"**
2. בחר רכב (או "כל הצי")
3. לחץ "חפש דפוסים"
4. קרא את ההמלצות

---

## 🧪 איך לבדוק שכל הפונקציות עובדות?

### הרץ את סקריפט הבדיקה:

```powershell
cd "C:\AI DEVELOPER\FleetGuardAI\FleetGuard"
python test_all_functions.py
```

**הסקריפט בודק:**
- ✅ DatabaseManager - כל הפונקציות
- ✅ AuthManager - כניסה והרשמה
- ✅ MaintenancePatternAgent - זיהוי דפוסים
- ✅ FileProcessor - עיבוד קבצים
- ✅ CrewOrchestrator - Multi-Agent
- ✅ FleetAIEngine - AI Chat

---

## 📋 רשימת כל הפונקציות

### DatabaseManager
- ✅ `get_all_invoices()` - כל החשבוניות
- ✅ `get_all_vehicles()` - כל הרכבים
- ✅ `get_vehicle_history()` - היסטוריית רכב
- ✅ `get_vehicle_with_stats()` - רכבים עם סטטיסטיקות
- ✅ `add_invoice()` - הוספת חשבונית **חדש!**
- ✅ `delete_invoice()` - מחיקת חשבונית **חדש!**
- ✅ `update_vehicle_odometer()` - עדכון קילומטראז' **חדש!**
- ✅ `search_invoices()` - חיפוש מתקדם **חדש!**

### MaintenancePatternAgent
- ✅ `analyze_maintenance_patterns()` - ניתוח דפוסים
- ✅ `get_maintenance_recommendations()` - המלצות

### FileProcessor
- ✅ `process_uploaded_file()` - עיבוד קבצים
- ✅ `save_to_uploads()` - שמירת קבצים

---

## 🎓 דוגמאות שימוש

### הוספת חשבונית ידנית:
```python
from src.database_manager import DatabaseManager

db = DatabaseManager()

invoice_data = {
    'invoice_no': 'INV-12345678',
    'date': '2024-12-15',
    'workshop': 'מוסך דוגמה',
    'vehicle_id': 'VH-01',
    'plate': '12-345-67',
    'make_model': 'Toyota Corolla',
    'odometer_km': 50000,
    'kind': 'routine',
    'subtotal': 1000,
    'vat': 170,
    'total': 1170
}

invoice_lines = [
    {
        'line_no': 1,
        'description': 'שמן מנוע',
        'type': 'part',
        'qty': 1,
        'unit_price': 200,
        'line_total': 200
    }
]

db.add_invoice(invoice_data, invoice_lines)
```

### מחיקת חשבונית:
```python
db.delete_invoice('INV-12345678')
```

### עדכון קילומטראז':
```python
db.update_vehicle_odometer('VH-01', 55000, '2024-12-15')
```

### ניתוח דפוסים:
```python
from src.maintenance_pattern_agent import MaintenancePatternAgent

agent = MaintenancePatternAgent()
patterns = agent.analyze_maintenance_patterns('VH-01')
recommendations = agent.get_maintenance_recommendations('VH-01')
```

---

## ✅ סיכום

### מה יש:
- ✅ 3 טבלאות: vehicles, invoices, invoice_lines
- ✅ פונקציות CRUD מלאות
- ✅ ממשק ניהול נתונים
- ✅ סוכן AI לזיהוי דפוסים
- ✅ סקריפט בדיקה

### מה חדש:
- ✅ הוספת חשבוניות
- ✅ מחיקת חשבוניות
- ✅ עדכון קילומטראז'
- ✅ ניתוח דפוסי תקלות
- ✅ המלצות תחזוקה

---

**הכל מוכן לשימוש! 🚛✨**

