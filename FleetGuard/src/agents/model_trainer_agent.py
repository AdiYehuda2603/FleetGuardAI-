# -*- coding: utf-8 -*-
"""
Agent E: Model Trainer + Performance Reporter
תפקיד: אימון מודלי ML + יצירת דוחות מפורטים לדשבורד

פלט צפוי:
✅ מודל מאומן (models/model.pkl)
✅ מטא-דאטה (models/model_metadata.json)
✅ דוח השוואת מודלים (models/models_comparison.json)

מדדי ביצוע מינימליים:
- R² > 0.75 (המודל מסביר 75%+ מהשונות)
- RMSE < ₪500 (שגיאה ממוצעת מתחת ל-500 ש"ח)
- MAE < ₪400 (שגיאה אבסולוטית ממוצעת מתחת ל-400 ש"ח)

המלצות לפעולה:
- אם R² > 0.9: המודל מוכן לפרודקשן ✅
- אם 0.75 < R² < 0.9: שקול הוספת פיצ'רים נוספים
- אם R² < 0.75: בדוק איכות נתונים ושקול מודלים מתקדמים יותר
"""

import pandas as pd
import numpy as np
import os
import json
import joblib
from datetime import datetime

# ML Libraries
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Optional: XGBoost (if available)
try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("[!] XGBoost not available - will use RandomForest and GradientBoosting only")


