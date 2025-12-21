"""
מודול לתחזיות ML בזמן אמת
טוען את המודל שאימן Agent E ומאפשר תחזיות על רכבים
"""

import pickle
import joblib
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path


class MLPredictor:
    """
    מחלקה לטעינת המודל ועשיית תחזיות
    """

    def __init__(self):
        self.model = None
        self.metadata = None
        self.features_order = None
        self.load_model()

    def load_model(self):
        """טוען את המודל ה-Metadata"""
        try:
            # נתיבים
            model_path = Path("models/model.pkl")
            metadata_path = Path("models/model_metadata.json")

            # טעינת מודל
            if model_path.exists():
                try:
                    # Try joblib first (preferred for sklearn models)
                    self.model = joblib.load(model_path)
                    print(f"[OK] Model loaded: {model_path}")
                except Exception as e:
                    # Fallback to pickle
                    try:
                        with open(model_path, 'rb') as f:
                            self.model = pickle.load(f)
                        print(f"[OK] Model loaded (pickle): {model_path}")
                    except Exception as e2:
                        print(f"[ERROR] Failed to load model: {e2}")
                        return False
            else:
                print(f"[ERROR] Model not found: {model_path}")
                return False

            # טעינת metadata
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                self.features_order = self.metadata.get('features', [])
                print(f"[OK] Metadata loaded: {metadata_path}")
            else:
                print(f"[WARNING] Metadata not found: {metadata_path}")

            return True

        except Exception as e:
            print(f"[ERROR] Error loading model: {e}")
            return False

    def get_model_info(self):
        """מחזיר מידע על המודל"""
        if not self.metadata:
            return {"error": "Model not loaded"}

        return {
            "model_name": self.metadata.get("model_name", "Unknown"),
            "train_date": self.metadata.get("train_date", "Unknown"),
            "test_r2": self.metadata.get("test_r2", 0),
            "rmse": self.metadata.get("rmse", 0),
            "mae": self.metadata.get("mae", 0),
            "features_count": len(self.features_order),
            "features": self.features_order
        }

    def predict_vehicle_cost(self, vehicle_data):
        """
        מחזה עלות תחזוקה חודשית לרכב

        Args:
            vehicle_data (dict): מילון עם פרטי הרכב

        Returns:
            dict: תחזית + רמת ביטחון
        """
        if not self.model:
            return {"error": "Model not loaded"}

        try:
            # יצירת DataFrame עם הפיצ'רים הנדרשים
            features_df = pd.DataFrame([vehicle_data])

            # ודא שיש את כל הפיצ'רים הנדרשים
            missing_features = set(self.features_order) - set(features_df.columns)
            if missing_features:
                # השלמת פיצ'רים חסרים עם 0
                for feat in missing_features:
                    features_df[feat] = 0

            # סידור הפיצ'רים לפי הסדר המקורי
            features_df = features_df[self.features_order]

            # תחזית
            prediction = self.model.predict(features_df)[0]

            # חישוב רמת ביטחון (על סמך RMSE)
            rmse = self.metadata.get('rmse', 15)
            confidence_interval = (prediction - rmse, prediction + rmse)

            return {
                "predicted_cost": round(prediction, 2),
                "confidence_interval": {
                    "lower": round(confidence_interval[0], 2),
                    "upper": round(confidence_interval[1], 2)
                },
                "rmse": rmse,
                "status": "success"
            }

        except Exception as e:
            return {"error": str(e)}

    def predict_fleet(self, vehicles_df):
        """
        תחזית לכל הצי

        Args:
            vehicles_df (pd.DataFrame): טבלת רכבים עם פיצ'רים

        Returns:
            pd.DataFrame: טבלה עם תחזיות
        """
        if not self.model:
            return pd.DataFrame()

        try:
            # ודא שיש את כל הפיצ'רים
            available_features = [f for f in self.features_order if f in vehicles_df.columns]

            if len(available_features) < len(self.features_order):
                print(f"[WARNING] Only {len(available_features)}/{len(self.features_order)} features available")

            # השלמת פיצ'רים חסרים
            for feat in self.features_order:
                if feat not in vehicles_df.columns:
                    vehicles_df[feat] = 0

            # סידור פיצ'רים
            X = vehicles_df[self.features_order]

            # תחזיות
            predictions = self.model.predict(X)

            # הוספת תחזיות לטבלה
            result_df = vehicles_df.copy()
            result_df['predicted_monthly_cost'] = predictions
            result_df['predicted_annual_cost'] = predictions * 12

            return result_df

        except Exception as e:
            print(f"[ERROR] Error predicting fleet: {e}")
            return pd.DataFrame()

    def get_feature_importance(self):
        """מחזיר חשיבות פיצ'רים"""
        if not self.model or not hasattr(self.model, 'feature_importances_'):
            return None

        try:
            importances = self.model.feature_importances_
            features = self.features_order

            importance_df = pd.DataFrame({
                'feature': features,
                'importance': importances
            }).sort_values('importance', ascending=False)

            return importance_df

        except Exception as e:
            print(f"[ERROR] Error getting feature importance: {e}")
            return None

    def compare_vehicle_to_fleet(self, vehicle_id, vehicles_df):
        """
        משווה רכב ספציפי לממוצע הצי

        Args:
            vehicle_id (str): מזהה רכב
            vehicles_df (pd.DataFrame): כל הצי

        Returns:
            dict: השוואה
        """
        try:
            # תחזית לצי
            predictions_df = self.predict_fleet(vehicles_df)

            if predictions_df.empty:
                return {"error": "Failed to predict fleet"}

            # מציאת הרכב
            vehicle_pred = predictions_df[predictions_df['vehicle_id'] == vehicle_id]

            if vehicle_pred.empty:
                return {"error": f"Vehicle {vehicle_id} not found"}

            # המרה מפורשת לסקלר
            vehicle_cost = float(vehicle_pred['predicted_monthly_cost'].iloc[0])
            fleet_avg = float(predictions_df['predicted_monthly_cost'].mean())
            fleet_median = float(predictions_df['predicted_monthly_cost'].median())

            # חישוב אחוזון
            num_cheaper = int((predictions_df['predicted_monthly_cost'] < vehicle_cost).sum())
            total_vehicles = int(len(predictions_df))
            percentile = float((num_cheaper / total_vehicles) * 100)

            return {
                "vehicle_id": vehicle_id,
                "predicted_cost": round(vehicle_cost, 2),
                "fleet_average": round(fleet_avg, 2),
                "fleet_median": round(fleet_median, 2),
                "percentile": round(percentile, 1),
                "status": "above_average" if vehicle_cost > fleet_avg else "below_average",
                "difference_from_avg": round(vehicle_cost - fleet_avg, 2),
                "difference_percent": round((vehicle_cost - fleet_avg) / fleet_avg * 100, 1)
            }

        except Exception as e:
            return {"error": str(e)}


