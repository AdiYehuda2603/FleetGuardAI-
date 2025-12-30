# 🚀 הדרכת פריסה ל-Streamlit Cloud

## ✅ דרישות מוקדמות
- [x] חשבון GitHub (יש לך!)
- [x] Repository FleetGuardAI ב-GitHub (יש לך!)
- [x] קובץ המודל הועלה ל-GitHub (יש לך!)
- [ ] חשבון Streamlit Cloud (צריך ליצור)

---

## שלב 1: יצירת חשבון Streamlit Cloud

1. **גש לאתר**: https://share.streamlit.io/
2. **התחבר עם GitHub**: לחץ על "Sign up" ובחר "Continue with GitHub"
3. **אשר הרשאות**: תן ל-Streamlit גישה ל-repositories שלך

---

## שלב 2: יצירת Secrets (מפתחות API)

**חשוב מאוד!** לפני הפריסה, הגדר את המפתחות הסודיים:

### בעמוד Streamlit Cloud:
1. לאחר שיצרת את האפליקציה, לך ל-**Settings** → **Secrets**
2. העתק את התוכן הבא (החלף במפתחות האמיתיים שלך):

```toml
# OpenAI API Configuration
OPENAI_API_KEY = "sk-proj-YOUR-ACTUAL-KEY-HERE"
OPENAI_MODEL_NAME = "gpt-4o-mini"

# Database Configuration
DATABASE_PATH = "FleetGuard/data/database/fleet.db"

# Application Settings
ENVIRONMENT = "production"
LOG_LEVEL = "INFO"

# Email Configuration (Optional - leave as false if not using)
EMAIL_FETCH_ENABLED = false
EMAIL_IMAP_SERVER = "imap.gmail.com"
EMAIL_IMAP_PORT = 993
EMAIL_ADDRESS = ""
EMAIL_PASSWORD = ""
EMAIL_FOLDER = "INBOX"
EMAIL_MARK_AS_READ = true
EMAIL_MAX_FETCH = 50
EMAIL_DATE_FILTER_DAYS = 30
```

3. **שמור את ה-Secrets**

---

## שלב 3: פריסת האפליקציה

### אופן 1: ממשק ה-Web של Streamlit Cloud

1. **לך ל-Dashboard**: https://share.streamlit.io/
2. **לחץ על "New app"**
3. **מלא את הפרטים**:
   - **Repository**: `AdiYehuda2603/FleetGuardAI-`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py` (זה בשורש!)
   - **App URL**: בחר שם (למשל: `fleetguard-ai`)

4. **לחץ "Deploy"**

### אופן 2: מה-CLI (אופציונלי)

אם יש לך Streamlit CLI:
```bash
streamlit run https://github.com/AdiYehuda2603/FleetGuardAI-/blob/main/streamlit_app.py
```

---

## שלב 4: המתן לבנייה

- ⏳ Streamlit Cloud יבנה את האפליקציה (1-3 דקות)
- 📦 יתקין את כל ה-dependencies מ-`requirements.txt`
- 🚀 יפעיל את האפליקציה

---

## שלב 5: בדיקה

1. **פתח את ה-URL** שקיבלת (משהו כמו `https://fleetguard-ai.streamlit.app`)
2. **בדוק שהדאשבורד נטען**
3. **בדוק שהמודל נטען** - גש ל-טאב "🎯 תחזיות ML"
   - אם אתה רואה את מדדי המודל (R², RMSE, MAE) - המודל נטען! ✅
   - אם אתה רואה "המודל לא נטען" - יש בעיה ❌

---

## 🐛 פתרון בעיות נפוצות

### בעיה 1: "המודל לא נטען"

**גורמים אפשריים**:
1. **קובץ model.pkl חסר ב-GitHub**
   - **פתרון**: וודא ש-`FleetGuard/models/model.pkl` קיים ב-repository
   - בדוק ב-GitHub: https://github.com/AdiYehuda2603/FleetGuardAI-/tree/main/FleetGuard/models

2. **בעיית נתיבים**
   - **פתרון**: הקוד כבר תוקן לשימוש ב-`path_resolver`
   - אם עדיין יש בעיה, בדוק את ה-logs ב-Streamlit Cloud

3. **חסר joblib ב-requirements**
   - **פתרון**: וודא ש-`joblib` מופיע ב-`requirements.txt`

### בעיה 2: "Module not found"

**פתרון**:
- וודא שכל החבילות ב-`FleetGuard/requirements.txt` מופיעות גם ב-`requirements.txt` בשורש
- הרץ:
  ```bash
  cat FleetGuard/requirements.txt >> requirements.txt
  git add requirements.txt
  git commit -m "Update requirements"
  git push
  ```

### בעיה 3: "API Key not found"

**פתרון**:
- וודא שהגדרת את ה-Secrets ב-Streamlit Cloud
- בדוק שהשם `OPENAI_API_KEY` זהה בדיוק

### בעיה 4: "Database not found"

**פתרון**:
- וודא ש-`FleetGuard/data/database/fleet.db` קיים ב-GitHub
- בדוק ש-`.gitignore` **לא** חוסם את הקובץ הזה

---

## 📊 איך לראות Logs

1. בדף האפליקציה ב-Streamlit Cloud
2. לחץ על **"Manage app"** (ימין למעלה)
3. לחץ על **"Logs"**
4. חפש שורות עם:
   - `[OK] Model loaded:` - המודל נטען בהצלחה ✅
   - `[ERROR] Model not found:` - המודל לא נמצא ❌
   - `[ERROR] Failed to load model:` - שגיאה בטעינה ❌

---

## 🔄 עדכון האפליקציה

כל פעם שאתה עושה `git push` ל-`main`, Streamlit Cloud **אוטומטית**:
1. מזהה שינוי ב-repository
2. בונה מחדש את האפליקציה
3. מפרוס את הגרסה החדשה

**זה אומר**: כל תיקון שאתה דוחף ל-GitHub יעודכן באוויר תוך דקות!

---

## ✅ Checklist לפני פריסה

- [ ] וודאתי ש-`model.pkl` קיים ב-GitHub (`FleetGuard/models/model.pkl`)
- [ ] וודאתי ש-`fleet.db` קיים ב-GitHub (`FleetGuard/data/database/fleet.db`)
- [ ] וודאתי ש-`streamlit_app.py` קיים בשורש
- [ ] וודאתי ש-`requirements.txt` קיים בשורש
- [ ] יצרתי חשבון Streamlit Cloud
- [ ] הגדרתי את ה-Secrets (OPENAI_API_KEY)
- [ ] הכל ב-`main` branch ודחוף ל-GitHub

---

## 🎯 הצלחה!

אם כל השלבים עברו, האפליקציה שלך אמורה להיות זמינה ב-URL ציבורי!

**URL לדוגמה**: `https://fleetguard-ai-adiyehuda.streamlit.app`

---

## 📞 עזרה נוספת

- **Streamlit Community**: https://discuss.streamlit.io/
- **Docs**: https://docs.streamlit.io/streamlit-community-cloud
- **GitHub Issues**: https://github.com/AdiYehuda2603/FleetGuardAI-/issues

---

**נוצר ב**: 30 דצמבר 2025
**עבור**: FleetGuardAI v2.1.0
