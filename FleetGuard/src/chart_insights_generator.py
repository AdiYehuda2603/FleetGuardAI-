# -*- coding: utf-8 -*-
"""
Chart Insights Generator
מייצר תובנות אוטומטיות לגרפים בדשבורד
"""

import pandas as pd
import numpy as np
from datetime import datetime


class ChartInsightsGenerator:
    """
    מחלקה לייצור תובנות אוטומטיות מגרפים
    """

    def __init__(self):
        pass

    def analyze_workshop_costs(self, df):
        """
        ניתוח הוצאות לפי מוסך

        Args:
            df: DataFrame עם עמודות workshop, total

        Returns:
            dict: תובנות על התפלגות עלויות בין מוסכים
        """
        if df.empty or 'workshop' not in df.columns or 'total' not in df.columns:
            return {"insights": [], "alert_level": "info"}

        cost_by_garage = df.groupby('workshop')['total'].agg(['sum', 'mean', 'count']).reset_index()
        cost_by_garage = cost_by_garage.sort_values('sum', ascending=False)

        insights = []
        alert_level = "success"

        # מוסך הכי יקר
        most_expensive = cost_by_garage.iloc[0]
        insights.append(
            f"🏆 **המוסך עם ההוצאה הכוללת הגבוהה ביותר:** {most_expensive['workshop']} "
            f"(₪{most_expensive['sum']:,.0f}, {most_expensive['count']:.0f} טיפולים)"
        )

        # מוסך הכי זול
        cheapest = cost_by_garage.iloc[-1]
        insights.append(
            f"💰 **המוסך הכלכלי ביותר:** {cheapest['workshop']} "
            f"(₪{cheapest['sum']:,.0f}, {cheapest['count']:.0f} טיפולים)"
        )

        # השוואת עלות ממוצעת
        avg_cost_per_workshop = cost_by_garage['mean'].mean()
        expensive_workshops = cost_by_garage[cost_by_garage['mean'] > avg_cost_per_workshop * 1.3]

        if len(expensive_workshops) > 0:
            alert_level = "warning"
            insights.append(
                f"⚠️ **מוסכים יקרים מהממוצע ב-30%+:** {', '.join(expensive_workshops['workshop'].tolist())}"
            )

        # המלצה
        price_diff_percent = ((most_expensive['mean'] - cheapest['mean']) / cheapest['mean']) * 100
        if price_diff_percent > 50:
            alert_level = "warning"
            insights.append(
                f"💡 **המלצה:** שקול להעביר טיפולים מ-{most_expensive['workshop']} "
                f"ל-{cheapest['workshop']} - חיסכון פוטנציאלי של {price_diff_percent:.0f}% בעלות ממוצעת"
            )
        else:
            insights.append(
                f"✅ **המסקנה:** הפער בין המוסכים סביר ({price_diff_percent:.0f}%)"
            )

        return {
            "insights": insights,
            "alert_level": alert_level,
            "stats": {
                "most_expensive": most_expensive['workshop'],
                "cheapest": cheapest['workshop'],
                "price_diff_percent": price_diff_percent
            }
        }

    def analyze_cost_trends(self, df):
        """
        ניתוח מגמות עלויות לאורך זמן

        Args:
            df: DataFrame עם עמודות date, total

        Returns:
            dict: תובנות על מגמות ושינויים
        """
        if df.empty or 'date' not in df.columns or 'total' not in df.columns:
            return {"insights": [], "alert_level": "info"}

        insights = []
        alert_level = "success"

        # המרת תאריך
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        monthly_costs = df.set_index('date').resample('ME')['total'].sum().reset_index()

        if len(monthly_costs) < 2:
            return {
                "insights": ["📊 אין מספיק נתונים לניתוח מגמות (נדרשים לפחות 2 חודשים)"],
                "alert_level": "info"
            }

        # חישוב מגמה
        recent_3_months = monthly_costs.tail(3)['total'].mean() if len(monthly_costs) >= 3 else monthly_costs['total'].mean()
        prev_3_months = monthly_costs.head(len(monthly_costs)-3).tail(3)['total'].mean() if len(monthly_costs) >= 6 else monthly_costs.head(3)['total'].mean()

        trend_change = ((recent_3_months - prev_3_months) / prev_3_months) * 100 if prev_3_months > 0 else 0

        # זיהוי מגמה
        if abs(trend_change) < 10:
            insights.append(f"📊 **מגמה יציבה:** העלויות נשמרות יציבות (שינוי של {trend_change:+.1f}%)")
            alert_level = "success"
        elif trend_change > 10:
            insights.append(f"📈 **עלייה בעלויות:** גידול של {trend_change:.1f}% ב-3 החודשים האחרונים")
            alert_level = "warning"

            # בדיקת סיבות אפשריות
            if len(monthly_costs) >= 3:
                last_month_increase = ((monthly_costs.iloc[-1]['total'] - monthly_costs.iloc[-2]['total']) / monthly_costs.iloc[-2]['total']) * 100
                if last_month_increase > 30:
                    insights.append(f"⚠️ **שים לב:** קפיצה חדה בחודש האחרון ({last_month_increase:.0f}%)")
        else:
            insights.append(f"📉 **ירידה בעלויות:** חיסכון של {abs(trend_change):.1f}% ב-3 החודשים האחרונים")
            alert_level = "success"
            insights.append("✅ **מעולה!** המגמה חיובית")

        # זיהוי חודשים חריגים
        monthly_costs['z_score'] = (monthly_costs['total'] - monthly_costs['total'].mean()) / monthly_costs['total'].std()
        outliers = monthly_costs[abs(monthly_costs['z_score']) > 2]

        if len(outliers) > 0:
            for _, outlier in outliers.iterrows():
                month_name = outlier['date'].strftime('%Y-%m')
                insights.append(
                    f"🔍 **חודש חריג:** {month_name} - עלות של ₪{outlier['total']:,.0f} "
                    f"(סטיית תקן: {outlier['z_score']:.1f})"
                )

        return {
            "insights": insights,
            "alert_level": alert_level,
            "stats": {
                "trend_change_percent": trend_change,
                "recent_avg": recent_3_months,
                "outliers_count": len(outliers)
            }
        }

    def analyze_vehicle_model_costs(self, df):
        """
        ניתוח עלויות לפי דגם רכב

        Args:
            df: DataFrame עם עמודות make_model, total

        Returns:
            dict: תובנות על דגמים יקרים/זולים
        """
        if df.empty or 'make_model' not in df.columns or 'total' not in df.columns:
            return {"insights": [], "alert_level": "info"}

        insights = []
        alert_level = "success"

        # ניתוח לפי דגם
        model_analysis = df.groupby('make_model').agg({
            'total': ['sum', 'mean', 'count']
        }).reset_index()
        model_analysis.columns = ['make_model', 'total_cost', 'avg_cost', 'service_count']
        model_analysis = model_analysis.sort_values('total_cost', ascending=False)

        # דגם הכי יקר
        most_expensive = model_analysis.iloc[0]
        insights.append(
            f"🚗 **הדגם היקר ביותר:** {most_expensive['make_model']} - "
            f"₪{most_expensive['total_cost']:,.0f} סה\"כ "
            f"({most_expensive['service_count']:.0f} טיפולים)"
        )

        # דגם הכלכלי
        cheapest = model_analysis.iloc[-1]
        insights.append(
            f"💚 **הדגם הכלכלי ביותר:** {cheapest['make_model']} - "
            f"₪{cheapest['total_cost']:,.0f} סה\"כ"
        )

        # עלות ממוצעת לטיפול
        overall_avg = model_analysis['avg_cost'].mean()
        expensive_models = model_analysis[model_analysis['avg_cost'] > overall_avg * 1.5]

        if len(expensive_models) > 0:
            alert_level = "warning"
            insights.append(
                f"⚠️ **דגמים עם עלות טיפול גבוהה (50%+ מהממוצע):** "
                f"{', '.join(expensive_models['make_model'].tolist())}"
            )
            insights.append(
                f"💡 **המלצה:** שקול להחליף דגמים אלו בגריטה הבאה בדגמים כלכליים יותר"
            )

        # חלוקה באחוזים
        model_analysis['percentage'] = (model_analysis['total_cost'] / model_analysis['total_cost'].sum()) * 100
        top_contributor = model_analysis.iloc[0]

        if top_contributor['percentage'] > 40:
            insights.append(
                f"📊 **ריכוז עלויות:** {top_contributor['make_model']} אחראי ל-{top_contributor['percentage']:.0f}% מסך ההוצאות"
            )

        return {
            "insights": insights,
            "alert_level": alert_level,
            "stats": {
                "most_expensive_model": most_expensive['make_model'],
                "cheapest_model": cheapest['make_model'],
                "top_percentage": top_contributor['percentage']
            }
        }

    def analyze_scatter_outliers(self, df):
        """
        ניתוח חריגות בגרף הפיזור (קילומטראז' vs עלות)

        Args:
            df: DataFrame עם עמודות odometer_km, total, kind (optional)

        Returns:
            dict: תובנות על חריגות ודפוסים
        """
        if df.empty or 'odometer_km' not in df.columns or 'total' not in df.columns:
            return {"insights": [], "alert_level": "info"}

        insights = []
        alert_level = "success"

        # זיהוי חריגות סטטיסטיות
        df = df.copy()

        # חישוב Z-score לעלויות
        df['cost_z_score'] = (df['total'] - df['total'].mean()) / df['total'].std()

        # זיהוי חריגות חמורות (Z > 3)
        severe_outliers = df[abs(df['cost_z_score']) > 3]

        if len(severe_outliers) > 0:
            alert_level = "warning"
            insights.append(
                f"⚠️ **זוהו {len(severe_outliers)} חריגות חמורות** - טיפולים עם עלות גבוהה בצורה חריגה"
            )

            # פירוט החריגות הקיצוניות
            top_outliers = severe_outliers.nlargest(3, 'total')
            for idx, row in top_outliers.iterrows():
                km = row['odometer_km']
                cost = row['total']
                kind = row.get('kind', 'לא ידוע')
                plate = row.get('plate', 'לא ידוע')

                insights.append(
                    f"  🔴 {plate}: ₪{cost:,.0f} ב-{km:,.0f} ק\"מ ({kind})"
                )

        # ניתוח לפי סוג טיפול
        if 'kind' in df.columns:
            kind_analysis = df.groupby('kind').agg({
                'total': ['mean', 'count']
            }).reset_index()
            kind_analysis.columns = ['kind', 'avg_cost', 'count']
            kind_analysis = kind_analysis.sort_values('avg_cost', ascending=False)

            most_expensive_kind = kind_analysis.iloc[0]
            insights.append(
                f"💰 **סוג הטיפול היקר ביותר:** {most_expensive_kind['kind']} "
                f"(ממוצע ₪{most_expensive_kind['avg_cost']:,.0f})"
            )

        # ניתוח קורלציה
        correlation = df['odometer_km'].corr(df['total'])

        if abs(correlation) < 0.3:
            insights.append(
                "📊 **אין קשר חזק** בין קילומטראז' לעלות טיפול - העלויות מושפעות מגורמים אחרים"
            )
        elif correlation > 0.5:
            insights.append(
                f"📈 **קשר חיובי חזק** ({correlation:.2f}) - ככל שהרכב מזדקן, העלויות עולות"
            )
            alert_level = "info"

        # זיהוי דפוס של קבוצות
        low_km_high_cost = df[(df['odometer_km'] < df['odometer_km'].quantile(0.25)) &
                              (df['total'] > df['total'].quantile(0.75))]

        if len(low_km_high_cost) > 5:
            insights.append(
                f"🔍 **דפוס מעניין:** {len(low_km_high_cost)} טיפולים יקרים ברכבים עם קילומטראז' נמוך - "
                "ייתכן שמדובר בתאונות או תקלות מיוחדות"
            )

        # סיכום כללי
        if alert_level == "success":
            insights.insert(0, "✅ **מצב תקין:** העלויות נמצאות בטווח סביר ללא חריגות משמעותיות")

        return {
            "insights": insights,
            "alert_level": alert_level,
            "stats": {
                "severe_outliers": len(severe_outliers),
                "correlation": correlation
            }
        }


def render_insights_box(insights_data):
    """
    מציג את התובנות בממשק Streamlit

    Args:
        insights_data: dict עם insights, alert_level
    """
    import streamlit as st

    if not insights_data or not insights_data.get("insights"):
        return

    alert_level = insights_data.get("alert_level", "info")
    insights = insights_data.get("insights", [])

    # בחירת צבע לפי רמת התראה
    if alert_level == "warning":
        st.warning("📊 **תובנות AI מהגרף:**")
    elif alert_level == "success":
        st.success("📊 **תובנות AI מהגרף:**")
    else:
        st.info("📊 **תובנות AI מהגרף:**")

    # הצגת כל התובנות
    for insight in insights:
        st.markdown(f"- {insight}")
