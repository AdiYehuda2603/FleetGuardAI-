# 🎯 מדריך: היסטוריית שיחות ותבניות פרויקטים

## ✅ מה הוספנו?

### 1. **טבלאות חדשות במסד הנתונים**
- ✅ `conversations` - שיחות (כל שיחה עם ID ייחודי)
- ✅ `chat_messages` - הודעות בשיחה
- ✅ `project_templates` - תבניות מוכנות מראש לדוחות

### 2. **5 תבניות ברירת מחדל**
1. **דוח רבעוני** - עלויות, תחזוקה, המלצות
2. **דוח שנתי** - דוח מקיף עם תובנות אסטרטגיות
3. **דוח תחזוקה חודשי** - טיפולים לפי רכב ומוסך
4. **תכנון גריטה** - ניתוח רכבים לגריטה
5. **ניתוח עלויות מעמיק** - אופטימיזציה וחיסכון

### 3. **פונקציות חדשות ב-DatabaseManager**

```python
# שמירת שיחות
db.save_conversation(conversation_id, title, template_id)
db.save_message(conversation_id, role, content)

# טעינת שיחות
db.get_conversation_history(conversation_id)  # הודעות של שיחה
db.get_all_conversations(limit=50)            # רשימת כל השיחות

# מחיקת שיחה
db.delete_conversation(conversation_id)

# ניהול תבניות
db.get_all_templates()
db.get_template(template_id)
db.save_template(template_data)
db.update_template_last_used(template_id)
db.delete_template(template_id)
```

### 4. **ChatManager - מנהל השיחות**

```python
from src.chat_manager import ChatManager

chat_mgr = ChatManager(db)

# יצירת שיחה חדשה
conv_id = chat_mgr.create_new_conversation(title="שיחה חדשה")

# טעינת שיחה
messages = chat_mgr.load_conversation(conv_id)

# שמירת הודעות
chat_mgr.save_user_message(conv_id, "השאלה שלי")
chat_mgr.save_assistant_message(conv_id, "התשובה")

# שימוש בתבנית
conv_id, prompt = chat_mgr.apply_template("TPL-QUARTERLY")
```

## 📊 איך להשתמש?

### דוגמה 1: שיחה רגילה עם שמירה

```python
import streamlit as st
from src.database_manager import DatabaseManager
from src.chat_manager import ChatManager
from src.ai_engine import FleetAIEngine

# אתחול
db = DatabaseManager()
chat_mgr = ChatManager(db)
ai = FleetAIEngine()

# יצירת/טעינת שיחה
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = chat_mgr.create_new_conversation()
    st.session_state.messages = []
else:
    # טעינת שיחה קיימת
    st.session_state.messages = chat_mgr.load_conversation(
        st.session_state.conversation_id
    )

# הצגת הודעות
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# קלט משתמש
if prompt := st.chat_input("שאלה?"):
    # שמירת שאלת המשתמש
    chat_mgr.save_user_message(st.session_state.conversation_id, prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # קבלת תשובה
    response = ai.ask_analyst(prompt)

    # שמירת תשובת ה-AI
    chat_mgr.save_assistant_message(st.session_state.conversation_id, response)
    st.session_state.messages.append({"role": "assistant", "content": response})
```

### דוגמה 2: שימוש בתבנית דוח רבעוני

```python
# לחיצה על כפתור "דוח רבעוני"
if st.button("📊 דוח רבעוני"):
    # יצירת שיחה חדשה מהתבנית
    conv_id, prompt = chat_mgr.apply_template("TPL-QUARTERLY")

    if prompt:
        # עדכון session state
        st.session_state.conversation_id = conv_id
        st.session_state.messages = []

        # שמירת הפרומפט
        chat_mgr.save_user_message(conv_id, prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # קבלת תשובה
        response = ai.ask_analyst(prompt)

        # שמירת התשובה
        chat_mgr.save_assistant_message(conv_id, response)
        st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()
```

### דוגמה 3: הצגת היסטוריית שיחות

```python
# Sidebar - רשימת שיחות
with st.sidebar:
    st.header("📜 היסטוריית שיחות")

    conversations = db.get_all_conversations(limit=20)

    for _, conv in conversations.iterrows():
        if st.button(
            f"{conv['title'][:30]}...",
            key=f"conv_{conv['conversation_id']}"
        ):
            # טעינת השיחה
            st.session_state.conversation_id = conv['conversation_id']
            st.session_state.messages = chat_mgr.load_conversation(
                conv['conversation_id']
            )
            st.rerun()
```

## 🎨 UI מומלץ ל-main.py

אני ממליץ להוסיף:

1. **Sidebar עם:**
   - כפתור "שיחה חדשה"
   - רשימת שיחות אחרונות (עם תאריכים)
   - כפתורי תבניות מהירות

2. **Tab 2 (צ'אט) משודרג עם:**
   - כותרת עם שם השיחה
   - כפתור "שמור שיחה זו"
   - כפתור "התחל שיחה חדשה"
   - תפריט תבניות מהיר

3. **Tab חדש "ניהול פרויקטים":**
   - רשימת כל התבניות
   - יצירת תבנית חדשה
   - עריכה/מחיקה של תבניות

## 🚀 השלבים הבאים

1. ✅ **הטבלאות נוצרו** (הרצת `chat_history_schema.py`)
2. ✅ **5 תבניות ברירת מחדל נוספו**
3. ✅ **DatabaseManager מעודכן** עם כל הפונקציות
4. ✅ **ChatManager מוכן**
5. ⏳ **צריך לעדכן את `main.py`** - להוסיף UI
6. ⏳ **בדיקה מלאה**

## 💡 טיפים

**עבור דוח רבעוני:**
```python
conv_id, prompt = chat_mgr.apply_template("TPL-QUARTERLY")
# prompt יהיה: "תן לי דוח רבעוני מלא: סיכום עלויות..."
```

**עבור דוח שנתי:**
```python
conv_id, prompt = chat_mgr.apply_template("TPL-ANNUAL")
# prompt יהיה: "תן לי דוח שנתי מקיף: סיכום עלויות שנתי..."
```

**יצירת תבנית מותאמת אישית:**
```python
custom_template = {
    'template_id': 'TPL-CUSTOM-01',
    'template_name': 'דוח מותאם שלי',
    'description': 'דוח מיוחד לצרכים שלי',
    'template_type': 'custom',
    'configuration': json.dumps({
        "prompt": "תן לי ניתוח של...",
        "sections": ["cost", "performance"],
        "date_range": "last_month"
    })
}
db.save_template(custom_template)
```

## 📝 המשך הפיתוח

אני יכול להמשיך ולהוסיף ל-`main.py`:
1. Sidebar עם היסטוריה
2. כפתורי תבניות מהירות
3. ממשק לניהול תבניות
4. סינון וחיפוש בשיחות

האם תרצה שאמשיך עם העדכון ל-`main.py`?
