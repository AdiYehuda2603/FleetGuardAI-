# FleetGuard AI
## מערכת אוטונומית לניהול צי רכב מבוססת בינה מלאכותית

**מנהל פרויקט**: [שמך]

---

## 🎯 הבעיה

ארגונים המנהלים צי רכב מתמודדים עם אתגרים משמעותיים:
- **עלויות תחזוקה בלתי צפויות** שפוגעות בתקציבים שנתיים
- **היעדר ניתוח אינטליגנטי** של דפוסי תחזוקה וכשלים
- **קושי בתכנון תקציבי** בגלל חוסר יכולת חיזוי עלויות עתידיות
- **החלטות מבוססות אינטואיציה** במקום נתונים מדעיים

**באופן קריטי, נתוני התחזוקה נשארים לכודים במערכות ידניות (חשבוניות, אקסל), ללא ניתוח פרואקטיבי המונע תקלות, אשפוזים מכניים, ועלויות גבוהות.**

---

## 💡 הפתרון שלנו

**מערכת FleetGuard AI** היא מערכת אוטונומית אינטליגנטית המנתחת נתוני צי רכב באופן אוטומטי, מחזה עלויות תחזוקה עתידיות, ומספקת תובנות פרואקטיביות - **ללא צורך בהתערבות ידנית**.

### ארכיטקטורת המערכת האוטונומית

