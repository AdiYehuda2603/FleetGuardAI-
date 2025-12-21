# 🔮 FleetGuard Predictive Features - הוספה מושלמת!

## ✅ מה הוסף למערכת:

### 1. טבלת רכבים חדשה (vehicles table)
```sql
CREATE TABLE vehicles (
    vehicle_id TEXT PRIMARY KEY,
    plate TEXT,                  -- מספר רישוי
    make_model TEXT,             -- דגם
    year INTEGER,                -- שנת ייצור
    fleet_entry_date TEXT,       -- תאריך כניסה לצי
    initial_km INTEGER,          -- קילומטרז' התחלתי
    status TEXT                  -- סטטוס (active/retired)
)
```

**דוגמה:**
- VH-01: Mazda 3, שנת 2019, נכנס לצי ב-13/04/2019, התחיל עם 2,253 ק"מ

---

### 2. AI Agent לחיזוי (`src/predictive_agent.py`)

#### תכונות:

**A. חיזוי טיפול הבא (`predict_next_service`)**
- מחשב מתי הרכב צריך טיפול שוטף (כל 15,000 ק"מ)
- מחשב מתי צריך טיפול גדול (כל 60,000 ק"מ)
- מבוסס על קצב נסיעה ממוצע
- מחזיר תאריך משוער וימים נותרים

**B. החלטת החלפת רכב (`should_replace_vehicle`)**

קריטריונים:
1. **גיל**: מעל 8 שנים → ציון 40
2. **קילומטרז'**: מעל 180,000 ק"מ → ציון 40
3. **עלויות**: פי 2.5 מהממוצע → ציון 30

המלצות:
- ציון 80+: "החלף בהקדם"
- ציון 50-79: "שקול החלפה"
- ציון 20-49: "המשך להשתמש"
- ציון 0-19: "רכב במצב טוב"

**C. תחזית לכל הצי (`get_fleet_predictions`)**
- מחזיר טבלה עם חיזויים לכל 85 רכבים
- כולל טיפול הבא + המלצת החלפה

---

### 3. עדכוני Database Manager

פונקציות חדשות ב-`database_manager.py`:

```python
get_all_vehicles()           # כל הרכבים
get_vehicle_info(id)         # מידע על רכב ספציפי
get_vehicle_with_stats()     # רכבים + סטטיסטיקות (ק"מ נוכחי, עלויות וכו')
```

---

## 🚀 איך להשתמש:

### דוגמה 1: חיזוי טיפול לרכב
```python
from src.predictive_agent import PredictiveMaintenanceAgent

agent = PredictiveMaintenanceAgent()
prediction = agent.predict_next_service("VH-01")

print(f"Routine service in {prediction['next_routine']['days_remaining']} days")
print(f"Estimated date: {prediction['next_routine']['estimated_date']}")
```

### דוגמה 2: בדיקת החלפה
```python
replacement = agent.should_replace_vehicle("VH-15")

print(f"Recommendation: {replacement['recommendation']}")
print(f"Score: {replacement['replacement_score']}/100")
print(f"Reasons: {replacement['reasons']}")
```

### דוגמה 3: תחזית לכל הצי
```python
fleet_df = agent.get_fleet_predictions()

# רכבים שצריכים החלפה
urgent = fleet_df[fleet_df['replacement_score'] >= 80]
print(f"{len(urgent)} vehicles need replacement urgently")
```

---

## 📊 הוספת הטאב ל-Dashboard

כדי להוסיף טאב "🔮 חיזויים" ב-`main.py`:

### שלב 1: ייבוא המודול
```python
from src.predictive_agent import PredictiveMaintenanceAgent
```

### שלב 2: יצירת הטאב
```python
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 לוח בקרה",
    "🤖 צ'אט אנליסט",
    "🔮 חיזויים וטיפולים",  # טאב חדש!
    "📋 נתונים גולמיים"
])
```

### שלב 3: תוכן הטאב
```python
with tab3:
    st.header("🔮 חיזוי טיפולים והחלפות")

    agent = PredictiveMaintenanceAgent()
    predictions = agent.get_fleet_predictions()

    # סינון לפי דחיפות
    urgent_replacement = predictions[predictions['replacement_score'] >= 80]
    needs_service_soon = predictions[predictions['next_service_days'] <= 30]

    st.subheader("⚠️ דחוף - רכבים להחלפה")
    if not urgent_replacement.empty:
        st.dataframe(urgent_replacement[['vehicle_id', 'make_model', 'age',
                     'current_km', 'recommendation']])
    else:
        st.success("אין רכבים הדורשים החלפה דחופה")

    st.subheader("🔧 טיפולים קרובים (30 ימים)")
    if not needs_service_soon.empty:
        st.dataframe(needs_service_soon[['vehicle_id', 'make_model',
                     'next_service_days', 'next_service_date']])
    else:
        st.info("אין טיפולים מתוכננים ב-30 הימים הקרובים")
```

---

## 🧪 בדיקה

הרץ את הסקריפט לבדיקה:
```bash
cd FleetGuard
python src/predictive_agent.py
```

פלט לדוגמה:
```
Testing predictive agent...

Next service for VH-01:
  Current KM: 75,234
  Routine: 42 days (2025-01-24)

Replacement analysis for VH-01:
  Score: 45
  Recommendation: המשך להשתמש
```

---

## 📈 סטטיסטיקות הנתונים החדשים

- **85 רכבים** בצי
- שנות ייצור: 2019-2023
- תאריכי כניסה לצי: 2019-2023
- קילומטרז' התחלתי: 0-5,000 ק"מ
- **1,012 חשבוניות** עם היסטוריית קילומטרז' מלאה

---

## 🎯 הצעדים הבאים (אופציונלי)

1. **ויזואליזציה**: גרפים של מצב הצי
2. **התראות**: התראות אוטומטיות לרכבים דחופים
3. **אופטימיזציה**: המלצות על סדר עדיפויות להחלפה
4. **דוחות**: ייצוא דוח PDF עם המלצות

---

**המערכת כעת מלאה ומתקדמת!** 🚀

כל הנתונים והחיזויים מוכנים. תוכל להוסיף את הטאב הגרפי ל-main.py או להשתמש ב-API ישירות.
