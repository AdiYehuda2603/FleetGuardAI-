# 🚀 מדריך הפעלה מהיר - FleetGuard

## 📋 שלבים להפעלת המערכת המלאה

### שלב 1: התקנת תלויות (פעם אחת בלבד)

פתח **PowerShell** או **Command Prompt** בתיקיית הפרויקט:

```powershell
cd "C:\AI DEVELOPER\FleetGuardAI\FleetGuard"
pip install -r requirements.txt
```

⏱️ **זמן משוער:** 2-5 דקות (תלוי במהירות האינטרנט)

---

### שלב 2: יצירת נתוני דמו (אם עדיין לא קיימים)

אם מסד הנתונים לא קיים, הרץ:

```powershell
python generate_data.py
```

⏱️ **זמן משוער:** 1-2 דקות

זה יוצר:
- ✅ ~1000 חשבוניות PDF
- ✅ מסד נתונים SQLite (`fleet.db`)
- ✅ קובץ CSV (`invoices.csv`)
- ✅ 85 רכבים בצי

---

### שלב 3: הפעלת הדשבורד

#### אופציה A: שימוש בסקריפט אוטומטי (מומלץ)

**Windows (PowerShell):**
```powershell
.\RUN_SYSTEM.ps1
```

**Windows (Command Prompt):**
```cmd
RUN_SYSTEM.bat
```

#### אופציה B: הפעלה ידנית

```powershell
streamlit run main.py
```

---

### שלב 4: פתיחת הדפדפן

הדשבורד יפתח אוטומטית ב:
**http://localhost:8501**

אם לא נפתח, פתח ידנית את הכתובת בדפדפן.

---

## 🎯 מה תראה בדשבורד?

### 📊 לשונית 1: לוח בקרה
- KPIs: סה"כ הוצאות, רכבים פעילים, עלות ממוצעת
- גרפים: הוצאות לפי מוסך, מגמות לאורך זמן
- זיהוי חריגות

### 🤖 לשונית 2: צ'אט אנליסט (AI)
- שאל שאלות בעברית על הנתונים
- דוגמה: "איזה מוסך הכי יקר החודש?"
- **נדרש:** מפתח OpenAI API (ראה למטה)

### 📋 לשונית 3: נתונים גולמיים
- טבלה מלאה של כל החשבוניות
- ניתן לסנן ולחפש

---

## 🔐 הגדרת OpenAI API (אופציונלי - רק לצ'אט AI)

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

## ✅ בדיקת תקינות המערכת

הרץ את הפקודה הבאה כדי לוודא שהכל עובד:

```powershell
python -c "from src.database_manager import DatabaseManager; db = DatabaseManager(); df = db.get_all_invoices(); print(f'✅ מסד נתונים: {len(df)} חשבוניות'); print(f'✅ רכבים: {df[\"vehicle_id\"].nunique()}'); print('✅ המערכת מוכנה!')"
```

---

## 🛠️ פתרון בעיות נפוצות

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

### ❌ "Hebrew text not displaying correctly"
- ודא שהדפדפן מוגדר ל-UTF-8
- נסה דפדפן אחר (Chrome מומלץ)

---

## 📁 מבנה קבצים חשובים

```
FleetGuard/
├── main.py                    # ⭐ הדשבורד הראשי
├── generate_data.py          # ⭐ יצירת נתוני דמו
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

## 🎓 שימוש במערכת Multi-Agent (CrewAI)

לאחר הפעלת הדשבורד:

1. **העלה קובץ** (PDF או CSV) דרך סרגל הצד
2. המערכת תפעיל אוטומטית:
   - ✅ ולידציה של נתונים
   - ✅ ניתוח EDA
   - ✅ אימון מודלי ML
   - ✅ יצירת דוחות

3. התוצאות יוצגו בלשונית **לוח בקרה**

---

## 💡 טיפים

- **הפעלה ראשונה:** הרץ `generate_data.py` לפני `main.py`
- **API Key:** לא חובה, אבל נדרש לצ'אט AI
- **ביצועים:** המערכת עובדת טוב עם 1000+ חשבוניות
- **גיבוי:** שמור עותק של `fleet.db` לפני שינויים גדולים

---

## 🚀 מוכן להתחיל!

1. ✅ התקן תלויות: `pip install -r requirements.txt`
2. ✅ צור נתונים: `python generate_data.py`
3. ✅ הפעל דשבורד: `streamlit run main.py`
4. ✅ פתח בדפדפן: http://localhost:8501

**בהצלחה! 🚛✨**

