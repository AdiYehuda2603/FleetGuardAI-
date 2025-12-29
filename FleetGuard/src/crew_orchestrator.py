"""
Crew Orchestrator - FIXED VERSION
Properly uses CrewAI framework with crew.kickoff() while maintaining functional utility logic
"""

# Windows patch - must be imported before crewai
try:
    from src.crewai_windows_patch import *
except ImportError:
    pass  # If patch doesn't exist, continue anyway

from crewai import Crew, Process, Task
import pandas as pd
from datetime import datetime
import json
import os

from src.crewai_agents import (
    data_validator_agent,
    eda_explorer_agent,
    report_generator_agent,
    feature_engineer_agent,
    cost_predictor_agent,
    maintenance_predictor_agent
)

from src.utils.data_validator import DataValidator
from src.utils.eda_generator import EDAGenerator
from src.utils.ml_trainer import FleetMLTrainer
from src.database_manager import DatabaseManager
from src.utils.path_resolver import path_resolver


class CrewOrchestrator:
    """
    Orchestrates the multi-agent system using TRUE CrewAI framework
    Uses crew.kickoff() for agent coordination
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.results = {
            'analyst_crew': None,
            'scientist_crew': None,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Shared state for data passing between agents
        self.shared_state = {
            'uploaded_df': None,
            'clean_df': None,
            'alerts': [],
            'insights': {},
            'report_path': None,
            'features_df': None,
            'cost_metrics': {},
            'service_metrics': {},
            'model_paths': {}
        }

    def run_analyst_crew(self, uploaded_df):
        """
        Execute Data Analyst Crew using TRUE CrewAI orchestration

        Args:
            uploaded_df: pandas DataFrame of uploaded invoice data

        Returns:
            dict: {clean_df, alerts, report_path, insights}
        """
        print("\n" + "=" * 80)
        print("🚀 CREW 1: DATA ANALYST CREW - STARTING (TRUE CrewAI)")
        print("=" * 80)

        # Store data in shared state
        self.shared_state['uploaded_df'] = uploaded_df

        # Save uploaded data to temp file for agents to access
        temp_path = self._save_temp_data(uploaded_df, 'uploaded_data.csv')

        # Create tasks for Crew 1
        validation_task = Task(
            description=f"""Validate the uploaded fleet data from {temp_path}:

            **IMPORTANT:** You have FULL ACCESS to the database via database_access_tool.
            Use it to compare uploaded data with existing records for consistency.

            1. Use database_access_tool("all_invoices") to get ALL existing invoices
            2. Use database_access_tool("all_vehicles") to get ALL vehicles
            3. Load data from the CSV file
            4. Check critical fields: vehicle_id, date, odometer_km, workshop, total
            5. Compare with existing database records to ensure consistency
            6. DROP any row missing critical data
            7. Log specific alert for EACH dropped row: "Vehicle [ID] data ignored due to missing fields: [list]"
            8. Save cleaned data to data/processed/clean_data.csv
            9. Save validation log to data/reports/validation_log.txt

            Return summary: "Validation complete: X rows clean, Y rows dropped"
            """,
            agent=data_validator_agent,
            expected_output='Summary of validation results with counts'
        )

        eda_task = Task(
            description=f"""Perform comprehensive EDA on cleaned data from data/processed/clean_data.csv:

            **IMPORTANT:** You have FULL ACCESS to the ENTIRE database via database_access_tool.
            Use it to access ALL historical data for comprehensive analysis:
            - database_access_tool("all_invoices") - ALL invoices from database
            - database_access_tool("full_view") - Invoices with detailed line items
            - database_access_tool("vehicle_stats") - All vehicles with statistics
            - database_access_tool("all_vehicles") - All vehicle details

            This gives you COMPLETE CONTEXT, not just the uploaded data.

            1. Use database_access_tool to get ALL invoices and vehicles from database
            2. Analyze cost distributions (mean, median, std, quartiles) - use ALL data
            3. Detect anomalies using IQR method - compare with ALL historical invoices
            4. Compare workshop pricing (identify >15% deviations) - use ALL workshops
            5. Analyze temporal trends (monthly patterns) - use ALL historical data
            6. Identify high-cost vehicles - use vehicle_stats for complete information
            7. Save insights to data/processed/eda_insights.json

            Return summary: "EDA complete: X anomalies found, Y workshops analyzed"
            """,
            agent=eda_explorer_agent,
            expected_output='Summary of EDA findings',
            context=[validation_task]  # Depends on validation
        )

        report_task = Task(
            description=f"""Generate professional HTML EDA report:

            1. Load insights from data/processed/eda_insights.json
            2. Create HTML report with Hebrew/RTL support
            3. Include sections: distributions, anomalies, workshops, temporal, vehicles
            4. Use professional styling with gradients
            5. Save to data/reports/eda_report_[timestamp].html

            Return: "Report generated: [filepath]"
            """,
            agent=report_generator_agent,
            expected_output='Path to generated HTML report',
            context=[eda_task]  # Depends on EDA
        )

        # Create Crew 1
        analyst_crew = Crew(
            agents=[data_validator_agent, eda_explorer_agent, report_generator_agent],
            tasks=[validation_task, eda_task, report_task],
            process=Process.sequential,
            verbose=True
        )

        # Execute with CrewAI - THIS IS THE KEY!
        print("\n🤖 Executing CrewAI Analyst Crew with kickoff()...")
        crew_output = analyst_crew.kickoff()

        print("\n" + "=" * 80)
        print("📄 CREW 1 OUTPUT:")
        print("=" * 80)
        print(crew_output)
        print("=" * 80)

        # Load results from files (agents saved them)
        clean_df = self._load_processed_data('clean_data.csv')
        insights = self._load_json('eda_insights.json')
        alerts = self._load_validation_log()
        report_path = self._find_latest_report()

        result = {
            'clean_df': clean_df,
            'alerts': alerts,
            'dropped_count': len(uploaded_df) - len(clean_df),
            'insights': insights,
            'report_path': report_path,
            'crew_output': str(crew_output)
        }

        self.results['analyst_crew'] = result

        print("\n✅ CREW 1: DATA ANALYST CREW - COMPLETED")
        return result

    def run_scientist_crew(self, clean_df=None):
        """
        Execute Data Scientist Crew using TRUE CrewAI orchestration

        Args:
            clean_df: Validated DataFrame (optional)

        Returns:
            dict: {models, metrics, model_card_path}
        """
        print("\n" + "=" * 80)
        print("🤖 CREW 2: DATA SCIENTIST CREW - STARTING (TRUE CrewAI)")
        print("=" * 80)

        # Save clean data if provided
        if clean_df is not None:
            self._save_temp_data(clean_df, 'clean_data.csv')

        # Create tasks for Crew 2
        feature_task = Task(
            description="""Engineer features for ML models:

            **IMPORTANT:** You have FULL ACCESS to the database via database_access_tool.
            Use it to get COMPLETE data for feature engineering:
            - database_access_tool("vehicle_stats") - All vehicles with current_km, last_service_date, total_cost
            - database_access_tool("all_invoices") - ALL historical invoices for accurate cost calculations
            - database_access_tool("full_view") - Detailed invoice line items

            1. Use database_access_tool("vehicle_stats") to get ALL vehicles with complete statistics
            2. Use database_access_tool("all_invoices") to get ALL invoices for cost calculations
            3. Calculate: age, days_in_fleet, km_per_day, cost_vs_fleet_avg, days_since_last_service
            4. Encode categorical variables (make_model) - use ALL vehicles
            5. Create targets: annual_cost, next_service_cost - use ALL historical data
            6. Save to data/processed/features.csv

            Return summary: "Features engineered: X features, Y samples"
            """,
            agent=feature_engineer_agent,
            expected_output='Summary of feature engineering'
        )

        cost_model_task = Task(
            description="""Train Annual Cost Prediction Model (MODEL 1):

            1. Load features from data/processed/features.csv
            2. Train RandomForestRegressor for annual_cost target
            3. Evaluate: calculate R², RMSE, MAE, cross-validation scores
            4. Save model to data/models/annual_cost_predictor.pkl
            5. Save metrics to data/models/cost_metrics.json

            Return summary: "Model 1 trained: R²=[score], RMSE=[value]"
            """,
            agent=cost_predictor_agent,
            expected_output='Summary of Model 1 performance',
            context=[feature_task]
        )

        service_model_task = Task(
            description="""Train Next Service Cost Prediction Model (MODEL 2):

            1. Load features from data/processed/features.csv
            2. Train RandomForestRegressor for next_service_cost target
            3. Evaluate: calculate R², RMSE, MAE, cross-validation scores
            4. Save model to data/models/service_cost_predictor.pkl
            5. Save metrics to data/models/service_metrics.json

            Return summary: "Model 2 trained: R²=[score], RMSE=[value]"
            """,
            agent=maintenance_predictor_agent,
            expected_output='Summary of Model 2 performance',
            context=[feature_task]
        )

        model_card_task = Task(
            description="""Generate comprehensive model_card.md:

            1. Load metrics from cost_metrics.json and service_metrics.json
            2. Document both models: architecture, features, performance
            3. Include usage instructions and limitations
            4. Save to data/models/model_card.md

            Return: "Model card generated: [filepath]"
            """,
            agent=maintenance_predictor_agent,
            expected_output='Path to model card',
            context=[cost_model_task, service_model_task]
        )

        # Create Crew 2
        scientist_crew = Crew(
            agents=[feature_engineer_agent, cost_predictor_agent, maintenance_predictor_agent],
            tasks=[feature_task, cost_model_task, service_model_task, model_card_task],
            process=Process.sequential,
            verbose=True
        )

        # Execute with CrewAI - THIS IS THE KEY!
        print("\n🤖 Executing CrewAI Scientist Crew with kickoff()...")
        crew_output = scientist_crew.kickoff()

        print("\n" + "=" * 80)
        print("📄 CREW 2 OUTPUT:")
        print("=" * 80)
        print(crew_output)
        print("=" * 80)

        # Load results from files
        cost_metrics = self._load_json('cost_metrics.json')
        service_metrics = self._load_json('service_metrics.json')
        model_card_path = os.path.join(self.db.db_path.replace('fleet.db', ''), 'models', 'model_card.md')

        result = {
            'cost_metrics': cost_metrics if cost_metrics else {},
            'service_metrics': service_metrics if service_metrics else {},
            'model_paths': {
                'cost_model': 'data/models/annual_cost_predictor.pkl',
                'service_model': 'data/models/service_cost_predictor.pkl'
            },
            'model_card_path': model_card_path,
            'crew_output': str(crew_output)
        }

        self.results['scientist_crew'] = result

        print("\n✅ CREW 2: DATA SCIENTIST CREW - COMPLETED")
        return result

    def run_full_pipeline(self, uploaded_df):
        """
        Execute both crews sequentially using TRUE CrewAI orchestration

        Args:
            uploaded_df: pandas DataFrame of uploaded data

        Returns:
            dict: Combined results from both crews
        """
        print("\n" + "🚛" * 40)
        print("FLEETGUARD MULTI-AGENT SYSTEM - FULL PIPELINE (TRUE CrewAI)")
        print("🚛" * 40)

        # Crew 1: Data Analysis (with CrewAI)
        analyst_result = self.run_analyst_crew(uploaded_df)

        # Crew 2: Machine Learning (with CrewAI)
        scientist_result = self.run_scientist_crew(analyst_result['clean_df'])

        # Combined results
        combined = {
            'timestamp': self.results['timestamp'],
            'analyst': analyst_result,
            'scientist': scientist_result,
            'summary': self._generate_summary(analyst_result, scientist_result)
        }

        self.results['combined'] = combined

        print("\n" + "=" * 80)
        print("🎉 FULL PIPELINE COMPLETED SUCCESSFULLY (TRUE CrewAI)")
        print("=" * 80)
        print("\nSUMMARY:")
        print(combined['summary'])

        return combined

    # Helper methods for file-based data passing

    def _save_temp_data(self, df, filename):
        """Save DataFrame to temp file for agents to access"""
        processed_dir = path_resolver.get_path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)

        filepath = processed_dir / filename
        df.to_csv(filepath, index=False)
        return str(filepath)

    def _load_processed_data(self, filename):
        """Load DataFrame from processed directory"""
        filepath = path_resolver.get_path(f"data/processed/{filename}")

        if filepath.exists():
            return pd.read_csv(filepath)
        else:
            return pd.DataFrame()

    def _load_json(self, filename):
        """Load JSON from processed directory"""
        # Try processed dir first
        filepath = path_resolver.get_path(f"data/processed/{filename}")
        if not filepath.exists():
            # Try models dir
            filepath = path_resolver.get_path(f"data/models/{filename}")

        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        else:
            return {}

    def _load_validation_log(self):
        """Load validation alerts from log file"""
        reports_dir = path_resolver.get_path("data/reports")
        log_files = []

        if reports_dir.exists():
            log_files = [f for f in os.listdir(reports_dir) if f.startswith('validation_log')]

        if log_files:
            latest_log = sorted(log_files)[-1]
            filepath = reports_dir / latest_log

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract alerts (lines starting with ⚠️ or containing "Vehicle")
                alerts = [line.strip() for line in content.split('\n') if '⚠️' in line or 'Vehicle' in line]
                return alerts

        return []

    def _find_latest_report(self):
        """Find most recent EDA report"""
        reports_dir = path_resolver.get_path("data/reports")

        if reports_dir.exists():
            html_files = [f for f in os.listdir(reports_dir) if f.startswith('eda_report') and f.endswith('.html')]

            if html_files:
                latest = sorted(html_files)[-1]
                return str(reports_dir / latest)

        return None

    def _generate_summary(self, analyst_result, scientist_result):
        """Generate executive summary"""
        summary = f"""
