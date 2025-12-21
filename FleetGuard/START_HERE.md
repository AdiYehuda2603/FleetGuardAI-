# 🚀 איך להריץ את FleetGuard - מדריך מהיר

## ⚡ הפעלה מהירה (3 שלבים)

### שלב 1: פתח PowerShell
פתח **PowerShell** או **Command Prompt** בתיקיית הפרויקט

### שלב 2: הרץ את הסקריפט
```powershell
cd "C:\AI DEVELOPER\FleetGuardAI\FleetGuard"
.\RUN_SYSTEM.ps1
```

**או לחיצה כפולה על:**
- `RUN_SYSTEM.bat` (Windows)
- `RUN_SYSTEM.ps1` (PowerShell)

### שלב 3: פתח בדפדפן
הדפדפן יפתח אוטומטית ב: **http://localhost:8501**

אם לא נפתח, פתח ידנית את הכתובת בדפדפן.

---

## 📋 הפעלה ידנית (שלב אחר שלב)

### 1. פתח PowerShell
```powershell
cd "C:\AI DEVELOPER\FleetGuardAI\FleetGuard"
```

### 2. בדוק שהכל מותקן
```powershell
python -c "import streamlit; import pandas; import crewai; print('All OK!')"
```

אם יש שגיאה, התקן תלויות:
```powershell
pip install -r requirements.txt
```

### 3. הפעל את הדשבורד
```powershell
streamlit run main.py
```

### 4. פתח בדפדפן
פתח: **http://localhost:8501**

---

## 🎯 מה תראה בדשבורד?

### 📊 לשונית 1: לוח בקרה
- **KPIs:** סה"כ הוצאות, רכבים פעילים, עלות ממוצעת
- **גרפים:** הוצאות לפי מוסך, מגמות לאורך זמן
- **ויזואליזציות:** חריגות, התפלגויות

### 🤖 לשונית 2: צ'אט אנליסט (AI)
- שאל שאלות בעברית על הנתונים
- דוגמה: "איזה מוסך הכי יקר החודש?"
- **נדרש:** מפתח OpenAI API (ראה למטה)

### 📋 לשונית 3: נתונים גולמיים
- טבלה מלאה של כל החשבוניות
- ניתן לסנן ולחפש

---

## 🔐 הגדרת OpenAI API (אופציונלי)

### אופציה 1: קובץ .env (מומלץ)
1. צור קובץ `.env` בתיקיית `FleetGuard`:
```env
OPENAI_API_KEY=sk-your-key-here
```

2. הדשבורד יטען את המפתח אוטומטית

### אופציה 2: הזנה ידנית
1. פתח את הדשבורד
2. בסרגל הצד, הזן את מפתח ה-API
3. המפתח נשמר רק לסשן הנוכחי

**איפה להשיג מפתח?**
- https://platform.openai.com/api-keys
- הירשם/התחבר
- צור מפתח חדש

---

## ✅ בדיקת תקינות

הרץ את הפקודה הבאה:
```powershell
python -c "import sys; sys.path.insert(0, '.'); import src; from src.database_manager import DatabaseManager; db = DatabaseManager(); df = db.get_all_invoices(); print(f'✅ מסד נתונים: {len(df)} חשבוניות'); print(f'✅ רכבים: {df[\"vehicle_id\"].nunique()}'); print('✅ המערכת מוכנה!')"
```

---

## 🛠️ פתרון בעיות

### ❌ "Module not found"
```powershell
pip install -r requirements.txt
```

### ❌ "Database not found"
```powershell
python generate_data.py
```

### ❌ "Port 8501 already in use"
```powershell
streamlit run main.py --server.port 8502
```

### ❌ "CrewAI error"
✅ **תוקן!** ה-patch רץ אוטומטית. אם עדיין יש בעיה, ודא ש-`src/__init__.py` קיים.

---

## 🎓 שימוש במערכת Multi-Agent

לאחר הפעלת הדשבורד:

1. **העלה קובץ** (PDF או CSV) דרך סרגל הצד
2. המערכת תפעיל אוטומטית:
   - ✅ ולידציה של נתונים
   - ✅ ניתוח EDA
   - ✅ אימון מודלי ML
   - ✅ יצירת דוחות

3. התוצאות יוצגו בלשונית **לוח בקרה**

---

## 📁 מבנה קבצים חשובים

```
FleetGuard/
├── main.py                    # ⭐ הדשבורד הראשי
├── generate_data.py          # יצירת נתוני דמו
├── RUN_SYSTEM.bat            # סקריפט הפעלה (Windows)
├── RUN_SYSTEM.ps1            # סקריפט הפעלה (PowerShell)
├── requirements.txt          # רשימת תלויות
├── .env                      # מפתח API (צור בעצמך)
├── data/
│   └── database/
│       └── fleet.db          # מסד נתונים
└── src/                      # קוד המקור
```

---

## 🚀 מוכן להתחיל!

**הדרך המהירה ביותר:**
```powershell
cd "C:\AI DEVELOPER\FleetGuardAI\FleetGuard"
.\RUN_SYSTEM.ps1
```

**או:**
```powershell
streamlit run main.py
```

---

**בהצלחה! 🚛✨**

