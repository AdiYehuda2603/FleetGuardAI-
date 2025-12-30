# 🚀 מדריך מהיר: פריסה ל-Streamlit Cloud (5 דקות)

## ✅ לפני שמתחילים - וודא שיש לך:
- [x] חשבון GitHub ✅
- [x] הקוד ב-GitHub (https://github.com/AdiYehuda2603/FleetGuardAI-) ✅
- [x] קובץ המודל ב-GitHub (`FleetGuard/models/model.pkl`) ✅
- [ ] מפתח OpenAI API ([קבל כאן](https://platform.openai.com/api-keys))

---

## שלב 1: צור חשבון Streamlit Cloud (2 דקות)

1. **גש ל**: https://share.streamlit.io/
2. **לחץ**: "Sign up" → "Continue with GitHub"
3. **אשר**: תן גישה ל-repositories

✅ **סיימת!** עכשיו יש לך חשבון.

---

## שלב 2: פרוס את האפליקציה (1 דקה)

1. **לחץ**: "New app" (כפתור כחול)
2. **מלא**:
   ```
   Repository: AdiYehuda2603/FleetGuardAI-
   Branch: main
   Main file: streamlit_app.py
   App URL: fleetguard-ai (או כל שם שתרצה)
   ```
3. **לחץ**: "Deploy"

⏳ **המתן** 2-3 דקות לבנייה...

---

## שלב 3: הגדר Secrets (2 דקות)

**בזמן שהאפליקציה נבנית:**

1. **לחץ**: "Settings" → "Secrets" (בצד שמאל)
2. **העתק והדבק** (החלף במפתח שלך!):

```toml
OPENAI_API_KEY = "sk-proj-YOUR-KEY-HERE"
OPENAI_MODEL_NAME = "gpt-4o-mini"
DATABASE_PATH = "FleetGuard/data/database/fleet.db"
ENVIRONMENT = "production"
LOG_LEVEL = "INFO"
EMAIL_FETCH_ENABLED = false
```

3. **לחץ**: "Save"

---

## ✅ זהו! האפליקציה שלך באוויר!

פתח את ה-URL שקיבלת (משהו כמו `https://fleetguard-ai-adiyehuda.streamlit.app`)

---

## 🔍 בדיקה מהירה:

1. **דף הבית נטען?** ✅
2. **יש נתונים בטבלאות?** ✅
3. **טאב "תחזיות ML"** מציג R²=0.9638? ✅

**אם הכל OK** → מזל טוב! 🎉

**אם "המודל לא נטען"** → ראה פתרון למטה 👇

---

## 🐛 תיקון "המודל לא נטען"

### אם אתה רואה את ההודעה:
> "❌ המודל לא נטען. הרץ את המערכת AI קודם"

### בדוק:

1. **Logs** (Settings → Logs):
   - חפש: `[OK] Model loaded:` ✅
   - או: `[ERROR] Model not found:` ❌

2. **אם השגיאה היא path**:
   ```
   הקוד כבר תוקן! אם עדיין לא עובד:
   - Reboot the app (Settings → Reboot)
   - Clear cache (Settings → Clear cache)
   ```

3. **אם השגיאה היא "file not found"**:
   ```
   וודא שהקובץ קיים ב-GitHub:
   https://github.com/AdiYehuda2603/FleetGuardAI-/blob/main/FleetGuard/models/model.pkl
   ```

---

## 📞 עזרה נוספת?

**מדריך מלא**: קרא את `DEPLOY_TO_STREAMLIT_CLOUD.md`

**Logs**: Settings → Logs → חפש `[ERROR]`

**Reboot**: Settings → Reboot app

---

**הצלחה!** 🚀
