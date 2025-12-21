"""
CrewAI Tasks Definition
Defines all tasks for the FleetGuard Multi-Agent System
"""

# Windows patch - must be imported before crewai
try:
    from src.crewai_windows_patch import *
except ImportError:
    pass  # If patch doesn't exist, continue anyway

from crewai import Task
from src.crewai_agents import (
    data_validator_agent,
    eda_explorer_agent,
    report_generator_agent,
    feature_engineer_agent,
    cost_predictor_agent,
    maintenance_predictor_agent
)


# ===== CREW 1 TASKS: DATA ANALYST CREW =====

def create_validation_task(uploaded_data):
    """
    Task 1: Validate uploaded data

    Args:
        uploaded_data: DataFrame or dict of uploaded invoice data

    Returns:
        CrewAI Task object
    """
    return Task(
        description=f"""Validate the uploaded fleet data against dataset_contract.json:

        **Critical Fields Required:**
        - vehicle_id
        - date
        - odometer_km
        - workshop
        - total

        **Instructions:**
        1. Use database_access_tool to access ALL existing invoices and vehicles from the database
        2. Compare uploaded data with existing records to ensure consistency
        3. Check each row for missing critical fields
        4. DROP any row missing critical data (zero tolerance policy)
        5. Log specific alert for each dropped row:
           "⚠️ Vehicle [ID] data ignored due to missing fields: [field1, field2, ...]"
        6. Return cleaned DataFrame and complete list of alerts
        7. Provide summary: "X/Y rows dropped"

        **IMPORTANT:** You have FULL ACCESS to the database via database_access_tool.
        Use it to access all_invoices, all_vehicles, and full_view to get complete context.

        **Input Data:**
        {str(uploaded_data)[:500]}...

        **Expected Output:**
        - clean_df: Validated DataFrame (JSON format)
        - alerts: List of specific violation messages
        - dropped_count: Number of rows removed
        """,
        agent=data_validator_agent,
        expected_output='Dictionary with clean_df (JSON), alerts (list), and dropped_count (int)'
    )


def create_eda_task(clean_data):
    """
    Task 2: Perform EDA analysis

    Args:
        clean_data: Validated DataFrame from Task 1

    Returns:
        CrewAI Task object
    """
    return Task(
        description=f"""Perform comprehensive exploratory data analysis on validated fleet data:

        **IMPORTANT:** You have FULL ACCESS to the ENTIRE database via database_access_tool.
        Use it to access ALL historical data, not just the uploaded/cleaned data:
        - Use "all_invoices" to get ALL invoices from the database
        - Use "full_view" to get invoices with detailed line items
        - Use "vehicle_stats" to get complete vehicle information with current odometer
        - Use "all_vehicles" to get all vehicle details
        
        This gives you COMPLETE CONTEXT for comprehensive analysis.

        **Required Analyses:**
        1. **Distribution Analysis:**
           - Cost statistics (mean, median, std, min, max, quartiles) - use ALL invoices
           - Odometer statistics - use current_km from vehicle_stats
           - Invoice count by workshop - use ALL invoices

        2. **Anomaly Detection:**
           - Identify outliers using IQR method on ALL invoices
           - Flag invoices > 1.5 * IQR above Q3 as "high cost anomalies"
           - Return top 5 most expensive anomalies with details

        3. **Workshop Comparison:**
           - Average cost per workshop - compare ALL workshops from database
           - Total services per workshop - use ALL invoices
           - Identify workshops with >15% price deviation from fleet average
           - Rank workshops by cost (cheapest to most expensive)

        4. **Temporal Analysis:**
           - Monthly cost trends - analyze ALL historical invoices
           - Busiest month (most services) - use ALL invoices
           - Most expensive month (highest total cost) - use ALL invoices

        5. **Vehicle Insights:**
           - Top 5 highest-cost vehicles - use vehicle_stats for complete data
           - Average fleet age and mileage - use vehicle_stats

        **Input Data:**
        {str(clean_data)[:500]}...

        **Expected Output:**
        Comprehensive insights dictionary with all analysis results
        """,
        agent=eda_explorer_agent,
        expected_output='Dictionary containing distributions, anomalies, workshops, temporal, and vehicles insights'
    )


def create_report_task(eda_insights):
    """
    Task 3: Generate HTML EDA report

    Args:
        eda_insights: Insights dictionary from Task 2

    Returns:
        CrewAI Task object
    """
    return Task(
        description=f"""Generate professional HTML EDA report:

        **Report Requirements:**
        1. **Header Section:**
           - FleetGuard branding
           - Generation timestamp
           - Executive summary with key metrics

        2. **Summary Metrics (Cards):**
           - Total invoices
           - Total spend
           - Average invoice cost
           - Number of vehicles

        3. **Cost Analysis Section:**
           - Distribution statistics
           - Quartile breakdown
           - Min/max values

        4. **Anomalies Section:**
           - Highlight high-cost outliers with warning boxes
           - List specific invoices (vehicle, workshop, amount)
           - Calculate % of anomalous invoices

        5. **Workshop Comparison:**
           - Table with all workshop statistics
           - Highlight pricing concerns (>15% deviation)
           - Show cheapest and most expensive workshops

        6. **Temporal Trends:**
           - Date range covered
           - Monthly patterns
           - Peak months

        7. **Vehicle Analysis:**
           - Fleet summary
           - High-cost vehicles table

        **Styling:**
        - Hebrew/RTL support
        - Professional gradient design
        - Color-coded alerts (red for urgent, yellow for warnings)
        - Responsive tables

        **Output:**
        Save to `data/reports/eda_report_[timestamp].html`

        **Input Insights:**
        {str(eda_insights)[:500]}...

        **Expected Output:**
        File path to generated HTML report
        """,
        agent=report_generator_agent,
        expected_output='String path to generated HTML report file'
    )


