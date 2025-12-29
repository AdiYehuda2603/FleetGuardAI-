"""
ML Trainer - Agent E/F Logic
Trains machine learning models for cost and maintenance prediction
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
import os
import json

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

try:
    from src.database_manager import DatabaseManager
    from src.predictive_agent import PredictiveMaintenanceAgent
    from src.utils.file_handler import file_handler
    from src.utils.path_resolver import path_resolver
except ImportError:
    from database_manager import DatabaseManager
    from predictive_agent import PredictiveMaintenanceAgent
    from utils.file_handler import file_handler
    from utils.path_resolver import path_resolver


class FleetMLTrainer:
    """
    Trains ML models for fleet predictions:
    1. Annual Maintenance Cost (Regression)
    2. Next Service Cost (Regression)
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.pred_agent = PredictiveMaintenanceAgent()

        self.cost_model = None
        self.service_cost_model = None

        self.label_encoders = {}
        self.feature_names = []

        self.metrics = {}

    def prepare_features(self, df_vehicles=None, df_invoices=None):
        """
        Feature engineering for ML models

        Args:
            df_vehicles: Vehicle stats DataFrame (from get_vehicle_with_stats)
            df_invoices: Invoice history DataFrame (from get_all_invoices)

        Returns:
            pandas DataFrame with engineered features
        """
        # Load data if not provided
        if df_vehicles is None:
            df_vehicles = self.db.get_vehicle_with_stats()

        if df_invoices is None:
            df_invoices = self.db.get_all_invoices()

        # Convert date columns
        df_invoices['date'] = pd.to_datetime(df_invoices['date'])
        df_vehicles['fleet_entry_date'] = pd.to_datetime(df_vehicles['fleet_entry_date'])

        # Calculate vehicle age
        current_year = datetime.now().year
        df_vehicles['age'] = current_year - df_vehicles['year']

        # Calculate days in fleet
        df_vehicles['days_in_fleet'] = (datetime.now() - df_vehicles['fleet_entry_date']).dt.days

        # Encode categorical variables
        categorical_cols = ['make_model']

        for col in categorical_cols:
            if col in df_vehicles.columns:
                le = LabelEncoder()
                df_vehicles[f'{col}_encoded'] = le.fit_transform(df_vehicles[col].astype(str))
                self.label_encoders[col] = le

        # Calculate cost ratios
        if 'avg_service_cost' in df_vehicles.columns:
            fleet_avg_cost = df_vehicles['avg_service_cost'].mean()
            df_vehicles['cost_vs_fleet_avg'] = df_vehicles['avg_service_cost'] / fleet_avg_cost
        else:
            df_vehicles['cost_vs_fleet_avg'] = 1.0

        # Time-based features
        if 'last_service_date' in df_vehicles.columns:
            df_vehicles['last_service_date'] = pd.to_datetime(df_vehicles['last_service_date'])
            df_vehicles['days_since_last_service'] = (datetime.now() - df_vehicles['last_service_date']).dt.days
            # Fill NaN with median
            df_vehicles['days_since_last_service'].fillna(df_vehicles['days_since_last_service'].median(), inplace=True)
        else:
            df_vehicles['days_since_last_service'] = 180  # Default

        # Calculate km per day
        if 'current_km' in df_vehicles.columns and 'initial_km' in df_vehicles.columns:
            km_driven = df_vehicles['current_km'] - df_vehicles['initial_km']
            df_vehicles['km_per_day'] = km_driven / df_vehicles['days_in_fleet']
            # Replace invalid values
            df_vehicles['km_per_day'] = df_vehicles['km_per_day'].replace([np.inf, -np.inf], 30)
            df_vehicles['km_per_day'].fillna(30, inplace=True)
        else:
            df_vehicles['km_per_day'] = 30

        # Fill missing values
        numeric_cols = df_vehicles.select_dtypes(include=[np.number]).columns
        df_vehicles[numeric_cols] = df_vehicles[numeric_cols].fillna(0)

        return df_vehicles

    def train_annual_cost_model(self, df_features=None, test_size=0.2, model_type='random_forest'):
        """
        Train annual maintenance cost prediction model (MODEL 1)

        Args:
            df_features: DataFrame with engineered features
            test_size: Test split ratio
            model_type: 'random_forest' or 'gradient_boosting'

        Returns:
            dict: Model and evaluation metrics
        """
        # Prepare data
        if df_features is None:
            df_features = self.prepare_features()

        # Target: Annual maintenance cost (total_cost projected to 1 year)
        # Calculate annual cost based on days in fleet
        df_features['annual_cost'] = (df_features['total_cost'] / df_features['days_in_fleet']) * 365
        # Handle edge cases
        df_features['annual_cost'] = df_features['annual_cost'].replace([np.inf, -np.inf], df_features['total_cost'].mean())
        df_features['annual_cost'].fillna(df_features['total_cost'].mean(), inplace=True)

        # Select features
        feature_cols = [
            'age',
            'current_km',
            'total_services',
            'avg_service_cost',
            'make_model_encoded',
            'days_in_fleet',
            'cost_vs_fleet_avg',
            'km_per_day',
            'days_since_last_service'
        ]

        # Ensure all feature columns exist
        feature_cols = [col for col in feature_cols if col in df_features.columns]
        self.feature_names = feature_cols

        X = df_features[feature_cols].copy()
        y = df_features['annual_cost'].copy()

        # Remove any rows with NaN
        mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[mask]
        y = y[mask]

        if len(X) < 10:
            raise ValueError("Insufficient data for training (need at least 10 samples)")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        # Train model
        if model_type == 'random_forest':
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
        else:  # gradient_boosting
            model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )

        model.fit(X_train, y_train)

        # Predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Metrics
        metrics = {
            'model_name': 'Annual Cost Predictor',
            'model_type': model_type,
            'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
            'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'train_r2': r2_score(y_train, y_pred_train),
            'test_r2': r2_score(y_test, y_pred_test),
            'feature_importance': dict(zip(feature_cols, model.feature_importances_))
        }

        # Cross-validation
        cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
        metrics['cv_r2_mean'] = cv_scores.mean()
        metrics['cv_r2_std'] = cv_scores.std()

        self.cost_model = model
        self.metrics['annual_cost'] = metrics

        return {'model': model, 'metrics': metrics, 'X_test': X_test, 'y_test': y_test, 'y_pred': y_pred_test}

    def train_service_cost_model(self, df_features=None, test_size=0.2, model_type='random_forest'):
        """
        Train next service cost prediction model (MODEL 2)

        Args:
            df_features: DataFrame with engineered features
            test_size: Test split ratio
            model_type: 'random_forest' or 'gradient_boosting'

        Returns:
            dict: Model and evaluation metrics
        """
        # Prepare data
        if df_features is None:
            df_features = self.prepare_features()

        # Target: Average service cost (next service expected to be similar to average)
        # Use avg_service_cost as target
        df_features['next_service_cost'] = df_features['avg_service_cost']

        # For vehicles with few services, adjust based on km and age
        low_service_mask = df_features['total_services'] < 3
        df_features.loc[low_service_mask, 'next_service_cost'] = df_features.loc[low_service_mask, 'avg_service_cost'] * 1.1

        # Select features
        feature_cols = [
            'age',
            'current_km',
            'total_services',
            'make_model_encoded',
            'km_per_day',
            'days_since_last_service',
            'cost_vs_fleet_avg'
        ]

        # Ensure all feature columns exist
        feature_cols = [col for col in feature_cols if col in df_features.columns]

        X = df_features[feature_cols].copy()
        y = df_features['next_service_cost'].copy()

        # Remove any rows with NaN or zero target
        mask = ~(X.isna().any(axis=1) | y.isna() | (y == 0))
        X = X[mask]
        y = y[mask]

        if len(X) < 10:
            raise ValueError("Insufficient data for training (need at least 10 samples)")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        # Train model
        if model_type == 'random_forest':
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=8,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
        else:  # gradient_boosting
            model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                random_state=42
            )

        model.fit(X_train, y_train)

        # Predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Metrics
        metrics = {
            'model_name': 'Next Service Cost Predictor',
            'model_type': model_type,
            'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
            'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'train_r2': r2_score(y_train, y_pred_train),
            'test_r2': r2_score(y_test, y_pred_test),
            'feature_importance': dict(zip(feature_cols, model.feature_importances_))
        }

        # Cross-validation
        cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
        metrics['cv_r2_mean'] = cv_scores.mean()
        metrics['cv_r2_std'] = cv_scores.std()

        self.service_cost_model = model
        self.metrics['service_cost'] = metrics

        return {'model': model, 'metrics': metrics, 'X_test': X_test, 'y_test': y_test, 'y_pred': y_pred_test}

    def save_models(self, output_dir=None):
        """
        Save trained models and encoders to pickle files

        Args:
            output_dir: Directory to save models (auto-generates if None)

        Returns:
            dict: Paths to saved model files
        """
        if output_dir is None:
            output_dir = str(path_resolver.get_path("data/models"))

        # Create directory if local, handled by file_handler if cloud
        if not file_handler.is_cloud:
            os.makedirs(output_dir, exist_ok=True)

        paths = {}

        # Save annual cost model
        if self.cost_model:
            cost_model_data = pickle.dumps(self.cost_model)
            cost_model_path = file_handler.write_binary("data/models/annual_cost_predictor.pkl", cost_model_data)
            paths['cost_model'] = cost_model_path

        # Save service cost model
        if self.service_cost_model:
            service_model_data = pickle.dumps(self.service_cost_model)
            service_model_path = file_handler.write_binary("data/models/service_cost_predictor.pkl", service_model_data)
            paths['service_model'] = service_model_path

        # Save label encoders
        if self.label_encoders:
            encoders_data = pickle.dumps(self.label_encoders)
            encoders_path = file_handler.write_binary("data/models/label_encoders.pkl", encoders_data)
            paths['encoders'] = encoders_path

        # Save feature names
        features_json = json.dumps(self.feature_names)
        features_path = file_handler.write_text("data/models/feature_names.json", features_json)
        paths['features'] = features_path

        return paths

    def generate_model_card(self, output_path=None):
        """
        Generate model_card.md documentation

        Args:
            output_path: Path to save model card (auto-generates if None)

        Returns:
            str: Path to saved model card
        """
        if output_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            output_path = os.path.join(base_dir, "data", "models", "model_card.md")

        # Build model card content
        content = f"""# FleetGuard ML Models - Model Card

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Model 1: Annual Maintenance Cost Predictor

### Description
Predicts the expected annual maintenance cost for each vehicle in the fleet based on vehicle characteristics and service history.

### Architecture
- **Algorithm:** {self.metrics.get('annual_cost', {}).get('model_type', 'N/A').title()}
- **Type:** Regression
- **Framework:** scikit-learn

### Features
{chr(10).join([f"- {feat}" for feat in self.feature_names]) if self.feature_names else "- Features not available"}

### Performance Metrics
- **Train R² Score:** {self.metrics.get('annual_cost', {}).get('train_r2', 0):.4f}
- **Test R² Score:** {self.metrics.get('annual_cost', {}).get('test_r2', 0):.4f}
- **Train RMSE:** ₪{self.metrics.get('annual_cost', {}).get('train_rmse', 0):,.2f}
- **Test RMSE:** ₪{self.metrics.get('annual_cost', {}).get('test_rmse', 0):,.2f}
- **Train MAE:** ₪{self.metrics.get('annual_cost', {}).get('train_mae', 0):,.2f}
- **Test MAE:** ₪{self.metrics.get('annual_cost', {}).get('test_mae', 0):,.2f}
- **Cross-Validation R² (5-fold):** {self.metrics.get('annual_cost', {}).get('cv_r2_mean', 0):.4f} ± {self.metrics.get('annual_cost', {}).get('cv_r2_std', 0):.4f}

### Feature Importance
{chr(10).join([f"- **{feat}:** {imp:.4f}" for feat, imp in sorted(self.metrics.get('annual_cost', {}).get('feature_importance', {}).items(), key=lambda x: x[1], reverse=True)]) if 'annual_cost' in self.metrics and 'feature_importance' in self.metrics['annual_cost'] else "- Feature importance not available"}

### Target Variable
- **Name:** Annual Maintenance Cost
- **Unit:** Israeli Shekels (₪)
- **Calculation:** Total maintenance cost normalized to annual rate based on days in fleet

### Use Cases
- Budget planning for fleet maintenance
- Identifying high-cost vehicles for potential replacement
- Comparing actual costs vs predicted costs to detect anomalies

---

## Model 2: Next Service Cost Predictor

### Description
Predicts the expected cost of the next maintenance service for each vehicle based on service history and vehicle characteristics.

### Architecture
- **Algorithm:** {self.metrics.get('service_cost', {}).get('model_type', 'N/A').title()}
- **Type:** Regression
- **Framework:** scikit-learn

### Features
{chr(10).join([f"- {feat}" for feat in self.metrics.get('service_cost', {}).get('feature_importance', {}).keys()]) if 'service_cost' in self.metrics and 'feature_importance' in self.metrics['service_cost'] else "- Features not available"}

### Performance Metrics
- **Train R² Score:** {self.metrics.get('service_cost', {}).get('train_r2', 0):.4f}
- **Test R² Score:** {self.metrics.get('service_cost', {}).get('test_r2', 0):.4f}
- **Train RMSE:** ₪{self.metrics.get('service_cost', {}).get('train_rmse', 0):,.2f}
- **Test RMSE:** ₪{self.metrics.get('service_cost', {}).get('test_rmse', 0):,.2f}
- **Train MAE:** ₪{self.metrics.get('service_cost', {}).get('train_mae', 0):,.2f}
- **Test MAE:** ₪{self.metrics.get('service_cost', {}).get('test_mae', 0):,.2f}
- **Cross-Validation R² (5-fold):** {self.metrics.get('service_cost', {}).get('cv_r2_mean', 0):.4f} ± {self.metrics.get('service_cost', {}).get('cv_r2_std', 0):.4f}

### Feature Importance
{chr(10).join([f"- **{feat}:** {imp:.4f}" for feat, imp in sorted(self.metrics.get('service_cost', {}).get('feature_importance', {}).items(), key=lambda x: x[1], reverse=True)]) if 'service_cost' in self.metrics and 'feature_importance' in self.metrics['service_cost'] else "- Feature importance not available"}

### Target Variable
- **Name:** Next Service Cost
- **Unit:** Israeli Shekels (₪)
- **Calculation:** Based on average service cost with adjustments for vehicle history

### Use Cases
- Estimating costs for upcoming scheduled maintenance
- Budgeting for individual vehicle services
- Comparing rule-based predictions (PredictiveMaintenanceAgent) with ML predictions

---

## Training Data
- **Source:** FleetGuard SQLite database (`fleet.db`)
- **Tables:** vehicles, invoices
- **Total Vehicles:** {len(self.db.get_all_vehicles())}
- **Total Invoices:** {len(self.db.get_all_invoices())}

## Limitations
- Models trained on synthetic data generated by `generate_data.py`
- Performance on real-world data may vary
- Assumes consistent data quality and schema
- Workshop pricing biases (30% variations) are embedded in training data
- Limited to Israeli Shekel currency

## Usage Instructions

### Loading Models
```python
import pickle
with open('data/models/annual_cost_predictor.pkl', 'rb') as f:
    cost_model = pickle.load(f)

with open('data/models/service_cost_predictor.pkl', 'rb') as f:
    service_model = pickle.load(f)
```

### Making Predictions
```python
from src.utils.ml_trainer import FleetMLTrainer

trainer = FleetMLTrainer()
df_features = trainer.prepare_features()

# Annual cost prediction
annual_cost_pred = trainer.cost_model.predict(df_features[trainer.feature_names])

# Service cost prediction
service_cost_pred = trainer.service_cost_model.predict(df_features[service_features])
```

---

**Generated by FleetGuard Multi-Agent System (CrewAI)**
"""

        # Save model card
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path


