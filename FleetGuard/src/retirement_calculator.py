# -*- coding: utf-8 -*-
"""
Retirement Calculator - Fleet Vehicle Retirement Logic
חישוב תאריך גריטה משוער לפי כללי החברה
"""

from datetime import datetime, timedelta
import pandas as pd

class RetirementCalculator:
    """
    מחשב תאריך גריטה משוער לרכב לפי:
    1. 5 שנים מרכישה
    2. 250,000 ק"מ

    **המוקדם מבין השניים!**
    """

    RETIREMENT_YEARS = 5  # שנים עד גריטה
    RETIREMENT_KM = 250000  # קילומטרים עד גריטה

    def __init__(self):
        pass

    def calculate_retirement_date(self, purchase_date: str, current_km: int, avg_km_per_day: float = None):
        """
        מחשב תאריך גריטה משוער

        Args:
            purchase_date: תאריך רכישה (YYYY-MM-DD)
            current_km: קילומטראז' נוכחי
            avg_km_per_day: ממוצע ק"מ ליום (אופציונלי)

        Returns:
            dict עם:
                - retirement_date: תאריך גריטה משוער
                - reason: סיבה (age/mileage)
                - days_until_retirement: ימים עד גריטה
                - km_until_retirement: ק"מ עד גריטה
                - status: active/near_retirement/retired
        """
        try:
            purchase_dt = datetime.strptime(purchase_date, "%Y-%m-%d")
        except:
            purchase_dt = datetime.now()

        today = datetime.now()

        # חישוב 1: גריטה לפי גיל (5 שנים)
        retirement_by_age = purchase_dt + timedelta(days=365 * self.RETIREMENT_YEARS)
        days_until_age_retirement = (retirement_by_age - today).days

        # חישוב 2: גריטה לפי קילומטראז' (250,000 ק"מ)
        km_remaining = self.RETIREMENT_KM - current_km

        if avg_km_per_day and avg_km_per_day > 0:
            days_until_km_retirement = int(km_remaining / avg_km_per_day)
            retirement_by_km = today + timedelta(days=days_until_km_retirement)
        else:
            # אם אין נתון ק"מ ליום, נניח ממוצע של 100 ק"מ ליום
            days_until_km_retirement = int(km_remaining / 100)
            retirement_by_km = today + timedelta(days=days_until_km_retirement)

        # בחירת התאריך המוקדם יותר
        if retirement_by_age < retirement_by_km:
            retirement_date = retirement_by_age
            reason = "age"
            days_until = days_until_age_retirement
        else:
            retirement_date = retirement_by_km
            reason = "mileage"
            days_until = days_until_km_retirement

        # קביעת סטטוס
        if days_until < 0:
            status = "retired"
        elif days_until < 180:  # פחות מ-6 חודשים
            status = "near_retirement"
        else:
            status = "active"

        return {
            'retirement_date': retirement_date.strftime("%Y-%m-%d"),
            'reason': reason,
            'days_until_retirement': max(0, days_until),
            'km_until_retirement': max(0, km_remaining),
            'status': status,
            'retirement_by_age': retirement_by_age.strftime("%Y-%m-%d"),
            'retirement_by_km': retirement_by_km.strftime("%Y-%m-%d")
        }

    def calculate_avg_km_per_day(self, purchase_date: str, current_km: int, initial_km: int = 0):
        """
        מחשב ממוצע ק"מ ליום לפי התקופה מאז רכישה

        Args:
            purchase_date: תאריך רכישה
            current_km: קילומטראז' נוכחי
            initial_km: קילומטראז' התחלתי (בעת רכישה)

        Returns:
            float: ממוצע ק"מ ליום
        """
        try:
            purchase_dt = datetime.strptime(purchase_date, "%Y-%m-%d")
        except:
            return 0

        today = datetime.now()
        days_in_fleet = (today - purchase_dt).days

        if days_in_fleet <= 0:
            return 0

        km_driven = current_km - initial_km
        avg_km = km_driven / days_in_fleet

        return max(0, avg_km)

    def get_retirement_summary(self, vehicles_df: pd.DataFrame):
        """
        מחשב סיכום גריטה לכל הצי

        Args:
            vehicles_df: DataFrame עם עמודות:
                - vehicle_id
                - purchase_date
                - initial_km (או 0)
                - (current_km מחושב מהחשבוניות)

        Returns:
            DataFrame מעודכן עם עמודות גריטה
        """
        results = []

        for _, row in vehicles_df.iterrows():
            purchase_date = row.get('purchase_date', datetime.now().strftime("%Y-%m-%d"))
            current_km = row.get('current_km', row.get('initial_km', 0))
            initial_km = row.get('initial_km', 0)

            # חישוב ממוצע ק"מ ליום
            avg_km_per_day = self.calculate_avg_km_per_day(purchase_date, current_km, initial_km)

            # חישוב גריטה
            retirement_info = self.calculate_retirement_date(purchase_date, current_km, avg_km_per_day)

            results.append({
                'vehicle_id': row['vehicle_id'],
                'retirement_date': retirement_info['retirement_date'],
                'retirement_reason': retirement_info['reason'],
                'days_until_retirement': retirement_info['days_until_retirement'],
                'km_until_retirement': retirement_info['km_until_retirement'],
                'retirement_status': retirement_info['status'],
                'avg_km_per_day': round(avg_km_per_day, 1)
            })

        return pd.DataFrame(results)


# דוגמה לשימוש
if __name__ == "__main__":
    calc = RetirementCalculator()

    # דוגמה 1: רכב בן 3 שנים עם 150,000 ק"מ
    result1 = calc.calculate_retirement_date("2022-01-01", 150000, avg_km_per_day=137)
    print("Example 1 (3 years, 150K km):")
    print(f"  Retirement date: {result1['retirement_date']}")
    print(f"  Reason: {result1['reason']}")
    print(f"  Days until: {result1['days_until_retirement']}")
    print(f"  Status: {result1['status']}")
    print()

    # דוגמה 2: רכב בן שנה עם 240,000 ק"מ (קרוב ל-250K)
    result2 = calc.calculate_retirement_date("2024-01-01", 240000, avg_km_per_day=650)
    print("Example 2 (1 year, 240K km - close to limit):")
    print(f"  Retirement date: {result2['retirement_date']}")
    print(f"  Reason: {result2['reason']}")
    print(f"  Days until: {result2['days_until_retirement']}")
    print(f"  Status: {result2['status']}")
