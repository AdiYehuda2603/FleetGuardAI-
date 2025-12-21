"""
FleetGuard Predictive Maintenance Agent
----------------------------------------
חוכמה מלאכותית לחיזוי טיפולים והחלפת רכבים
"""

import pandas as pd
from datetime import datetime, timedelta
try:
    from src.database_manager import DatabaseManager
except ImportError:
    from database_manager import DatabaseManager


class PredictiveMaintenanceAgent:
    """
    Agent שמנתח נתונים ומחזה:
    1. מתי רכב צריך טיפול הבא
    2. מתי כדאי להחליף רכב
    """

    # קבועים לחיזוי - קריטריונים מחמירים
    ROUTINE_SERVICE_KM = 15000  # טיפול שוטף כל 15,000 ק"מ
    MAJOR_SERVICE_KM = 60000    # טיפול גדול כל 60,000 ק"מ
    REPLACEMENT_KM_THRESHOLD = 80000  # החלפה מעל 80,000 ק"מ (הוחמר מ-100,000)
    REPLACEMENT_AGE_YEARS = 3   # החלפה אחרי 3 שנים (הוחמר מ-8)
    HIGH_COST_MULTIPLIER = 1.5  # עלות גבוהה = פי 1.5 מהממוצע (הוחמר מ-2.5)

    def __init__(self):
        self.db = DatabaseManager()

    def predict_next_service(self, vehicle_id):
        """
        חוזה מתי הרכב צריך את הטיפול הבא
        מבוסס על:
        - קילומטרז' נוכחי
        - תאריך טיפול אחרון
        - קצב נסיעה ממוצע
        """
        # שליפת נתוני הרכב
        vehicle_stats = self.db.get_vehicle_with_stats()
        vehicle = vehicle_stats[vehicle_stats['vehicle_id'] == vehicle_id]

        if vehicle.empty:
            return None

        vehicle = vehicle.iloc[0]

        current_km = vehicle['current_km'] if pd.notna(vehicle['current_km']) else vehicle['initial_km']
        last_service = pd.to_datetime(vehicle['last_service_date']) if pd.notna(vehicle['last_service_date']) else None

        # חישוב ק"מ עד לטיפול הבא
        km_since_last_major = current_km % self.MAJOR_SERVICE_KM
        km_to_major = self.MAJOR_SERVICE_KM - km_since_last_major

        km_since_last_routine = current_km % self.ROUTINE_SERVICE_KM
        km_to_routine = self.ROUTINE_SERVICE_KM - km_since_last_routine

        # חישוב קצב נסיעה (ק"מ ליום)
        if last_service:
            days_since_service = (datetime.now() - last_service).days
            if days_since_service > 0:
                history = self.db.get_vehicle_history(vehicle_id)
                if len(history) >= 2:
                    km_driven = history['odometer_km'].iloc[0] - history['odometer_km'].iloc[-1]
                    total_days = (pd.to_datetime(history['date'].iloc[0]) -
                                pd.to_datetime(history['date'].iloc[-1])).days
                    km_per_day = km_driven / total_days if total_days > 0 else 30
                else:
                    km_per_day = 30  # ברירת מחדל
            else:
                km_per_day = 30
        else:
            km_per_day = 30

        # חיזוי תאריך
        days_to_routine = int(km_to_routine / km_per_day) if km_per_day > 0 else 180
        days_to_major = int(km_to_major / km_per_day) if km_per_day > 0 else 180

        next_routine_date = datetime.now() + timedelta(days=days_to_routine)
        next_major_date = datetime.now() + timedelta(days=days_to_major)

        return {
            "vehicle_id": vehicle_id,
            "current_km": int(current_km),
            "km_per_day": round(km_per_day, 1),
            "next_routine": {
                "km_remaining": int(km_to_routine),
                "estimated_date": next_routine_date.date(),
                "days_remaining": days_to_routine
            },
            "next_major": {
                "km_remaining": int(km_to_major),
                "estimated_date": next_major_date.date(),
                "days_remaining": days_to_major
            }
        }

    def should_replace_vehicle(self, vehicle_id):
        """
        מחליט האם כדאי להחליף את הרכב
        קריטריונים:
        1. גיל הרכב (מעל 8 שנים)
        2. קילומטרז' (מעל 180,000)
        3. עלויות תחזוקה גבוהות
        """
        vehicle_stats = self.db.get_vehicle_with_stats()
        vehicle = vehicle_stats[vehicle_stats['vehicle_id'] == vehicle_id]

        if vehicle.empty:
            return None

        vehicle = vehicle.iloc[0]

        # חישוב גיל
        vehicle_age = datetime.now().year - vehicle['year']

        # קילומטרז' נוכחי
        current_km = vehicle['current_km'] if pd.notna(vehicle['current_km']) else vehicle['initial_km']

        # עלויות ממוצעות
        avg_cost = vehicle['avg_service_cost'] if pd.notna(vehicle['avg_service_cost']) else 0
        fleet_avg_cost = vehicle_stats['avg_service_cost'].mean()

        # בדיקת קריטריונים
        reasons = []
        score = 0  # ציון: ככל שגבוה יותר, יותר דחוף להחליף

        # 1. גיל (משקל מוגבר)
        if vehicle_age >= self.REPLACEMENT_AGE_YEARS:
            reasons.append(f"גיל: {vehicle_age} שנים (סף: {self.REPLACEMENT_AGE_YEARS})")
            score += 50  # הוגבר מ-40 ל-50

        # 2. קילומטרז'
        if current_km >= self.REPLACEMENT_KM_THRESHOLD:
            reasons.append(f"ק\"מ: {current_km:,} (סף: {self.REPLACEMENT_KM_THRESHOLD:,})")
            score += 40

        # 3. עלויות תחזוקה גבוהות
        if avg_cost > fleet_avg_cost * self.HIGH_COST_MULTIPLIER:
            reasons.append(f"עלות גבוהה: ₪{avg_cost:,.0f} (ממוצע צי: ₪{fleet_avg_cost:,.0f})")
            score += 30

        # החלטה
        recommendation = "החלף בהקדם" if score >= 80 else \
                        "שקול החלפה" if score >= 50 else \
                        "המשך להשתמש" if score >= 20 else \
                        "רכב במצב טוב"

        return {
            "vehicle_id": vehicle_id,
            "make_model": vehicle['make_model'],
            "year": int(vehicle['year']),
            "age": vehicle_age,
            "current_km": int(current_km),
            "total_cost": float(vehicle['total_cost']) if pd.notna(vehicle['total_cost']) else 0,
            "avg_service_cost": float(avg_cost),
            "fleet_avg_cost": float(fleet_avg_cost),
            "replacement_score": score,
            "recommendation": recommendation,
            "reasons": reasons
        }

    def get_fleet_predictions(self):
        """
        מחזיר חיזויים לכל הצי
        """
        vehicles = self.db.get_all_vehicles()
        predictions = []

        for _, vehicle in vehicles.iterrows():
            vid = vehicle['vehicle_id']

            # חיזוי טיפול
            service_pred = self.predict_next_service(vid)

            # חיזוי החלפה
            replacement_pred = self.should_replace_vehicle(vid)

            if service_pred and replacement_pred:
                predictions.append({
                    **replacement_pred,
                    "next_service_days": service_pred['next_routine']['days_remaining'],
                    "next_service_date": service_pred['next_routine']['estimated_date']
                })

        return pd.DataFrame(predictions)


# --- בדיקה ---
if __name__ == "__main__":
    agent = PredictiveMaintenanceAgent()

    # בדיקה לרכב אחד
    print("Testing predictive agent...")
    pred = agent.predict_next_service("VH-01")
    if pred:
        print(f"\nNext service for VH-01:")
        print(f"  Current KM: {pred['current_km']}")
        print(f"  Routine: {pred['next_routine']['days_remaining']} days ({pred['next_routine']['estimated_date']})")

    replacement = agent.should_replace_vehicle("VH-01")
    if replacement:
        print(f"\nReplacement analysis for VH-01:")
        print(f"  Score: {replacement['replacement_score']}")
        print(f"  Recommendation: {replacement['recommendation']}")
