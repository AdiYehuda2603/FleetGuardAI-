# Import warning suppression FIRST (before streamlit)
import sys
import warnings
import logging
import os

# Suppress all warnings before importing anything
warnings.filterwarnings('ignore')
os.environ['STREAMLIT_LOGGER_LEVEL'] = 'error'

# Configure logging to suppress Streamlit warnings
logging.basicConfig(level=logging.ERROR)
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime.scriptrunner').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime.caching').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime.state').setLevel(logging.ERROR    )

# Now import streamlit and other modules
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

# טעינת משתני סביבה מקובץ .env
load_dotenv()

# ייבוא המודולים שבנינו בתיקיית src
try:
    from src.database_manager import DatabaseManager
    from src.ai_engine import FleetAIEngine
    from src.auth_manager import AuthManager
except ImportError:
    st.error("❌ לא מצליח למצוא את תיקיית src. וודא שאתה מריץ את הפקודה מתיקיית FleetGuard.")
    st.stop()

# אתחול מנהל Authentication
auth = AuthManager()

# בדיקת Authentication - אם לא מחובר, הצג עמוד כניסה
if not auth.is_authenticated():
    # הצג עמוד כניסה ישירות
    st.set_page_config(
        page_title="כניסה - FleetGuard",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    st.title("🔐 כניסה למערכת")
    st.markdown("---")
    
    # בדיקת query params לניווט
    query_params = st.query_params
    show_register = query_params.get("page") == "register"
    
    if show_register:
        # הצג עמוד הרשמה
        st.title("📝 הרשמה למערכת")
        st.markdown("---")
        
        with st.form("register_form"):
            st.subheader("יצירת חשבון חדש")
            
            full_name = st.text_input("שם מלא", placeholder="הזן שם מלא (אופציונלי)")
            username = st.text_input("שם משתמש *", placeholder="הזן שם משתמש")
            email = st.text_input("כתובת אימייל *", placeholder="example@email.com")
            password = st.text_input("סיסמה *", type="password", placeholder="לפחות 6 תווים")
            password_confirm = st.text_input("אישור סיסמה *", type="password", placeholder="הזן שוב את הסיסמה")
            
            st.caption("* שדות חובה")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                submit_button = st.form_submit_button("הרשם", use_container_width=True)
            with col2:
                if st.form_submit_button("כבר רשום? התחבר כאן", use_container_width=True):
                    st.query_params.clear()
                    st.rerun()
            
            if submit_button:
                if not username or not email or not password:
                    st.error("❌ נא למלא את כל השדות החובה")
                elif len(password) < 6:
                    st.error("❌ הסיסמה חייבת להכיל לפחות 6 תווים")
                elif password != password_confirm:
                    st.error("❌ הסיסמאות לא תואמות")
                else:
                    success, message = auth.register_user(username, email, password, full_name)
                    if success:
                        st.success(f"✅ {message}")
                        st.info("אנא התחבר עם הפרטים שיצרת")
                        import time
                        time.sleep(2)
                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        st.markdown("---")
        st.markdown("כבר רשום? [התחבר כאן](?page=login)")
    else:
        # הצג עמוד כניסה
        with st.form("login_form"):
            st.subheader("התחברות")
            
            username = st.text_input("שם משתמש", placeholder="הזן שם משתמש")
            password = st.text_input("סיסמה", type="password", placeholder="הזן סיסמה")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                submit_button = st.form_submit_button("התחבר", use_container_width=True)
            with col2:
                if st.form_submit_button("עדיין לא רשום? הרשם כאן", use_container_width=True):
                    st.query_params.page = "register"
                    st.rerun()
            
            if submit_button:
                if username and password:
                    success, message, user_data = auth.login_user(username, password)
                    if success:
                        st.session_state['authenticated'] = True
                        st.session_state['user_data'] = user_data
                        st.success(f"✅ {message}")
                        st.info(f"ברוך הבא, {user_data.get('full_name', user_data.get('username', ''))}!")
                        import time
                        time.sleep(1)
                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.warning("⚠️ נא למלא את כל השדות")
        
        st.markdown("---")
        st.markdown("עדיין לא רשום? [הרשם כאן](?page=register)")
    
    st.stop()

# --- הגדרת עמוד (Page Config) ---
# רק אם המשתמש מחובר
st.set_page_config(
    page_title="FleetGuard Pro",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- עיצוב CSS לתמיכה בעברית (RTL) ---
st.markdown("""
<style>
    .stApp { direction: rtl; }
    h1, h2, h3, p, div { text-align: right; }
    .stMetric { text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- כותרת ראשית ---
st.title("🚛 FleetGuard - מערכת לניהול צי רכב חכם")
st.markdown("---")

# --- טעינת נתונים ---
@st.cache_data
def load_data():
    try:
        db = DatabaseManager()
        # שליפת נתונים מחוברים (חשבונית + שורות)
        df_full = db.get_full_view()
        # שליפת חשבוניות בלבד לסיכומים
        df_invoices = db.get_all_invoices()
        return df_full, df_invoices
    except Exception as e:
        return None, None

df_full, df_invoices = load_data()

# יצירת instance של DatabaseManager לשימוש גלובלי
db = DatabaseManager()

# ===== Email Auto-Sync (Silent Background) =====
# Runs automatically when dashboard loads if EMAIL_FETCH_ENABLED=true
if os.getenv('EMAIL_FETCH_ENABLED', 'false').lower() == 'true':
    try:
        from src.email_fetcher import EmailInvoiceProcessor

        processor = EmailInvoiceProcessor()
        result = processor.sync_emails(silent=True)

        # Show toast notification if new invoices found
        if result['new_invoices'] > 0:
            st.toast(f"📧 {result['new_invoices']} חשבוניות חדשות מאימייל!", icon="✅")
            st.cache_data.clear()  # Refresh cache to show new data
    except Exception as e:
        # Silent failure - don't block dashboard loading
        # Error will be visible in email sync tab if user checks
        pass

# בדיקה שהנתונים נטענו בהצלחה
if df_full is None or df_invoices is None:
    st.error("⚠️ לא נמצא קובץ נתונים! אנא הרץ קודם את `generate_data.py`.")
    st.info("💡 הרץ את הפקודה: `python generate_data.py`")
    st.stop()

# בדיקה שהנתונים לא ריקים (רק אם הם לא None)
if df_invoices is not None and df_invoices.empty:
    st.warning("⚠️ מסד הנתונים ריק. אנא הוסף נתונים דרך לשונית 'ניהול נתונים'.")
    st.stop()

# אם עדיין None למרות הבדיקות, יצור DataFrame ריק
if df_invoices is None:
    df_invoices = pd.DataFrame()
if df_full is None:
    df_full = pd.DataFrame()

# --- סרגל צד (Sidebar) ---
with st.sidebar:
    # מידע משתמש
    user_data = auth.get_current_user()
    st.header(f"👤 {user_data.get('full_name', user_data.get('username', 'משתמש'))}")
    
    if st.button("🚪 התנתק", use_container_width=True):
        auth.logout()
    
    st.markdown("---")
    
    st.header("⚙️ הגדרות וסינון")
    
    # מפתח OpenAI - נטען אוטומטית מ-.env או session
    # לא מוצג למשתמש כדי לשמור על אבטחה
    api_key = auth.get_api_key()
    if not api_key:
        # נסה לטעון מ-.env
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if api_key:
            auth.set_api_key(api_key)
    
    if api_key:
        st.success("✅ מפתח API נטען")
    else:
        st.warning("⚠️ מפתח API לא נמצא. הוסף ל-.env או הזן בהגדרות")
        # אפשרות להזנה חד-פעמית (רק לסשן הנוכחי)
        with st.expander("🔐 הגדר מפתח API (זמני)"):
            temp_key = st.text_input("מפתח OpenAI API", type="password", placeholder="sk-...", key="temp_api_key")
            if temp_key:
                auth.set_api_key(temp_key)
                st.success("✅ מפתח נשמר לסשן זה בלבד")
    
    st.markdown("---")
    
    # פילטרים
    st.subheader("🔍 סינון נתונים")
    if df_invoices is not None and not df_invoices.empty and 'workshop' in df_invoices.columns:
        selected_garages = st.multiselect("בחר מוסכים", df_invoices['workshop'].unique())
    else:
        selected_garages = []
    
    if df_invoices is not None and not df_invoices.empty and 'make_model' in df_invoices.columns:
        selected_models = st.multiselect("בחר דגמי רכב", df_invoices['make_model'].unique())
    else:
        selected_models = []
    
    # החלת פילטרים
    if df_invoices is not None and not df_invoices.empty:
        filtered_df = df_invoices.copy()
        if selected_garages:
            filtered_df = filtered_df[filtered_df['workshop'].isin(selected_garages)]
        if selected_models:
            filtered_df = filtered_df[filtered_df['make_model'].isin(selected_models)]
    else:
        filtered_df = pd.DataFrame()

# --- לשוניות ראשיות (Tabs) ---
tab1, tab2, tab_rules, tab3, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📊 לוח בקרה (Dashboard)",
    "🤖 צ'אט אנליסט (AI)",
    "🚨 התראות חכמות (Rules Engine)",
    "🎯 תחזיות ML (AI Predictions)",
    "📋 נתונים גולמיים",
    "⚙️ ניהול נתונים",
    "🔍 דפוסי תחזוקה",
    "🚗 ניהול הצי",
    "💼 תובנות אסטרטגיות"
])

# === לשונית 1: דשבורד ===
with tab1:
    # בדיקה שהנתונים קיימים
    if filtered_df.empty:
        st.warning("⚠️ אין נתונים להצגה. אנא הוסף נתונים דרך לשונית 'ניהול נתונים'.")
    else:
        # שורת מדדים (KPIs)
        c1, c2, c3, c4 = st.columns(4)
        
        total_spend = filtered_df['total'].sum() if 'total' in filtered_df.columns else 0
        total_km = filtered_df['odometer_km'].max() if 'odometer_km' in filtered_df.columns else 0
        avg_invoice = filtered_df['total'].mean() if 'total' in filtered_df.columns else 0
        vehicle_count = filtered_df['vehicle_id'].nunique() if 'vehicle_id' in filtered_df.columns else 0

        c1.metric("💰 סה\"כ הוצאות", f"₪{total_spend:,.0f}")
        c2.metric("🚘 רכבים פעילים", vehicle_count)
        c3.metric("🧾 עלות ממוצעת לטיפול", f"₪{avg_invoice:,.0f}")
        c4.metric("🔧 סה\"כ חשבוניות", len(filtered_df))

        st.markdown("---")

        # גרפים - שורה עליונה
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            st.subheader("💸 הוצאות לפי מוסך")
            if 'workshop' in filtered_df.columns and 'total' in filtered_df.columns:
                cost_by_garage = filtered_df.groupby('workshop')['total'].sum().reset_index()
                fig_garage = px.bar(cost_by_garage, x='workshop', y='total', text_auto='.2s', color='total')
                fig_garage.update_layout(xaxis_title="מוסך", yaxis_title="סה\"כ ש\"ח")
                st.plotly_chart(fig_garage, width='stretch')

                # תובנות AI
                from src.chart_insights_generator import ChartInsightsGenerator, render_insights_box
                insights_gen = ChartInsightsGenerator()
                insights_data = insights_gen.analyze_workshop_costs(filtered_df)
                render_insights_box(insights_data)
            else:
                st.info("אין נתונים להצגה")

        with row1_col2:
            st.subheader("📈 מגמת הוצאות לאורך זמן")
            if 'date' in filtered_df.columns and 'total' in filtered_df.columns:
                # המרת תאריך ואיגוד לפי חודש
                filtered_df_with_date = filtered_df.copy()
                filtered_df_with_date['date'] = pd.to_datetime(filtered_df_with_date['date'])
                cost_over_time = filtered_df_with_date.set_index('date').resample('ME')['total'].sum().reset_index()
                fig_time = px.line(cost_over_time, x='date', y='total', markers=True)
                fig_time.update_layout(xaxis_title="תאריך", yaxis_title="הוצאה חודשית")
                st.plotly_chart(fig_time, width='stretch')

                # תובנות AI
                from src.chart_insights_generator import ChartInsightsGenerator, render_insights_box
                insights_gen = ChartInsightsGenerator()
                insights_data = insights_gen.analyze_cost_trends(filtered_df_with_date)
                render_insights_box(insights_data)
            else:
                st.info("אין נתונים להצגה")

        # גרפים - שורה תחתונה
        row2_col1, row2_col2 = st.columns(2)
        
        with row2_col1:
            st.subheader("🚗 הוצאות לפי דגם רכב")
            if 'make_model' in filtered_df.columns and 'total' in filtered_df.columns:
                fig_pie = px.pie(filtered_df, values='total', names='make_model', hole=0.4)
                st.plotly_chart(fig_pie, width='stretch')

                # תובנות AI
                from src.chart_insights_generator import ChartInsightsGenerator, render_insights_box
                insights_gen = ChartInsightsGenerator()
                insights_data = insights_gen.analyze_vehicle_model_costs(filtered_df)
                render_insights_box(insights_data)
            else:
                st.info("אין נתונים להצגה")

        with row2_col2:
            st.subheader("⚠️ זיהוי חריגות (Scatter Plot)")
            if 'odometer_km' in filtered_df.columns and 'total' in filtered_df.columns:
                # קשר בין קילומטראז' לעלות טיפול
                fig_scatter = px.scatter(filtered_df, x='odometer_km', y='total', color='kind' if 'kind' in filtered_df.columns else None, hover_data=['plate', 'workshop'] if 'plate' in filtered_df.columns and 'workshop' in filtered_df.columns else None)
                st.plotly_chart(fig_scatter, width='stretch')

                # תובנות AI
                from src.chart_insights_generator import ChartInsightsGenerator, render_insights_box
                insights_gen = ChartInsightsGenerator()
                insights_data = insights_gen.analyze_scatter_outliers(filtered_df)
                render_insights_box(insights_data)
            else:
                st.info("אין נתונים להצגה")

# === לשונית 2: AI עם היסטוריה ===
with tab2:
    from src.chat_ui_upgrade import render_chat_with_history
    render_chat_with_history(db, auth)

# === לשונית Rules Engine: התראות חכמות ===
with tab_rules:
    st.header("🚨 התראות חכמות - Rules Engine")
    st.caption("מערכת התראות אוטומטית מבוססת כללים קבועים - משלימה את חיזויי ה-ML")
    st.markdown("---")

    try:
        from src.rules_engine import FleetRulesEngine

        # Initialize Rules Engine
        rules_engine = FleetRulesEngine(db)

        # Get list of all vehicles
        vehicles_df = db.get_vehicle_with_stats()

        if not vehicles_df.empty:
            # Vehicle selection filter
            vehicle_list = ["כל הרכבים"] + vehicles_df['vehicle_id'].tolist()
            selected_vehicle_filter = st.selectbox(
                "בחר רכב לבדיקה",
                vehicle_list,
                key="rules_engine_vehicle_select"
            )

            # Evaluate rules
            if selected_vehicle_filter == "כל הרכבים":
                with st.spinner("מעריך כללים עבור כל הצי..."):
                    results = rules_engine.evaluate_all_rules()
            else:
                with st.spinner(f"מעריך כללים עבור {selected_vehicle_filter}..."):
                    results = rules_engine.evaluate_all_rules(vehicle_id=selected_vehicle_filter)

            # Summary statistics at top
            st.subheader("📊 סטטיסטיקת התראות")
            col1, col2, col3, col4 = st.columns(4)

            stats = results['stats']
            col1.metric("🚨 דחופות (URGENT)", stats.get('urgent_count', 0))
            col2.metric("⚠️ אזהרות (WARNING)", stats.get('warning_count', 0))
            col3.metric("ℹ️ מידע (INFO)", stats.get('info_count', 0))
            col4.metric("🔍 רכבים נבדקו", stats.get('vehicles_checked', 0))

            st.markdown("---")

            # Separate alerts by severity
            alerts = results['alerts']
            urgent_alerts = [a for a in alerts if a['severity'] == 'URGENT']
            warning_alerts = [a for a in alerts if a['severity'] == 'WARNING']
            info_alerts = [a for a in alerts if a['severity'] == 'INFO']

            # Display URGENT alerts
            if urgent_alerts:
                st.error(f"🚨 **{len(urgent_alerts)} התראות דחופות** - טיפול מיידי נדרש!")

                for alert in urgent_alerts:
                    with st.expander(f"🚗 {alert['plate']} - {alert['message']}", expanded=False):
                        st.markdown(f"**רכב:** {alert['vehicle_id']}")
                        st.markdown(f"**כלל:** {alert['rule_name']}")
                        st.markdown(f"**המלצה:** {alert['recommendation']}")

                        st.markdown("**פרטים טכניים:**")
                        st.json(alert['details'])
            else:
                st.success("✅ אין התראות דחופות - כל הרכבים בסדר")

            st.markdown("---")

            # Display WARNING alerts
            if warning_alerts:
                st.warning(f"⚠️ **{len(warning_alerts)} אזהרות** - מומלץ לטפל בהקדם")

                for alert in warning_alerts:
                    with st.expander(f"🚗 {alert['plate']} - {alert['message']}"):
                        st.markdown(f"**רכב:** {alert['vehicle_id']}")
                        st.markdown(f"**כלל:** {alert['rule_name']}")
                        st.markdown(f"**המלצה:** {alert['recommendation']}")

                        st.markdown("**פרטים טכניים:**")
                        st.json(alert['details'])

            st.markdown("---")

            # Display INFO alerts
            if info_alerts:
                st.info(f"ℹ️ **{len(info_alerts)} התראות מידע** - למעקב ותכנון")

                with st.expander("הצג התראות מידע"):
                    for alert in info_alerts:
                        st.markdown(f"**🚗 {alert['plate']}** - {alert['message']}")
                        st.markdown(f"   └─ {alert['recommendation']}")
                        st.markdown("---")

            # Custom Alerts Section
            st.markdown("---")
            st.subheader("📌 התראות מותאמות אישית")

            col_custom1, col_custom2 = st.columns([2, 1])

            with col_custom1:
                with st.expander("➕ הוסף התראה מותאמת אישית", expanded=False):
                    st.markdown("**צור התראה מותאמת אישית לרכב ספציפי**")

                    # Vehicle selection for custom alert
                    custom_vehicle = st.selectbox(
                        "בחר רכב",
                        vehicles_df['vehicle_id'].tolist(),
                        key="custom_alert_vehicle"
                    )

                    # Alert details
                    custom_title = st.text_input(
                        "כותרת ההתראה",
                        placeholder="לדוגמה: ביטוח מסתיים בקרוב",
                        key="custom_alert_title"
                    )

                    custom_message = st.text_area(
                        "תוכן ההתראה",
                        placeholder="תיאור מפורט של ההתראה...",
                        key="custom_alert_message"
                    )

                    col_sev, col_date = st.columns(2)

                    with col_sev:
                        custom_severity = st.selectbox(
                            "רמת חומרה",
                            ["INFO", "WARNING", "URGENT"],
                            key="custom_alert_severity"
                        )

                    with col_date:
                        custom_due_date = st.date_input(
                            "תאריך יעד (אופציונלי)",
                            value=None,
                            key="custom_alert_due_date"
                        )

                    custom_notes = st.text_input(
                        "הערות נוספות (אופציונלי)",
                        key="custom_alert_notes"
                    )

                    if st.button("✅ שמור התראה", key="save_custom_alert"):
                        if custom_title and custom_message:
                            try:
                                alert_data = {
                                    'vehicle_id': custom_vehicle,
                                    'alert_title': custom_title,
                                    'alert_message': custom_message,
                                    'severity': custom_severity,
                                    'created_by': st.session_state.get('username', 'system'),
                                    'due_date': str(custom_due_date) if custom_due_date else None,
                                    'notes': custom_notes if custom_notes else None
                                }

                                alert_id = db.add_custom_alert(alert_data)
                                st.success(f"✅ ההתראה נשמרה בהצלחה! (ID: {alert_id})")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ שגיאה בשמירת ההתראה: {str(e)}")
                        else:
                            st.warning("⚠️ אנא מלא כותרת ותוכן להתראה")

            with col_custom2:
                # Display count of custom alerts
                try:
                    all_custom_alerts = db.get_custom_alerts(active_only=True)
                    st.metric("📌 התראות מותאמות פעילות", len(all_custom_alerts))
                except:
                    st.metric("📌 התראות מותאמות פעילות", 0)

            # Display existing custom alerts
            with st.expander("📋 נהל התראות מותאמות אישית", expanded=False):
                try:
                    custom_alerts_df = db.get_custom_alerts(active_only=True)

                    if not custom_alerts_df.empty:
                        for idx, alert in custom_alerts_df.iterrows():
                            severity_emoji = {
                                'URGENT': '🚨',
                                'WARNING': '⚠️',
                                'INFO': 'ℹ️'
                            }

                            col_a, col_b = st.columns([4, 1])

                            with col_a:
                                st.markdown(f"{severity_emoji.get(alert['severity'], '📌')} **{alert['alert_title']}** - {alert['vehicle_id']}")
                                st.caption(f"{alert['alert_message']}")
                                if alert['due_date']:
                                    st.caption(f"📅 תאריך יעד: {alert['due_date']}")

                            with col_b:
                                if st.button("🗑️ מחק", key=f"delete_custom_{alert['alert_id']}"):
                                    try:
                                        db.delete_custom_alert(alert['alert_id'])
                                        st.success("✅ ההתראה נמחקה")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ שגיאה: {str(e)}")

                            st.markdown("---")
                    else:
                        st.info("ℹ️ אין התראות מותאמות אישית")
                except Exception as e:
                    st.error(f"❌ שגיאה בטעינת התראות: {str(e)}")

            # Show rule thresholds
            st.markdown("---")
            st.subheader("⚙️ הגדרות כללים")

            with st.expander("הצג ספי כללים נוכחיים"):
                thresholds = rules_engine.get_rule_thresholds()

                st.markdown("**תחזוקה מאולצת:**")
                st.write(f"- מקסימום ק\"מ: {thresholds['maintenance_overdue']['km_threshold']:,}")
                st.write(f"- מקסימום ימים: {thresholds['maintenance_overdue']['days_threshold']}")

                st.markdown("**חריגות עלות:**")
                st.write(f"- מכפיל: {thresholds['cost_anomaly']['multiplier']}x מעל ממוצע")

                st.markdown("**אזהרת פרישה:**")
                st.write(f"- ימים עד פרישה: < {thresholds['retirement_warning']['days_threshold']}")
                st.write(f"- גיל רכב: > {thresholds['retirement_warning']['age_years']} שנים")
                st.write(f"- ק\"מ מקסימלי: > {thresholds['retirement_warning']['km_threshold']:,}")

                st.markdown("**ניצולת גבוהה:**")
                st.write(f"- ק\"מ לחודש: > {thresholds['high_utilization']['km_per_month_threshold']:,}")

                st.markdown("**איכות מוסך:**")
                st.write(f"- עלייה מעל ממוצע: > {int(thresholds['workshop_quality']['cost_increase_threshold'] * 100)}%")

            # Explanation section
            st.markdown("---")
            st.subheader("ℹ️ מהו Rules Engine?")
            st.markdown("""
            **Rules Engine** הוא מערכת התראות מבוססת כללים קבועים המשלימה את חיזויי ה-ML:

            - **ML (Machine Learning)**: מנתח נתונים היסטוריים ומחזה עלויות עתידיות
            - **Rules Engine**: אוכף מדיניות ארגונית ומזהה הפרות בזמן אמת

            **דוגמה לשילוב:**
            - 🤖 **ML אומר**: "הרכב צפוי לעלות ₪450 בחודש הבא"
            - 🚨 **Rules אומר**: "הרכב עבר 12,000 ק\"מ ללא תחזוקה - הפרת מדיניות!"

            **יתרון**: ML מזהה מגמות, Rules מאכפים סטנדרטים. יחד - מערכת מושלמת! 🎯
            """)

        else:
            st.warning("⚠️ אין נתוני רכבים זמינים")

    except Exception as e:
        st.error(f"❌ שגיאה בטעינת Rules Engine: {str(e)}")
        st.exception(e)

# === לשונית 3: תחזיות ML (טאב חדש!) ===
with tab3:
    st.header("🎯 תחזיות ML - GradientBoosting Model")
    st.caption("תחזיות עלות תחזוקה בזמן אמת מבוססות על המודל שאימן Agent E")
    st.markdown("---")

    try:
        from src.ml_predictor import MLPredictor

        # טעינת מודל
        predictor = MLPredictor()

        if predictor.model:
            # מידע על המודל
            model_info = predictor.get_model_info()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🤖 מודל", model_info['model_name'])
            col2.metric("🎯 R² Score", f"{model_info['test_r2']:.4f}")
            col3.metric("📊 RMSE", f"₪{model_info['rmse']:.2f}")
            col4.metric("📉 MAE", f"₪{model_info['mae']:.2f}")

            st.markdown("---")

            # תת-טאבים
            subtab1, subtab2, subtab3 = st.tabs([
                "🚗 תחזית לרכב בודד",
                "🚛 תחזית לכל הצי",
                "📊 השוואה בין רכבים"
            ])

            # תת-טאב 1: תחזית לרכב בודד
            with subtab1:
                st.subheader("🚗 תחזית עלות חודשית לרכב")

                # בחירת רכב
                vehicles_list = db.get_all_vehicles()
                if not vehicles_list.empty:
                    vehicle_ids = vehicles_list['vehicle_id'].tolist()
                    selected_vehicle = st.selectbox("בחר רכב", vehicle_ids, key="ml_predictions_vehicle_select")

                    if st.button("🔮 חזה עלות", type="primary"):
                        with st.spinner("מחשב תחזית..."):
                            # שליפת נתוני רכב
                            from src.agents.feature_engineer_agent import FeatureEngineer
                            feature_agent = FeatureEngineer()

                            try:
                                # קריאת הפיצ'רים הקיימים
                                import pandas as pd
                                features_path = "data/processed/features.csv"
                                if os.path.exists(features_path):
                                    features_df = pd.read_csv(features_path)
                                    vehicle_features = features_df[features_df['vehicle_id'] == selected_vehicle]

                                    if not vehicle_features.empty:
                                        vehicle_data = vehicle_features.iloc[0].to_dict()

                                        # תחזית
                                        prediction = predictor.predict_vehicle_cost(vehicle_data)

                                        if 'error' not in prediction:
                                            st.success("✅ תחזית הושלמה!")

                                            # הצגת תוצאות
                                            col1, col2, col3 = st.columns(3)

                                            with col1:
                                                st.metric(
                                                    "💰 עלות חודשית צפויה",
                                                    f"₪{prediction['predicted_cost']:.2f}"
                                                )

                                            with col2:
                                                st.metric(
                                                    "📊 טווח ביטחון (נמוך)",
                                                    f"₪{prediction['confidence_interval']['lower']:.2f}"
                                                )

                                            with col3:
                                                st.metric(
                                                    "📊 טווח ביטחון (גבוה)",
                                                    f"₪{prediction['confidence_interval']['upper']:.2f}"
                                                )

                                            # עלות שנתית
                                            annual_cost = prediction['predicted_cost'] * 12
                                            st.info(f"📅 **עלות שנתית צפויה:** ₪{annual_cost:,.2f}")

                                            # השוואה לממוצע
                                            fleet_with_features = features_df.copy()
                                            comparison = predictor.compare_vehicle_to_fleet(
                                                selected_vehicle,
                                                fleet_with_features
                                            )

                                            if 'error' not in comparison:
                                                st.markdown("### 📊 השוואה לצי")

                                                col1, col2 = st.columns(2)

                                                with col1:
                                                    st.metric(
                                                        "ממוצע צי",
                                                        f"₪{comparison['fleet_average']:.2f}"
                                                    )
                                                    st.metric(
                                                        "חציון צי",
                                                        f"₪{comparison['fleet_median']:.2f}"
                                                    )

                                                with col2:
                                                    diff = comparison['difference_from_avg']
                                                    diff_pct = comparison['difference_percent']

                                                    if comparison['status'] == 'above_average':
                                                        st.warning(f"⚠️ **מעל הממוצע ב-{diff_pct}%**")
                                                        st.caption(f"הרכב יקר ב-₪{diff:.2f} מהממוצע")
                                                    else:
                                                        st.success(f"✅ **מתחת לממוצע ב-{abs(diff_pct)}%**")
                                                        st.caption(f"הרכב זול ב-₪{abs(diff):.2f} מהממוצע")

                                                    st.metric(
                                                        "אחוזון",
                                                        f"{comparison['percentile']:.1f}%",
                                                        help="כמה אחוז מהרכבים זולים יותר"
                                                    )

                                                # === ML vs Rules Engine Comparison ===
                                                st.markdown("---")
                                                st.markdown("### 🔀 השוואה: חיזוי ML לעומת Rules Engine")
                                                st.caption("מערכת היברידית: ML מנבא עלויות, Rules מאכף מדיניות")

                                                try:
                                                    from src.rules_engine import FleetRulesEngine
                                                    rules_engine = FleetRulesEngine(db)

                                                    # Evaluate rules for this specific vehicle
                                                    vehicle_alerts = rules_engine.evaluate_all_rules(vehicle_id=selected_vehicle)

                                                    col_ml, col_rules = st.columns(2)

                                                    with col_ml:
                                                        st.markdown("**🤖 חיזוי ML (Data-Driven)**")
                                                        st.metric("עלות חודשית צפויה", f"₪{prediction['predicted_cost']:.2f}")
                                                        st.caption("מבוסס על ניתוח נתונים היסטוריים")

                                                    with col_rules:
                                                        st.markdown("**📋 Rules Engine (Policy-Driven)**")
                                                        urgent_count = vehicle_alerts['stats'].get('urgent_count', 0)
                                                        warning_count = vehicle_alerts['stats'].get('warning_count', 0)

                                                        if urgent_count > 0:
                                                            st.error(f"🚨 {urgent_count} התראות דחופות")
                                                            st.caption("דרושה תשומת לב מיידית!")
                                                        elif warning_count > 0:
                                                            st.warning(f"⚠️ {warning_count} אזהרות")
                                                            st.caption("מומלץ לטפל בהקדם")
                                                        else:
                                                            st.success("✅ אין התראות פעילות")
                                                            st.caption("הרכב עומד בסטנדרטים")

                                                    # Show specific alerts if any
                                                    if vehicle_alerts['alerts']:
                                                        with st.expander("הצג התראות Rules Engine לרכב זה"):
                                                            for alert in vehicle_alerts['alerts']:
                                                                severity_icon = "🚨" if alert['severity'] == 'URGENT' else "⚠️" if alert['severity'] == 'WARNING' else "ℹ️"
                                                                st.markdown(f"{severity_icon} **{alert['message']}**")
                                                                st.markdown(f"   └─ {alert['recommendation']}")
                                                                st.markdown("---")

                                                    # Quick add custom alert
                                                    with st.expander("➕ הוסף התראה מהירה לרכב זה"):
                                                        quick_title = st.text_input(
                                                            "כותרת",
                                                            key=f"quick_alert_title_{selected_vehicle}",
                                                            placeholder="לדוגמה: ביטוח מסתיים"
                                                        )
                                                        quick_message = st.text_input(
                                                            "תוכן",
                                                            key=f"quick_alert_msg_{selected_vehicle}",
                                                            placeholder="פרטים..."
                                                        )
                                                        quick_sev = st.selectbox(
                                                            "חומרה",
                                                            ["INFO", "WARNING", "URGENT"],
                                                            key=f"quick_alert_sev_{selected_vehicle}"
                                                        )

                                                        if st.button("💾 שמור", key=f"quick_alert_save_{selected_vehicle}"):
                                                            if quick_title and quick_message:
                                                                try:
                                                                    db.add_custom_alert({
                                                                        'vehicle_id': selected_vehicle,
                                                                        'alert_title': quick_title,
                                                                        'alert_message': quick_message,
                                                                        'severity': quick_sev,
                                                                        'created_by': st.session_state.get('username', 'system')
                                                                    })
                                                                    st.success("✅ התראה נוספה!")
                                                                    st.rerun()
                                                                except Exception as e:
                                                                    st.error(f"❌ שגיאה: {str(e)}")
                                                            else:
                                                                st.warning("⚠️ מלא כותרת ותוכן")

                                                except Exception as rules_error:
                                                    st.warning(f"⚠️ לא ניתן לטעון Rules Engine: {str(rules_error)}")

                                        else:
                                            st.error(f"❌ {prediction['error']}")
                                    else:
                                        st.warning(f"⚠️ לא נמצאו פיצ'רים לרכב {selected_vehicle}")
                                else:
                                    st.error("❌ קובץ פיצ'רים לא נמצא. הרץ את המערכת AI קודם.")

                            except Exception as e:
                                st.error(f"❌ שגיאה: {str(e)}")
                else:
                    st.warning("⚠️ אין רכבים במערכת")

            # תת-טאב 2: תחזית לכל הצי
            with subtab2:
                st.subheader("🚛 תחזיות לכל הצי")

                if st.button("🔮 חזה עלויות לכל הצי", type="primary"):
                    with st.spinner("מחשב תחזיות..."):
                        try:
                            features_path = "data/processed/features.csv"
                            if os.path.exists(features_path):
                                import pandas as pd
                                features_df = pd.read_csv(features_path)

                                # תחזיות
                                predictions_df = predictor.predict_fleet(features_df)

                                if not predictions_df.empty:
                                    st.success(f"✅ תחזיות הושלמו ל-{len(predictions_df)} רכבים!")

                                    # סטטיסטיקות
                                    col1, col2, col3, col4 = st.columns(4)

                                    col1.metric(
                                        "💰 סה\"כ חודשי צפוי",
                                        f"₪{predictions_df['predicted_monthly_cost'].sum():,.0f}"
                                    )
                                    col2.metric(
                                        "📊 ממוצע לרכב",
                                        f"₪{predictions_df['predicted_monthly_cost'].mean():,.2f}"
                                    )
                                    col3.metric(
                                        "📉 מינימום",
                                        f"₪{predictions_df['predicted_monthly_cost'].min():,.2f}"
                                    )
                                    col4.metric(
                                        "📈 מקסימום",
                                        f"₪{predictions_df['predicted_monthly_cost'].max():,.2f}"
                                    )

                                    st.markdown("---")

                                    # טבלה
                                    st.subheader("📋 תחזיות מפורטות")

                                    display_cols = ['vehicle_id', 'predicted_monthly_cost', 'predicted_annual_cost']
                                    if 'vehicle_age_years' in predictions_df.columns:
                                        display_cols.append('vehicle_age_years')
                                    if 'current_km' in predictions_df.columns:
                                        display_cols.append('current_km')
                                    if 'total_services' in predictions_df.columns:
                                        display_cols.append('total_services')

                                    available_cols = [c for c in display_cols if c in predictions_df.columns]

                                    st.dataframe(
                                        predictions_df[available_cols].sort_values(
                                            'predicted_monthly_cost', ascending=False
                                        ),
                                        use_container_width=True,
                                        height=400
                                    )

                                    # גרף
                                    st.subheader("📊 התפלגות עלויות צפויות")
                                    import plotly.express as px

                                    fig = px.histogram(
                                        predictions_df,
                                        x='predicted_monthly_cost',
                                        nbins=20,
                                        title="Distribution of Predicted Monthly Cost",
                                        labels={'predicted_monthly_cost': 'Monthly Cost (ILS)'}
                                    )
                                    st.plotly_chart(fig, use_container_width=True)

                                else:
                                    st.error("❌ לא הצלחתי לחזות")
                            else:
                                st.error("❌ קובץ פיצ'רים לא נמצא")

                        except Exception as e:
                            st.error(f"❌ שגיאה: {str(e)}")

            # תת-טאב 3: השוואה
            with subtab3:
                st.subheader("📊 השוואה בין רכבים")

                try:
                    features_path = "data/processed/features.csv"
                    if os.path.exists(features_path):
                        import pandas as pd
                        features_df = pd.read_csv(features_path)

                        # בחירת 2 רכבים
                        col1, col2 = st.columns(2)

                        with col1:
                            vehicle1 = st.selectbox("רכב 1", features_df['vehicle_id'].tolist(), key='v1')

                        with col2:
                            vehicle2 = st.selectbox("רכב 2", features_df['vehicle_id'].tolist(), key='v2')

                        if st.button("⚖️ השווה", type="primary"):
                            if vehicle1 == vehicle2:
                                st.warning("⚠️ בחר שני רכבים שונים")
                            else:
                                with st.spinner("משווה..."):
                                    try:
                                        # תחזיות
                                        predictions_df = predictor.predict_fleet(features_df)

                                        # שימוש ב-.iloc[0] עם המרה מפורשת
                                        v1_row = predictions_df[predictions_df['vehicle_id'] == vehicle1].iloc[0]
                                        v2_row = predictions_df[predictions_df['vehicle_id'] == vehicle2].iloc[0]

                                        v1_monthly = float(v1_row['predicted_monthly_cost'])
                                        v1_annual = float(v1_row['predicted_annual_cost'])
                                        v2_monthly = float(v2_row['predicted_monthly_cost'])
                                        v2_annual = float(v2_row['predicted_annual_cost'])

                                    except Exception as e:
                                        st.error(f"שגיאה בהשוואה: {str(e)}")
                                        import traceback
                                        st.code(traceback.format_exc())
                                        raise

                                    # השוואת עלויות
                                    col1, col2 = st.columns(2)

                                    with col1:
                                        st.markdown(f"### 🚗 {vehicle1}")
                                        st.metric("עלות חודשית", f"₪{v1_monthly:.2f}")
                                        st.metric("עלות שנתית", f"₪{v1_annual:.2f}")

                                    with col2:
                                        st.markdown(f"### 🚗 {vehicle2}")
                                        st.metric("עלות חודשית", f"₪{v2_monthly:.2f}")
                                        st.metric("עלות שנתית", f"₪{v2_annual:.2f}")

                                    # הפרש
                                    diff = v1_monthly - v2_monthly
                                    diff_pct = (diff / v2_monthly) * 100

                                    if diff > 0:
                                        st.info(f"📊 **{vehicle1}** יקר ב-₪{diff:.2f} ({diff_pct:.1f}%) מ-**{vehicle2}**")
                                    else:
                                        st.info(f"📊 **{vehicle2}** יקר ב-₪{abs(diff):.2f} ({abs(diff_pct):.1f}%) מ-**{vehicle1}**")

                    else:
                        st.error("❌ קובץ פיצ'רים לא נמצא")

                except Exception as e:
                    st.error(f"❌ שגיאה: {str(e)}")

        else:
            st.error("❌ המודל לא נטען. הרץ את המערכת AI קודם (RUN_AI_SYSTEM.ps1 → Option 1)")

    except ImportError as e:
        st.error(f"❌ לא ניתן לטעון MLPredictor: {str(e)}")
    except Exception as e:
        st.error(f"❌ שגיאה: {str(e)}")

# === לשונית 5: נתונים ===
with tab5:
    from src.utils.enhanced_datatable import render_data_table_tabs
    render_data_table_tabs(db)

# === לשונית 6: ניהול נתונים ===
with tab6:
    st.header("⚙️ ניהול נתונים")
    st.markdown("---")
    
    db = DatabaseManager()

    # תת-לשוניות לניהול
    sub_tab1, sub_tab2, sub_tab_email_settings, sub_tab3, sub_tab4 = st.tabs([
        "📤 העלאת חשבונית",
        "📧 סנכרון אימייל",
        "⚙️ הגדרות אימייל",
        "🗑️ מחיקת חשבונית",
        "📊 עדכון קילומטראז'"
    ])
    
    with sub_tab1:
        st.subheader("📤 העלאת חשבונית חדשה")
        
        upload_type = st.radio("סוג קובץ", ["PDF", "CSV"], horizontal=True)
        
        uploaded_file = st.file_uploader(
            f"העלה קובץ {upload_type}",
            type=['pdf', 'csv'] if upload_type == "PDF" else ['csv'],
            help="העלה חשבונית חדשה לעיבוד והוספה למסד הנתונים"
        )
        
        if uploaded_file is not None:
            try:
                from src.utils.file_processor import FileProcessor
                from src.crew_orchestrator import DirectOrchestrator
                
                processor = FileProcessor()
                file_type = uploaded_file.type
                
                with st.spinner("מעבד קובץ..."):
                    # עיבוד קובץ
                    processed_df = processor.process_uploaded_file(uploaded_file, file_type)
                    
                    if not processed_df.empty:
                        st.success(f"✅ קובץ עובד: {len(processed_df)} שורות")
                        st.dataframe(processed_df.head())
                        
                        if st.button("💾 שמור למסד נתונים"):
                            # כאן צריך להוסיף לוגיקה לשמירה למסד נתונים
                            # זה דורש המרה ל-format של invoice_data ו-invoice_lines_data
                            st.info("⚠️ פונקציונליות זו תשולב בקרוב עם DirectOrchestrator")
                    else:
                        st.error("❌ לא הצלחתי לעבד את הקובץ")
            
            except Exception as e:
                st.error(f"❌ שגיאה בעיבוד קובץ: {str(e)}")

    # Email Sync Tab (NEW)
    with sub_tab2:
        st.subheader("📧 סנכרון חשבוניות מאימייל")
        st.caption("משיכה אוטומטית של חשבוניות (PDF/Excel/CSV) מתיקיית מייל ייעודית")

        # הצג את התיקייה המוגדרת
        configured_folder = os.getenv('EMAIL_FOLDER', 'INBOX')
        if configured_folder == 'INBOX':
            st.error(f"""
            ⚠️ **שים לב!** התיקייה המוגדרת היא: **{configured_folder}**

            המערכת תמשוך **את כל המיילים** מתיבת הדואר הנכנס!

            **מומלץ מאוד:**
            1. צור תווית (Label) ב-Gmail בשם "חשבוניות" או "Invoices"
            2. עבור ל-**הגדרות אימייל** ובחר את התווית הספציפית
            3. כך המערכת תמשוך רק מיילים מהתווית הזו
            """)
        else:
            st.info(f"📂 התיקייה המוגדרת: **{configured_folder}**")

        # Check if email sync is enabled
        email_enabled = os.getenv('EMAIL_FETCH_ENABLED', 'false').lower() == 'true'

        if not email_enabled:
            st.warning("⚠️ סנכרון אימייל מכובה")
            st.markdown("""
            **כדי להפעיל:**
            1. ערוך את קובץ `.env`
            2. הגדר: `EMAIL_FETCH_ENABLED=true`
            3. הוסף פרטי חשבון המייל שלך
            4. אתחל מחדש את הדשבורד
            """)

            with st.expander("📋 הוראות הגדרה"):
                st.code("""
# הוסף ל-.env:
EMAIL_FETCH_ENABLED=true
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FOLDER=INBOX
                """, language="bash")

                st.markdown("""
                **חשוב: יש להשתמש ב-App-Specific Password!**
                - Gmail: https://myaccount.google.com/apppasswords
                - Outlook: https://account.microsoft.com/security
                """)
        else:
            # Email sync enabled - show full UI

            # Display last sync info
            st.markdown("### 📊 סטטוס סנכרון")

            sync_history = db.get_email_sync_history(limit=1)

            col1, col2, col3 = st.columns(3)

            if not sync_history.empty:
                last_sync = sync_history.iloc[0]

                with col1:
                    st.metric(
                        "סנכרון אחרון",
                        last_sync['processed_date'][:10] if pd.notna(last_sync['processed_date']) else "אף פעם",
                        delta=None
                    )

                with col2:
                    invoice_count = len(last_sync['invoice_numbers'].split(',')) if last_sync['invoice_numbers'] else 0
                    st.metric("חשבוניות נמצאו", invoice_count)

                with col3:
                    status_icon = "✅" if last_sync['status'] == 'success' else "❌"
                    st.metric("סטטוס", status_icon)
            else:
                with col1:
                    st.metric("סנכרון אחרון", "אף פעם")
                with col2:
                    st.metric("חשבוניות נמצאו", 0)
                with col3:
                    st.metric("סטטוס", "—")

            st.markdown("---")

            # Manual sync button
            st.markdown("### 🔄 סנכרון ידני")

            col_btn1, col_btn2 = st.columns([3, 1])

            with col_btn1:
                if st.button("🔄 סנכרן אימיילים עכשיו", type="primary", use_container_width=True):
                    with st.spinner("מתחבר לשרת המייל..."):
                        try:
                            from src.email_fetcher import EmailInvoiceProcessor

                            processor = EmailInvoiceProcessor()
                            result = processor.sync_emails(silent=False)

                            # Display results
                            if result['new_invoices'] > 0:
                                st.success(f"✅ {result['new_invoices']} חשבוניות חדשות נוספו!")
                                st.cache_data.clear()
                                st.rerun()
                            elif result['emails_processed'] > 0:
                                st.info(f"ℹ️ עובדו {result['emails_processed']} אימיילים, אבל לא נמצאו חשבוניות חדשות")
                            else:
                                st.info("ℹ️ לא נמצאו אימיילים חדשים עם חשבוניות")

                            if result['errors'] > 0:
                                st.warning(f"⚠️ {result['errors']} קבצים נכשלו בעיבוד")

                            if result.get('error_message'):
                                st.error(f"❌ שגיאה: {result['error_message']}")

                        except Exception as e:
                            st.error(f"❌ שגיאה בסנכרון: {str(e)}")
                            st.exception(e)

            with col_btn2:
                if st.button("🧪 בדוק חיבור", use_container_width=True):
                    try:
                        from src.email_fetcher import EmailInvoiceProcessor

                        processor = EmailInvoiceProcessor()
                        success, message = processor.test_connection()

                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"❌ שגיאה: {str(e)}")

            # Add button to list available folders
            if st.button("📂 הצג תיקיות זמינות", use_container_width=False, type="secondary"):
                try:
                    from src.email_fetcher import EmailInvoiceProcessor

                    with st.spinner("מחפש תיקיות..."):
                        processor = EmailInvoiceProcessor()
                        folders = processor.list_available_folders()

                        if folders:
                            st.success(f"נמצאו {len(folders)} תיקיות:")
                            # Display folders in an expander
                            with st.expander("רשימת תיקיות", expanded=True):
                                for folder in folders:
                                    st.code(folder, language=None)
                        else:
                            st.warning("לא נמצאו תיקיות או שגיאה בחיבור")
                except Exception as e:
                    st.error(f"❌ שגיאה בקבלת רשימת תיקיות: {str(e)}")

            st.markdown("---")

            # Sync history table
            st.markdown("### 📜 היסטוריית סנכרונים")

            all_history = db.get_email_sync_history(limit=20)

            if not all_history.empty:
                # Format the dataframe for display
                display_df = all_history.copy()

                # Rename columns to Hebrew
                display_df.columns = [
                    'ID',
                    'מזהה מייל',
                    'נושא',
                    'שולח',
                    'תאריך קבלה',
                    'תאריך עיבוד',
                    'חשבוניות',
                    'סטטוס'
                ]

                # Show only relevant columns for display (keep ID for deletion)
                display_df_for_table = display_df[['ID', 'תאריך עיבוד', 'נושא', 'שולח', 'חשבוניות', 'סטטוס']]

                st.dataframe(
                    display_df_for_table,
                    use_container_width=True,
                    height=400
                )

                # Delete options
                st.markdown("---")
                st.markdown("### 🗑️ ניהול היסטוריה")

                col_delete1, col_delete2, col_delete3 = st.columns(3)

                with col_delete1:
                    # Delete specific record by ID
                    with st.form(key="delete_specific_form"):
                        st.caption("מחיקת רשומה ספציפית")
                        sync_id_to_delete = st.number_input(
                            "הזן ID למחיקה",
                            min_value=1,
                            step=1,
                            help="ניתן לראות את ה-ID בטבלה למעלה"
                        )
                        delete_specific_btn = st.form_submit_button("🗑️ מחק רשומה")

                        if delete_specific_btn:
                            if db.delete_email_sync_record(int(sync_id_to_delete)):
                                st.success(f"✅ רשומה {sync_id_to_delete} נמחקה בהצלחה")
                                st.rerun()
                            else:
                                st.error(f"❌ שגיאה במחיקת רשומה {sync_id_to_delete}")

                with col_delete2:
                    # Delete failed records only
                    st.caption("מחיקת רשומות כושלות")
                    failed_count = len(display_df[display_df['סטטוס'] == 'failed'])
                    st.info(f"📊 {failed_count} רשומות כושלות")

                    if st.button("🗑️ מחק רשומות כושלות", key="delete_failed"):
                        if failed_count > 0:
                            if db.delete_failed_email_sync_records():
                                st.success(f"✅ {failed_count} רשומות כושלות נמחקו")
                                st.rerun()
                            else:
                                st.error("❌ שגיאה במחיקת רשומות כושלות")
                        else:
                            st.warning("אין רשומות כושלות למחיקה")

                with col_delete3:
                    # Delete all records
                    st.caption("מחיקת כל ההיסטוריה")
                    total_count = len(display_df)
                    st.info(f"📊 {total_count} רשומות סה\"כ")

                    if st.button("🗑️ מחק הכל", key="delete_all"):
                        # Add confirmation
                        if 'confirm_delete_all' not in st.session_state:
                            st.session_state.confirm_delete_all = True
                            st.warning("⚠️ לחץ שוב לאישור מחיקת כל ההיסטוריה")
                        else:
                            if db.delete_all_email_sync_records():
                                st.success(f"✅ כל {total_count} הרשומות נמחקו")
                                del st.session_state.confirm_delete_all
                                st.rerun()
                            else:
                                st.error("❌ שגיאה במחיקת כל הרשומות")
                                del st.session_state.confirm_delete_all
            else:
                st.info("ℹ️ עדיין לא בוצעו סנכרונים")

            # Configuration info
            with st.expander("🔧 הגדרות סנכרון נוכחיות"):
                config_info = f"""
                **שרת IMAP:** {os.getenv('EMAIL_IMAP_SERVER', 'לא הוגדר')}
                **פורט:** {os.getenv('EMAIL_IMAP_PORT', 'לא הוגדר')}
                **כתובת מייל:** {os.getenv('EMAIL_ADDRESS', 'לא הוגדר')}
                **תיקייה:** {os.getenv('EMAIL_FOLDER', 'INBOX')}
                **סימון כנקרא:** {os.getenv('EMAIL_MARK_AS_READ', 'true')}
                **מקסימום משיכה:** {os.getenv('EMAIL_MAX_FETCH', '50')} מיילים
                **פילטר ימים:** {os.getenv('EMAIL_DATE_FILTER_DAYS', '30')} ימים אחרונים
                """
                st.markdown(config_info)

    # === סאב-טאב 3: הגדרות אימייל ===
    with sub_tab_email_settings:
        st.subheader("⚙️ הגדרות סנכרון אימייל")
        st.caption("הגדר את המערכת למשוך חשבוניות אוטומטית מתיקיית מייל ייעודית")

        # Import EmailConfigManager
        try:
            from src.email_config_manager import EmailConfigManager, PROVIDERS

            config_manager = EmailConfigManager()

            # חלוקה ל-2 עמודות ראשיות
            col_settings, col_status = st.columns([2, 1])

            with col_settings:
                st.subheader("🔧 הגדרות חיבור")

                # בחירת ספק אימייל
                provider_names = list(PROVIDERS.keys())
                current_provider = st.session_state.get('email_provider', 'Gmail')

                selected_provider = st.selectbox(
                    "🌐 בחר ספק אימייל",
                    options=provider_names,
                    index=provider_names.index(current_provider) if current_provider in provider_names else 0,
                    help="בחר את ספק שירות האימייל שלך",
                    key="settings_provider"
                )
                st.session_state['email_provider'] = selected_provider

                # קבל מידע על הספק שנבחר
                provider_info = PROVIDERS[selected_provider]

                # הצג קישור לקבלת סיסמת אפליקציה
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px 0;">
                    <h4 style="margin: 0 0 10px 0;">📝 לפני שמתחילים:</h4>
                    <p style="margin: 5px 0;">1. יש להפעיל אימות דו-שלבי (2FA) בחשבון המייל שלך</p>
                    <p style="margin: 5px 0;">2. צור <b>סיסמת אפליקציה</b> (App-Specific Password) - <b>לא הסיסמה הרגילה!</b></p>
                    <p style="margin: 5px 0;">3. לחץ כאן: <a href="{provider_info.app_password_url}" target="_blank" style="color: #0066cc; font-weight: bold;">🔗 קבל סיסמת אפליקציה ל-{selected_provider}</a></p>
                </div>
                """, unsafe_allow_html=True)

                # שדות קלט
                st.markdown("---")

                email_address = st.text_input(
                    "📧 כתובת אימייל",
                    value=st.session_state.get('email_address_settings', ''),
                    placeholder=f"example@{'gmail.com' if selected_provider == 'Gmail' else 'outlook.com' if selected_provider == 'Outlook' else 'yahoo.com'}",
                    help="הזן את כתובת המייל המלאה שלך",
                    key="settings_email"
                )
                st.session_state['email_address_settings'] = email_address

                email_password = st.text_input(
                    "🔐 סיסמת אפליקציה",
                    type="password",
                    value=st.session_state.get('email_password_settings', ''),
                    placeholder="xxxx xxxx xxxx xxxx",
                    help="הזן את סיסמת האפליקציה שקיבלת (16 תווים)",
                    key="settings_password"
                )
                st.session_state['email_password_settings'] = email_password

                st.markdown("---")

                # כפתור לגילוי תיקיות
                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    if st.button("🔍 גלה תיקיות זמינות", type="secondary", disabled=not (email_address and email_password), use_container_width=True, key="discover_folders"):
                        with st.spinner(f"מתחבר ל-{selected_provider}..."):
                            success, message, folders = config_manager.test_connection(
                                email_address=email_address,
                                password=email_password,
                                provider=selected_provider
                            )

                            if success:
                                st.session_state['discovered_folders'] = folders
                                st.session_state['connection_tested'] = True
                                st.success(message)
                                st.info(f"✅ נמצאו {len(folders)} תיקיות במייל שלך")
                                st.rerun()
                            else:
                                st.error(message)
                                st.session_state['connection_tested'] = False

                with col_btn2:
                    # כפתור בדיקת חיבור
                    if st.button("✅ בדוק חיבור", type="primary", disabled=not (email_address and email_password), use_container_width=True, key="test_connection"):
                        with st.spinner("בודק חיבור..."):
                            success, message, _ = config_manager.test_connection(
                                email_address=email_address,
                                password=email_password,
                                provider=selected_provider
                            )

                            if success:
                                st.success(message)
                                st.session_state['connection_tested'] = True
                            else:
                                st.error(message)
                                st.session_state['connection_tested'] = False

                # בחירת תיקייה
                st.markdown("---")
                st.subheader("📁 בחר תיקיית מייל")

                # אם יש תיקיות שהתגלו, הצג אותן
                if 'discovered_folders' in st.session_state and st.session_state['discovered_folders']:
                    folders = st.session_state['discovered_folders']

                    # נסה למצוא את התיקייה הנוכחית
                    current_folder = config_manager.current_config.get('EMAIL_FOLDER', 'INBOX')

                    selected_folder = st.selectbox(
                        "📂 תיקייה לסנכרון",
                        options=folders,
                        index=folders.index(current_folder) if current_folder in folders else 0,
                        help="בחר את התיקייה שממנה למשוך חשבוניות",
                        key="settings_folder"
                    )
                    st.session_state['selected_folder'] = selected_folder

                else:
                    # אם לא התגלו תיקיות, הצג דוגמאות לפי הספק
                    st.info("💡 לחץ על 'גלה תיקיות זמינות' כדי לראות את התיקיות שלך")
                    st.caption(f"דוגמאות לתיקיות ב-{selected_provider}: {', '.join(provider_info.folder_examples)}")

                    selected_folder = st.text_input(
                        "📂 שם תיקייה / תווית (Label)",
                        value=config_manager.current_config.get('EMAIL_FOLDER', 'INBOX'),
                        placeholder="INBOX",
                        help="לדוגמה: חשבוניות, Invoices, או השאר INBOX לכל המיילים",
                        key="settings_folder_manual"
                    )

                    st.warning("""
                    ⚠️ **חשוב!** כדי למשוך מיילים מתווית ספציפית ב-Gmail:
                    - בדוק שהתווית קיימת ב-Gmail שלך
                    - הזן את שם התווית בדיוק כפי שהיא מופיעה (case-sensitive)
                    - לדוגמה: אם יצרת תווית "חשבוניות" ב-Gmail, הזן: **חשבוניות**
                    - אם השארת INBOX, המערכת תמשוך **את כל המיילים** מתיבת הדואר הנכנס!
                    """)

                    st.session_state['selected_folder'] = selected_folder

                # כפתור שמירה
                st.markdown("---")

                if st.button("💾 שמור הגדרות ל-.env", type="primary", use_container_width=True, disabled=not (email_address and email_password and selected_folder), key="save_settings"):
                    with st.spinner("שומר הגדרות..."):
                        success, message = config_manager.save_configuration(
                            provider=selected_provider,
                            email_address=email_address,
                            password=email_password,
                            folder=selected_folder,
                            enabled=True
                        )

                        if success:
                            st.success(message)
                            st.info("ℹ️ ההגדרות נשמרו בהצלחה! הסנכרון האוטומטי מופעל.")

                            # ניקוי session state
                            for key in ['email_address_settings', 'email_password_settings', 'discovered_folders', 'connection_tested']:
                                if key in st.session_state:
                                    del st.session_state[key]

                            # Reload page to apply changes
                            import time
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(message)

            with col_status:
                st.subheader("📊 סטטוס נוכחי")

                # הצג הגדרות נוכחיות
                current_config = config_manager.current_config

                is_enabled = current_config.get('EMAIL_FETCH_ENABLED', 'false').lower() == 'true'

                if is_enabled:
                    st.success("✅ סנכרון אימייל **מופעל**")
                else:
                    st.warning("⚠️ סנכרון אימייל **כבוי**")

                st.markdown("---")

                # פרטי תצורה נוכחית
                st.markdown("**הגדרות שמורות:**")

                config_display = {
                    "ספק": current_config.get('EMAIL_IMAP_SERVER', 'לא מוגדר'),
                    "אימייל": current_config.get('EMAIL_ADDRESS', 'לא מוגדר'),
                    "תיקייה": current_config.get('EMAIL_FOLDER', 'INBOX'),
                    "מקסימום למשיכה": current_config.get('EMAIL_MAX_FETCH', '50'),
                    "סנן ימים אחרונים": current_config.get('EMAIL_DATE_FILTER_DAYS', '30')
                }

                for key, value in config_display.items():
                    st.text(f"{key}: {value}")

                st.markdown("---")

                # כפתור ביטול הפעלה
                if is_enabled:
                    if st.button("🔴 בטל הפעלת סנכרון", type="secondary", use_container_width=True, key="disable_sync"):
                        success, message = config_manager.save_configuration(
                            provider=current_config.get('EMAIL_IMAP_SERVER', 'Gmail'),
                            email_address=current_config.get('EMAIL_ADDRESS', ''),
                            password=current_config.get('EMAIL_PASSWORD', ''),
                            folder=current_config.get('EMAIL_FOLDER', 'INBOX'),
                            enabled=False
                        )

                        if success:
                            st.success("הסנכרון בוטל")
                            import time
                            time.sleep(1)
                            st.rerun()

                # הוראות שימוש
                st.markdown("---")
                st.markdown("**📖 איך זה עובד?**")
                st.markdown("""
                1. בחר ספק אימייל
                2. צור סיסמת אפליקציה
                3. הזן פרטי חיבור
                4. גלה תיקיות זמינות
                5. בחר תיקייה לסנכרון
                6. שמור הגדרות

                המערכת תמשוך חשבוניות אוטומטית בכל פעם שהדשבורד נטען!
                """)

        except ImportError as e:
            st.error(f"❌ שגיאה בטעינת מודול EmailConfigManager: {str(e)}")
            st.info("ודא שהקובץ src/email_config_manager.py קיים במערכת")
        except Exception as e:
            st.error(f"❌ שגיאה כללית: {str(e)}")

    with sub_tab3:
        st.subheader("🗑️ מחיקת חשבונית")
        
        # חיפוש חשבונית למחיקה
        search_invoice = st.text_input("מספר חשבונית למחיקה", placeholder="INV-12345678")
        
        if search_invoice:
            invoice_df = db.get_invoice_by_no(search_invoice)
            
            if not invoice_df.empty:
                st.dataframe(invoice_df)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ מחק חשבונית", type="primary", use_container_width=True):
                        try:
                            if db.delete_invoice(search_invoice):
                                st.success("✅ חשבונית נמחקה בהצלחה!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ לא הצלחתי למחוק את החשבונית")
                        except Exception as e:
                            st.error(f"❌ שגיאה: {str(e)}")
                
                with col2:
                    if st.button("❌ ביטול", use_container_width=True):
                        st.rerun()
            else:
                st.warning(f"⚠️ חשבונית {search_invoice} לא נמצאה")

    with sub_tab4:
        st.subheader("📊 עדכון קילומטראז' ידני")
        
        # בחירת רכב
        vehicles_df = db.get_all_vehicles()
        if not vehicles_df.empty:
            vehicle_list = vehicles_df['vehicle_id'].tolist()
            selected_vehicle = st.selectbox("בחר רכב", vehicle_list, key="data_management_vehicle_select")
            
            if selected_vehicle:
                vehicle_info = db.get_vehicle_info(selected_vehicle)
                if not vehicle_info.empty:
                    current_km = db.get_vehicle_with_stats()
                    current_km = current_km[current_km['vehicle_id'] == selected_vehicle]
                    
                    if not current_km.empty and pd.notna(current_km.iloc[0]['current_km']):
                        st.info(f"קילומטראז' נוכחי: {current_km.iloc[0]['current_km']:,.0f} ק\"מ")
                    else:
                        st.info(f"קילומטראז' התחלתי: {vehicle_info.iloc[0]['initial_km']:,.0f} ק\"מ")
                    
                    new_km = st.number_input("קילומטראז' חדש", min_value=0, step=1000, value=int(current_km.iloc[0]['current_km']) if not current_km.empty and pd.notna(current_km.iloc[0]['current_km']) else vehicle_info.iloc[0]['initial_km'])
                    
                    update_date = st.date_input("תאריך עדכון")
                    
                    if st.button("💾 עדכן קילומטראז'"):
                        try:
                            db.update_vehicle_odometer(selected_vehicle, int(new_km), update_date.strftime("%Y-%m-%d"))
                            st.success("✅ קילומטראז' עודכן בהצלחה!")
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"❌ שגיאה: {str(e)}")
        else:
            st.warning("⚠️ לא נמצאו רכבים במערכת")

# === לשונית 7: דפוסי תחזוקה ===
with tab7:
    st.header("🔍 דפוסי תחזוקה לפי קילומטראז'")
    st.caption("ניתוח דפוסי תקלות ותחזוקה עם CrewAI")
    
    try:
        from src.maintenance_pattern_agent import MaintenancePatternAgent
        
        pattern_agent = MaintenancePatternAgent()
        
        # בחירת רכב לניתוח
        vehicles_df = db.get_all_vehicles()
        if not vehicles_df.empty:
            vehicle_list = ["כל הצי"] + vehicles_df['vehicle_id'].tolist()
            selected_vehicle = st.selectbox("בחר רכב לניתוח", vehicle_list, key="maintenance_patterns_vehicle_select")
            
            if st.button("🔍 חפש דפוסים", type="primary"):
                with st.spinner("מנתח דפוסי תחזוקה..."):
                    vehicle_id = None if selected_vehicle == "כל הצי" else selected_vehicle
                    patterns = pattern_agent.analyze_maintenance_patterns(vehicle_id)
                    
                    if "error" not in patterns:
                        # הצגת תוצאות
                        st.success("✅ ניתוח הושלם!")
                        
                        # דפוסי צמיגים
                        if 'tire_replacements' in patterns:
                            tire_info = patterns['tire_replacements']
                            if 'recommendation' in tire_info:
                                st.subheader("🔧 דפוסי החלפת צמיגים")
                                st.info(tire_info['recommendation'])
                                if 'average_km_interval' in tire_info:
                                    st.metric("מרווח ממוצע", f"{tire_info['average_km_interval']:,} ק\"מ")
                        
                        # דפוסי טיפול שוטף
                        if 'routine_services' in patterns:
                            routine_info = patterns['routine_services']
                            if 'recommendation' in routine_info:
                                st.subheader("🔧 דפוסי טיפול שוטף")
                                st.info(routine_info['recommendation'])
                        
                        # מגמות עלויות
                        if 'cost_trends' in patterns:
                            cost_info = patterns['cost_trends']
                            st.subheader("💰 מגמות עלויות לפי קילומטראז'")
                            if 'cost_by_km_range' in cost_info:
                                cost_df = pd.DataFrame(cost_info['cost_by_km_range'])
                                st.dataframe(cost_df)
                                
                                # גרף מגמות
                                if len(cost_df) > 1:
                                    fig = px.line(cost_df, x='km_range', y='avg_cost', markers=True, title="מגמת עלויות לפי קילומטראז'")
                                    st.plotly_chart(fig)
                        
                        # המלצות
                        if selected_vehicle != "כל הצי":
                            recommendations = pattern_agent.get_maintenance_recommendations(selected_vehicle)
                            if recommendations.get('recommendations'):
                                st.subheader("💡 המלצות תחזוקה")
                                for rec in recommendations['recommendations']:
                                    st.info(rec)
                    else:
                        st.error(patterns['error'])
        else:
            st.warning("⚠️ לא נמצאו רכבים במערכת")
    
    except ImportError:
        st.error("❌ לא ניתן לטעון את MaintenancePatternAgent")
    except Exception as e:
        st.error(f"❌ שגיאה בניתוח: {str(e)}")

# === לשונית 8: ניהול הצי ===
with tab8:
    st.header("🚗 ניהול הצי")
    st.caption("ממשק קצין רכב - הוספת רכבים וצפייה בסטטוס מלא")

    # תת-לשוניות
    subtab1, subtab2, subtab3 = st.tabs(["📊 סקירת צי", "➕ הוספת רכב יחיד", "📤 העלאת רכבים באצ'"])

    # תת-לשונית 1: סקירת צי
    with subtab1:
        st.subheader("📊 סקירת צי מלאה")

        try:
            from src.fleet_analysis_tools import FleetAnalyzer

            analyzer = FleetAnalyzer()
            fleet_df = analyzer.get_fleet_status_summary()

            if not fleet_df.empty:
                # מדדים עיקריים
                col1, col2, col3, col4 = st.columns(4)

                total_vehicles = len(fleet_df)
                active_vehicles = len(fleet_df[fleet_df['status'] == 'active'])
                near_retirement = len(fleet_df[fleet_df.get('retirement_status', '') == 'near_retirement'])
                avg_annual_cost = fleet_df['annual_cost'].mean()

                col1.metric("סה\"כ רכבים", total_vehicles)
                col2.metric("רכבים פעילים", active_vehicles)
                col3.metric("קרובים לגריטה", near_retirement, delta=f"-{near_retirement}")
                col4.metric("עלות שנתית ממוצעת", f"₪{avg_annual_cost:,.0f}")

                st.markdown("---")

                # טבלה מפורטת
                st.subheader("פירוט מלא לכל רכב")

                # בחירת עמודות להצגה
                display_cols = [
                    'vehicle_id', 'plate', 'make_model', 'year', 'assigned_to',
                    'current_km', 'purchase_date', 'last_test_date', 'next_test_date',
                    'estimated_retirement_date', 'days_until_retirement',
                    'total_services', 'annual_cost', 'status'
                ]

                available_cols = [col for col in display_cols if col in fleet_df.columns]

                # עיצוב הטבלה
                styled_df = fleet_df[available_cols].copy()

                # צביעת שורות לפי סטטוס
                def highlight_status(row):
                    if row.get('status') == 'retired':
                        return ['background-color: #ffcccc'] * len(row)
                    elif row.get('days_until_retirement', 999) < 180:
                        return ['background-color: #fff3cd'] * len(row)
                    else:
                        return [''] * len(row)

                st.dataframe(
                    styled_df.style.apply(highlight_status, axis=1),
                    use_container_width=True,
                    height=600
                )

                # הורדת דוח Excel
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    fleet_df.to_excel(writer, index=False, sheet_name='Fleet Overview')

                st.download_button(
                    label="📥 הורד דוח Excel",
                    data=buffer.getvalue(),
                    file_name=f"fleet_overview_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.ms-excel"
                )
            else:
                st.info("אין רכבים במערכת")

        except Exception as e:
            st.error(f"שגיאה בטעינת נתוני צי: {str(e)}")

    # תת-לשונית 2: הוספת רכב יחיד
    with subtab2:
        st.subheader("➕ הוספת רכב חדש לצי")

        with st.form("add_single_vehicle"):
            col1, col2 = st.columns(2)

            with col1:
                vehicle_id = st.text_input("מזהה רכב *", placeholder="VH-86")
                plate = st.text_input("לוחית רישוי *", placeholder="12-345-67")
                make_model = st.text_input("דגם *", placeholder="טויוטה קורולה")
                year = st.number_input("שנה *", min_value=2000, max_value=2030, value=2023)
                initial_km = st.number_input("ק\"מ התחלתי *", min_value=0, value=0)

            with col2:
                purchase_date = st.date_input("תאריך רכישה *", value=pd.Timestamp.now())
                assigned_to = st.text_input("משוייך ל", placeholder="דוד כהן (משלוחים)")
                last_test_date = st.date_input("תאריך טסט אחרון", value=None)
                next_test_date = st.date_input("תאריך טסט הבא", value=None)
                status = st.selectbox("סטטוס", ["active", "maintenance", "retired"])

            st.caption("* שדות חובה")

            submitted = st.form_submit_button("💾 הוסף רכב", use_container_width=True)

            if submitted:
                if not vehicle_id or not plate or not make_model:
                    st.error("❌ נא למלא את כל השדות החובה")
                else:
                    try:
                        from src.retirement_calculator import RetirementCalculator

                        # חישוב תאריך גריטה
                        calc = RetirementCalculator()
                        retirement_info = calc.calculate_retirement_date(
                            purchase_date.strftime("%Y-%m-%d"),
                            initial_km
                        )

                        vehicle_data = {
                            'vehicle_id': vehicle_id,
                            'plate': plate,
                            'make_model': make_model,
                            'year': year,
                            'initial_km': initial_km,
                            'purchase_date': purchase_date.strftime("%Y-%m-%d"),
                            'assigned_to': assigned_to if assigned_to else '',
                            'last_test_date': last_test_date.strftime("%Y-%m-%d") if last_test_date else '',
                            'next_test_date': next_test_date.strftime("%Y-%m-%d") if next_test_date else '',
                            'estimated_retirement_date': retirement_info['retirement_date'],
                            'status': status
                        }

                        success = db.add_vehicle(vehicle_data)

                        if success:
                            st.success(f"✅ רכב {vehicle_id} נוסף בהצלחה!")
                            st.cache_data.clear()
                        else:
                            st.error("❌ שגיאה בהוספת רכב")

                    except Exception as e:
                        st.error(f"❌ שגיאה: {str(e)}")

    # תת-לשונית 3: העלאת באצ'
    with subtab3:
        st.subheader("📤 העלאת רכבים באצ' (Excel)")

        # הורדת תבנית
        st.markdown("### 1️⃣ הורד תבנית Excel")

        template_path = os.path.join("data", "templates", "vehicle_template.csv")
        if os.path.exists(template_path):
            with open(template_path, 'rb') as f:
                st.download_button(
                    label="📥 הורד תבנית CSV",
                    data=f,
                    file_name="vehicle_template.csv",
                    mime="text/csv"
                )

        st.caption("התבנית כוללת 2 שורות דוגמה. מחק אותן ומלא בנתונים שלך.")

        # העלאת קובץ
        st.markdown("### 2️⃣ העלה קובץ ממולא")

        uploaded_file = st.file_uploader(
            "בחר קובץ CSV או Excel",
            type=['csv', 'xlsx'],
            help="הקובץ חייב לכלול את העמודות: vehicle_id, plate, make_model, year, initial_km, purchase_date"
        )

        if uploaded_file is not None:
            try:
                # קריאת הקובץ
                if uploaded_file.name.endswith('.csv'):
                    vehicles_df = pd.read_csv(uploaded_file)
                else:
                    vehicles_df = pd.read_excel(uploaded_file)

                st.success(f"✅ קובץ נקרא: {len(vehicles_df)} שורות")

                # תצוגה מקדימה
                st.subheader("תצוגה מקדימה")
                st.dataframe(vehicles_df.head(10), use_container_width=True)

                # בדיקת עמודות חובה
                required_cols = ['vehicle_id', 'plate', 'make_model', 'year', 'initial_km', 'purchase_date']
                missing_cols = [col for col in required_cols if col not in vehicles_df.columns]

                if missing_cols:
                    st.error(f"❌ עמודות חסרות: {', '.join(missing_cols)}")
                else:
                    if st.button("💾 העלה את כל הרכבים", type="primary", use_container_width=True):
                        with st.spinner("מעלה רכבים..."):
                            result = db.bulk_add_vehicles(vehicles_df)

                            st.success(f"✅ {result['success']} רכבים נוספו בהצלחה!")

                            if result['failed'] > 0:
                                st.warning(f"⚠️ {result['failed']} רכבים נכשלו:")
                                for error in result['errors'][:10]:
                                    st.caption(f"- {error}")

                            st.cache_data.clear()

            except Exception as e:
                st.error(f"❌ שגיאה בעיבוד קובץ: {str(e)}")

# === לשונית 9: תובנות אסטרטגיות ===
with tab9:
    st.header("💼 תובנות אסטרטגיות")
    st.caption("ניתוח עסקי ברמת ניהול עליון")

    try:
        from src.fleet_analysis_tools import FleetAnalyzer

        analyzer = FleetAnalyzer()
        insights = analyzer.get_strategic_insights()

        # אמינות לפי דגם
        st.subheader("🏆 אמינות לפי דגם")

        reliability = insights.get('reliability_by_model', {})
        if reliability:
            col1, col2 = st.columns(2)

            with col1:
                st.metric("דגם מומלץ ביותר", reliability.get('best_model', 'N/A'))
                st.caption("הדגם עם הכי פחות תקלות")

            with col2:
                st.metric("דגם פחות מומלץ", reliability.get('worst_model', 'N/A'))
                st.caption("הדגם עם הכי הרבה תקלות")

            # טבלה מפורטת
            if reliability.get('details'):
                reliability_df = pd.DataFrame(reliability['details'])
                st.dataframe(reliability_df, use_container_width=True)

        st.markdown("---")

        # המלצות החלפה
        st.subheader("🔄 המלצות להחלפת רכבים")

        replacements = insights.get('replacement_recommendations', [])
        if replacements:
            st.warning(f"⚠️ {len(replacements)} רכבים מומלצים להחלפה:")

            for rec in replacements[:10]:
                with st.expander(f"{rec['vehicle_id']} - {rec['plate']} ({rec['priority_score']} נקודות)"):
                    st.write(f"**דגם:** {rec['make_model']}")
                    st.write("**סיבות:**")
                    for reason in rec['reasons']:
                        st.write(f"- {reason}")
        else:
            st.success("✅ אין רכבים הדורשים החלפה דחופה")

        st.markdown("---")

        # רכבים מצטיינים
        st.subheader("⭐ רכבים מצטיינים (Top 5)")

        top_performers = insights.get('top_performers', [])
        if top_performers:
            performers_df = pd.DataFrame(top_performers)
            st.dataframe(performers_df, use_container_width=True)

        st.markdown("---")

        # ניתוח נהגים
        st.subheader("👥 ביצועי נהגים")
        st.caption("ניתוח מבוסס על עלויות תחזוקה וכמות תקלות")

        try:
            from src.ai_engine import FleetAIEngine
            ai_engine = FleetAIEngine()
            driver_analysis = ai_engine._analyze_drivers()

            if driver_analysis and driver_analysis.get('total_drivers', 0) > 0:
                st.info(f"📊 סה\"כ נהגים פעילים: {driver_analysis['total_drivers']}")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 🏆 נהגים מצטיינים (TOP 3)")
                    top_drivers = driver_analysis.get('top_performers', [])

                    if top_drivers:
                        for i, driver in enumerate(top_drivers, 1):
                            with st.container():
                                st.markdown(f"**{i}. {driver['driver']}**")
                                metric_col1, metric_col2 = st.columns(2)
                                with metric_col1:
                                    st.metric("רכבים", driver['num_vehicles'])
                                    st.metric("טיפולים", driver['total_services'])
                                with metric_col2:
                                    st.metric("עלות כוללת", f"₪{driver['total_cost']:,.0f}")
                                    st.metric("ממוצע/רכב", f"₪{driver['avg_cost_per_vehicle']:,.0f}")
                                st.caption(f"🚗 רכבים: {', '.join(driver['vehicles'])}")
                                st.markdown("---")
                    else:
                        st.info("אין נתוני נהגים זמינים")

                with col2:
                    st.markdown("### ⚠️ נהגים לשיפור (TOP 3)")
                    bottom_drivers = driver_analysis.get('need_improvement', [])

                    if bottom_drivers:
                        for i, driver in enumerate(bottom_drivers, 1):
                            with st.container():
                                st.markdown(f"**{i}. {driver['driver']}**")
                                metric_col1, metric_col2 = st.columns(2)
                                with metric_col1:
                                    st.metric("רכבים", driver['num_vehicles'])
                                    st.metric("טיפולים", driver['total_services'])
                                with metric_col2:
                                    st.metric("עלות כוללת", f"₪{driver['total_cost']:,.0f}")
                                    st.metric("ממוצע/רכב", f"₪{driver['avg_cost_per_vehicle']:,.0f}")
                                st.caption(f"🚗 רכבים: {', '.join(driver['vehicles'])}")
                                st.markdown("---")
                    else:
                        st.info("כל הנהגים מצטיינים!")

                # טבלה מלאה של כל הנהגים
                st.markdown("### 📋 טבלת נהגים מלאה")
                all_drivers = driver_analysis.get('all_drivers', [])
                if all_drivers:
                    drivers_df = pd.DataFrame(all_drivers)
                    drivers_df = drivers_df[['driver', 'num_vehicles', 'total_services', 'total_cost', 'avg_cost_per_vehicle', 'performance_score']]
                    drivers_df.columns = ['נהג', 'מס\' רכבים', 'סה"כ טיפולים', 'עלות כוללת', 'ממוצע לרכב', 'ציון ביצועים']

                    # עיצוב הטבלה
                    st.dataframe(
                        drivers_df.style.format({
                            'עלות כוללת': '₪{:,.0f}',
                            'ממוצע לרכב': '₪{:,.0f}',
                            'ציון ביצועים': '{:.1f}'
                        }),
                        use_container_width=True
                    )

            else:
                st.warning("⚠️ לא נמצאו נתוני נהגים")

        except Exception as e:
            st.error(f"❌ שגיאה בניתוח נהגים: {str(e)}")

        st.markdown("---")

        # השוואת מוסכים
        st.subheader("🔧 השוואת מוסכים")

        workshop_comp = insights.get('workshop_comparison', {})
        if workshop_comp.get('all_workshops'):
            workshops_df = pd.DataFrame(workshop_comp['all_workshops'])

            fig = px.bar(
                workshops_df,
                x='workshop',
                y='avg_cost',
                title="עלות ממוצעת לפי מוסך",
                color='avg_cost',
                text_auto='.0f'
            )
            st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                cheapest = workshop_comp.get('cheapest', {})
                if cheapest:
                    st.success(f"✅ **מוסך הזול ביותר:** {cheapest.get('workshop')}")
                    st.caption(f"ממוצע: ₪{cheapest.get('avg_cost', 0):,.0f}")

            with col2:
                expensive = workshop_comp.get('most_expensive', {})
                if expensive:
                    st.error(f"❌ **מוסך היקר ביותר:** {expensive.get('workshop')}")
                    st.caption(f"ממוצע: ₪{expensive.get('avg_cost', 0):,.0f}")

    except Exception as e:
        st.error(f"❌ שגיאה בטעינת תובנות: {str(e)}")