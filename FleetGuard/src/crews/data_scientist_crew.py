# -*- coding: utf-8 -*-
"""
Crew 2: Data Scientist Crew
תפקיד: תיאום בין 3 סוכני ML - Feature Engineering, Model Training, Model Evaluation
"""

import os
import sys
import json
from datetime import datetime

# הוספת נתיב לייבוא
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ייבוא 3 הסוכנים
try:
    from agents.feature_engineer_agent import FeatureEngineer
    from agents.model_trainer_agent import ModelTrainer
    from agents.model_evaluator_agent import ModelEvaluator
except ImportError:
    from src.agents.feature_engineer_agent import FeatureEngineer
    from src.agents.model_trainer_agent import ModelTrainer
    from src.agents.model_evaluator_agent import ModelEvaluator


class DataScientistCrew:
    """
    Crew 2 - Data Scientist Crew
    מתאם אוטומטי בין 3 סוכני ML:
    - Agent D: Feature Engineer
    - Agent E: Model Trainer
    - Agent F: Model Evaluator
    """

    def __init__(self):
        self.agent_d = None
        self.agent_e = None
        self.agent_f = None
        self.results = {
            'crew_name': 'Data Scientist Crew',
            'crew_id': 'CREW_2',
            'execution_time': None,
            'status': 'NOT_STARTED',
            'steps': {}
        }

    def validate_step(self, step_name, result):
        """
        ולידציה של תוצאות כל שלב
        """
        if not result.get('success', False):
            error_msg = result.get('error', 'Unknown error')
            print(f"\n[ERROR] {step_name} FAILED: {error_msg}")
            self.results['status'] = 'FAILED'
            self.results['failed_step'] = step_name
            self.results['error'] = error_msg
            return False

        print(f"[+] {step_name} completed successfully")
        return True

    def run_feature_engineering(self):
        """
        שלב 1: Feature Engineering (Agent D)
        """
        print("\n" + "="*60)
        print("[STEP 1/3] Running Feature Engineering (Agent D)...")
        print("="*60)

        self.agent_d = FeatureEngineer()
        result = self.agent_d.run()

        if self.validate_step("Feature Engineering", result):
            self.results['steps']['feature_engineering'] = {
                'status': 'SUCCESS',
                'output_file': result.get('output_file'),
                'num_records': result.get('num_records'),
                'num_features': result.get('num_features'),
                'target_variable': result.get('target_variable')
            }
            print(f"[+] Features created: {result['num_records']} records, {result['num_features']} features")
            return result
        else:
            self.results['steps']['feature_engineering'] = {
                'status': 'FAILED',
                'error': result.get('error')
            }
            return None

    def run_model_training(self):
        """
        שלב 2: Model Training (Agent E)
        """
        print("\n" + "="*60)
        print("[STEP 2/3] Running Model Training (Agent E)...")
        print("="*60)

        self.agent_e = ModelTrainer()
        result = self.agent_e.run()

        if self.validate_step("Model Training", result):
            perf = result.get('performance', {})
            self.results['steps']['model_training'] = {
                'status': 'SUCCESS',
                'best_model_name': result.get('best_model_name'),
                'model_path': result.get('model_path'),
                'test_r2': perf.get('test_r2'),
                'train_r2': perf.get('train_r2'),
                'rmse': perf.get('rmse'),
                'mae': perf.get('mae'),
                'ready_for_production': result.get('ready_for_production', False),
                'recommendations': result.get('recommendations', [])
            }
            print(f"[+] Model trained: {result['best_model_name']}, R2={perf.get('test_r2', 0):.4f}")
            if result.get('recommendations'):
                print(f"[+] Recommendations: {len(result['recommendations'])} items")
            return result
        else:
            self.results['steps']['model_training'] = {
                'status': 'FAILED',
                'error': result.get('error')
            }
            return None

    def run_model_evaluation(self):
        """
        שלב 3: Model Evaluation (Agent F)
        """
        print("\n" + "="*60)
        print("[STEP 3/3] Running Model Evaluation (Agent F)...")
        print("="*60)

        self.agent_f = ModelEvaluator()
        result = self.agent_f.run()

        if self.validate_step("Model Evaluation", result):
            self.results['steps']['model_evaluation'] = {
                'status': 'SUCCESS',
                'evaluation_status': result.get('status'),
                'report_path': result.get('report_path'),
                'metrics': result.get('metrics'),
                'plots': result.get('plots')
            }
            print(f"[+] Evaluation completed: {result['status']}")
            return result
        else:
            self.results['steps']['model_evaluation'] = {
                'status': 'FAILED',
                'error': result.get('error')
            }
            return None

    def run_pipeline(self):
        """
        הרצת Pipeline מלא: D → E → F
        """
        start_time = datetime.now()

        print("\n" + "="*70)
        print("CREW 2: DATA SCIENTIST CREW - STARTING FULL PIPELINE")
        print("="*70)
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")

        # שלב 1: Feature Engineering
        feature_result = self.run_feature_engineering()
        if feature_result is None:
            return self._finalize_results(start_time, success=False)

        # שלב 2: Model Training
        training_result = self.run_model_training()
        if training_result is None:
            return self._finalize_results(start_time, success=False)

        # שלב 3: Model Evaluation
        evaluation_result = self.run_model_evaluation()
        if evaluation_result is None:
            return self._finalize_results(start_time, success=False)

        # הכל הצליח!
        return self._finalize_results(start_time, success=True)

    def _finalize_results(self, start_time, success=True):
        """
        סיכום תוצאות והחזרה
        """
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        self.results['execution_time'] = f"{duration:.2f} seconds"
        self.results['start_time'] = start_time.isoformat()
        self.results['end_time'] = end_time.isoformat()

        if success:
            self.results['status'] = 'SUCCESS'
            self._print_success_summary()
        else:
            self.results['status'] = 'FAILED'
            self._print_failure_summary()

        # שמירת דוח JSON
        self._save_crew_report()

        return self.results

    def _print_success_summary(self):
        """
        הדפסת סיכום הצלחה
        """
        print("\n" + "="*70)
        print("CREW 2: PIPELINE COMPLETED SUCCESSFULLY")
        print("="*70)

        print("\nFinal Results:")
        print("-" * 70)

        # Feature Engineering
        if 'feature_engineering' in self.results['steps']:
            fe = self.results['steps']['feature_engineering']
            print(f"[+] Features: {fe.get('output_file')}")
            print(f"    Records: {fe.get('num_records')}, Features: {fe.get('num_features')}")

        # Model Training
        if 'model_training' in self.results['steps']:
            mt = self.results['steps']['model_training']
            print(f"[+] Model: {mt.get('model_path')}")
            print(f"    Type: {mt.get('best_model_name')}, R2: {mt.get('test_r2', 0):.4f}")

        # Model Evaluation
        if 'model_evaluation' in self.results['steps']:
            me = self.results['steps']['model_evaluation']
            print(f"[+] Report: {me.get('report_path')}")
            print(f"    Status: {me.get('evaluation_status')}")

        print("-" * 70)
        print(f"[+] Total execution time: {self.results['execution_time']}")
        print("="*70 + "\n")

        # המלצה
        if self.results['steps'].get('model_evaluation', {}).get('evaluation_status') == 'PASS':
            print("[RECOMMENDATION] Model is READY FOR PRODUCTION")
        else:
            print("[RECOMMENDATION] Model needs further tuning")

    def _print_failure_summary(self):
        """
        הדפסת סיכום כשלון
        """
        print("\n" + "="*70)
        print("CREW 2: PIPELINE FAILED")
        print("="*70)

        failed_step = self.results.get('failed_step', 'Unknown')
        error = self.results.get('error', 'Unknown error')

        print(f"\n[ERROR] Pipeline failed at: {failed_step}")
        print(f"[ERROR] Reason: {error}")
        print("\n" + "="*70 + "\n")

    def _save_crew_report(self):
        """
        שמירת דוח Crew 2 ל-JSON
        """
        report_dir = 'reports'
        os.makedirs(report_dir, exist_ok=True)

        report_path = os.path.join(report_dir, 'crew2_report.json')

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n[+] Crew 2 report saved: {report_path}")
        return report_path

    def get_summary(self):
        """
        החזרת סיכום מקוצר
        """
        return {
            'crew_id': self.results['crew_id'],
            'status': self.results['status'],
            'execution_time': self.results['execution_time'],
            'model_ready': self.results['steps'].get('model_evaluation', {}).get('evaluation_status') == 'PASS'
        }


# =============================================
# הרצה עצמאית לבדיקה
# =============================================
if __name__ == "__main__":
    print("\n" + "#"*70)
    print("# FleetGuard AI - Data Scientist Crew (Crew 2)")
    print("# Full ML Pipeline: Feature Engineering -> Training -> Evaluation")
    print("#"*70 + "\n")

    crew = DataScientistCrew()
    results = crew.run_pipeline()

    # הדפסת תוצאה סופית
    if results['status'] == 'SUCCESS':
        print("\n" + "="*70)
        print("FINAL STATUS: SUCCESS")
        print("="*70)
        summary = crew.get_summary()
        print(f"Model Ready for Production: {summary['model_ready']}")
        exit(0)
    else:
        print("\n" + "="*70)
        print("FINAL STATUS: FAILED")
        print("="*70)
        exit(1)