# --- Testing ---
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("FLEET ML TRAINER - TESTING BOTH MODELS")
    print("=" * 80)

    trainer = FleetMLTrainer()

    # Prepare features
    print("\n[1/5] Preparing features...")
    df_features = trainer.prepare_features()
    print(f"✓ Feature engineering complete. Shape: {df_features.shape}")

    # Train Model 1: Annual Cost
    print("\n[2/5] Training Model 1: Annual Cost Predictor...")
    result_cost = trainer.train_annual_cost_model(df_features)
    print(f"✓ Annual Cost Model Trained")
    print(f"  - Test R²: {result_cost['metrics']['test_r2']:.4f}")
    print(f"  - Test RMSE: ₪{result_cost['metrics']['test_rmse']:,.2f}")
    print(f"  - Test MAE: ₪{result_cost['metrics']['test_mae']:,.2f}")

    # Train Model 2: Service Cost
    print("\n[3/5] Training Model 2: Next Service Cost Predictor...")
    result_service = trainer.train_service_cost_model(df_features)
    print(f"✓ Service Cost Model Trained")
    print(f"  - Test R²: {result_service['metrics']['test_r2']:.4f}")
    print(f"  - Test RMSE: ₪{result_service['metrics']['test_rmse']:,.2f}")
    print(f"  - Test MAE: ₪{result_service['metrics']['test_mae']:,.2f}")

    # Save models
    print("\n[4/5] Saving models...")
    paths = trainer.save_models()
    for key, path in paths.items():
        print(f"  ✓ {key}: {path}")

    # Generate model card
    print("\n[5/5] Generating model card...")
    card_path = trainer.generate_model_card()
    print(f"  ✓ Model card saved: {card_path}")

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE!")
    print("=" * 80)
