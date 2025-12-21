# ✅ תיקון ניווט - FleetGuard

## הבעיה:
`st.switch_page()` לא עבד עם שמות קבצים עם אימוג'ים או עם נתיבים.

## הפתרון:
שימוש ב-`st.rerun()` עם `query_params` במקום `st.switch_page()`.

## איך זה עובד עכשיו:

### 1. עמוד כניסה והרשמה ב-`main.py`
- אם המשתמש לא מחובר, `main.py` מציג את עמוד הכניסה ישירות
- ניווט בין כניסה להרשמה דרך `query_params`
- אחרי התחברות מוצלחת, `query_params` מתנקה והדשבורד מוצג

### 2. שימוש ב-query_params:
```python
# מעבר לעמוד הרשמה
st.query_params.page = "register"
st.rerun()

# מעבר לעמוד כניסה
st.query_params.page = "login"
st.rerun()

# חזרה לדשבורד
st.query_params.clear()
st.rerun()
```

### 3. קישורים:
```markdown
[הרשם כאן](?page=register)
[התחבר כאן](?page=login)
```

## יתרונות:
- ✅ עובד בלי בעיות עם Streamlit
- ✅ פשוט יותר - הכל ב-`main.py`
- ✅ לא צריך `st.switch_page()`
- ✅ ניווט חלק עם query params

---

**תוקן ב:** 2025-01-XX  
**סטטוס:** ✅ עובד!

