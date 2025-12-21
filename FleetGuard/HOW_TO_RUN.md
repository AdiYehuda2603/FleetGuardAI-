# 🚀 איך להריץ את FleetGuard במלואו

## 📋 הוראות הפעלה מהירות

### שיטה 1: הפעלה אוטומטית (מומלץ) ⭐

#### Windows - PowerShell:
```powershell
cd "C:\AI DEVELOPER\FleetGuardAI\FleetGuard"
.\RUN_SYSTEM.ps1
```

#### Windows - Command Prompt:
```cmd
cd "C:\AI DEVELOPER\FleetGuardAI\FleetGuard"
RUN_SYSTEM.bat
```

הסקריפט יבצע אוטומטית:
1. ✅ בדיקת Python
2. ✅ התקנת תלויות (אם חסרות)
3. ✅ יצירת נתונים (אם לא קיימים)
4. ✅ הפעלת הדשבורד

---

### שיטה 2: הפעלה ידנית

#### שלב 1: התקנת תלויות (פעם אחת בלבד)
```powershell
cd "C:\AI DEVELOPER\FleetGuardAI\FleetGuard"
pip install -r requirements.txt
```

#### שלב 2: יצירת נתוני דמו (אם לא קיימים)
```powershell
python generate_data.py
```

#### שלב 3: הפעלת הדשבורד
```powershell
streamlit run main.py
```

---

## 🌐 פתיחת הדשבורד

לאחר ההפעלה, הדשבורד יפתח אוטומטית ב:
**http://localhost:8501**

אם לא נפתח, פתח ידנית את הכתובת בדפדפן.

---

## 🔐 הגדרת OpenAI API (אופציונלי - רק לצ'אט AI)

### אופציה 1: קובץ .env (מומלץ)

1. צור קובץ `.env` בתיקיית `FleetGuard`:
```env
OPENAI_API_KEY=sk-your-key-here
```

2. הדשבורד יטען את המפתח אוטומטית

### אופציה 2: הזנה ידנית בדשבורד

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
cd "C:\AI DEVELOPER\FleetGuardAI\FleetGuard"
python -c "from src.database_manager import DatabaseManager; db = DatabaseManager(); df = db.get_all_invoices(); print(f'✅ מסד נתונים: {len(df)} חשבוניות'); print(f'✅ רכבים: {df[\"vehicle_id\"].nunique()}'); print('✅ המערכת מוכנה!')"
```

---

## 🎯 מה תראה בדשבורד?

### 1. 🔐 עמוד כניסה/הרשמה
- אם זו הפעלה ראשונה, תתבקש להירשם
- אם כבר יש לך חשבון, התחבר

### 2. 📊 לוח בקרה (Dashboard)
- KPIs: סה"כ הוצאות, רכבים פעילים, עלות ממוצעת
- גרפים: הוצאות לפי מוסך, מגמות לאורך זמן
- זיהוי חריגות

### 3. 🤖 צ'אט אנליסט (AI)
- שאל שאלות בעברית על הנתונים
- דוגמה: "איזה רכב נסע הכי הרבה השנה?"
- **נדרש:** מפתח OpenAI API

### 4. 📋 נתונים גולמיים
- טבלה מלאה של כל החשבוניות
- ניתן לסנן ולחפש

### 5. ⚙️ ניהול נתונים
- העלאת חשבוניות חדשות
- מחיקת חשבוניות
- עדכון קילומטראז' ידני

### 6. 🔍 דפוסי תחזוקה
- ניתוח AI של דפוסי תחזוקה
- זיהוי דפוסי החלפת צמיגים
- המלצות תחזוקה

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

### ❌ "Authentication error"
- ודא שיש לך קובץ `data/database/users.db`
- אם לא, המערכת תיצור אותו אוטומטית

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
│   ├── database/
│   │   ├── fleet.db          # מסד נתונים - חשבוניות ורכבים
│   │   └── users.db          # מסד נתונים - משתמשים
│   ├── processed/            # קבצים מעובדים
│   ├── reports/              # דוחות EDA
│   └── models/               # מודלי ML
└── src/                      # קוד המקור
    ├── database_manager.py   # ניהול מסד נתונים
    ├── ai_engine.py          # AI Analyst
    ├── auth_manager.py       # ניהול משתמשים
    ├── crewai_agents.py      # סוכני CrewAI
    └── ...
```

---

## 🎓 שימוש במערכת Multi-Agent (CrewAI)

לאחר הפעלת הדשבורד:

1. **העלה קובץ** (PDF או CSV) דרך לשונית **"⚙️ ניהול נתונים"** → **"📤 העלאת חשבונית"**
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
- **עצירת השרת:** לחץ `Ctrl+C` בטרמינל

---

## 🚀 סיכום - 3 שלבים פשוטים

1. ✅ **התקן תלויות:**
   ```powershell
   pip install -r requirements.txt
   ```

2. ✅ **צור נתונים (אם לא קיימים):**
   ```powershell
   python generate_data.py
   ```

3. ✅ **הפעל דשבורד:**
   ```powershell
   streamlit run main.py
   ```
   
   או פשוט:
   ```powershell
   .\RUN_SYSTEM.ps1
   ```

---

## ✅ בדיקת כל הפונקציות

לאחר ההפעלה, תוכל לבדוק שכל הפונקציות עובדות:

```powershell
python test_all_functions.py
```

זה יבדוק:
- ✅ DatabaseManager
- ✅ AuthManager
- ✅ MaintenancePatternAgent
- ✅ FileProcessor
- ✅ CrewOrchestrator
- ✅ FleetAIEngine

---

**בהצלחה! 🚛✨**

