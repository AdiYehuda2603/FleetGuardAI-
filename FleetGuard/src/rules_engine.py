"""
FleetGuard AI - Rules Engine
=============================
Logic-based alert system that complements ML predictions with threshold enforcement.

This module provides rule-based analysis of fleet vehicles to detect:
- Maintenance overdue (km/time thresholds)
- Cost anomalies (threshold violations)
- Vehicle retirement readiness
- High utilization patterns
- Workshop quality issues

Author: FleetGuard AI System
Date: 2025-12-18
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np


class FleetRulesEngine:
    """
    Rules Engine for fleet management - provides logic-based alerts.

    This system complements ML predictions by enforcing organizational policies
    and detecting rule violations in real-time.
    """

    def __init__(self, db_manager):
        """
        Initialize Rules Engine with database connection.

        Args:
            db_manager: DatabaseManager instance for data access
        """
        self.db = db_manager

        # Define rule thresholds (can be customized per organization)
        self.rules = {
            'maintenance_overdue': {
                'km_threshold': 10000,      # Max km since last service
                'days_threshold': 180       # Max days since last service
            },
            'cost_anomaly': {
                'multiplier': 2.0           # Alert if cost > 2x average
            },
            'retirement_warning': {
                'days_threshold': 90,       # Warn if retirement < 90 days
                'age_years': 10,            # Warn if vehicle age > 10 years
                'km_threshold': 300000      # Warn if total km > 300,000
            },
            'high_utilization': {
                'km_per_month_threshold': 3000  # High usage threshold
            },
            'workshop_quality': {
                'cost_increase_threshold': 0.5  # 50% above fleet average
            }
        }

    def evaluate_all_rules(self, vehicle_id: Optional[str] = None) -> Dict:
        """
        Evaluate all rules for one vehicle or entire fleet.

        Args:
            vehicle_id: Specific vehicle to check (None = all vehicles)

        Returns:
            Dict with structure:
            {
                'alerts': [list of alert dicts],
                'alert_level': 'urgent|warning|info',
                'stats': {summary statistics}
            }
        """
        # Get vehicle data with statistics
        vehicles_df = self.db.get_vehicle_with_stats()
        invoices_df = self.db.get_all_invoices()

        # Filter to specific vehicle if requested
        if vehicle_id:
            vehicles_df = vehicles_df[vehicles_df['vehicle_id'] == vehicle_id]
            invoices_df = invoices_df[invoices_df['vehicle_id'] == vehicle_id]

        if vehicles_df.empty:
            return {
                'alerts': [],
                'alert_level': 'info',
                'stats': {'total_alerts': 0}
            }

        # Collect all alerts
        all_alerts = []

        for _, vehicle in vehicles_df.iterrows():
            vehicle_invoices = invoices_df[
                invoices_df['vehicle_id'] == vehicle['vehicle_id']
            ]

            # Run all rule checks
            all_alerts.extend(self.check_maintenance_overdue(vehicle))
            all_alerts.extend(self.check_cost_anomaly(vehicle, vehicle_invoices, vehicles_df))
            all_alerts.extend(self.check_retirement_readiness(vehicle))
            all_alerts.extend(self.check_high_utilization(vehicle))
            all_alerts.extend(self.check_workshop_quality(vehicle, vehicle_invoices, vehicles_df))

        # Add custom alerts
        all_alerts.extend(self.get_custom_alerts(vehicle_id))

        # Determine overall alert level
        severity_counts = {
            'URGENT': sum(1 for a in all_alerts if a['severity'] == 'URGENT'),
            'WARNING': sum(1 for a in all_alerts if a['severity'] == 'WARNING'),
            'INFO': sum(1 for a in all_alerts if a['severity'] == 'INFO')
        }

        if severity_counts['URGENT'] > 0:
            overall_level = 'urgent'
        elif severity_counts['WARNING'] > 0:
            overall_level = 'warning'
        else:
            overall_level = 'info'

        return {
            'alerts': all_alerts,
            'alert_level': overall_level,
            'stats': {
                'total_alerts': len(all_alerts),
                'urgent_count': severity_counts['URGENT'],
                'warning_count': severity_counts['WARNING'],
                'info_count': severity_counts['INFO'],
                'vehicles_checked': len(vehicles_df)
            }
        }

    def check_maintenance_overdue(self, vehicle: pd.Series) -> List[Dict]:
        """
        Check if vehicle maintenance is overdue based on km or time.

        Rule: Alert if:
        - km_since_service > 10,000 km OR
        - days_since_service > 180 days

        Args:
            vehicle: Vehicle data row with statistics

        Returns:
            List of alert dicts (empty if no violation)
        """
        alerts = []

        # Skip if no service history
        if pd.isna(vehicle.get('last_service_date')) or pd.isna(vehicle.get('current_km')):
            return alerts

        # Calculate km since last service
        initial_km = vehicle.get('initial_km', 0) or 0
        current_km = vehicle.get('current_km', 0) or 0
        total_services = vehicle.get('total_services', 0) or 0

        # Rough estimate: km per service interval
        if total_services > 0 and current_km > initial_km:
            total_km_driven = current_km - initial_km
            avg_km_per_service = total_km_driven / total_services
            km_since_service = avg_km_per_service  # Approximation
        else:
            km_since_service = 0

        # Calculate days since last service
        try:
            last_service = datetime.strptime(str(vehicle['last_service_date']), '%Y-%m-%d')
            days_since_service = (datetime.now() - last_service).days
        except (ValueError, TypeError):
            days_since_service = 0

        # Check thresholds
        km_threshold = self.rules['maintenance_overdue']['km_threshold']
        days_threshold = self.rules['maintenance_overdue']['days_threshold']

        if km_since_service > km_threshold:
            alerts.append({
                'rule_name': 'maintenance_overdue_km',
                'severity': 'URGENT',
                'vehicle_id': vehicle['vehicle_id'],
                'plate': vehicle.get('plate', 'N/A'),
                'message': f"🚨 תחזוקה דחופה! כ-{int(km_since_service):,} ק\"מ מהשירות האחרון",
                'details': {
                    'km_since_service': int(km_since_service),
                    'threshold': km_threshold,
                    'last_service_date': str(vehicle['last_service_date']),
                    'current_km': int(current_km)
                },
                'recommendation': "תזמן תחזוקה שגרתית בדחיפות גבוהה למניעת תקלות"
            })

        if days_since_service > days_threshold:
            alerts.append({
                'rule_name': 'maintenance_overdue_time',
                'severity': 'URGENT',
                'vehicle_id': vehicle['vehicle_id'],
                'plate': vehicle.get('plate', 'N/A'),
                'message': f"🚨 תחזוקה דחופה! {days_since_service} ימים מהשירות האחרון",
                'details': {
                    'days_since_service': days_since_service,
                    'threshold': days_threshold,
                    'last_service_date': str(vehicle['last_service_date'])
                },
                'recommendation': f"תחזוקה אחרונה הייתה לפני {days_since_service} ימים - תזמן בדיקה מיידית"
            })

        return alerts

    def check_cost_anomaly(self, vehicle: pd.Series, invoices: pd.DataFrame,
                          all_vehicles: pd.DataFrame) -> List[Dict]:
        """
        Check for unusual cost spikes compared to vehicle's average.

        Rule: Alert if most recent invoice > 2x vehicle's average cost

        Args:
            vehicle: Vehicle data row
            invoices: Vehicle's invoice history
            all_vehicles: All vehicles for fleet comparison

        Returns:
            List of alert dicts
        """
        alerts = []

        if invoices.empty or pd.isna(vehicle.get('avg_service_cost')):
            return alerts

        # Get most recent invoice
        recent_invoice = invoices.sort_values('date', ascending=False).iloc[0]
        recent_cost = recent_invoice.get('total', 0)
        avg_cost = vehicle.get('avg_service_cost', 0) or 1  # Avoid division by zero

        multiplier = self.rules['cost_anomaly']['multiplier']

        if recent_cost > (avg_cost * multiplier):
            cost_increase_pct = ((recent_cost - avg_cost) / avg_cost) * 100

            alerts.append({
                'rule_name': 'cost_anomaly',
                'severity': 'WARNING',
                'vehicle_id': vehicle['vehicle_id'],
                'plate': vehicle.get('plate', 'N/A'),
                'message': f"⚠️ עלייה חריגה בעלות תחזוקה ({cost_increase_pct:.0f}%)",
                'details': {
                    'recent_cost': float(recent_cost),
                    'average_cost': float(avg_cost),
                    'increase_percent': float(cost_increase_pct),
                    'threshold_multiplier': multiplier,
                    'invoice_date': str(recent_invoice['date']),
                    'workshop': str(recent_invoice.get('workshop', 'N/A'))
                },
                'recommendation': f"בדוק את החשבונית האחרונה מ-{recent_invoice.get('workshop', 'N/A')} - עלות חריגה"
            })

        return alerts

    def check_retirement_readiness(self, vehicle: pd.Series) -> List[Dict]:
        """
        Check if vehicle is approaching retirement criteria.

        Rule: Alert if:
        - days_until_retirement < 90 OR
        - vehicle_age > 10 years OR
        - total_km > 300,000

        Args:
            vehicle: Vehicle data row

        Returns:
            List of alert dicts
        """
        alerts = []

        # Calculate vehicle age
        try:
            purchase_date = datetime.strptime(str(vehicle.get('purchase_date', '')), '%Y-%m-%d')
            vehicle_age_years = (datetime.now() - purchase_date).days / 365.25
        except (ValueError, TypeError):
            vehicle_age_years = 0

        # Get current km
        current_km = vehicle.get('current_km', 0) or 0

        # Check retirement date
        if not pd.isna(vehicle.get('estimated_retirement_date')):
            try:
                retirement_date = datetime.strptime(str(vehicle['estimated_retirement_date']), '%Y-%m-%d')
                days_until_retirement = (retirement_date - datetime.now()).days

                if days_until_retirement < self.rules['retirement_warning']['days_threshold']:
                    alerts.append({
                        'rule_name': 'retirement_approaching',
                        'severity': 'INFO',
                        'vehicle_id': vehicle['vehicle_id'],
                        'plate': vehicle.get('plate', 'N/A'),
                        'message': f"ℹ️ רכב מתקרב לפרישה ({days_until_retirement} ימים)",
                        'details': {
                            'days_until_retirement': days_until_retirement,
                            'retirement_date': str(vehicle['estimated_retirement_date']),
                            'vehicle_age_years': round(vehicle_age_years, 1)
                        },
                        'recommendation': "תכנן החלפת רכב - בדוק מחירי רכבים חלופיים"
                    })
            except (ValueError, TypeError):
                pass

        # Check age threshold
        if vehicle_age_years > self.rules['retirement_warning']['age_years']:
            alerts.append({
                'rule_name': 'vehicle_too_old',
                'severity': 'WARNING',
                'vehicle_id': vehicle['vehicle_id'],
                'plate': vehicle.get('plate', 'N/A'),
                'message': f"⚠️ רכב ישן ({vehicle_age_years:.1f} שנים)",
                'details': {
                    'vehicle_age_years': round(vehicle_age_years, 1),
                    'age_threshold': self.rules['retirement_warning']['age_years'],
                    'purchase_date': str(vehicle.get('purchase_date', 'N/A'))
                },
                'recommendation': "שקול החלפת רכב - רכבים ישנים מגדילים עלויות תחזוקה"
            })

        # Check km threshold
        if current_km > self.rules['retirement_warning']['km_threshold']:
            alerts.append({
                'rule_name': 'high_mileage',
                'severity': 'WARNING',
                'vehicle_id': vehicle['vehicle_id'],
                'plate': vehicle.get('plate', 'N/A'),
                'message': f"⚠️ קילומטראז' גבוה ({int(current_km):,} ק\"מ)",
                'details': {
                    'current_km': int(current_km),
                    'threshold': self.rules['retirement_warning']['km_threshold']
                },
                'recommendation': "רכב עם קילומטראז' גבוה - העלות התחזוקתית עשויה לעלות"
            })

        return alerts

    def check_high_utilization(self, vehicle: pd.Series) -> List[Dict]:
        """
        Check if vehicle has unusually high utilization (accelerated wear).

        Rule: Alert if km_per_month > 3,000

        Args:
            vehicle: Vehicle data row

        Returns:
            List of alert dicts
        """
        alerts = []

        # Calculate km per month
        try:
            purchase_date = datetime.strptime(str(vehicle.get('purchase_date', '')), '%Y-%m-%d')
            months_in_service = max(1, (datetime.now() - purchase_date).days / 30.44)

            initial_km = vehicle.get('initial_km', 0) or 0
            current_km = vehicle.get('current_km', 0) or 0
            km_driven = current_km - initial_km

            km_per_month = km_driven / months_in_service if months_in_service > 0 else 0

            threshold = self.rules['high_utilization']['km_per_month_threshold']

            if km_per_month > threshold:
                alerts.append({
                    'rule_name': 'high_utilization',
                    'severity': 'INFO',
                    'vehicle_id': vehicle['vehicle_id'],
                    'plate': vehicle.get('plate', 'N/A'),
                    'message': f"ℹ️ ניצולת גבוהה ({int(km_per_month):,} ק\"מ/חודש)",
                    'details': {
                        'km_per_month': int(km_per_month),
                        'threshold': threshold,
                        'total_km_driven': int(km_driven),
                        'months_in_service': round(months_in_service, 1)
                    },
                    'recommendation': "רכב בשימוש אינטנסיבי - שקול תדירות תחזוקה מוגברת"
                })
        except (ValueError, TypeError):
            pass

        return alerts

    def check_workshop_quality(self, vehicle: pd.Series, invoices: pd.DataFrame,
                               all_vehicles: pd.DataFrame) -> List[Dict]:
        """
        Check if workshop costs are significantly higher than fleet average.

        Rule: Alert if vehicle's avg cost > 50% above fleet average

        Args:
            vehicle: Vehicle data row
            invoices: Vehicle's invoice history
            all_vehicles: All vehicles for fleet comparison

        Returns:
            List of alert dicts
        """
        alerts = []

        if invoices.empty or all_vehicles.empty:
            return alerts

        vehicle_avg_cost = vehicle.get('avg_service_cost', 0) or 0
        fleet_avg_cost = all_vehicles['avg_service_cost'].mean()

        if pd.isna(fleet_avg_cost) or fleet_avg_cost == 0:
            return alerts

        cost_ratio = vehicle_avg_cost / fleet_avg_cost
        threshold = 1 + self.rules['workshop_quality']['cost_increase_threshold']

        if cost_ratio > threshold:
            cost_increase_pct = ((vehicle_avg_cost - fleet_avg_cost) / fleet_avg_cost) * 100

            # Find most common workshop
            most_common_workshop = invoices['workshop'].mode()[0] if not invoices.empty else 'N/A'

            alerts.append({
                'rule_name': 'workshop_expensive',
                'severity': 'INFO',
                'vehicle_id': vehicle['vehicle_id'],
                'plate': vehicle.get('plate', 'N/A'),
                'message': f"ℹ️ עלות תחזוקה גבוהה מהממוצע ({cost_increase_pct:.0f}%)",
                'details': {
                    'vehicle_avg_cost': float(vehicle_avg_cost),
                    'fleet_avg_cost': float(fleet_avg_cost),
                    'cost_increase_percent': float(cost_increase_pct),
                    'most_common_workshop': str(most_common_workshop),
                    'total_services': int(vehicle.get('total_services', 0))
                },
                'recommendation': f"בדוק אלטרנטיבות ל-{most_common_workshop} - עלויות גבוהות יחסית"
            })

        return alerts

    def get_rule_thresholds(self) -> Dict:
        """
        Get current rule thresholds for display/configuration.

        Returns:
            Dict of all rule thresholds
        """
        return self.rules.copy()

    def update_rule_threshold(self, rule_name: str, param_name: str, new_value):
        """
        Update a specific rule threshold (for customization).

        Args:
            rule_name: Rule category (e.g., 'maintenance_overdue')
            param_name: Parameter to update (e.g., 'km_threshold')
            new_value: New threshold value
        """
        if rule_name in self.rules and param_name in self.rules[rule_name]:
            self.rules[rule_name][param_name] = new_value
            return True
        return False

    def get_custom_alerts(self, vehicle_id: Optional[str] = None) -> List[Dict]:
        """
        Get custom user-defined alerts from database.

        Args:
            vehicle_id: Specific vehicle to filter (None = all vehicles)

        Returns:
            List of custom alert dicts
        """
        try:
            # Get custom alerts from database
            custom_alerts_df = self.db.get_custom_alerts(vehicle_id=vehicle_id, active_only=True)

            if custom_alerts_df.empty:
                return []

            # Get vehicle data to enrich with plate numbers
            vehicles_df = self.db.get_vehicle_with_stats()

            # Convert to standard alert format
            alerts = []
            for _, alert in custom_alerts_df.iterrows():
                # Get plate number for this vehicle
                vehicle_info = vehicles_df[vehicles_df['vehicle_id'] == alert['vehicle_id']]
                plate = vehicle_info.iloc[0]['plate'] if not vehicle_info.empty else alert['vehicle_id']

                alert_dict = {
                    'rule_name': 'custom_alert',
                    'severity': alert['severity'],
                    'vehicle_id': alert['vehicle_id'],
                    'plate': plate,
                    'message': f"📌 {alert['alert_title']}: {alert['alert_message']}",
                    'details': {
                        'alert_id': int(alert['alert_id']),
                        'alert_title': alert['alert_title'],
                        'created_at': alert['created_at'],
                        'created_by': alert.get('created_by', 'system'),
                        'due_date': alert.get('due_date'),
                        'notes': alert.get('notes')
                    },
                    'recommendation': alert.get('notes', 'התראה מותאמת אישית')
                }
                alerts.append(alert_dict)

            return alerts

        except Exception as e:
            # If table doesn't exist or other error, return empty list
            return []
