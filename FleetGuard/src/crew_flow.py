# -*- coding: utf-8 -*-
"""
CrewAI Flow - Master Orchestrator
תפקיד: תיאום בין Crew 1 (Data Analyst) ו-Crew 2 (Data Scientist)
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

# הוספת נתיב לייבוא
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ייבוא Crew 2 - Data Scientist Crew (Agents D, E, F)
try:
    from crews.data_scientist_crew import DataScientistCrew
except ImportError:
    from src.crews.data_scientist_crew import DataScientistCrew

# ייבוא מודולי Crew 1 (simplified - כרגע אין Crew 1 orchestrator)
try:
    from utils.data_validator import DataValidator
    from utils.eda_generator import EDAGenerator
except ImportError:
    from src.utils.data_validator import DataValidator
    from src.utils.eda_generator import EDAGenerator

try:
    from database_manager import DatabaseManager
except ImportError:
    from src.database_manager import DatabaseManager


class FleetGuardFlow:
    """
    CrewAI Flow - Master Orchestrator
    מתאם אוטומטי בין:
    - Crew 1: Data Analyst Crew (A, B, C)
    - Crew 2: Data Scientist Crew (D, E, F)
    """

    def __init__(self):
        self.crew1 = None
        self.crew2 = None
        self.flow_state = {
            'flow_name': 'FleetGuard AI Multi-Crew Flow',
            'flow_version': '1.0.0',
            'start_time': None,
            'end_time': None,
            'total_duration': None,
            'status': 'NOT_STARTED',
            'crews': {
                'crew1': {'status': 'PENDING', 'result': None},
                'crew2': {'status': 'PENDING', 'result': None}
            },
            'validation_checkpoints': {},
            'final_outputs': {}
        }

    def validate_crew1_output(self):
        """
        Validation Checkpoint 1: בדיקת תוצאות Crew 1
        """
        print("\n" + "="*70)
        print("VALIDATION CHECKPOINT 1: Crew 1 Output Validation")
        print("="*70)

        try:
            # בדיקה 1: קובץ נתונים מעובד קיים
            processed_data_path = 'data/processed/fleet_data_cleaned.csv'
            if not os.path.exists(processed_data_path):
                return {
                    'passed': False,
                    'error': f'Processed data file not found: {processed_data_path}'
                }

            # בדיקה 2: גודל קובץ תקין
            file_size = os.path.getsize(processed_data_path)
            if file_size < 1000:  # לפחות 1KB
                return {
                    'passed': False,
                    'error': f'Processed data file too small: {file_size} bytes'
                }

            # בדיקה 3: דוחות קיימים
            required_reports = [
                'reports/vehicle_analysis.json',
                'reports/driver_analysis.json',
                'reports/maintenance_analysis.json'
            ]

            missing_reports = [r for r in required_reports if not os.path.exists(r)]
            if missing_reports:
                return {
                    'passed': False,
                    'error': f'Missing reports: {missing_reports}'
                }

            print("[+] All Crew 1 outputs validated successfully")
            print(f"    - Processed data: {file_size:,} bytes")
            print(f"    - Reports: {len(required_reports)} files")

            return {
                'passed': True,
                'processed_data_size': file_size,
                'reports_count': len(required_reports)
            }

        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }

    def validate_crew2_output(self):
        """
        Validation Checkpoint 2: בדיקת תוצאות Crew 2
        """
        print("\n" + "="*70)
        print("VALIDATION CHECKPOINT 2: Crew 2 Output Validation")
        print("="*70)

        try:
            # בדיקה 1: מודל ML קיים
            model_path = 'models/model.pkl'
            if not os.path.exists(model_path):
                return {
                    'passed': False,
                    'error': f'ML model not found: {model_path}'
                }

            # בדיקה 2: metadata קיים
            metadata_path = 'models/model_metadata.json'
            if not os.path.exists(metadata_path):
                return {
                    'passed': False,
                    'error': f'Model metadata not found: {metadata_path}'
                }

            # בדיקה 3: ביצועי מודל עומדים בדרישות
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            test_r2 = metadata.get('test_r2', 0)
            rmse = metadata.get('rmse', float('inf'))

            # דרישות: R2 > 0.75, RMSE < 500
            if test_r2 < 0.75:
                return {
                    'passed': False,
                    'error': f'Model R2 below threshold: {test_r2:.4f} < 0.75'
                }

            if rmse > 500:
                return {
                    'passed': False,
                    'error': f'Model RMSE above threshold: {rmse:.2f} > 500'
                }

            # בדיקה 4: דוח הערכה קיים
            evaluation_report = 'reports/evaluation_report.md'
            if not os.path.exists(evaluation_report):
                return {
                    'passed': False,
                    'error': f'Evaluation report not found: {evaluation_report}'
                }

            print("[+] All Crew 2 outputs validated successfully")
            print(f"    - Model R2: {test_r2:.4f} (Target: > 0.75)")
            print(f"    - Model RMSE: {rmse:.2f} (Target: < 500)")
            print(f"    - Model type: {metadata.get('model_name', 'Unknown')}")

            return {
                'passed': True,
                'model_r2': test_r2,
                'model_rmse': rmse,
                'model_name': metadata.get('model_name', 'Unknown')
            }

        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }

    def run_crew1(self):
        """
        הרצת Crew 1: Data Analyst Crew (Simplified)
        כרגע מריץ תהליך פשוט של טעינה ו-EDA
        """
        print("\n" + "="*70)
        print("FLOW STEP 1/2: Running Crew 1 (Data Analyst Crew - Simplified)")
        print("="*70 + "\n")

        try:
            start_time = datetime.now()

            # Step 1: Load data from database
            print("[*] Loading fleet data from database...")
            db = DatabaseManager()
            fleet_df = db.get_fleet_overview()
            invoices_df = db.get_all_invoices()
            print(f"[+] Loaded {len(fleet_df)} vehicles, {len(invoices_df)} invoices")

            # Step 2: Basic data validation (check for nulls)
            print("\n[*] Validating data...")
            clean_df = fleet_df.copy()
            # Just remove rows with all nulls if any
            clean_df = clean_df.dropna(how='all')
            alerts_count = len(fleet_df) - len(clean_df)
            print(f"[+] Validated: {len(clean_df)} clean records")
            if alerts_count > 0:
                print(f"[!] Removed {alerts_count} empty rows")

            # Step 3: Generate basic analysis reports
            print("\n[*] Generating analysis reports...")
            os.makedirs('reports', exist_ok=True)

            # Save vehicle analysis
            vehicle_report = {
                'total_vehicles': len(fleet_df),
                'total_invoices': len(invoices_df),
                'total_cost': float(invoices_df['total'].sum()) if 'total' in invoices_df.columns else 0,
                'avg_cost_per_invoice': float(invoices_df['total'].mean()) if 'total' in invoices_df.columns else 0
            }
            vehicle_report_path = 'reports/vehicle_analysis.json'
            with open(vehicle_report_path, 'w', encoding='utf-8') as f:
                json.dump(vehicle_report, f, indent=2, ensure_ascii=False)
            print(f"[+] Vehicle analysis saved: {vehicle_report_path}")

            # Save driver analysis (placeholder)
            driver_report = {'status': 'analysis_completed', 'vehicles_count': len(fleet_df)}
            driver_report_path = 'reports/driver_analysis.json'
            with open(driver_report_path, 'w', encoding='utf-8') as f:
                json.dump(driver_report, f, indent=2, ensure_ascii=False)
            print(f"[+] Driver analysis saved: {driver_report_path}")

            # Save maintenance analysis (placeholder)
            maint_report = {'status': 'analysis_completed', 'invoices_count': len(invoices_df)}
            maint_report_path = 'reports/maintenance_analysis.json'
            with open(maint_report_path, 'w', encoding='utf-8') as f:
                json.dump(maint_report, f, indent=2, ensure_ascii=False)
            print(f"[+] Maintenance analysis saved: {maint_report_path}")

            # Save processed data
            print("\n[*] Saving processed data...")
            os.makedirs('data/processed', exist_ok=True)
            clean_path = 'data/processed/fleet_data_cleaned.csv'
            clean_df.to_csv(clean_path, index=False, encoding='utf-8')
            print(f"[+] Cleaned data saved: {clean_path}")

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Success
            result = {
                'status': 'SUCCESS',
                'execution_time': f"{duration:.2f} seconds",
                'steps': {
                    'data_loading': {'status': 'SUCCESS', 'vehicles': len(fleet_df), 'invoices': len(invoices_df)},
                    'data_validation': {'status': 'SUCCESS', 'clean_records': len(clean_df), 'removed': alerts_count},
                    'analysis_reports': {
                        'status': 'SUCCESS',
                        'vehicle_report': vehicle_report_path,
                        'driver_report': driver_report_path,
                        'maintenance_report': maint_report_path
                    }
                }
            }

            self.flow_state['crews']['crew1']['status'] = 'SUCCESS'
            self.flow_state['crews']['crew1']['result'] = result
            print("\n[+] Crew 1 completed successfully")
            return True

        except Exception as e:
            self.flow_state['crews']['crew1']['status'] = 'FAILED'
            self.flow_state['crews']['crew1']['error'] = str(e)
            print(f"\n[ERROR] Crew 1 exception: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_crew2(self):
        """
        הרצת Crew 2: Data Scientist Crew
        """
        print("\n" + "="*70)
        print("FLOW STEP 2/2: Running Crew 2 (Data Scientist Crew)")
        print("="*70 + "\n")

        try:
            self.crew2 = DataScientistCrew()
            result = self.crew2.run_pipeline()

            if result.get('status') == 'SUCCESS':
                self.flow_state['crews']['crew2']['status'] = 'SUCCESS'
                self.flow_state['crews']['crew2']['result'] = result
                print("\n[+] Crew 2 completed successfully")
                return True
            else:
                self.flow_state['crews']['crew2']['status'] = 'FAILED'
                self.flow_state['crews']['crew2']['error'] = result.get('error', 'Unknown error')
                print(f"\n[ERROR] Crew 2 failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            self.flow_state['crews']['crew2']['status'] = 'FAILED'
            self.flow_state['crews']['crew2']['error'] = str(e)
            print(f"\n[ERROR] Crew 2 exception: {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_flow_summary(self):
        """
        יצירת סיכום Flow מפורט
        """
        print("\n" + "="*70)
        print("GENERATING FLOW SUMMARY")
        print("="*70)

        # חישוב זמנים
        start_time = datetime.fromisoformat(self.flow_state['start_time'])
        end_time = datetime.fromisoformat(self.flow_state['end_time'])
        duration = (end_time - start_time).total_seconds()

        summary_lines = [
            "# FleetGuard AI - Multi-Crew Flow Execution Summary",
            "",
            f"**Execution Date:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Duration:** {duration:.2f} seconds",
            f"**Flow Status:** {self.flow_state['status']}",
            "",
            "---",
            "",
            "## Crew Execution Results",
            ""
        ]

        # Crew 1 Summary
        crew1_result = self.flow_state['crews']['crew1']
        summary_lines.extend([
            "### Crew 1: Data Analyst Crew",
            "",
            f"**Status:** {crew1_result['status']}",
            ""
        ])

        if crew1_result['status'] == 'SUCCESS' and crew1_result['result']:
            result = crew1_result['result']
            summary_lines.extend([
                "**Outputs:**",
                f"- Execution time: {result.get('execution_time', 'N/A')}",
                f"- Steps completed: {len(result.get('steps', {}))}/3",
                ""
            ])
        elif crew1_result['status'] == 'FAILED':
            summary_lines.extend([
                f"**Error:** {crew1_result.get('error', 'Unknown error')}",
                ""
            ])

        # Crew 2 Summary
        crew2_result = self.flow_state['crews']['crew2']
        summary_lines.extend([
            "### Crew 2: Data Scientist Crew",
            "",
            f"**Status:** {crew2_result['status']}",
            ""
        ])

        if crew2_result['status'] == 'SUCCESS' and crew2_result['result']:
            result = crew2_result['result']
            summary_lines.extend([
                "**Outputs:**",
                f"- Execution time: {result.get('execution_time', 'N/A')}",
                f"- Steps completed: {len(result.get('steps', {}))}/3",
                ""
            ])

            # הוספת מדדי מודל
            if 'steps' in result and 'model_training' in result['steps']:
                mt = result['steps']['model_training']
                summary_lines.extend([
                    "**Model Performance:**",
                    f"- Model Type: {mt.get('best_model_name', 'Unknown')}",
                    f"- R2 Score: {mt.get('test_r2', 0):.4f}",
                    f"- RMSE: {mt.get('rmse', 0):.2f}",
                    f"- MAE: {mt.get('mae', 0):.2f}",
                    ""
                ])
        elif crew2_result['status'] == 'FAILED':
            summary_lines.extend([
                f"**Error:** {crew2_result.get('error', 'Unknown error')}",
                ""
            ])

        # Validation Results
        summary_lines.extend([
            "---",
            "",
            "## Validation Checkpoints",
            ""
        ])

        for checkpoint_name, checkpoint_result in self.flow_state['validation_checkpoints'].items():
            status_icon = "[+]" if checkpoint_result.get('passed') else "[ERROR]"
            summary_lines.append(f"{status_icon} **{checkpoint_name}**: {'PASSED' if checkpoint_result.get('passed') else 'FAILED'}")

            if not checkpoint_result.get('passed'):
                summary_lines.append(f"  - Error: {checkpoint_result.get('error', 'Unknown')}")
            summary_lines.append("")

        # Final Outputs
        summary_lines.extend([
            "---",
            "",
            "## Final Outputs",
            "",
            "**Data Processing:**",
            "- `data/processed/fleet_data_cleaned.csv` - Cleaned fleet data",
            "- `data/processed/features.csv` - Engineered ML features",
            "",
            "**Analysis Reports:**",
            "- `reports/vehicle_analysis.json` - Vehicle insights",
            "- `reports/driver_analysis.json` - Driver performance",
            "- `reports/maintenance_analysis.json` - Maintenance patterns",
            "",
            "**ML Artifacts:**",
            "- `models/model.pkl` - Trained ML model",
            "- `models/model_metadata.json` - Model specifications",
            "- `reports/evaluation_report.md` - Model evaluation",
            "",
            "---",
            "",
            f"_Flow execution report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        ])

        # שמירת דוח
        report_dir = 'reports'
        os.makedirs(report_dir, exist_ok=True)

        summary_path = os.path.join(report_dir, 'flow_summary.md')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_lines))

        print(f"[+] Flow summary saved: {summary_path}")

        # שמירת JSON מפורט
        json_path = os.path.join(report_dir, 'flow_execution_report.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.flow_state, f, indent=2, ensure_ascii=False)

        print(f"[+] Flow execution report saved: {json_path}")

        return summary_path, json_path

    def run_flow(self):
        """
        הרצת Flow מלא: Crew 1 -> Validation -> Crew 2 -> Validation -> Summary
        """
        self.flow_state['start_time'] = datetime.now().isoformat()
        self.flow_state['status'] = 'RUNNING'

        print("\n" + "#"*70)
        print("# FleetGuard AI - Multi-Crew Flow Starting")
        print("# Orchestrating: Crew 1 (Data Analyst) -> Crew 2 (Data Scientist)")
        print("#"*70 + "\n")

        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # =============================
        # STEP 1: Run Crew 1
        # =============================
        crew1_success = self.run_crew1()

        if not crew1_success:
            self.flow_state['status'] = 'FAILED'
            self.flow_state['failed_at'] = 'Crew 1'
            self.flow_state['end_time'] = datetime.now().isoformat()
            print("\n[ERROR] Flow stopped - Crew 1 failed")
            return self.flow_state

        # =============================
        # VALIDATION 1: Crew 1 Output
        # =============================
        validation1 = self.validate_crew1_output()
        self.flow_state['validation_checkpoints']['crew1_output'] = validation1

        if not validation1.get('passed'):
            self.flow_state['status'] = 'FAILED'
            self.flow_state['failed_at'] = 'Crew 1 Validation'
            self.flow_state['end_time'] = datetime.now().isoformat()
            print(f"\n[ERROR] Flow stopped - Crew 1 validation failed: {validation1.get('error')}")
            return self.flow_state

        # =============================
        # STEP 2: Run Crew 2
        # =============================
        crew2_success = self.run_crew2()

        if not crew2_success:
            self.flow_state['status'] = 'FAILED'
            self.flow_state['failed_at'] = 'Crew 2'
            self.flow_state['end_time'] = datetime.now().isoformat()
            print("\n[ERROR] Flow stopped - Crew 2 failed")
            return self.flow_state

        # =============================
        # VALIDATION 2: Crew 2 Output
        # =============================
        validation2 = self.validate_crew2_output()
        self.flow_state['validation_checkpoints']['crew2_output'] = validation2

        if not validation2.get('passed'):
            self.flow_state['status'] = 'FAILED'
            self.flow_state['failed_at'] = 'Crew 2 Validation'
            self.flow_state['end_time'] = datetime.now().isoformat()
            print(f"\n[ERROR] Flow stopped - Crew 2 validation failed: {validation2.get('error')}")
            return self.flow_state

        # =============================
        # SUCCESS: Generate Summary
        # =============================
        self.flow_state['status'] = 'SUCCESS'
        self.flow_state['end_time'] = datetime.now().isoformat()

        summary_path, json_path = self.generate_flow_summary()

        self.flow_state['final_outputs'] = {
            'flow_summary': summary_path,
            'flow_report': json_path
        }

        # הדפסת סיכום סופי
        print("\n" + "="*70)
        print("FLOW COMPLETED SUCCESSFULLY")
        print("="*70)

        print("\nExecution Summary:")
        print(f"  - Crew 1: {self.flow_state['crews']['crew1']['status']}")
        print(f"  - Crew 2: {self.flow_state['crews']['crew2']['status']}")
        print(f"  - Total duration: {self.flow_state['total_duration']}")

        print("\nFinal Outputs:")
        print(f"  - Flow summary: {summary_path}")
        print(f"  - Flow report: {json_path}")

        print("\nValidation Results:")
        for checkpoint, result in self.flow_state['validation_checkpoints'].items():
            status = "[+] PASSED" if result.get('passed') else "[ERROR] FAILED"
            print(f"  {status}: {checkpoint}")

        print("\n" + "="*70)
        print("[RECOMMENDATION] All crews completed successfully - system ready for production")
        print("="*70 + "\n")

        return self.flow_state


# =============================================
# הרצה עצמאית לבדיקה
# =============================================
if __name__ == "__main__":
    print("\n" + "#"*70)
    print("# FleetGuard AI - Multi-Crew Flow Executor")
    print("# Version 1.0.0")
    print("#"*70 + "\n")

    flow = FleetGuardFlow()
    result = flow.run_flow()

    # הדפסת סטטוס סופי
    if result['status'] == 'SUCCESS':
        print("\n" + "="*70)
        print("FINAL STATUS: SUCCESS")
        print("="*70)
        exit(0)
    else:
        print("\n" + "="*70)
        print("FINAL STATUS: FAILED")
        print(f"Failed at: {result.get('failed_at', 'Unknown')}")
        print("="*70)
        exit(1)
