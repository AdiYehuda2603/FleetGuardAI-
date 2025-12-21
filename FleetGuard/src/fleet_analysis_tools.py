# -*- coding: utf-8 -*-
"""
Fleet Analysis Tools - Agent G & H Support Functions
כלים לניתוח צי רכב ותובנות אסטרטגיות
"""

import pandas as pd
from datetime import datetime, timedelta
from src.database_manager import DatabaseManager
from src.retirement_calculator import RetirementCalculator


class FleetAnalyzer:
    """
    מנתח את הצי ומספק תובנות עסקיות
    תומך ב-Agent G (Fleet Overview) ו-Agent H (Strategic Analyst)
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.retirement_calc = RetirementCalculator()

    def get_fleet_status_summary(self):
        """
        סיכום מצב הצי - לשימוש Agent G
        """
        fleet_df = self.db.get_fleet_overview()

        # חישוב גריטה לכל רכב
        retirement_data = self.retirement_calc.get_retirement_summary(fleet_df)

        # מיזוג נתונים
        fleet_df = fleet_df.merge(retirement_data, on='vehicle_id', how='left')

        # חישוב עלות שנתית ממוצעת
        fleet_df['annual_cost'] = fleet_df.apply(
            lambda row: self._calculate_annual_cost(row),
            axis=1
        )

        return fleet_df

    def _calculate_annual_cost(self, row):
        """מחשב עלות שנתית ממוצעת"""
        if pd.isna(row['purchase_date']) or pd.isna(row['total_cost']):
            return 0

        try:
            purchase_date = datetime.strptime(row['purchase_date'], "%Y-%m-%d")
            days_in_fleet = (datetime.now() - purchase_date).days

            if days_in_fleet <= 0:
                return 0

            years_in_fleet = days_in_fleet / 365.25
            annual_cost = row['total_cost'] / years_in_fleet

            return round(annual_cost, 2)
        except:
            return 0

    def get_strategic_insights(self):
        """
        תובנות אסטרטגיות - לשימוש Agent H
        """
        fleet_df = self.get_fleet_status_summary()
        invoices_df = self.db.get_all_invoices()

        insights = {
            'reliability_by_model': self._analyze_reliability(fleet_df),
            'cost_efficiency': self._analyze_cost_efficiency(fleet_df),
            'replacement_recommendations': self._get_replacement_recommendations(fleet_df),
            'top_performers': self._get_top_performers(fleet_df),
            'cost_trends': self._analyze_cost_trends(invoices_df),
            'workshop_comparison': self._compare_workshops(invoices_df)
        }

        return insights

    def _analyze_reliability(self, fleet_df):
        """
        ניתוח אמינות לפי דגם
        אמינות = פחות טיפולים = טוב יותר
        """
        if fleet_df.empty:
            return {}

        # קיבוץ לפי דגם
        by_model = fleet_df.groupby('make_model').agg({
            'vehicle_id': 'count',
            'total_services': 'mean',
            'total_cost': 'mean',
            'annual_cost': 'mean',
            'year': 'mean'
        }).reset_index()

        by_model.columns = ['make_model', 'vehicle_count', 'avg_services',
                            'avg_total_cost', 'avg_annual_cost', 'avg_year']

        # חישוב ציון אמינות (ככל שפחות טיפולים = ציון גבוה יותר)
        max_services = by_model['avg_services'].max()
        if max_services > 0:
            by_model['reliability_score'] = 100 * (1 - by_model['avg_services'] / max_services)
        else:
            by_model['reliability_score'] = 100

        by_model = by_model.sort_values('reliability_score', ascending=False)

        return {
            'best_model': by_model.iloc[0]['make_model'] if len(by_model) > 0 else 'N/A',
            'worst_model': by_model.iloc[-1]['make_model'] if len(by_model) > 0 else 'N/A',
            'details': by_model.to_dict('records')
        }

    def _analyze_cost_efficiency(self, fleet_df):
        """ניתוח יעילות עלויות"""
        if fleet_df.empty:
            return {}

        fleet_df_sorted = fleet_df.sort_values('annual_cost')

        return {
            'most_economical': fleet_df_sorted.iloc[0].to_dict() if len(fleet_df_sorted) > 0 else {},
            'most_expensive': fleet_df_sorted.iloc[-1].to_dict() if len(fleet_df_sorted) > 0 else {},
            'fleet_avg_annual_cost': fleet_df['annual_cost'].mean()
        }

    def _get_replacement_recommendations(self, fleet_df):
        """המלצות להחלפת רכבים"""
        recommendations = []

        for _, row in fleet_df.iterrows():
            score = 0
            reasons = []

            # קריטריון 1: קרוב לגריטה
            if row.get('days_until_retirement', 365) < 180:
                score += 40
                reasons.append('קרוב למועד גריטה')

            # קריטריון 2: עלות שנתית גבוהה
            avg_cost = fleet_df['annual_cost'].mean()
            if row.get('annual_cost', 0) > avg_cost * 1.5:
                score += 30
                reasons.append('עלות תחזוקה גבוהה מאוד')

            # קריטריון 3: הרבה תקלות
            avg_services = fleet_df['total_services'].mean()
            if row.get('total_services', 0) > avg_services * 1.3:
                score += 20
                reasons.append('תקלות תכופות')

            # קריטריון 4: רכב ישן
            current_year = datetime.now().year
            vehicle_age = current_year - int(row.get('year', current_year))
            if vehicle_age >= 4:
                score += 10
                reasons.append(f'גיל הרכב: {vehicle_age} שנים')

            if score >= 50:
                recommendations.append({
                    'vehicle_id': row['vehicle_id'],
                    'plate': row['plate'],
                    'make_model': row['make_model'],
                    'priority_score': score,
                    'reasons': reasons
                })

        recommendations = sorted(recommendations, key=lambda x: x['priority_score'], reverse=True)

        return recommendations

    def _get_top_performers(self, fleet_df):
        """רכבים מצטיינים (זולים בתחזוקה)"""
        if fleet_df.empty:
            return []

        # רכבים עם עלות נמוכה וטיפולים מעטים
        fleet_df_active = fleet_df[fleet_df['status'] == 'active'].copy()

        if fleet_df_active.empty:
            return []

        fleet_df_active['performance_score'] = (
            (1 / (fleet_df_active['annual_cost'] + 1)) * 50 +
            (1 / (fleet_df_active['total_services'] + 1)) * 50
        )

        top_5 = fleet_df_active.nlargest(5, 'performance_score')

        return top_5[['vehicle_id', 'plate', 'make_model', 'annual_cost',
                      'total_services', 'performance_score']].to_dict('records')

    def _analyze_cost_trends(self, invoices_df):
        """ניתוח מגמות עלויות"""
        if invoices_df.empty:
            return {}

        invoices_df['date'] = pd.to_datetime(invoices_df['date'])
        invoices_df['year_month'] = invoices_df['date'].dt.to_period('M')

        monthly_costs = invoices_df.groupby('year_month')['total'].sum().reset_index()
        monthly_costs.columns = ['month', 'total_cost']
        monthly_costs['month'] = monthly_costs['month'].astype(str)

        return {
            'monthly_trend': monthly_costs.to_dict('records'),
            'avg_monthly': monthly_costs['total_cost'].mean()
        }

    def _compare_workshops(self, invoices_df):
        """השוואת מוסכים"""
        if invoices_df.empty:
            return {}

        by_workshop = invoices_df.groupby('workshop').agg({
            'total': ['mean', 'sum', 'count']
        }).reset_index()

        by_workshop.columns = ['workshop', 'avg_cost', 'total_cost', 'invoice_count']
        by_workshop = by_workshop.sort_values('avg_cost')

        return {
            'cheapest': by_workshop.iloc[0].to_dict() if len(by_workshop) > 0 else {},
            'most_expensive': by_workshop.iloc[-1].to_dict() if len(by_workshop) > 0 else {},
            'all_workshops': by_workshop.to_dict('records')
        }


# שימוש לדוגמה
if __name__ == "__main__":
    analyzer = FleetAnalyzer()

    print("=== Fleet Status Summary ===")
    fleet_status = analyzer.get_fleet_status_summary()
    print(f"Total vehicles: {len(fleet_status)}")
    print(f"Active vehicles: {len(fleet_status[fleet_status['status'] == 'active'])}")

    print("\n=== Strategic Insights ===")
    insights = analyzer.get_strategic_insights()
    print(f"Best reliability model: {insights['reliability_by_model'].get('best_model')}")
    print(f"Replacement recommendations: {len(insights['replacement_recommendations'])}")
