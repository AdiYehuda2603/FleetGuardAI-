"""
Maintenance Pattern Agent - CrewAI
מזהה דפוסי תקלות לפי קילומטראז' נסוע
"""

import pandas as pd
from datetime import datetime
from src.database_manager import DatabaseManager


class MaintenancePatternAgent:
    """
    סוכן AI שמזהה דפוסי תקלות לפי קילומטראז' נסוע
    עובד עם CrewAI Analysts כדי לזהות תבניות
    """
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def analyze_maintenance_patterns(self, vehicle_id=None):
        """
        מנתח דפוסי תחזוקה לפי קילומטראז'
        
        Args:
            vehicle_id: מזהה רכב ספציפי (אופציונלי, אם None מנתח את כל הצי)
        
        Returns:
            dict: תוצאות ניתוח עם דפוסים מזוהים
        """
        # שליפת נתונים
        if vehicle_id:
            invoices = self.db.get_vehicle_history(vehicle_id)
        else:
            invoices = self.db.get_all_invoices()
        
        if invoices.empty:
            return {"error": "אין נתונים לניתוח"}
        
        # המרת תאריכים
        invoices['date'] = pd.to_datetime(invoices['date'])
        invoices = invoices.sort_values('date')
        
        # חישוב קילומטראז' בין טיפולים
        patterns = {
            'tire_replacements': self._analyze_tire_patterns(invoices),
            'routine_services': self._analyze_routine_patterns(invoices),
            'major_repairs': self._analyze_major_repairs(invoices),
            'cost_trends': self._analyze_cost_trends(invoices),
            'km_intervals': self._analyze_km_intervals(invoices)
        }
        
        return patterns
    
    def _analyze_tire_patterns(self, invoices):
        """מזהה דפוסי החלפת צמיגים"""
        tire_invoices = invoices[invoices['kind'].str.contains('tire|צמיג', case=False, na=False)]
        
        if tire_invoices.empty:
            return {"message": "לא נמצאו החלפות צמיגים"}
        
        # חישוב מרווחים בין החלפות
        tire_invoices = tire_invoices.sort_values('odometer_km')
        intervals = []
        
        for i in range(1, len(tire_invoices)):
            prev_km = tire_invoices.iloc[i-1]['odometer_km']
            curr_km = tire_invoices.iloc[i]['odometer_km']
            interval = curr_km - prev_km
            intervals.append(interval)
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            return {
                "average_km_interval": round(avg_interval),
                "min_interval": min(intervals),
                "max_interval": max(intervals),
                "recommendation": f"החלף צמיגים כל {round(avg_interval)} ק\"מ או כל שנתיים (לפי מה שמגיע קודם)"
            }
        
        return {"message": "לא מספיק נתונים לזיהוי דפוס"}
    
    def _analyze_routine_patterns(self, invoices):
        """מזהה דפוסי טיפולים שוטפים"""
        routine = invoices[invoices['kind'] == 'routine']
        
        if routine.empty:
            return {"message": "לא נמצאו טיפולים שוטפים"}
        
        routine = routine.sort_values('odometer_km')
        intervals = []
        
        for i in range(1, len(routine)):
            prev_km = routine.iloc[i-1]['odometer_km']
            curr_km = routine.iloc[i]['odometer_km']
            interval = curr_km - prev_km
            intervals.append(interval)
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            return {
                "average_km_interval": round(avg_interval),
                "recommendation": f"טיפול שוטף מומלץ כל {round(avg_interval)} ק\"מ"
            }
        
        return {"message": "לא מספיק נתונים"}
    
    def _analyze_major_repairs(self, invoices):
        """מזהה תקלות גדולות"""
        major = invoices[~invoices['kind'].isin(['routine', 'tires'])]
        
        if major.empty:
            return {"message": "לא נמצאו תקלות גדולות"}
        
        # קבוצת לפי סוג תקלה
        by_kind = major.groupby('kind').agg({
            'odometer_km': ['min', 'max', 'mean'],
            'total': 'mean'
        }).round(0)
        
        return {
            "breakdown_types": by_kind.to_dict(),
            "total_major_repairs": len(major)
        }
    
    def _analyze_cost_trends(self, invoices):
        """מנתח מגמות עלויות"""
        invoices_sorted = invoices.sort_values('odometer_km')
        
        # חישוב עלות ממוצעת לפי טווחי קילומטראז'
        cost_by_km_range = []
        km_ranges = [(0, 20000), (20000, 40000), (40000, 60000), (60000, 80000), (80000, 100000)]
        
        for min_km, max_km in km_ranges:
            range_invoices = invoices_sorted[
                (invoices_sorted['odometer_km'] >= min_km) & 
                (invoices_sorted['odometer_km'] < max_km)
            ]
            if not range_invoices.empty:
                cost_by_km_range.append({
                    'km_range': f"{min_km}-{max_km}",
                    'avg_cost': round(range_invoices['total'].mean(), 2),
                    'count': len(range_invoices)
                })
        
        return {
            "cost_by_km_range": cost_by_km_range,
            "trend": "עולה" if len(cost_by_km_range) > 1 and cost_by_km_range[-1]['avg_cost'] > cost_by_km_range[0]['avg_cost'] else "יציב"
        }
    
    def _analyze_km_intervals(self, invoices):
        """מנתח מרווחי קילומטראז' בין טיפולים"""
        invoices_sorted = invoices.sort_values(['vehicle_id', 'odometer_km'])
        
        intervals_by_vehicle = {}
        
        for vehicle_id in invoices_sorted['vehicle_id'].unique():
            vehicle_invoices = invoices_sorted[invoices_sorted['vehicle_id'] == vehicle_id]
            
            if len(vehicle_invoices) < 2:
                continue
            
            intervals = []
            for i in range(1, len(vehicle_invoices)):
                prev_km = vehicle_invoices.iloc[i-1]['odometer_km']
                curr_km = vehicle_invoices.iloc[i]['odometer_km']
                interval = curr_km - prev_km
                intervals.append(interval)
            
            if intervals:
                intervals_by_vehicle[vehicle_id] = {
                    'avg_interval': round(sum(intervals) / len(intervals)),
                    'min_interval': min(intervals),
                    'max_interval': max(intervals)
                }
        
        return intervals_by_vehicle
    
    def get_maintenance_recommendations(self, vehicle_id):
        """
        מחזיר המלצות תחזוקה לרכב ספציפי
        מבוסס על דפוסים מזוהים
        """
        patterns = self.analyze_maintenance_patterns(vehicle_id)
        
        recommendations = []
        
        # המלצות צמיגים
        if 'tire_replacements' in patterns and 'average_km_interval' in patterns['tire_replacements']:
            tire_rec = patterns['tire_replacements']['recommendation']
            recommendations.append(f"🔧 צמיגים: {tire_rec}")
        
        # המלצות טיפול שוטף
        if 'routine_services' in patterns and 'recommendation' in patterns['routine_services']:
            routine_rec = patterns['routine_services']['recommendation']
            recommendations.append(f"🔧 טיפול שוטף: {routine_rec}")
        
        # המלצות על בסיס מגמות עלויות
        if 'cost_trends' in patterns:
            trend = patterns['cost_trends'].get('trend', '')
            if trend == "עולה":
                recommendations.append("⚠️ עלויות עולות - שקול בדיקה מקיפה")
        
        return {
            'patterns': patterns,
            'recommendations': recommendations
        }

