import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- הגדרות עמוד ---
st.set_page_config(page_title="FleetGuard AI Pro", layout="wide", page_icon="🚛")

# --- לוגיקה ופונקציות עזר (המוח של המערכת) ---

def classify_item(description):
    """סיווג חכם של פריטים לקטגוריות על בסיס מילות מפתח"""
    desc = description.lower()
    if any(x in desc for x in ['צמיג', 'tires', 'pancher', 'איזון']):
        return 'צמיגים'
    elif any(x in desc for x in ['שמן', 'oil', 'filter', 'פילטר', 'טיפול']):
        return 'טיפול תקופתי'
    elif any(x in desc for x in ['בלם', 'brake', 'רפידות', 'צלחות']):
        return 'בלמים'
    elif any(x in desc for x in ['מצבר', 'battery', 'nura', 'נורה', 'פנס', 'חשמל']):
        return 'חשמל ותאורה'
    else:
        return 'כללי/אחר'

def load_data():
    """טעינת נתונים ועיבוד ראשוני"""
    # שימוש ב-DatabaseManager לניהול חיבור תקין
    from src.database_manager import DatabaseManager

    try:
        db = DatabaseManager()
        # טעינת חשבוניות
        df_inv = db.get_all_invoices()
        df_inv['date'] = pd.to_datetime(df_inv['date'])

        # טעינת שורות פירוט (חלקים)
        df_lines = db.get_invoice_lines()

        # הפעלת סיווג על כל השורות
        df_lines['category'] = df_lines['description'].apply(classify_item)

        return df_inv, df_lines
    except Exception as e:
        st.error(f"⚠️ שגיאה בטעינת נתונים: {str(e)}")
        return None, None

def calculate_fleet_stats(df_inv):
    """חישוב סטטיסטיקות מתקדמות לכל רכב (חיזוי)"""
    vehicle_stats = []
    
    for vid, group in df_inv.groupby('vehicle_id'):
        group = group.sort_values('date')
        
        if len(group) < 2:
            continue
            
        # חישוב קצב נסיעה (ק"מ ליום)
        last_date = group['date'].iloc[-1]
        first_date = group['date'].iloc[0]
        days_diff = (last_date - first_date).days
        
        last_km = group['odometer_km'].iloc[-1]
        first_km = group['odometer_km'].iloc[0]
        km_diff = last_km - first_km
        
        if days_diff > 0:
            avg_km_per_day = km_diff / days_diff
        else:
            avg_km_per_day = 0
            
        # חיזוי טיפול הבא (נניח כל 15,000 ק"מ)
        next_service_km = (int(last_km / 15000) + 1) * 15000
        km_remaining = next_service_km - last_km
        
        if avg_km_per_day > 0:
            days_to_service = km_remaining / avg_km_per_day
            predicted_date = last_date + timedelta(days=days_to_service)
        else:
            predicted_date = None
            
        vehicle_stats.append({
            'vehicle_id': vid,
            'avg_km_day': round(avg_km_per_day, 1),
            'last_km': last_km,
            'next_service_km': next_service_km,
            'predicted_date': predicted_date.date() if predicted_date else "לא ניתן לחשב"
        })
        
    return pd.DataFrame(vehicle_stats)

# --- טעינת הנתונים ---
df_invoices, df_lines = load_data()

# בדיקה שהנתונים נטענו בהצלחה
if df_invoices is None or df_lines is None:
    st.error("⚠️ לא נמצא קובץ נתונים! אנא הרץ קודם את `generate_data.py`.")
    st.stop()

df_stats = calculate_fleet_stats(df_invoices)

# --- ממשק משתמש ---
st.title("🚛 FleetGuard AI – מערכת ניהול ובקרה")

# לשוניות ניווט
tab1, tab2, tab3 = st.tabs(["📊 מבט על", "🔮 חיזוי ותחזוקה", "💰 ניתוח עלויות וספקים"])