class ModelTrainer:
    """
    סוכן E - Model Trainer
    אחראי על אימון מודלי ML וחיזוי עלויות תחזוקה
    """

    def __init__(self, features_path='data/processed/features.csv'):
        self.features_path = features_path
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.feature_names = None

    def load_features(self):
        """
        טעינת פיצ'רים מעובדים מ-Agent D
        """
        print("[*] Agent E: Loading processed features...")

        if not os.path.exists(self.features_path):
            raise FileNotFoundError(f"Features file not found: {self.features_path}")

        df = pd.read_csv(self.features_path)
        print(f"[+] Loaded {len(df)} records with {len(df.columns)} columns")

        return df

    def prepare_data(self, df, target_column='monthly_maintenance_cost', test_size=0.2, random_state=42):
        """
        הכנת נתונים: הפרדת features ו-target, חלוקה לאימון ובדיקה
        """
        print("[*] Agent E: Preparing data for training...")

        # הסרת עמודות מזהות (לא לאימון)
        id_columns = ['vehicle_id', 'plate']
        features_to_drop = id_columns + [target_column, 'annual_cost']  # annual_cost הוא נגזרת

        # יצירת X (features) ו-y (target)
        X = df.drop(columns=[col for col in features_to_drop if col in df.columns])
        y = df[target_column]

        self.feature_names = X.columns.tolist()

        print(f"[+] Features shape: {X.shape}")
        print(f"[+] Target shape: {y.shape}")
        print(f"[+] Feature columns: {self.feature_names}")

        # Train-Test Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test

        print(f"[+] Training set: {len(X_train)} samples")
        print(f"[+] Test set: {len(X_test)} samples")

        return X_train, X_test, y_train, y_test

    def train_random_forest(self, n_estimators=100, max_depth=10, random_state=42):
        """
        אימון Random Forest Regressor
        """
        print("\n[*] Agent E: Training Random Forest model...")

        model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1
        )

        model.fit(self.X_train, self.y_train)

        # Evaluation
        train_score = model.score(self.X_train, self.y_train)
        test_score = model.score(self.X_test, self.y_test)

        y_pred = model.predict(self.X_test)
        rmse = np.sqrt(mean_squared_error(self.y_test, y_pred))
        mae = mean_absolute_error(self.y_test, y_pred)

        print(f"[+] Random Forest trained successfully")
        print(f"    Train R2: {train_score:.4f}")
        print(f"    Test R2: {test_score:.4f}")
        print(f"    RMSE: {rmse:.2f}")
        print(f"    MAE: {mae:.2f}")

        self.models['RandomForest'] = {
            'model': model,
            'train_r2': train_score,
            'test_r2': test_score,
            'rmse': rmse,
            'mae': mae
        }

        return model

    def train_gradient_boosting(self, n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42):
        """
        אימון Gradient Boosting Regressor
        """
        print("\n[*] Agent E: Training Gradient Boosting model...")

        model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state
        )

        model.fit(self.X_train, self.y_train)

        # Evaluation
        train_score = model.score(self.X_train, self.y_train)
        test_score = model.score(self.X_test, self.y_test)

        y_pred = model.predict(self.X_test)
        rmse = np.sqrt(mean_squared_error(self.y_test, y_pred))
        mae = mean_absolute_error(self.y_test, y_pred)

        print(f"[+] Gradient Boosting trained successfully")
        print(f"    Train R2: {train_score:.4f}")
        print(f"    Test R2: {test_score:.4f}")
        print(f"    RMSE: {rmse:.2f}")
        print(f"    MAE: {mae:.2f}")

        self.models['GradientBoosting'] = {
            'model': model,
            'train_r2': train_score,
            'test_r2': test_score,
            'rmse': rmse,
            'mae': mae
        }

        return model

    def train_xgboost(self, n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42):
        """
        אימון XGBoost Regressor (אם זמין)
        """
        if not XGBOOST_AVAILABLE:
            print("[!] XGBoost not available - skipping")
            return None

        print("\n[*] Agent E: Training XGBoost model...")

        model = XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            n_jobs=-1
        )

        model.fit(self.X_train, self.y_train)

        # Evaluation
        train_score = model.score(self.X_train, self.y_train)
        test_score = model.score(self.X_test, self.y_test)

        y_pred = model.predict(self.X_test)
        rmse = np.sqrt(mean_squared_error(self.y_test, y_pred))
        mae = mean_absolute_error(self.y_test, y_pred)

        print(f"[+] XGBoost trained successfully")
        print(f"    Train R2: {train_score:.4f}")
        print(f"    Test R2: {test_score:.4f}")
        print(f"    RMSE: {rmse:.2f}")
        print(f"    MAE: {mae:.2f}")

        self.models['XGBoost'] = {
            'model': model,
            'train_r2': train_score,
            'test_r2': test_score,
            'rmse': rmse,
            'mae': mae
        }

        return model

    def select_best_model(self):
        """
        בחירת המודל הטוב ביותר לפי R² על test set
        """
        print("\n[*] Agent E: Selecting best model...")

        if not self.models:
            raise ValueError("No models trained yet!")

        # מציאת המודל עם R² הגבוה ביותר על test
        best_name = max(self.models.keys(), key=lambda k: self.models[k]['test_r2'])
        self.best_model = self.models[best_name]['model']
        self.best_model_name = best_name

        print(f"[+] Best model: {best_name}")
        print(f"    Test R2: {self.models[best_name]['test_r2']:.4f}")
        print(f"    RMSE: {self.models[best_name]['rmse']:.2f}")
        print(f"    MAE: {self.models[best_name]['mae']:.2f}")

        return self.best_model, best_name

    def generate_recommendations(self):
        """
        יצירת המלצות אוטומטיות לפי ביצועי המודל
        """
        if not self.best_model_name:
            return []

        r2 = self.models[self.best_model_name]['test_r2']
        rmse = self.models[self.best_model_name]['rmse']
        mae = self.models[self.best_model_name]['mae']

        recommendations = []

        # המלצה לפי R²
        if r2 > 0.9:
            recommendations.append("[OK] המודל מוכן לפרודקשן - דיוק מעולה!")
            recommendations.append(f"המודל מסביר {r2*100:.1f}% מהשונות בעלויות")
        elif r2 > 0.75:
            recommendations.append("[WARNING] ביצועים טובים - שקול שיפור נוסף")
            recommendations.append("המלצה: הוסף פיצ'רים נוספים או כוונן היפר-פרמטרים")
        else:
            recommendations.append("[ERROR] ביצועים נמוכים - נדרש שיפור משמעותי")
            recommendations.append("בדוק איכות נתונים ושקול מודלים מתקדמים יותר")

        # המלצה לפי דיוק תחזית
        recommendations.append(f"[INFO] דיוק תחזית ממוצע: ±₪{int(mae)} לחודש")

        if mae < 50:
            recommendations.append("[OK] דיוק תחזית מצוין - מתאים לתקצוב מדויק")
        elif mae < 100:
            recommendations.append("[OK] דיוק תחזית טוב - מתאים לתכנון חודשי")
        else:
            recommendations.append("[WARNING] שקול הוספת נתונים היסטוריים נוספים")

        # המלצה לפי RMSE
        if rmse < 100:
            recommendations.append("[OK] שגיאות קיצוניות נמוכות - המודל יציב")

        return recommendations

    def save_model(self, output_dir='models'):
        """
        שמירת המודל הטוב ביותר לקובץ + המלצות
        """
        print(f"\n[*] Agent E: Saving best model to {output_dir}...")

        os.makedirs(output_dir, exist_ok=True)

        # שמירת המודל
        model_path = os.path.join(output_dir, 'model.pkl')
        joblib.dump(self.best_model, model_path)
        print(f"[+] Model saved: {model_path}")

        # יצירת המלצות
        recommendations = self.generate_recommendations()

        # שמירת מטא-דאטה
        metadata = {
            'model_name': self.best_model_name,
            'train_r2': float(self.models[self.best_model_name]['train_r2']),
            'test_r2': float(self.models[self.best_model_name]['test_r2']),
            'rmse': float(self.models[self.best_model_name]['rmse']),
            'mae': float(self.models[self.best_model_name]['mae']),
            'features': self.feature_names,
            'target_variable': 'monthly_maintenance_cost',
            'train_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'training_samples': len(self.X_train),
            'test_samples': len(self.X_test),
            'recommendations': recommendations
        }

        metadata_path = os.path.join(output_dir, 'model_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"[+] Metadata saved: {metadata_path}")

        # הצגת המלצות
        print("\n[*] Agent E Recommendations:")
        for rec in recommendations:
            print(f"    {rec}")

        # שמירת השוואת מודלים
        comparison = {
            model_name: {
                'test_r2': float(info['test_r2']),
                'rmse': float(info['rmse']),
                'mae': float(info['mae'])
            }
            for model_name, info in self.models.items()
        }

        comparison_path = os.path.join(output_dir, 'models_comparison.json')
        with open(comparison_path, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2)
        print(f"[+] Model comparison saved: {comparison_path}")

        return model_path, metadata_path

    def run(self):
        """
        הרצת תהליך אימון המודל המלא
        """
        print("\n" + "="*60)
        print("AGENT E: MODEL TRAINER - STARTING")
        print("="*60 + "\n")

        try:
            # 1. טעינת פיצ'רים
            df = self.load_features()

            # 2. הכנת נתונים
            self.prepare_data(df)

            # 3. אימון מודלים
            self.train_random_forest(n_estimators=100, max_depth=10)
            self.train_gradient_boosting(n_estimators=100, max_depth=5, learning_rate=0.1)

            if XGBOOST_AVAILABLE:
                self.train_xgboost(n_estimators=100, max_depth=5, learning_rate=0.1)

            # 4. בחירת המודל הטוב ביותר
            best_model, best_name = self.select_best_model()

            # 5. שמירת המודל
            model_path, metadata_path = self.save_model()

            # יצירת המלצות
            recommendations = self.generate_recommendations()

            print("\n" + "="*60)
            print("AGENT E: MODEL TRAINING COMPLETED SUCCESSFULLY")
            print("="*60 + "\n")

            return {
                'success': True,
                'best_model_name': best_name,
                'model_path': model_path,
                'metadata_path': metadata_path,
                'performance': {
                    'test_r2': self.models[best_name]['test_r2'],
                    'train_r2': self.models[best_name]['train_r2'],
                    'rmse': self.models[best_name]['rmse'],
                    'mae': self.models[best_name]['mae']
                },
                'recommendations': recommendations,
                'ready_for_production': self.models[best_name]['test_r2'] > 0.9
            }

        except Exception as e:
            print(f"\n[ERROR] AGENT E ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }


# =============================================
# הרצה עצמאית לבדיקה
# =============================================
if __name__ == "__main__":
    trainer = ModelTrainer()
    result = trainer.run()

    if result['success']:
        print(f"\n[SUCCESS] Model training completed!")
        print(f"[+] Best model: {result['best_model_name']}")
        print(f"[+] Test R2: {result['performance']['test_r2']:.4f}")
        print(f"[+] RMSE: {result['performance']['rmse']:.2f}")
        print(f"[+] MAE: {result['performance']['mae']:.2f}")
        print(f"[+] Ready for production: {result['ready_for_production']}")
        print(f"[+] Model saved: {result['model_path']}")
        print(f"\n[INFO] Recommendations ({len(result['recommendations'])} items):")
        for rec in result['recommendations']:
            print(f"    {rec}")
    else:
        print(f"\n[FAILED] {result['error']}")