# ===== CREW 2 TASKS: DATA SCIENTIST CREW =====

def create_feature_engineering_task(clean_data):
    """
    Task 4: Feature engineering

    Args:
        clean_data: Validated DataFrame

    Returns:
        CrewAI Task object
    """
    return Task(
        description=f"""Engineer features for machine learning models:

        **IMPORTANT:** You have FULL ACCESS to the database via database_access_tool.
        Use it to get COMPLETE data for feature engineering:
        - Use "vehicle_stats" to get ALL vehicles with current_km, last_service_date, total_cost
        - Use "all_invoices" to get ALL historical invoices for accurate cost calculations
        - Use "full_view" to get detailed invoice line items for service type analysis

        **Required Features:**
        1. **Vehicle Age:**
           - Calculate: current_year - vehicle year
           - Use vehicle_stats for vehicle year
           - Name: 'age'

        2. **Days in Fleet:**
           - Calculate: days since fleet_entry_date
           - Use vehicle_stats for fleet_entry_date
           - Name: 'days_in_fleet'

        3. **Km Per Day:**
           - Calculate: (current_km - initial_km) / days_in_fleet
           - Use vehicle_stats for current_km (from last invoice)
           - Use vehicles table for initial_km
           - Handle edge cases (division by zero → default 30 km/day)
           - Name: 'km_per_day'

        4. **Cost Ratio:**
           - Calculate: vehicle avg_cost / fleet avg_cost
           - Use ALL invoices from database for accurate fleet average
           - Name: 'cost_vs_fleet_avg'

        5. **Days Since Last Service:**
           - Calculate: days since last_service_date
           - Use vehicle_stats for last_service_date
           - Fill NaN with median
           - Name: 'days_since_last_service'

        6. **Categorical Encoding:**
           - Label encode 'make_model'
           - Use ALL vehicles from database for complete encoding
           - Name: 'make_model_encoded'
           - Save encoder for later use

        7. **Derived Targets:**
           - Annual cost: (total_cost / days_in_fleet) * 365
           - Next service cost: avg_service_cost (with adjustments)
           - Use ALL invoices for accurate calculations

        **Data Quality:**
        - Handle NaN values appropriately
        - Replace inf/-inf with defaults
        - Ensure all features are numeric

        **Input Data:**
        {str(clean_data)[:500]}...

        **Expected Output:**
        Feature-engineered DataFrame with all calculated features
        """,
        agent=feature_engineer_agent,
        expected_output='DataFrame with engineered features ready for ML training (JSON format)'
    )


def create_annual_cost_training_task(features_data):
    """
    Task 5: Train annual cost model (MODEL 1)

    Args:
        features_data: Feature-engineered DataFrame

    Returns:
        CrewAI Task object
    """
    return Task(
        description=f"""Train Annual Maintenance Cost Prediction Model (MODEL 1):

        **Model Specifications:**
        - **Algorithm:** RandomForestRegressor (100 trees, max_depth=10)
        - **Target:** Annual maintenance cost per vehicle (₪/year)
        - **Features:** age, current_km, total_services, avg_service_cost,
                       make_model_encoded, days_in_fleet, cost_vs_fleet_avg,
                       km_per_day, days_since_last_service

        **Training Process:**
        1. Split data 80/20 (train/test)
        2. Train RandomForestRegressor
        3. Evaluate on both train and test sets
        4. Perform 5-fold cross-validation
        5. Calculate metrics: RMSE, MAE, R²
        6. Extract feature importance rankings

        **Performance Targets:**
        - Test R² > 0.5 (acceptable)
        - Test R² > 0.7 (good)
        - RMSE < ₪2000 (practical accuracy)

        **Model Persistence:**
        - Save model to: data/models/annual_cost_predictor.pkl
        - Save label encoders to: data/models/label_encoders.pkl
        - Save feature names to: data/models/feature_names.json

        **Input Features:**
        {str(features_data)[:500]}...

        **Expected Output:**
        Dictionary with:
        - metrics (train/test RMSE, MAE, R², CV scores)
        - model_path (path to saved .pkl file)
        - feature_importance (ranked features)
        """,
        agent=cost_predictor_agent,
        expected_output='Dictionary with model metrics, path, and feature importance'
    )