# --- טאב 1: מבט על (KPIs) ---
with tab1:
    # מדדים ראשיים
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("סה'כ הוצאות השנה", f"₪{df_invoices['total'].sum():,.0f}")
    c2.metric("טיפולים שבוצעו", len(df_invoices))
    c3.metric("ממוצע לחשבונית", f"₪{df_invoices['total'].mean():,.0f}")
    c4.metric("רכבים פעילים", df_invoices['vehicle_id'].nunique())
    
    st.divider()
    
    # גרף הוצאות לאורך זמן
    st.subheader("מגמת הוצאות חודשית")
    df_monthly = df_invoices.set_index('date').resample('M')['total'].sum().reset_index()
    fig_line = px.line(df_monthly, x='date', y='total', markers=True, title="הוצאות לפי חודש")
    st.plotly_chart(fig_line, use_container_width=True)

    # התפלגות קטגוריות (פאי)
    st.subheader("לאן הולך הכסף? (חלוקה לקטגוריות)")
    # מחברים את המחיר מהשורות לקטגוריות
    cat_spend = df_lines.groupby('category')['line_total'].sum().reset_index()
    fig_pie = px.pie(cat_spend, values='line_total', names='category', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

# --- טאב 2: חיזוי ותחזוקה ---
with tab2:
    st.header("מערכת חיזוי טיפולים (Predictive Maintenance)")
    st.info("המערכת מנתחת את היסטוריית הקילומטרז' של כל רכב ומחשבת מתי יידרש הטיפול הבא.")
    
    # מציגים את הטבלה החכמה שיצרנו בפונקציה
    st.dataframe(
        df_stats.style.format({"avg_km_day": "{:.1f}", "last_km": "{:,.0f}", "next_service_km": "{:,.0f}"}),
        width="stretch"
    )
    
    # גרף שימוש ברכב
    st.subheader("מי " + "קורע" + " את הרכב? (קילומטרז' יומי ממוצע)")
    fig_bar = px.bar(df_stats.sort_values('avg_km_day', ascending=False), 
                     x='vehicle_id', y='avg_km_day', color='avg_km_day',
                     labels={'avg_km_day': 'ק"מ ליום', 'vehicle_id': 'רכב'})
    st.plotly_chart(fig_bar, use_container_width=True)

# --- טאב 3: ניתוח עלויות וספקים ---
with tab3:
    st.header("השוואת מחירים וספקים")
    
    # בחירת קטגוריה להשוואה
    selected_cat = st.selectbox("בחר קטגוריה להשוואה:", df_lines['category'].unique())
    
    # סינון הנתונים לפי הקטגוריה
    filtered_lines = df_lines[df_lines['category'] == selected_cat]
    
    # חיבור עם טבלת החשבוניות כדי לקבל את שם המוסך ואת התאריך
    # התיקון: הוספנו את 'date' לרשימת העמודות כאן למטה
    merged = pd.merge(filtered_lines, df_invoices[['invoice_no', 'workshop', 'date']], on='invoice_no')
    
    if not merged.empty:
        # חישוב מחיר ממוצע לפריט במוסכים שונים
        # אנו מסתכלים על unit_price כדי להשוות תפוחים לתפוחים
        price_comparison = merged.groupby('workshop')['unit_price'].mean().reset_index().sort_values('unit_price')
        
        st.subheader(f"מי המוסך הכי זול עבור {selected_cat}?")
        fig_compare = px.bar(price_comparison, x='workshop', y='unit_price', 
                             color='unit_price', color_continuous_scale='RdYlGn_r', # ירוק=זול, אדום=יקר
                             title=f"מחיר יחידה ממוצע: {selected_cat}")
        st.plotly_chart(fig_compare, use_container_width=True)
        
        st.write("פירוט עסקאות אחרונות בקטגוריה זו:")
        # עכשיו המיון יעבוד כי העמודה date קיימת
        st.dataframe(merged[['date', 'workshop', 'description', 'unit_price', 'qty', 'line_total']].sort_values('date', ascending=False).head(5), width="stretch")
    else:
        st.warning("אין מספיק נתונים לקטגוריה זו.")