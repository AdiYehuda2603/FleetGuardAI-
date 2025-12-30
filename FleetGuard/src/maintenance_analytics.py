"""
Advanced Maintenance Analytics Module

מודול ניתוח מתקדם לחקר הקשרים בין:
- קילומטראז' ושכיחות טיפולים
- עיתוי טיפולים (בזמן/מאוחר/מוקדם) ועלויות
- דפוסי תחזוקה ותוצאות כלכליות

Author: FleetGuardAI Team
Date: December 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional


class MaintenanceAnalytics:
    """מחלקה לניתוחים מתקדמים של תחזוקת צי רכב"""

    def __init__(self, db_manager):
        """
        אתחול מנתח התחזוקה

        Args:
            db_manager: מופע של DatabaseManager
        """
        self.db = db_manager

    def analyze_odometer_vs_maintenance_frequency(self) -> Dict:
        """
        ניתוח הקשר בין קילומטראז' לשכיחות טיפולים

        בודק:
        - מתאם בין ק"מ שנצברו לבין מספר הטיפולים
        - זיהוי רכבים עם טיפולים תכופים יחסית לק"מ
        - חישוב ממוצע ק"מ בין טיפולים

        Returns:
            dict: תוצאות הניתוח כולל מתאמים, ממוצעים וחריגים
        """
        try:
            # קבלת נתוני צי מלאים
            fleet_df = self.db.get_fleet_overview()
            invoices_df = self.db.get_all_invoices()

            if fleet_df.empty or invoices_df.empty:
                return {'error': 'No data available for analysis'}

            # חישוב קילומטראז' כולל לכל רכב
            vehicle_stats = []

            for _, vehicle in fleet_df.iterrows():
                vehicle_id = vehicle['vehicle_id']

                # קבלת כל החשבוניות של הרכב
                vehicle_invoices = invoices_df[invoices_df['vehicle_id'] == vehicle_id]

                if vehicle_invoices.empty:
                    continue

                # מיון לפי תאריך
                vehicle_invoices = vehicle_invoices.sort_values('date')

                # קילומטראז' ראשון ואחרון
                first_km = vehicle.get('initial_km', 0)
                latest_invoice = vehicle_invoices.iloc[-1]
                current_km = latest_invoice.get('odometer_km', first_km)

                total_km = current_km - first_km if current_km > first_km else 0

                # מספר טיפולים
                total_services = len(vehicle_invoices)
                routine_services = len(vehicle_invoices[vehicle_invoices['kind'] == 'routine'])

                # ממוצע ק"מ בין טיפולים
                km_per_service = total_km / total_services if total_services > 0 else 0

                # עלות כוללת
                total_cost = vehicle_invoices['total'].sum()
                cost_per_km = total_cost / total_km if total_km > 0 else 0

                vehicle_stats.append({
                    'vehicle_id': vehicle_id,
                    'plate': vehicle.get('plate', ''),
                    'make_model': vehicle.get('make_model', ''),
                    'total_km': total_km,
                    'total_services': total_services,
                    'routine_services': routine_services,
                    'km_per_service': km_per_service,
                    'total_cost': total_cost,
                    'cost_per_km': cost_per_km
                })

            if not vehicle_stats:
                return {'error': 'No vehicle statistics available'}

            stats_df = pd.DataFrame(vehicle_stats)

            # חישוב מתאם בין ק"מ לבין מספר טיפולים
            correlation = stats_df['total_km'].corr(stats_df['total_services'])

            # זיהוי רכבים עם תדירות טיפולים גבוהה/נמוכה
            median_km_per_service = stats_df['km_per_service'].median()
            high_maintenance = stats_df[stats_df['km_per_service'] < median_km_per_service * 0.7]
            low_maintenance = stats_df[stats_df['km_per_service'] > median_km_per_service * 1.3]

            return {
                'correlation_km_services': round(correlation, 3),
                'average_km_per_service': round(stats_df['km_per_service'].mean(), 0),
                'median_km_per_service': round(median_km_per_service, 0),
                'average_cost_per_km': round(stats_df['cost_per_km'].mean(), 3),
                'high_maintenance_vehicles': high_maintenance[['vehicle_id', 'plate', 'km_per_service', 'total_services']].to_dict('records'),
                'low_maintenance_vehicles': low_maintenance[['vehicle_id', 'plate', 'km_per_service', 'total_services']].to_dict('records'),
                'total_vehicles_analyzed': len(stats_df),
                'interpretation': self._interpret_km_correlation(correlation)
            }

        except Exception as e:
            return {'error': f'Analysis failed: {str(e)}'}

    def analyze_late_maintenance_cost_impact(self) -> Dict:
        """
        ניתוח השפעת איחורים בתחזוקה על העלויות

        משווה עלויות של:
        - טיפולים שבוצעו בזמן (±30 יום)
        - טיפולים מאוחרים (30+ יום)
        - טיפולים מוקדמים (לפני המועד)

        Returns:
            dict: השוואת עלויות וניתוח סטטיסטי
        """
        try:
            fleet_df = self.db.get_fleet_overview()
            invoices_df = self.db.get_all_invoices()

            if fleet_df.empty or invoices_df.empty:
                return {'error': 'No data available for analysis'}

            # סיווג טיפולים לפי עיתוי
            on_time_services = []
            late_services = []
            early_services = []

            for _, vehicle in fleet_df.iterrows():
                vehicle_id = vehicle['vehicle_id']
                last_test = vehicle.get('last_test_date')
                next_test = vehicle.get('next_test_date')

                if not last_test or not next_test:
                    continue

                try:
                    last_test_dt = datetime.strptime(str(last_test), '%Y-%m-%d')
                    next_test_dt = datetime.strptime(str(next_test), '%Y-%m-%d')
                except (ValueError, TypeError):
                    continue

                # קבלת טיפולי routine
                vehicle_invoices = invoices_df[
                    (invoices_df['vehicle_id'] == vehicle_id) &
                    (invoices_df['kind'] == 'routine')
                ]

                for _, invoice in vehicle_invoices.iterrows():
                    try:
                        invoice_date = datetime.strptime(str(invoice['date']), '%Y-%m-%d')
                        invoice_cost = invoice['total']

                        days_after_last = (invoice_date - last_test_dt).days
                        days_before_next = (next_test_dt - invoice_date).days

                        # סיווג לפי עיתוי
                        if days_after_last >= 0:  # אחרי הטיפול האחרון
                            if days_before_next >= -30:  # עד 30 יום איחור
                                on_time_services.append({
                                    'vehicle_id': vehicle_id,
                                    'cost': invoice_cost,
                                    'delay_days': -days_before_next if days_before_next < 0 else 0
                                })
                            else:  # יותר מ-30 יום איחור
                                late_services.append({
                                    'vehicle_id': vehicle_id,
                                    'cost': invoice_cost,
                                    'delay_days': -days_before_next
                                })
                        else:  # לפני הטיפול האחרון (מוקדם)
                            early_services.append({
                                'vehicle_id': vehicle_id,
                                'cost': invoice_cost,
                                'early_days': abs(days_after_last)
                            })
                    except (ValueError, TypeError):
                        continue

            # חישוב סטטיסטיקות
            on_time_costs = [s['cost'] for s in on_time_services] if on_time_services else [0]
            late_costs = [s['cost'] for s in late_services] if late_services else [0]
            early_costs = [s['cost'] for s in early_services] if early_services else [0]

            avg_on_time = np.mean(on_time_costs)
            avg_late = np.mean(late_costs)
            avg_early = np.mean(early_costs)

            # אחוז עלייה בעלות עבור טיפולים מאוחרים
            late_cost_increase_pct = ((avg_late - avg_on_time) / avg_on_time * 100) if avg_on_time > 0 else 0

            return {
                'on_time_maintenance': {
                    'count': len(on_time_services),
                    'average_cost': round(avg_on_time, 2),
                    'median_cost': round(np.median(on_time_costs), 2),
                    'total_cost': round(sum(on_time_costs), 2)
                },
                'late_maintenance': {
                    'count': len(late_services),
                    'average_cost': round(avg_late, 2),
                    'median_cost': round(np.median(late_costs), 2),
                    'total_cost': round(sum(late_costs), 2),
                    'average_delay_days': round(np.mean([s['delay_days'] for s in late_services]), 1) if late_services else 0
                },
                'early_maintenance': {
                    'count': len(early_services),
                    'average_cost': round(avg_early, 2),
                    'median_cost': round(np.median(early_costs), 2),
                    'total_cost': round(sum(early_costs), 2)
                },
                'cost_impact': {
                    'late_vs_on_time_increase_pct': round(late_cost_increase_pct, 1),
                    'late_vs_on_time_difference': round(avg_late - avg_on_time, 2),
                    'early_vs_on_time_difference': round(avg_early - avg_on_time, 2)
                },
                'interpretation': self._interpret_timing_impact(late_cost_increase_pct)
            }

        except Exception as e:
            return {'error': f'Analysis failed: {str(e)}'}

    def analyze_timing_compliance_vs_total_cost(self) -> Dict:
        """
        השוואה מקיפה: עלות תחזוקה כוללת לפי דפוס עיתוי

        משווה את העלות הכוללת לאורך זמן של רכבים שמתוחזקים:
        - בזמן (compliance גבוה)
        - באיחור משמעותי (compliance נמוך)
        - מוקדם מדי

        Returns:
            dict: ניתוח מקיף של עלויות לפי דפוסי תחזוקה
        """
        try:
            fleet_df = self.db.get_fleet_overview()
            invoices_df = self.db.get_all_invoices()

            if fleet_df.empty or invoices_df.empty:
                return {'error': 'No data available for analysis'}

            vehicle_profiles = []

            for _, vehicle in fleet_df.iterrows():
                vehicle_id = vehicle['vehicle_id']

                # קבלת כל הטיפולים
                vehicle_invoices = invoices_df[invoices_df['vehicle_id'] == vehicle_id]

                if vehicle_invoices.empty:
                    continue

                # חישוב compliance score (מ-driver analysis)
                compliance = self._calculate_vehicle_compliance(vehicle, invoices_df)

                # סיווג לקטגוריות
                if compliance >= 70:
                    timing_category = 'on_time'
                elif compliance >= 40:
                    timing_category = 'moderate_delay'
                else:
                    timing_category = 'significant_delay'

                # חישוב עלויות
                total_cost = vehicle_invoices['total'].sum()
                num_services = len(vehicle_invoices)
                avg_cost_per_service = total_cost / num_services if num_services > 0 else 0

                vehicle_profiles.append({
                    'vehicle_id': vehicle_id,
                    'timing_category': timing_category,
                    'compliance_score': compliance,
                    'total_cost': total_cost,
                    'num_services': num_services,
                    'avg_cost_per_service': avg_cost_per_service
                })

            if not vehicle_profiles:
                return {'error': 'No vehicle profiles available'}

            profiles_df = pd.DataFrame(vehicle_profiles)

            # ניתוח לפי קטגוריה
            categories = {}
            for category in ['on_time', 'moderate_delay', 'significant_delay']:
                cat_data = profiles_df[profiles_df['timing_category'] == category]

                if not cat_data.empty:
                    categories[category] = {
                        'vehicle_count': len(cat_data),
                        'average_total_cost': round(cat_data['total_cost'].mean(), 2),
                        'average_cost_per_service': round(cat_data['avg_cost_per_service'].mean(), 2),
                        'average_compliance': round(cat_data['compliance_score'].mean(), 1),
                        'total_fleet_cost': round(cat_data['total_cost'].sum(), 2)
                    }

            # חישוב חיסכון פוטנציאלי
            on_time_avg = categories.get('on_time', {}).get('average_total_cost', 0)
            delay_avg = categories.get('significant_delay', {}).get('average_total_cost', 0)
            potential_savings_per_vehicle = delay_avg - on_time_avg if delay_avg > on_time_avg else 0

            return {
                'timing_categories': categories,
                'insights': {
                    'potential_savings_per_vehicle': round(potential_savings_per_vehicle, 2),
                    'recommendation': self._generate_timing_recommendation(categories)
                },
                'total_vehicles_analyzed': len(profiles_df)
            }

        except Exception as e:
            return {'error': f'Analysis failed: {str(e)}'}

    def _calculate_vehicle_compliance(self, vehicle_data, invoices_df) -> float:
        """חישוב אחוז עמידה בזמנים לרכב בודד"""
        try:
            vehicle_id = vehicle_data['vehicle_id']
            last_test = vehicle_data.get('last_test_date')
            next_test = vehicle_data.get('next_test_date')

            if not last_test or not next_test:
                return 50.0

            last_test_dt = datetime.strptime(str(last_test), '%Y-%m-%d')
            next_test_dt = datetime.strptime(str(next_test), '%Y-%m-%d')

            vehicle_invoices = invoices_df[
                (invoices_df['vehicle_id'] == vehicle_id) &
                (invoices_df['kind'] == 'routine')
            ]

            if vehicle_invoices.empty:
                return 50.0

            total = 0
            on_time = 0

            for _, invoice in vehicle_invoices.iterrows():
                try:
                    invoice_date = datetime.strptime(str(invoice['date']), '%Y-%m-%d')
                    days_after_last = (invoice_date - last_test_dt).days
                    days_before_next = (next_test_dt - invoice_date).days

                    if days_after_last >= 0:
                        total += 1
                        if days_before_next >= -30:
                            on_time += 1
                except:
                    continue

            return (on_time / total * 100) if total > 0 else 50.0

        except:
            return 50.0

    def _interpret_km_correlation(self, correlation: float) -> str:
        """פרשנות למתאם בין ק"מ לטיפולים"""
        if correlation > 0.7:
            return "מתאם חזק מאוד - ככל שהרכב נוסע יותר, יש יותר טיפולים (צפוי)"
        elif correlation > 0.5:
            return "מתאם בינוני-חזק - קיים קשר ברור בין ק\"מ לטיפולים"
        elif correlation > 0.3:
            return "מתאם חלש-בינוני - יש גורמים נוספים שמשפיעים על תדירות הטיפולים"
        else:
            return "מתאם חלש - תדירות הטיפולים לא תלויה בעיקר בק\"מ"

    def _interpret_timing_impact(self, increase_pct: float) -> str:
        """פרשנות להשפעת איחורים על עלויות"""
        if increase_pct > 30:
            return f"טיפולים מאוחרים יקרים יותר ב-{increase_pct:.1f}% - איחורים גורמים לנזקים משמעותיים!"
        elif increase_pct > 15:
            return f"טיפולים מאוחרים יקרים יותר ב-{increase_pct:.1f}% - יש השפעה כלכלית ניכרת לאיחורים"
        elif increase_pct > 5:
            return f"טיפולים מאוחרים יקרים יותר ב-{increase_pct:.1f}% - השפעה קטנה אך מזוהה"
        elif increase_pct < -5:
            return f"טיפולים מאוחרים זולים יותר ב-{abs(increase_pct):.1f}% - תוצאה לא צפויה, יש לבדוק נתונים"
        else:
            return "אין הבדל משמעותי בעלויות בין טיפולים בזמן למאוחרים"

    def _generate_timing_recommendation(self, categories: Dict) -> str:
        """המלצות על בסיס ניתוח עיתוי"""
        on_time = categories.get('on_time', {})
        delayed = categories.get('significant_delay', {})

        on_time_cost = on_time.get('average_total_cost', 0)
        delayed_cost = delayed.get('average_total_cost', 0)

        if delayed_cost > on_time_cost * 1.2:
            return "המלצה חזקה: רכבים שמתוחזקים בזמן חוסכים כסף משמעותי. יש להקפיד על עמידה בלוחות זמנים!"
        elif delayed_cost > on_time_cost * 1.1:
            return "המלצה: עמידה בזמני תחזוקה משתלמת כלכלית. יש לשפר את הציות ללוחות זמנים."
        else:
            return "לא נמצא הבדל משמעותי בעלויות בין דפוסי תחזוקה שונים."

    def get_comprehensive_maintenance_insights(self) -> Dict:
        """
        קבלת כל התובנות במכה אחת - לשימוש ב-AI Analyst

        Returns:
            dict: כל הניתוחים במבנה מאורגן
        """
        return {
            'odometer_analysis': self.analyze_odometer_vs_maintenance_frequency(),
            'timing_cost_impact': self.analyze_late_maintenance_cost_impact(),
            'compliance_comparison': self.analyze_timing_compliance_vs_total_cost()
        }