| **שלב** | **תיאור** | **טכנולוגיה** |
|---------|-----------|----------------|
| 1. טעינה אוטומטית של נתונים | ייבוא אוטומטי של נתוני רכב וחשבוניות מ-SQLite | Python + Pandas |
| 2. ניקוי וולידציה חכמים | זיהוי אוטומטי של ערכים חסרים, חריגות וטיפול בהם | CrewAI Agent A |
| 3. הנדסת פיצ'רים | יצירת 15 פיצ'רים מתקדמים (גיל רכב, תדירות טיפולים, ק"מ חודשי) | CrewAI Agent D |
| 4. אימון מודל ML + Rules Engine | אימון Gradient Boosting + הגדרת כללי אכיפה | CrewAI Agent E + Rules Engine |
| 5. הערכה ואופטימיזציה | מדידת ביצועים (R², RMSE, MAE) והמלצות שיפור | CrewAI Agent F |
| 6. דשבורד אינטראקטיבי | ויזואליזציות + תובנות AI + התראות Rules | Streamlit |

---

## 🔑 יכולות מרכזיות

| **יכולת** | **מצב ראשי** | **גיבוי** |
|-----------|-------------|----------|
| איסוף נתונים | ■ ייבוא אוטומטי מ-SQLite | ■ העלאת CSV ידנית |
| זיהוי דפוסי תחזוקה | ניתוח אוטומטי של תדירות טיפולים, עלויות חריגות | N/A |
| חיזוי עלויות חודשיות | מודל ML עם R²=96.88% (דיוק מצוין) | N/A |
| תובנות AI לגרפים | ניתוח אוטומטי של כל גרף עם המלצות אקשן | N/A |
| זיהוי חריגות | זיהוי סטטיסטי של חריגות (Z-score > 3) | N/A |
| מערכת התראות | התראות על מגמות עלייה בעלויות (>30%) | N/A |

---

## 🏗️ ארכיטקטורה טכנית

**מערכת Multi-Agent עם CrewAI**:
- **Crew 1 - Data Analyst Team** (3 Agents):
  - Agent A: Data Loader - טעינה וולידציה של נתונים מ-SQLite
  - Agent B: Data Cleaner - ניקוי אוטומטי של ערכים חסרים וחריגות
  - Agent C: Data Validator - וולידציה מול Dataset Contract (JSON schema)

- **Crew 2 - Data Scientist Team** (3 Agents):
  - Agent D: Feature Engineer - יצירת 15 פיצ'רים ML
  - Agent E: Model Trainer - אימון Gradient Boosting Regressor
  - Agent F: Model Evaluator - הערכת ביצועים ויצירת דוחות

**אינטגרציות**:
- **Database**: SQLite עם 86 רשומות רכב + 150+ חשבוניות תחזוקה
- **ML Framework**: scikit-learn 1.8.0 (GradientBoostingRegressor)
- **Rules Engine**: מערכת התראות מבוססת כללים עם 5 קטגוריות (תחזוקה, עלויות, פרישה, ניצולת, איכות)
- **Dashboard**: Streamlit עם 10 טאבים אינטראקטיביים (כולל טאב Rules Engine חדש)
- **AI Insights**: מודול תובנות אוטומטי (4 סוגי ניתוחים)
- **Authentication**: מערכת login/register מובנית

**עיבוד נתונים**: Python, Pandas, NumPy | **AI/ML**: scikit-learn, Time Series Analysis | **Rules Engine**: Logic-based alerts + threshold enforcement | **התראות**: מערכת התראות היברידית (ML + Rules) | **דשבורד**: Streamlit, Plotly | **Version Control**: Git + GitHub with PR workflow

---

## 👥 תפקידי צוות נדרשים

| **תפקיד** | **אחריות** | **כישורים** |
|-----------|-----------|-------------|
| מהנדס אוטומציה | פיתוח Agents של CrewAI, אינטגרציית SQLite | Python, CrewAI, SQL |
| מהנדס נתונים | עיצוב פייפליין נתונים, הנדסת פיצ'רים | Python, Pandas, SQL |
| מהנדס ML | זיהוי חריגות, חיזוי עלויות, אופטימיזציה | scikit-learn, Statistics |
| מפתח Backend | מערכת התראות, API, אינטגרציות | Python, Flask (אופציונלי) |
| Frontend/UX | עיצוב דשבורד, ויזואליזציות נתונים | Streamlit, Plotly |

*הערה: כל התפקידים פתוחים למתחילים - נלמד ונבנה ביחד!*

---

## 🎓 למה להצטרף לפרויקט הזה?

- **השפעה אמיתית**: עזרו לארגונים לחסוך מיליוני ₪ בעלויות תחזוקה מיותרות
- **טכנולוגיה חדשנית**: בנו מערכת Multi-Agent אוטונומית מאפס
- **למידה מעשית**: יישום RAG, Agents, ניתוח נתונים, ML לפתרון בעיה אמיתית
- **כל הרמות מוזמנות**: תרמו לפי רמת הכישורים שלכם - נגדל ביחד
- **פוטנציאל מסחרי**: הזדמנות שוק משמעותית מעבר לפרויקט אקדמי
- **תיק עבודות מתקדם**: הצגת מערכת AI מקצה-לקצה עם אוטומציה, ML והשפעה בעולם האמיתי

---

## 🎯 חידוש ייחודי: מערכת AI היברידית

**FleetGuard AI משלבת שני מנועי ניתוח משלימים:**

### 1. Machine Learning (חיזוי נתוני)
- אלגוריתם: GradientBoosting Regressor
- דיוק: R²=96.88% (מצוין)
- תפקיד: מנבא עלויות תחזוקה עתידיות על בסיס נתונים היסטוריים
- יתרון: זיהוי מגמות ודפוסים סמויים

### 2. Rules Engine (אכיפת מדיניות)
- 5 קטגוריות כללים: תחזוקה, עלויות, פרישה, ניצולת, איכות מוסך
- 3 רמות חומרה: URGENT, WARNING, INFO
- תפקיד: אוכף סטנדרטים ארגוניים ומדיניות בזמן אמת
- יתרון: מונע הפרות מדיניות לפני שהן הופכות לבעיות יקרות

### דוגמה לשילוב בפעולה:

**תרחיש**: רכב מספר 1234 חוזר מטיפול שגרתי

- 🤖 **ML אומר**:
  - "הרכב צפוי לעלות ₪450 בחודש הבא"
  - "זה 15% מעל הממוצע שלו (₪391)"
  - "אבל בטווח הנורמלי לרכב בגיל זה"

- 🚨 **Rules Engine אומר**:
  - "⚠️ אזהרה: הרכב עבר 12,450 ק\"מ מהטיפול האחרון"
  - "הפרת מדיניות: מקסימום 10,000 ק\"מ בין טיפולים"
  - "המלצה: תזמן תחזוקה בדחיפות גבוהה"

### היתרון המשולב:
- **ML**: מזהה שהעלות תהיה גבוהה אבל לא חריגה (insight חשוב)
- **Rules**: מזהה הפרת מדיניות שצריכה טיפול מיידי (enforcement קריטי)
- **יחד**: מערכת מושלמת שמשלבת חיזוי חכם עם אכיפה קפדנית! 🎯

---

## 📅 שלבי הפרויקט

**שלב 1 (שבועות 1-4)**: מנוע ניתוח ליבה + אב-טיפוס אוטומציה
- אתחול Git repository + GitHub
- בניית 6 Agents של CrewAI
- פייפליין נתונים מלא (Load → Clean → Validate → Feature Engineering)
- אימון מודל בסיסי (R² > 0.85)
- PR #1: Data pipeline infrastructure

**שלב 2 (שבועות 5-7)**: אוטומציה מלאה + מערכת התראות
- אינטגרציית Dataset Contract
- מערכת תובנות AI אוטומטית
- דשבורד Streamlit עם 9 טאבים
- PR #2: ML model & dashboard
- PR #3: AI insights system

**שלב 3 (שבועות 8-10)**: דשבורד + בדיקות + תיעוד
- מערכת אימות משתמשים
- HTML EDA Report
- Model Card מלא עם שיקולים אתיים
- תיעוד מקיף (README, docs)
- PR #4: Documentation & final polish

**מעבר לקורס**: פריסה בענן (Streamlit Cloud) + פיתוח מסחרי

---

## 🏆 מוכנים לבנות מערכת AI אוטונומית שמצילה תקציבים?

**בואו נהפוך את FleetGuard AI למציאות!**

---

**מדדי הצלחה**:
- ✅ R² Score > 0.95 (דיוק חיזוי מעולה)
- ✅ 6+ Agents פעילים עם תיאום מושלם
- ✅ אוטומציה 100% - ללא התערבות ידנית
- ✅ תובנות AI אוטומטיות לכל ויזואליזציה
- ✅ זמן עיבוד < 10 שניות לכל הפייפליין

**סטטוס נוכחי**: ✅ **פרוטוטייפ מלא מוכן - 100/100 נקודות**

---

## 🔄 Git & GitHub Workflow

### מבנה ניהול גרסאות
**Repository Structure**:
```
FleetGuard/
├── .git/                    # Git repository
├── .gitignore              # Ignore logs, cache, credentials
├── README.md               # Central documentation
├── src/                    # Source code
├── data/                   # Data files (gitignored)
├── models/                 # Trained models
├── reports/                # Analysis reports
└── requirements.txt        # Dependencies
```

### Pull Request Workflow

**תהליך פיתוח מומלץ**:

1. **Feature Branch Strategy**:
```bash
# יצירת branch חדש לכל פיצ'ר
git checkout -b feature/data-pipeline
git checkout -b feature/ml-model
git checkout -b feature/ai-insights
git checkout -b docs/final-documentation
```

2. **Commit Guidelines**:
```bash
# commits מתוארים היטב
git commit -m "feat: Add Feature Engineer Agent with 15 features"
git commit -m "fix: Resolve model loading error with joblib"
git commit -m "docs: Add complete Model Card with ethics section"
git commit -m "refactor: Modularize chart insights generator"
```

3. **Pull Request Process**:
   - יצירת PR מ-feature branch ל-main
   - Code review (לפחות reviewer אחד)
   - בדיקות אוטומטיות (optional: CI/CD)
   - Merge לאחר אישור

**דוגמת PRs מתוכננים**:
- **PR #1**: "Data Pipeline Infrastructure" (Crew 1 - Agents A, B, C)
- **PR #2**: "ML Model Training System" (Crew 2 - Agents D, E, F)
- **PR #3**: "AI Insights Generator" (Chart analysis system)
- **PR #4**: "Final Documentation & Polish" (README, Model Card, EDA)

### Collaboration Benefits
- ✅ **Code Review**: שיפור איכות קוד
- ✅ **Version Control**: מעקב אחר שינויים
- ✅ **Backup**: גיבוי אוטומטי בענן
- ✅ **Collaboration**: עבודת צוות יעילה
- ✅ **Portfolio**: הדגמת workflow מקצועי

### הקמת GitHub Repository

**הקמה ראשונית**:
```bash
# אתחול repository
git init
git add .
git commit -m "Initial commit: FleetGuard AI Multi-Agent System"

# יצירת GitHub repository והעלאה
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/FleetGuard-AI.git
git push -u origin main
```

**כללי הגנה על Branch** (מומלץ):
- דרישת code review לפני merge ל-main
- דרישת עמידה בבדיקות סטטוס
- ללא commits ישירים ל-main
- אכיפת היסטוריה לינארית

**הדגמת PR Workflow**:
לצורך עמידה בדרישות הקורס, הפרויקט ידגים:
1. לפחות 4 Pull Requests משמעותיים
2. הערות ודיונים בסקירת קוד
3. ניהול branches (feature → main)
4. שיטות עבודה מומלצות להודעות commit
5. פתרון merge conflicts (במידת הצורך)
