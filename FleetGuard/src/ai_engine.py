import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# טעינת משתני סביבה מקובץ .env
load_dotenv()

try:
    from src.database_manager import DatabaseManager
    from src.fleet_analysis_tools import FleetAnalyzer
except ImportError:
    # מאפשר הרצה גם כסקריפט עצמאי לבדיקה
    from database_manager import DatabaseManager
    try:
        from fleet_analysis_tools import FleetAnalyzer
    except ImportError:
        FleetAnalyzer = None

class FleetAIEngine:
    def __init__(self, api_key=None):
        # מנסה למשוך מפתח מהסביבה או מהארגומנט
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            print("⚠️ Warning: No OpenAI API Key found. AI features will not work.")

        self.client = OpenAI(api_key=self.api_key)
        self.db = DatabaseManager()
        self.analyzer = FleetAnalyzer() if FleetAnalyzer else None

    def _create_data_summary(self):
        """
        יוצר סיכום קומפקטי של הנתונים במקום לשלוח את כל הטבלה
        כולל מידע על קילומטראז' מעודכן מכל הרכבים
        """
        df_invoices = self.db.get_all_invoices()
        
        # קבלת מידע מלא על רכבים עם קילומטראז' מעודכן
        df_vehicles_stats = self.db.get_vehicle_with_stats()
        
        # חישוב קילומטראז' נסוע לכל רכב
        vehicle_mileage = {}
        for _, vehicle in df_vehicles_stats.iterrows():
            vehicle_id = vehicle['vehicle_id']
            initial_km = vehicle.get('initial_odometer_km', 0) or 0
            current_km = vehicle.get('current_km', 0) or 0
            
            # אם יש קילומטראז' מעודכן, חשב את הנסוע
            if pd.notna(current_km) and current_km > 0:
                km_driven = max(0, current_km - initial_km)
            else:
                # נסה למצוא מהחשבוניות
                vehicle_invoices = df_invoices[df_invoices['vehicle_id'] == vehicle_id]
                if len(vehicle_invoices) > 0:
                    max_km = vehicle_invoices['odometer_km'].max()
                    if pd.notna(max_km):
                        km_driven = max(0, max_km - initial_km)
                    else:
                        km_driven = 0
                else:
                    km_driven = 0
            
            vehicle_mileage[vehicle_id] = {
                'initial_km': initial_km,
                'current_km': current_km if pd.notna(current_km) else initial_km,
                'km_driven': km_driven,
                'last_service_date': vehicle.get('last_service_date'),
                'total_services': vehicle.get('total_services', 0),
                'total_cost': vehicle.get('total_cost', 0),
                'avg_service_cost': vehicle.get('avg_service_cost', 0)
            }
        
        # מידע על רכבים לפי קילומטראז' נסוע
        vehicles_by_mileage = sorted(
            vehicle_mileage.items(),
            key=lambda x: x[1]['km_driven'],
            reverse=True
        )[:10]  # 10 הרכבים עם הכי הרבה קילומטרים

        summary = {
            "total_invoices": len(df_invoices),
            "total_spent": df_invoices['total'].sum(),
            "date_range": f"{df_invoices['date'].min()} to {df_invoices['date'].max()}",
            "workshops": df_invoices.groupby('workshop')['total'].agg(['count', 'sum', 'mean']).to_dict('index'),
            "vehicles": df_invoices.groupby('vehicle_id')['total'].agg(['count', 'sum', 'mean']).to_dict('index'),
            "by_kind": df_invoices.groupby('kind')['total'].agg(['count', 'sum', 'mean']).to_dict('index'),
            "recent_invoices": df_invoices.head(20).to_dict('records'),  # רק 20 האחרונים מטבלת החשבוניות
            # מידע חדש על קילומטראז'
            "vehicle_mileage": vehicle_mileage,  # כל הרכבים עם קילומטראז'
            "top_vehicles_by_mileage": [
                {
                    'vehicle_id': vid,
                    'km_driven': info['km_driven'],
                    'current_km': info['current_km'],
                    'initial_km': info['initial_km'],
                    'total_services': info['total_services'],
                    'total_cost': info['total_cost']
                }
                for vid, info in vehicles_by_mileage
            ],
            # מידע על קילומטראז' מחשבוניות
            "invoices_with_odometer": df_invoices[df_invoices['odometer_km'].notna()].to_dict('records')[:50]  # 50 חשבוניות עם קילומטראז'
        }

        return summary

    def _create_strategic_summary(self):
        """
        יוצר סיכום אסטרטגי מלא מ-Agent H (Strategic Analyst)
        כולל: אמינות דגמים, המלצות החלפה, רכבים מצטיינים, השוואת מוסכים
        """
        if not self.analyzer:
            return {}

        try:
            # קבלת כל התובנות האסטרטגיות מ-Agent H
            strategic_insights = self.analyzer.get_strategic_insights()

            # קבלת נתוני צי מלאים
            fleet_summary = self.analyzer.get_fleet_status_summary()

            return {
                'strategic_insights': strategic_insights,
                'fleet_overview': {
                    'total_vehicles': len(fleet_summary),
                    'active_vehicles': len(fleet_summary[fleet_summary['status'] == 'active']),
                    'near_retirement': len(fleet_summary[fleet_summary.get('retirement_status', '') == 'near_retirement']),
                    'avg_annual_cost': fleet_summary['annual_cost'].mean() if 'annual_cost' in fleet_summary.columns else 0
                }
            }
        except Exception as e:
            print(f"Error creating strategic summary: {e}")
            return {}

    def _analyze_drivers(self):
        """
        ניתוח מעמיק של ביצועי נהגים
        מזהה נהגים מצטיינים ונהגים שצריכים שיפור
        """
        try:
            # קבלת נתוני צי מלאים עם נהגים
            fleet_df = self.db.get_fleet_overview()

            if fleet_df.empty or 'assigned_to' not in fleet_df.columns:
                return {}

            # ניתוח לפי נהג
            driver_stats = []

            for driver in fleet_df['assigned_to'].dropna().unique():
                if not driver or driver.strip() == '':
                    continue

                driver_vehicles = fleet_df[fleet_df['assigned_to'] == driver]

                total_services = driver_vehicles['total_services'].sum()
                total_cost = driver_vehicles['total_cost'].sum()
                num_vehicles = len(driver_vehicles)
                avg_cost_per_vehicle = total_cost / num_vehicles if num_vehicles > 0 else 0
                avg_services_per_vehicle = total_services / num_vehicles if num_vehicles > 0 else 0

                # חישוב ציון ביצועים (ככל שנמוך יותר - טוב יותר)
                # משקלל עלויות וכמות תקלות
                performance_score = (avg_cost_per_vehicle / 1000) + (avg_services_per_vehicle * 5)

                driver_stats.append({
                    'driver': driver,
                    'num_vehicles': num_vehicles,
                    'total_services': total_services,
                    'total_cost': total_cost,
                    'avg_cost_per_vehicle': avg_cost_per_vehicle,
                    'avg_services_per_vehicle': avg_services_per_vehicle,
                    'performance_score': performance_score,
                    'vehicles': driver_vehicles['vehicle_id'].tolist()
                })

            # מיון לפי ציון ביצועים
            driver_stats_sorted = sorted(driver_stats, key=lambda x: x['performance_score'])

            # 3 הטובים ביותר (ציון נמוך = טוב)
            top_3_drivers = driver_stats_sorted[:3]

            # 3 הגרועים ביותר (ציון גבוה = צריך שיפור)
            bottom_3_drivers = driver_stats_sorted[-3:] if len(driver_stats_sorted) >= 3 else []

            return {
                'all_drivers': driver_stats_sorted,
                'top_performers': top_3_drivers,
                'need_improvement': bottom_3_drivers,
                'total_drivers': len(driver_stats_sorted)
            }

        except Exception as e:
            print(f"Error analyzing drivers: {e}")
            return {}

    def _get_full_data_context(self):
        """
        מחזיר הקשר מלא של כל הנתונים:
        - טבלת רכבים מלאה
        - טבלת חשבוניות גולמית
        - ניתוחים צולבים
        - ניתוח נהגים
        """
        try:
            # נתוני צי מלאים
            fleet_df = self.db.get_fleet_overview()

            # חשבוניות גולמיות
            invoices_df = self.db.get_all_invoices()

            # נתונים מאוחדים (JOIN)
            full_view_df = self.db.get_full_view()

            return {
                'fleet_data': fleet_df.to_dict('records'),
                'raw_invoices': invoices_df.head(100).to_dict('records'),  # 100 אחרונות
                'full_view': full_view_df.head(100).to_dict('records'),
                'fleet_columns': fleet_df.columns.tolist(),
                'invoice_columns': invoices_df.columns.tolist()
            }
        except Exception as e:
            print(f"Error getting full data context: {e}")
            return {}

    def ask_analyst(self, user_question):
        """
        הפונקציה המרכזית: מקבלת שאלה בעברית, ומחזירה תשובה מבוססת נתונים
        כולל גישה מלאה לנתונים אסטרטגיים מ-Agent H וניתוח נהגים
        """
        # יצירת סיכום קומפקטי במקום לשלוח את כל הנתונים
        data_summary = self._create_data_summary()

        # הוספת נתונים אסטרטגיים מ-Agent H
        strategic_summary = self._create_strategic_summary()

        # ניתוח נהגים
        driver_analysis = self._analyze_drivers()

        # נתונים מלאים מכל הטבלאות
        full_data = self._get_full_data_context()

        # 3. בניית הפרומפט עם סיכום מלא כולל קילומטראז'
        # פורמט מידע על קילומטראז'
        mileage_info = "\n".join([
            f"  {v['vehicle_id']}: {v['km_driven']:,.0f} ק\"מ נסוע (מ-{v['initial_km']:,.0f} ל-{v['current_km']:,.0f}), {v['total_services']} טיפולים, ₪{v['total_cost']:,.0f} סה\"כ"
            for v in data_summary['top_vehicles_by_mileage']
        ])
        
        # מידע על חשבוניות עם קילומטראז'
        invoices_with_km_list = data_summary['invoices_with_odometer']
        if len(invoices_with_km_list) > 0:
            invoices_with_km = pd.DataFrame(invoices_with_km_list)
            # בדיקה שיש את העמודות הנדרשות
            required_cols = ['date', 'vehicle_id', 'plate', 'odometer_km', 'workshop', 'total']
            available_cols = [col for col in required_cols if col in invoices_with_km.columns]
            if len(available_cols) > 0:
                invoices_km_info = invoices_with_km[available_cols].head(20).to_string(index=False)
            else:
                invoices_km_info = "אין חשבוניות עם קילומטראז'"
        else:
            invoices_km_info = "אין חשבוניות עם קילומטראז'"

        # פורמט נתונים אסטרטגיים
        strategic_info = ""
        if strategic_summary:
            insights = strategic_summary.get('strategic_insights', {})
            fleet_overview = strategic_summary.get('fleet_overview', {})

            # אמינות דגמים
            reliability = insights.get('reliability_by_model', {})
            if reliability:
                strategic_info += f"\n**MODEL RELIABILITY ANALYSIS:**\n"
                strategic_info += f"  Best Model (Most Reliable): {reliability.get('best_model', 'N/A')}\n"
                strategic_info += f"  Worst Model (Least Reliable): {reliability.get('worst_model', 'N/A')}\n"
                if reliability.get('details'):
                    strategic_info += "  Detailed Rankings:\n"
                    for model in reliability['details'][:5]:
                        strategic_info += f"    - {model['make_model']}: Reliability Score {model.get('reliability_score', 0):.1f}, Avg Services: {model.get('avg_services', 0):.1f}\n"

            # המלצות החלפה
            replacements = insights.get('replacement_recommendations', [])
            if replacements:
                strategic_info += f"\n**REPLACEMENT RECOMMENDATIONS (סה\"כ {len(replacements)} רכבים):**\n"
                for rec in replacements[:5]:
                    strategic_info += f"  - {rec['vehicle_id']} ({rec['plate']}): Priority {rec['priority_score']}/100\n"
                    strategic_info += f"    Reasons: {', '.join(rec['reasons'])}\n"

            # רכבים מצטיינים
            top_performers = insights.get('top_performers', [])
            if top_performers:
                strategic_info += f"\n**TOP PERFORMING VEHICLES (רכבים מצטיינים):**\n"
                for performer in top_performers[:5]:
                    strategic_info += f"  - {performer['vehicle_id']} ({performer['plate']}): Annual Cost ₪{performer.get('annual_cost', 0):,.0f}, Services: {performer.get('total_services', 0)}\n"

            # השוואת מוסכים
            workshop_comp = insights.get('workshop_comparison', {})
            if workshop_comp:
                strategic_info += f"\n**WORKSHOP COMPARISON:**\n"
                cheapest = workshop_comp.get('cheapest', {})
                expensive = workshop_comp.get('most_expensive', {})
                if cheapest:
                    strategic_info += f"  Cheapest: {cheapest.get('workshop')} - Avg ₪{cheapest.get('avg_cost', 0):,.0f}\n"
                if expensive:
                    strategic_info += f"  Most Expensive: {expensive.get('workshop')} - Avg ₪{expensive.get('avg_cost', 0):,.0f}\n"

            # סקירת צי
            strategic_info += f"\n**FLEET OVERVIEW:**\n"
            strategic_info += f"  Total Vehicles: {fleet_overview.get('total_vehicles', 0)}\n"
            strategic_info += f"  Active Vehicles: {fleet_overview.get('active_vehicles', 0)}\n"
            strategic_info += f"  Near Retirement: {fleet_overview.get('near_retirement', 0)}\n"
            strategic_info += f"  Avg Annual Cost: ₪{fleet_overview.get('avg_annual_cost', 0):,.0f}\n"

        # פורמט ניתוח נהגים
        driver_info = ""
        if driver_analysis and driver_analysis.get('total_drivers', 0) > 0:
            driver_info += f"\n**DRIVER PERFORMANCE ANALYSIS (ניתוח ביצועי נהגים):**\n"
            driver_info += f"  Total Active Drivers: {driver_analysis['total_drivers']}\n\n"

            # 3 נהגים מצטיינים
            top_drivers = driver_analysis.get('top_performers', [])
            if top_drivers:
                driver_info += "  🏆 TOP 3 PERFORMING DRIVERS (נהגים מצטיינים):\n"
                for i, driver in enumerate(top_drivers, 1):
                    driver_info += f"    {i}. {driver['driver']}\n"
                    driver_info += f"       - Vehicles: {driver['num_vehicles']} | Total Services: {driver['total_services']}\n"
                    driver_info += f"       - Total Cost: ₪{driver['total_cost']:,.0f} | Avg/Vehicle: ₪{driver['avg_cost_per_vehicle']:,.0f}\n"
                    driver_info += f"       - Performance Score: {driver['performance_score']:.1f} (lower is better)\n"
                    driver_info += f"       - Vehicle IDs: {', '.join(driver['vehicles'])}\n"

            # 3 נהגים שצריכים שיפור
            bottom_drivers = driver_analysis.get('need_improvement', [])
            if bottom_drivers:
                driver_info += "\n  ⚠️ DRIVERS NEEDING IMPROVEMENT (נהגים שצריכים שיפור):\n"
                for i, driver in enumerate(bottom_drivers, 1):
                    driver_info += f"    {i}. {driver['driver']}\n"
                    driver_info += f"       - Vehicles: {driver['num_vehicles']} | Total Services: {driver['total_services']}\n"
                    driver_info += f"       - Total Cost: ₪{driver['total_cost']:,.0f} | Avg/Vehicle: ₪{driver['avg_cost_per_vehicle']:,.0f}\n"
                    driver_info += f"       - Performance Score: {driver['performance_score']:.1f} (higher = needs improvement)\n"
                    driver_info += f"       - Vehicle IDs: {', '.join(driver['vehicles'])}\n"

        # מידע על העמודות הזמינות
        data_schema_info = ""
        if full_data:
            data_schema_info += f"\n**AVAILABLE DATA SCHEMA (מבנה נתונים):**\n"
            data_schema_info += f"  Fleet Table Columns: {', '.join(full_data.get('fleet_columns', []))}\n"
            data_schema_info += f"  Invoice Table Columns: {', '.join(full_data.get('invoice_columns', []))}\n"
            data_schema_info += f"  Total Fleet Records: {len(full_data.get('fleet_data', []))}\n"
            data_schema_info += f"  Sample Invoices Available: {len(full_data.get('raw_invoices', []))}\n"

        system_prompt = f"""
        You are an expert Fleet Manager and Strategic Business Analyst named 'FleetGuard AI'.
        You have FULL ACCESS to fleet data including invoices, vehicles, mileage information,
        AND strategic business intelligence from Agent H (Strategic Analyst).

        SUMMARY:
        - Total Invoices: {data_summary['total_invoices']}
        - Total Spent: ₪{data_summary['total_spent']:,.2f}
        - Date Range: {data_summary['date_range']}

        BY WORKSHOP:
        {self._format_dict(data_summary['workshops'])}

        BY VEHICLE (Cost Summary):
        {self._format_dict(data_summary['vehicles'])}

        BY SERVICE TYPE:
        {self._format_dict(data_summary['by_kind'])}

        **VEHICLE MILEAGE INFORMATION (קילומטראז' נסוע):**
        Top vehicles by kilometers driven:
        {mileage_info}

        **INVOICES WITH ODOMETER READINGS (חשבוניות עם קילומטראז'):**
        {invoices_km_info}

        RECENT INVOICES (sample):
        {pd.DataFrame(data_summary['recent_invoices'])[['date', 'workshop', 'vehicle_id', 'plate', 'odometer_km', 'total']].to_string(index=False) if 'odometer_km' in pd.DataFrame(data_summary['recent_invoices']).columns else pd.DataFrame(data_summary['recent_invoices'])[['date', 'workshop', 'vehicle_id', 'plate', 'total']].to_string(index=False)}

        ═══════════════════════════════════════════════════════════════════
        **STRATEGIC BUSINESS INTELLIGENCE (Agent H Data):**
        {strategic_info}
        ═══════════════════════════════════════════════════════════════════

        ═══════════════════════════════════════════════════════════════════
        **DRIVER PERFORMANCE INTELLIGENCE:**
        {driver_info}
        ═══════════════════════════════════════════════════════════════════

        {data_schema_info}

        **IMPORTANT INSTRUCTIONS:**
        1. You have COMPLETE access to mileage data (odometer_km) from invoices and vehicle statistics.
        2. When asked about "which vehicle traveled the most" or "kilometers driven", use the vehicle_mileage data.
        3. The "km_driven" field shows total kilometers driven (current_km - initial_km).
        4. Answer in Hebrew (Professional/Technical tone).
        5. Be precise with numbers - format clearly (e.g., ₪1,200, 15,000 ק\"מ).
        6. If asked about mileage, provide specific numbers from the data above.
        7. You can now answer STRATEGIC BUSINESS QUESTIONS such as:
           - Which vehicle model is most reliable? (use MODEL RELIABILITY ANALYSIS)
           - Which vehicles should we replace? (use REPLACEMENT RECOMMENDATIONS)
           - Which vehicles are best performers? (use TOP PERFORMING VEHICLES)
           - Which workshop is cheapest/most expensive? (use WORKSHOP COMPARISON)
           - Should we buy more of a specific model? (use reliability and cost data)
           - What's our fleet retirement status? (use FLEET OVERVIEW)
        8. You can also answer operational questions about:
           - Which vehicle traveled the most (use top_vehicles_by_mileage)
           - Current odometer readings (use vehicle_mileage)
           - Kilometers driven per vehicle (use km_driven)
           - Service history with mileage (use invoices_with_odometer)
        9. You can now answer DRIVER PERFORMANCE questions:
           - Which drivers are performing best? (use TOP 3 PERFORMING DRIVERS)
           - Which drivers need improvement? (use DRIVERS NEEDING IMPROVEMENT)
           - How is driver X performing? (search in DRIVER PERFORMANCE ANALYSIS)
           - Which driver has the most/least service costs?
           - If a vehicle has many services, identify the assigned driver from fleet data
        10. You have access to ALL database columns listed in AVAILABLE DATA SCHEMA
        11. You can perform data cross-analysis:
            - Join fleet data with invoice data using vehicle_id
            - Analyze patterns by driver, vehicle model, workshop
            - Find correlations (e.g., high-cost vehicles and their drivers)
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # מודל זול וחסכוני יותר
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                temperature=0  # דיוק מקסימלי
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"שגיאה בתקשורת עם ה-AI: {str(e)}"

    def _format_dict(self, data_dict):
        """עוזר לעיצוב מילונים בצורה קריאה"""
        lines = []
        for key, values in data_dict.items():
            if isinstance(values, dict):
                count = values.get('count', 0)
                total = values.get('sum', 0)
                avg = values.get('mean', 0)
                lines.append(f"  {key}: {count} invoices, ₪{total:,.0f} total, ₪{avg:,.0f} average")
            else:
                lines.append(f"  {key}: {values}")
        return "\n".join(lines)

# --- בדיקה מהירה (אם מריצים את הקובץ ישירות) ---
if __name__ == "__main__":
    # וודא שיש לך OPENAI_API_KEY מוגדר במשתני הסביבה
    engine = FleetAIEngine()
    print("🤖 AI Engine Initialized.")
    
    q = "איזה רכב עשה הכי הרבה קילומטרים ומה היה הטיפול האחרון שלו?"
    print(f"שאלה: {q}")
    print("חושב...")
    ans = engine.ask_analyst(q)
    print("תשובה:")
    print(ans)