def load_crew_reports():
    """טוען את כל הדוחות שנוצרו על ידי הסוכנים"""
    reports = {}

    reports_dir = Path("reports")

    # דוחות JSON
    json_reports = [
        "vehicle_analysis.json",
        "driver_analysis.json",
        "maintenance_analysis.json",
        "evaluation_metrics.json",
        "contract_validation_report.json",
        "flow_execution_report.json"
    ]

    for report_name in json_reports:
        report_path = reports_dir / report_name
        if report_path.exists():
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    reports[report_name.replace('.json', '')] = json.load(f)
            except Exception as e:
                print(f"[WARNING] Failed to load {report_name}: {e}")

    # דוחות Markdown
    md_reports = [
        "evaluation_report.md",
        "flow_summary.md"
    ]

    for report_name in md_reports:
        report_path = reports_dir / report_name
        if report_path.exists():
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    reports[report_name.replace('.md', '')] = f.read()
            except Exception as e:
                print(f"[WARNING] Failed to load {report_name}: {e}")

    return reports


if __name__ == "__main__":
    # בדיקה
    predictor = MLPredictor()

    if predictor.model:
        info = predictor.get_model_info()
        print("\n=== Model Info ===")
        print(f"Model: {info['model_name']}")
        print(f"R²: {info['test_r2']:.4f}")
        print(f"RMSE: {info['rmse']:.2f}")
        print(f"MAE: {info['mae']:.2f}")
        print(f"Features: {info['features_count']}")

        # בדיקת feature importance
        importance = predictor.get_feature_importance()
        if importance is not None:
            print("\n=== Top 5 Features ===")
            print(importance.head(5))
