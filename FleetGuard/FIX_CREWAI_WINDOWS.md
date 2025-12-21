# 🔧 פתרון בעיית CrewAI ב-Windows

## הבעיה

CrewAI לא עובד ב-Windows בגלל `signal.SIGHUP` שלא קיים במערכת.

**שגיאה:**
```
AttributeError: module 'signal' has no attribute 'SIGHUP'
```

## ✅ פתרון

### אופציה 1: שימוש ב-DirectOrchestrator (מומלץ)

הדשבורד הבסיסי (`main.py`) **לא משתמש ב-CrewAI ישירות**, כך שהוא יעבוד בלי בעיה!

**הדשבורד כולל:**
- ✅ לוח בקרה עם KPIs וגרפים
- ✅ צ'אט AI (עם OpenAI API)
- ✅ נתונים גולמיים

**להפעלה:**
```powershell
streamlit run main.py
```

### אופציה 2: תיקון CrewAI (לשימוש ב-Multi-Agent)

אם אתה רוצה להשתמש במערכת Multi-Agent המלאה:

1. **השתמש ב-DirectOrchestrator** במקום CrewOrchestrator:

```python
# ב-main.py או בקוד שלך
from src.crew_orchestrator import DirectOrchestrator

orchestrator = DirectOrchestrator()
results = orchestrator.run_full_pipeline(uploaded_df)
```

DirectOrchestrator עובד **בלי CrewAI** ומבצע את כל הפונקציות:
- ✅ ולידציה של נתונים
- ✅ ניתוח EDA
- ✅ אימון מודלי ML
- ✅ יצירת דוחות

### אופציה 3: תיקון CrewAI (מתקדם)

אם אתה רוצה לתקן את CrewAI:

1. עדכן את `crewai` לגרסה חדשה יותר:
```powershell
pip install --upgrade crewai
```

2. או השתמש ב-conda environment נפרד:
```powershell
conda create -n fleetguard python=3.11
conda activate fleetguard
pip install -r requirements.txt
```

## 📊 סטטוס

- ✅ **מסד נתונים:** עובד (1012 חשבוניות)
- ✅ **Streamlit:** עובד
- ✅ **Pandas:** עובד
- ⚠️ **CrewAI:** לא עובד ב-Windows (אבל לא נדרש לדשבורד הבסיסי)
- ✅ **DirectOrchestrator:** עובד (אלטרנטיבה מלאה)

## 🚀 הפעלה

**הדשבורד יעבוד בלי בעיה:**
```powershell
cd "C:\AI DEVELOPER\FleetGuardAI\FleetGuard"
streamlit run main.py
```

**הערה על קונפליקט spyder:**
הקונפליקט עם `spyder` ו-`ipython` לא משפיע על FleetGuard. זה רק IDE, לא חלק מהפרויקט.

---

**המערכת מוכנה לשימוש! 🚛✨**