def create_service_cost_training_task(features_data):
    """
    Task 6: Train next service cost model (MODEL 2)

    Args:
        features_data: Feature-engineered DataFrame

    Returns:
        CrewAI Task object
    """
    return Task(
        description=f"""Train Next Service Cost Prediction Model (MODEL 2):

        **Model Specifications:**
        - **Algorithm:** RandomForestRegressor (100 trees, max_depth=8)
        - **Target:** Expected cost of next maintenance service (₪)
        - **Features:** age, current_km, total_services, make_model_encoded,
                       km_per_day, days_since_last_service, cost_vs_fleet_avg

        **Training Process:**
        1. Prepare target: use avg_service_cost as baseline
           - For vehicles with <3 services, multiply by 1.1 (uncertainty factor)
        2. Split data 80/20 (train/test)
        3. Train RandomForestRegressor
        4. Evaluate on both train and test sets
        5. Perform 5-fold cross-validation
        6. Calculate metrics: RMSE, MAE, R²

        **Model Purpose:**
        This model complements the existing rule-based PredictiveMaintenanceAgent
        by providing ML-based cost estimates. It should be compared with:
        - Rule-based predictions (15k km routine service intervals)
        - Historical average costs

        **Performance Targets:**
        - Test R² > 0.4 (acceptable - service costs vary widely)
        - Test R² > 0.6 (good)
        - MAE < ₪500 (practical budget accuracy)

        **Model Persistence:**
        - Save model to: data/models/service_cost_predictor.pkl

        **Input Features:**
        {str(features_data)[:500]}...

        **Expected Output:**
        Dictionary with:
        - metrics (train/test RMSE, MAE, R², CV scores)
        - model_path (path to saved .pkl file)
        - comparison_notes (how it relates to rule-based predictions)
        """,
        agent=maintenance_predictor_agent,
        expected_output='Dictionary with model metrics and path'
    )


def create_model_card_task(cost_metrics, service_metrics):
    """
    Task 7: Generate model documentation

    Args:
        cost_metrics: Metrics from Task 5
        service_metrics: Metrics from Task 6

    Returns:
        CrewAI Task object
    """
    return Task(
        description=f"""Generate comprehensive model_card.md documentation:

        **Required Sections:**
        1. **Model 1: Annual Cost Predictor**
           - Description and purpose
           - Architecture (algorithm, parameters)
           - Features used
           - Performance metrics (R², RMSE, MAE, CV scores)
           - Feature importance rankings
           - Target variable definition
           - Use cases

        2. **Model 2: Next Service Cost Predictor**
           - Description and purpose
           - Architecture
           - Features used
           - Performance metrics
           - Feature importance
           - Target variable definition
           - Comparison with rule-based predictions
           - Use cases

        3. **Training Data**
           - Source (fleet.db)
           - Table descriptions
           - Total vehicles and invoices
           - Data characteristics

        4. **Limitations**
           - Trained on synthetic data
           - Workshop pricing biases
           - Currency limitations (ILS only)
           - Assumptions

        5. **Usage Instructions**
           - Code examples for loading models
           - Making predictions
           - Interpreting results

        **Format:**
        - Markdown (.md)
        - Clear headings and sections
        - Code blocks for examples
        - Tables for metrics

        **Output:**
        Save to: data/models/model_card.md

        **Input Metrics:**
        Cost Model: {str(cost_metrics)[:300]}...
        Service Model: {str(service_metrics)[:300]}...

        **Expected Output:**
        File path to generated model_card.md
        """,
        agent=maintenance_predictor_agent,
        expected_output='String path to generated model_card.md file'
    )


# ===== TASK CREATION FUNCTIONS =====

def create_analyst_crew_tasks(uploaded_data):
    """
    Create all tasks for Data Analyst Crew

    Args:
        uploaded_data: Uploaded DataFrame

    Returns:
        list: [validation_task, eda_task, report_task]
    """
    validation_task = create_validation_task(uploaded_data)
    eda_task = create_eda_task("{clean_data}")  # Will be filled by crew context
    report_task = create_report_task("{eda_insights}")  # Will be filled by crew context

    # Set task dependencies
    eda_task.context = [validation_task]
    report_task.context = [eda_task]

    return [validation_task, eda_task, report_task]


def create_scientist_crew_tasks(clean_data):
    """
    Create all tasks for Data Scientist Crew

    Args:
        clean_data: Validated DataFrame

    Returns:
        list: [feature_task, cost_model_task, service_model_task, model_card_task]
    """
    feature_task = create_feature_engineering_task(clean_data)
    cost_model_task = create_annual_cost_training_task("{features_data}")
    service_model_task = create_service_cost_training_task("{features_data}")
    model_card_task = create_model_card_task("{cost_metrics}", "{service_metrics}")

    # Set task dependencies
    cost_model_task.context = [feature_task]
    service_model_task.context = [feature_task]
    model_card_task.context = [cost_model_task, service_model_task]

    return [feature_task, cost_model_task, service_model_task, model_card_task]


# ===== EXPORTS =====
__all__ = [
    'create_validation_task',
    'create_eda_task',
    'create_report_task',
    'create_feature_engineering_task',
    'create_annual_cost_training_task',
    'create_service_cost_training_task',
    'create_model_card_task',
    'create_analyst_crew_tasks',
    'create_scientist_crew_tasks'
]
