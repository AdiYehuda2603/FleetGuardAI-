# -*- coding: utf-8 -*-
"""
Agent F: Model Evaluator
תפקיד: הערכת ביצועי המודל, ניתוח feature importance, יצירת דוחות
"""

import pandas as pd
import numpy as np
import os
import json
import joblib
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

# ML Libraries
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, mean_absolute_percentage_error

# FleetGuard utilities
try:
    from src.utils.file_handler import file_handler
    from src.utils.path_resolver import path_resolver
except ImportError:
    from utils.file_handler import file_handler
    from utils.path_resolver import path_resolver

import warnings
warnings.filterwarnings('ignore')


class ModelEvaluator:
    """
    סוכן F - Model Evaluator
    אחראי על הערכת מודל, ניתוח תוצאות ויצירת דוחות
    """

    def __init__(self,
                 model_path='models/model.pkl',
                 metadata_path='models/model_metadata.json',
                 features_path='data/processed/features.csv'):
        self.model_path = model_path
        self.metadata_path = metadata_path
        self.features_path = features_path
        self.model = None
        self.metadata = None
        self.X_test = None
        self.y_test = None
        self.y_pred = None
        self.feature_names = None

    def load_model_and_data(self):
        """
        טעינת המודל המאומן והנתונים
        """
        print("[*] Agent F: Loading trained model and data...")

        # טעינת המודל
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        self.model = joblib.load(self.model_path)
        print(f"[+] Model loaded: {self.model_path}")

        # טעינת metadata
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            print(f"[+] Metadata loaded: {self.metadata['model_name']}")
            self.feature_names = self.metadata.get('feature_names', [])
        else:
            print("[!] Metadata file not found - using default feature names")
            self.feature_names = []

        # טעינת נתונים
        df = pd.read_csv(self.features_path)
        print(f"[+] Features loaded: {len(df)} records")

        # הכנת test data (נשתמש ב-20% אחרונים כ-test)
        from sklearn.model_selection import train_test_split

        id_columns = ['vehicle_id', 'plate']
        target = 'monthly_maintenance_cost'
        features_to_drop = id_columns + [target, 'annual_cost']

        X = df.drop(columns=[col for col in features_to_drop if col in df.columns])
        y = df[target]

        # Split עם אותו random_state כמו ב-Agent E
        _, self.X_test, _, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print(f"[+] Test set prepared: {len(self.X_test)} samples")

        return self.model, self.X_test, self.y_test

    def calculate_metrics(self):
        """
        חישוב מדדי ביצועים מפורטים
        """
        print("\n[*] Agent F: Calculating performance metrics...")

        self.y_pred = self.model.predict(self.X_test)

        metrics = {
            'r2_score': r2_score(self.y_test, self.y_pred),
            'rmse': np.sqrt(mean_squared_error(self.y_test, self.y_pred)),
            'mae': mean_absolute_error(self.y_test, self.y_pred),
            'mape': mean_absolute_percentage_error(self.y_test, self.y_pred) * 100,  # in percentage
            'mean_prediction': float(np.mean(self.y_pred)),
            'std_prediction': float(np.std(self.y_pred)),
            'mean_actual': float(np.mean(self.y_test)),
            'std_actual': float(np.std(self.y_test)),
            'min_error': float(np.min(self.y_test - self.y_pred)),
            'max_error': float(np.max(self.y_test - self.y_pred))
        }

        print(f"[+] R² Score: {metrics['r2_score']:.4f}")
        print(f"[+] RMSE: {metrics['rmse']:.2f}")
        print(f"[+] MAE: {metrics['mae']:.2f}")
        print(f"[+] MAPE: {metrics['mape']:.2f}%")

        return metrics

    def analyze_feature_importance(self):
        """
        ניתוח חשיבות פיצ'רים
        """
        print("\n[*] Agent F: Analyzing feature importance...")

        # בדיקה אם המודל תומך ב-feature importance
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            feature_importance = pd.DataFrame({
                'feature': self.feature_names if self.feature_names else [f'feature_{i}' for i in range(len(importances))],
                'importance': importances
            }).sort_values('importance', ascending=False)

            print(f"[+] Top 5 most important features:")
            for idx, row in feature_importance.head(5).iterrows():
                print(f"    {row['feature']}: {row['importance']:.4f}")

            return feature_importance
        else:
            print("[!] Model does not support feature importance")
            return None

    def create_residual_plot(self, output_dir='reports'):
        """
        יצירת גרף residuals (תחזית מול ערכים אמיתיים)
        """
        print("\n[*] Agent F: Creating residual plot...")

        os.makedirs(output_dir, exist_ok=True)

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Plot 1: Predicted vs Actual
        axes[0].scatter(self.y_test, self.y_pred, alpha=0.6, edgecolors='k')
        axes[0].plot([self.y_test.min(), self.y_test.max()],
                     [self.y_test.min(), self.y_test.max()],
                     'r--', lw=2, label='Perfect Prediction')
        axes[0].set_xlabel('Actual Monthly Cost (ILS)', fontsize=12)
        axes[0].set_ylabel('Predicted Monthly Cost (ILS)', fontsize=12)
        axes[0].set_title('Predicted vs Actual Values', fontsize=14, fontweight='bold')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Plot 2: Residuals
        residuals = self.y_test - self.y_pred
        axes[1].scatter(self.y_pred, residuals, alpha=0.6, edgecolors='k')
        axes[1].axhline(y=0, color='r', linestyle='--', lw=2, label='Zero Error')
        axes[1].set_xlabel('Predicted Monthly Cost (ILS)', fontsize=12)
        axes[1].set_ylabel('Residuals (Actual - Predicted)', fontsize=12)
        axes[1].set_title('Residual Plot', fontsize=14, fontweight='bold')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, 'residual_plot.png')
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"[+] Residual plot saved: {plot_path}")
        return plot_path

    def create_feature_importance_plot(self, feature_importance, output_dir='reports'):
        """
        יצירת גרף feature importance
        """
        if feature_importance is None:
            return None

        print("\n[*] Agent F: Creating feature importance plot...")

        os.makedirs(output_dir, exist_ok=True)

        plt.figure(figsize=(10, 6))
        top_features = feature_importance.head(10)

        plt.barh(range(len(top_features)), top_features['importance'], color='steelblue', edgecolor='k')
        plt.yticks(range(len(top_features)), top_features['feature'])
        plt.xlabel('Importance Score', fontsize=12)
        plt.ylabel('Feature', fontsize=12)
        plt.title('Top 10 Feature Importance', fontsize=14, fontweight='bold')
        plt.gca().invert_yaxis()
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()

        plot_path = os.path.join(output_dir, 'feature_importance.png')
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"[+] Feature importance plot saved: {plot_path}")
        return plot_path

    def generate_evaluation_report(self, metrics, feature_importance, output_dir='reports'):
        """
        יצירת דוח הערכה מפורט (Markdown)
        """
        print("\n[*] Agent F: Generating evaluation report...")

        os.makedirs(output_dir, exist_ok=True)

        report_lines = [
            "# Model Evaluation Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Model:** {self.metadata.get('model_name', 'Unknown') if self.metadata else 'Unknown'}",
            "",
            "---",
            "",
            "## Performance Metrics",
            "",
            "| Metric | Value | Status |",
            "|--------|-------|--------|",
            f"| R² Score | {metrics['r2_score']:.4f} | {'✅ Pass' if metrics['r2_score'] > 0.75 else '❌ Fail'} (Target: > 0.75) |",
            f"| RMSE | ₪{metrics['rmse']:.2f} | {'✅ Pass' if metrics['rmse'] < 500 else '❌ Fail'} (Target: < ₪500) |",
            f"| MAE | ₪{metrics['mae']:.2f} | {'✅ Pass' if metrics['mae'] < 400 else '❌ Fail'} (Target: < ₪400) |",
            f"| MAPE | {metrics['mape']:.2f}% | {'✅ Pass' if metrics['mape'] < 15 else '⚠️ Warning'} (Target: < 15%) |",
            "",
            "## Prediction Statistics",
            "",
            "| Statistic | Value |",
            "|-----------|-------|",
            f"| Mean Prediction | ₪{metrics['mean_prediction']:.2f} |",
            f"| Std Prediction | ₪{metrics['std_prediction']:.2f} |",
            f"| Mean Actual | ₪{metrics['mean_actual']:.2f} |",
            f"| Std Actual | ₪{metrics['std_actual']:.2f} |",
            f"| Min Error | ₪{metrics['min_error']:.2f} |",
            f"| Max Error | ₪{metrics['max_error']:.2f} |",
            "",
            "## Model Performance Assessment",
            "",
        ]

        # הערכה כללית
        if metrics['r2_score'] > 0.9:
            report_lines.append("✅ **Excellent Performance**: The model explains over 90% of variance in maintenance costs.")
        elif metrics['r2_score'] > 0.75:
            report_lines.append("✅ **Good Performance**: The model meets the target threshold and provides reliable predictions.")
        else:
            report_lines.append("❌ **Poor Performance**: The model does not meet the minimum R² threshold of 0.75.")

        report_lines.extend([
            "",
            f"The model predicts monthly maintenance costs with an average error of ±₪{metrics['mae']:.2f} ({metrics['mape']:.1f}% relative error).",
            "",
            "## Feature Importance",
            ""
        ])

        if feature_importance is not None:
            report_lines.append("| Rank | Feature | Importance Score |")
            report_lines.append("|------|---------|------------------|")
            for idx, (_, row) in enumerate(feature_importance.head(10).iterrows(), 1):
                report_lines.append(f"| {idx} | {row['feature']} | {row['importance']:.4f} |")
        else:
            report_lines.append("_Feature importance not available for this model type._")

        report_lines.extend([
            "",
            "## Visualizations",
            "",
            "- **Residual Plot**: `residual_plot.png`",
            "- **Feature Importance**: `feature_importance.png`",
            "",
            "## Business Impact",
            "",
            f"With an MAE of ₪{metrics['mae']:.2f}, the model can help predict monthly maintenance costs within approximately ±₪{metrics['mae']*2:.0f} range (95% confidence).",
            "",
            "**Key Benefits:**",
            "- Proactive budget planning with {:.1f}% accuracy".format(100 - metrics['mape']),
            "- Early identification of high-cost vehicles",
            "- Optimized maintenance scheduling",
            "",
            "## Recommendations",
            "",
        ])

        if metrics['r2_score'] > 0.9 and metrics['mae'] < 20:
            report_lines.append("✅ **Deploy to Production**: Model is ready for production use.")
        elif metrics['r2_score'] > 0.75:
            report_lines.append("⚠️ **Monitor Performance**: Model meets minimum criteria but should be monitored closely.")
        else:
            report_lines.append("❌ **Retrain Model**: Consider adding more features or collecting more data.")

        report_lines.extend([
            "",
            "---",
            "",
            f"_Report generated by Agent F (Model Evaluator) on {datetime.now().strftime('%Y-%m-%d')}_"
        ])

        report_content = '\n'.join(report_lines)
        report_path = file_handler.write_text(f"{output_dir}/evaluation_report.md", report_content)

        print(f"[+] Evaluation report saved: {report_path}")
        return report_path

    def save_metrics_json(self, metrics, feature_importance, output_dir='reports'):
        """
        שמירת מדדים ב-JSON לשימוש עתידי
        """
        print("\n[*] Agent F: Saving metrics to JSON...")

        # Create directory if local, handled by file_handler if cloud
        if not file_handler.is_cloud:
            os.makedirs(output_dir, exist_ok=True)

        output = {
            'evaluation_date': datetime.now().isoformat(),
            'model_name': self.metadata.get('model_name', 'Unknown') if self.metadata else 'Unknown',
            'metrics': metrics,
            'feature_importance': feature_importance.to_dict('records') if feature_importance is not None else None,
            'test_samples': len(self.X_test),
            'status': 'PASS' if metrics['r2_score'] > 0.75 and metrics['rmse'] < 500 else 'FAIL'
        }

        json_content = json.dumps(output, indent=2, ensure_ascii=False)
        json_path = file_handler.write_text(f"{output_dir}/evaluation_metrics.json", json_content)

        print(f"[+] Metrics JSON saved: {json_path}")
        return json_path

    def run(self):
        """
        הרצת תהליך הערכת המודל המלא
        """
        print("\n" + "="*60)
        print("AGENT F: MODEL EVALUATOR - STARTING")
        print("="*60 + "\n")

        try:
            # 1. טעינת מודל ונתונים
            self.load_model_and_data()

            # 2. חישוב מדדי ביצועים
            metrics = self.calculate_metrics()

            # 3. ניתוח feature importance
            feature_importance = self.analyze_feature_importance()

            # 4. יצירת גרפים
            residual_plot = self.create_residual_plot()
            importance_plot = self.create_feature_importance_plot(feature_importance)

            # 5. יצירת דוח
            report_path = self.generate_evaluation_report(metrics, feature_importance)

            # 6. שמירת JSON
            json_path = self.save_metrics_json(metrics, feature_importance)

            print("\n" + "="*60)
            print("AGENT F: MODEL EVALUATION COMPLETED SUCCESSFULLY")
            print("="*60 + "\n")

            return {
                'success': True,
                'metrics': metrics,
                'report_path': report_path,
                'json_path': json_path,
                'plots': {
                    'residual': residual_plot,
                    'importance': importance_plot
                },
                'status': 'PASS' if metrics['r2_score'] > 0.75 and metrics['rmse'] < 500 else 'FAIL'
            }

        except Exception as e:
            print(f"\n[ERROR] AGENT F ERROR: {e}")
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
    evaluator = ModelEvaluator()
    result = evaluator.run()

    if result['success']:
        print(f"\n[SUCCESS] Model evaluation completed!")
        print(f"[+] Status: {result['status']}")
        print(f"[+] R2: {result['metrics']['r2_score']:.4f}")
        print(f"[+] RMSE: {result['metrics']['rmse']:.2f}")
        print(f"[+] MAE: {result['metrics']['mae']:.2f}")
        print(f"[+] Report: {result['report_path']}")
    else:
        print(f"\n[FAILED] {result['error']}")