FLEETGUARD MULTI-AGENT SYSTEM - EXECUTION SUMMARY (TRUE CrewAI)
Generated: {self.results['timestamp']}

=== CREW 1: DATA ANALYST (CrewAI Orchestrated) ===
✓ Validation: {analyst_result.get('dropped_count', 0)} rows dropped, {len(analyst_result.get('clean_df', []))} rows validated
✓ Analysis: {analyst_result.get('insights', {}).get('distributions', {}).get('total_invoices', 0)} invoices analyzed
✓ Anomalies: {analyst_result.get('insights', {}).get('anomalies', {}).get('count', 0)} detected
✓ Report: {analyst_result.get('report_path', 'N/A')}

=== CREW 2: DATA SCIENTIST (CrewAI Orchestrated) ===
✓ Model 1 (Annual Cost): R²={scientist_result.get('cost_metrics', {}).get('test_r2', 0):.3f}
✓ Model 2 (Service Cost): R²={scientist_result.get('service_metrics', {}).get('test_r2', 0):.3f}
✓ Models saved: {len(scientist_result.get('model_paths', {}))} files
✓ Documentation: {scientist_result.get('model_card_path', 'N/A')}

=== ORCHESTRATION ===
✓ Both crews executed via crew.kickoff() - TRUE CrewAI framework used
"""
        return summary


# Fallback: Direct execution without CrewAI (for testing)
class DirectOrchestrator:
    """
    Fallback orchestrator that directly calls utilities
    Use this if CrewAI framework has issues
    """

    def __init__(self):
        self.db = DatabaseManager()

    def run_full_pipeline(self, uploaded_df):
        """Execute pipeline directly without CrewAI"""
        print("\n⚠️ Using Direct Orchestrator (Fallback - No CrewAI)")

        # Step 1: Validation
        validator = DataValidator()
        clean_df, alerts = validator.validate_dataframe(uploaded_df)
        validator.save_validation_log()

        # Step 2: EDA
        eda_gen = EDAGenerator()
        report_path, insights = eda_gen.generate_report(df=clean_df)

        # Step 3: ML Training
        trainer = FleetMLTrainer()
        df_features = trainer.prepare_features()
        result_cost = trainer.train_annual_cost_model(df_features)
        result_service = trainer.train_service_cost_model(df_features)
        trainer.save_models()
        model_card_path = trainer.generate_model_card()

        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'analyst': {
                'clean_df': clean_df,
                'alerts': alerts,
                'dropped_count': validator.dropped_count,
                'insights': insights,
                'report_path': report_path
            },
            'scientist': {
                'cost_metrics': result_cost['metrics'],
                'service_metrics': result_service['metrics'],
                'model_card_path': model_card_path
            }
        }


# === TESTING ===
if __name__ == "__main__":
    # Test with direct orchestrator (fallback)
    print("Testing DIRECT orchestrator (no CrewAI)...")
    direct_orch = DirectOrchestrator()

    db = DatabaseManager()
    df_test = db.get_all_invoices()

    results = direct_orch.run_full_pipeline(df_test)

    print("\n" + "=" * 80)
    print("DIRECT ORCHESTRATOR TEST COMPLETE")
    print("=" * 80)
