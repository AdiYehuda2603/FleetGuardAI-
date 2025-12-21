"""
CrewAI Agents Definition
Defines all 6 agents for the FleetGuard Multi-Agent System
"""

# Windows patch - must be imported before crewai
try:
    from src.crewai_windows_patch import *
except ImportError:
    pass  # If patch doesn't exist, continue anyway

from crewai import Agent
# Try to import tool decorator, fallback to no-op if not available
try:
    from crewai_tools import tool
except ImportError:
    # Fallback: create a no-op decorator if tool is not available
    def tool(name):
        def decorator(func):
            return func
        return decorator

import pandas as pd
import json

from src.utils.data_validator import DataValidator
from src.utils.eda_generator import EDAGenerator
from src.utils.ml_trainer import FleetMLTrainer
from src.predictive_agent import PredictiveMaintenanceAgent
from src.ai_engine import FleetAIEngine
from src.database_manager import DatabaseManager


# ===== DATABASE ACCESS TOOL (For All Agents) =====

@tool("Database Access Tool")
def database_access_tool(query_type: str, **kwargs) -> dict:
    """
    Provides full access to the FleetGuard database for all agents.
    
    Args:
        query_type: Type of query to execute. Options:
            - "all_invoices": Get all invoices
            - "all_vehicles": Get all vehicles
            - "full_view": Get invoices with line items (JOIN)
            - "vehicle_history": Get history for specific vehicle (requires vehicle_id)
            - "vehicle_info": Get info for specific vehicle (requires vehicle_id)
            - "vehicle_stats": Get all vehicles with statistics
            - "invoice_lines": Get all invoice line items
            - "search_invoices": Search invoices by criteria (vehicle_id, workshop, date_from, date_to)
        **kwargs: Additional parameters based on query_type
    
    Returns:
        dict with 'data' (DataFrame as JSON), 'row_count', and 'columns'
    """
    db = DatabaseManager()
    
    try:
        if query_type == "all_invoices":
            df = db.get_all_invoices()
        elif query_type == "all_vehicles":
            df = db.get_all_vehicles()
        elif query_type == "full_view":
            df = db.get_full_view()
        elif query_type == "vehicle_history":
            vehicle_id = kwargs.get('vehicle_id')
            if not vehicle_id:
                return {"error": "vehicle_id required for vehicle_history"}
            df = db.get_vehicle_history(vehicle_id)
        elif query_type == "vehicle_info":
            vehicle_id = kwargs.get('vehicle_id')
            if not vehicle_id:
                return {"error": "vehicle_id required for vehicle_info"}
            df = db.get_vehicle_info(vehicle_id)
        elif query_type == "vehicle_stats":
            df = db.get_vehicle_with_stats()
        elif query_type == "invoice_lines":
            df = db.get_invoice_lines()
        elif query_type == "search_invoices":
            df = db.search_invoices(
                vehicle_id=kwargs.get('vehicle_id'),
                workshop=kwargs.get('workshop'),
                date_from=kwargs.get('date_from'),
                date_to=kwargs.get('date_to')
            )
        else:
            return {"error": f"Unknown query_type: {query_type}"}
        
        # Convert DataFrame to JSON for agent consumption
        return {
            "data": df.to_dict('records'),
            "row_count": len(df),
            "columns": list(df.columns),
            "summary": {
                "shape": df.shape,
                "memory_usage": df.memory_usage(deep=True).sum()
            }
        }
    except Exception as e:
        return {"error": str(e)}


# ===== CREW 1: DATA ANALYST CREW =====

@tool("Data Validation Tool")
def validate_data_tool(data: str) -> dict:
    """
    Validates fleet data against dataset_contract.json schema.
    Drops rows with missing critical fields and returns alerts.

    Args:
        data: JSON string or path to data

    Returns:
        dict with 'clean_data', 'alerts', and 'dropped_count'
    """
    validator = DataValidator()

    # Parse data (assuming it's a JSON string or DataFrame path)
    try:
        import json
        data_dict = json.loads(data)
        df = pd.DataFrame(data_dict)
    except:
        # Assume it's already a DataFrame or path
        if isinstance(data, pd.DataFrame):
            df = data
        else:
            df = pd.read_csv(data)

    clean_df, alerts = validator.validate_dataframe(df)

    return {
        'clean_data': clean_df.to_dict('records'),
        'alerts': alerts,
        'dropped_count': validator.dropped_count
    }


@tool("EDA Generation Tool")
def generate_eda_tool(data: str) -> dict:
    """
    Performs comprehensive exploratory data analysis on fleet data.

    Args:
        data: JSON string or DataFrame

    Returns:
        dict with insights and analysis results
    """
    generator = EDAGenerator()

    # Parse data
    try:
        import json
        data_dict = json.loads(data)
        df = pd.DataFrame(data_dict)
    except:
        if isinstance(data, pd.DataFrame):
            df = data
        else:
            df = pd.read_csv(data)

    # Generate report (without saving yet - that's Reporter's job)
    generator._analyze_distributions(df)
    generator._identify_anomalies(df)
    generator._workshop_comparison(df)
    generator._temporal_analysis(df)

    return generator.insights


@tool("Report Generation Tool")
def generate_report_tool(insights: dict, output_path: str = None) -> str:
    """
    Generates professional HTML EDA report.

    Args:
        insights: Dictionary of EDA insights
        output_path: Path to save report

    Returns:
        str: Path to generated HTML report
    """
    generator = EDAGenerator()
    generator.insights = insights

    report_path, _ = generator.generate_report(output_path=output_path)

    return report_path


# Agent A: Data Validator
data_validator_agent = Agent(
    role='Data Quality Enforcer',
    goal='Validate incoming fleet data against strict schema (dataset_contract.json) and drop invalid rows with specific alerts',
    backstory="""You are a meticulous data validator with zero tolerance for
    incomplete records. You enforce the dataset_contract.json schema strictly.
    For every row with missing critical fields (vehicle_id, date, odometer_km,
    workshop, total), you DROP the row and log a specific alert:
    'Vehicle [ID] data ignored due to missing fields: [field_list]'.

    You maintain data integrity for the entire fleet management system.
    You have FULL ACCESS to the database via database_access_tool to compare
    uploaded data with existing records and ensure consistency.""",
    verbose=True,
    allow_delegation=False,
    tools=[database_access_tool, validate_data_tool]
)

# Agent B: EDA Explorer
eda_explorer_agent = Agent(
    role='Fleet Data Analyst',
    goal='Perform comprehensive exploratory data analysis on fleet maintenance data to uncover patterns, anomalies, and cost-saving opportunities',
    backstory="""You are an expert data scientist specializing in vehicle fleet
    analysis. You identify:
    - Cost distribution patterns
    - Workshop pricing anomalies (some workshops may be 30% cheaper/expensive)
    - Temporal trends in maintenance costs
    - Outlier detection for unusually high/low invoices
    - Vehicle-specific insights

    Your analysis forms the foundation for strategic fleet decisions.
    You have FULL ACCESS to the entire database via database_access_tool.
    Use it to analyze ALL historical invoices, vehicles, and maintenance patterns,
    not just the uploaded data. This gives you complete context for your analysis.""",
    verbose=True,
    allow_delegation=False,
    tools=[database_access_tool, generate_eda_tool]
)

# Agent C: Report Generator
report_generator_agent = Agent(
    role='Technical Report Writer',
    goal='Generate professional, actionable HTML reports with visualizations and insights for fleet managers',
    backstory="""You transform statistical findings into clear, actionable
    reports. Your reports include:
    - Executive summary with key metrics
    - Cost analysis with anomaly highlights
    - Workshop comparison tables
    - Temporal trends
    - Actionable recommendations

    Your reports are visual, comprehensive, and highlight critical issues
    that require immediate attention.
    You have FULL ACCESS to the database via database_access_tool to enrich
    your reports with complete historical context and comprehensive statistics.""",
    verbose=True,
    allow_delegation=False,
    tools=[database_access_tool, generate_report_tool]
)


# ===== CREW 2: DATA SCIENTIST CREW =====

@tool("Feature Engineering Tool")
def feature_engineering_tool(data: str) -> dict:
    """
    Performs feature engineering for ML models.

    Args:
        data: JSON string or DataFrame

    Returns:
        dict with engineered features DataFrame
    """
    trainer = FleetMLTrainer()

    # Parse data
    try:
        import json
        data_dict = json.loads(data)
        df = pd.DataFrame(data_dict)
    except:
        if isinstance(data, pd.DataFrame):
            df = data
        else:
            df = None  # Will use database

    df_features = trainer.prepare_features(df_vehicles=df)

    return {
        'features': df_features.to_dict('records'),
        'feature_names': trainer.feature_names,
        'label_encoders': {k: v.classes_.tolist() for k, v in trainer.label_encoders.items()}
    }


@tool("Annual Cost Model Training Tool")
def train_annual_cost_model_tool(features_data: str) -> dict:
    """
    Trains annual maintenance cost prediction model (MODEL 1).

    Args:
        features_data: JSON string of feature-engineered data

    Returns:
        dict with model metrics and paths
    """
    trainer = FleetMLTrainer()

    # Parse features
    try:
        import json
        features_dict = json.loads(features_data)
        df_features = pd.DataFrame(features_dict)
    except:
        df_features = None  # Will prepare internally

    # Train model
    result = trainer.train_annual_cost_model(df_features)

    # Save model
    paths = trainer.save_models()

    return {
        'metrics': result['metrics'],
        'model_path': paths.get('cost_model'),
        'r2_score': result['metrics']['test_r2'],
        'rmse': result['metrics']['test_rmse']
    }


@tool("Service Cost Model Training Tool")
def train_service_cost_model_tool(features_data: str) -> dict:
    """
    Trains next service cost prediction model (MODEL 2).

    Args:
        features_data: JSON string of feature-engineered data

    Returns:
        dict with model metrics and paths
    """
    trainer = FleetMLTrainer()

    # Parse features
    try:
        import json
        features_dict = json.loads(features_data)
        df_features = pd.DataFrame(features_dict)
    except:
        df_features = None  # Will prepare internally

    # Train model
    result = trainer.train_service_cost_model(df_features)

    # Save model
    paths = trainer.save_models()

    return {
        'metrics': result['metrics'],
        'model_path': paths.get('service_model'),
        'r2_score': result['metrics']['test_r2'],
        'rmse': result['metrics']['test_rmse']
    }


@tool("Model Card Generation Tool")
def generate_model_card_tool(cost_metrics: dict, service_metrics: dict) -> str:
    """
    Generates model_card.md documentation.

    Args:
        cost_metrics: Metrics from annual cost model
        service_metrics: Metrics from service cost model

    Returns:
        str: Path to model_card.md
    """
    trainer = FleetMLTrainer()
    trainer.metrics['annual_cost'] = cost_metrics
    trainer.metrics['service_cost'] = service_metrics

    card_path = trainer.generate_model_card()

    return card_path


# Agent D: Feature Engineer
feature_engineer_agent = Agent(
    role='ML Feature Engineer',
    goal='Transform raw fleet data into powerful predictive features for machine learning models',
    backstory="""You are a feature engineering expert who creates meaningful
    features from vehicle data. You calculate:
    - Vehicle age from year
    - Days in fleet since entry
    - Km per day (usage intensity)
    - Cost ratios vs fleet average
    - Days since last service
    - Encoded categorical variables (make/model)

    Your engineered features determine model performance and predictive accuracy.
    You have FULL ACCESS to the database via database_access_tool to access
    ALL vehicles, invoices, and historical data for comprehensive feature engineering.
    Use vehicle_stats to get complete vehicle information with current odometer readings.""",
    verbose=True,
    allow_delegation=False,
    tools=[database_access_tool, feature_engineering_tool]
)

# Agent E: Cost Predictor (MODEL 1)
cost_predictor_agent = Agent(
    role='Annual Cost Prediction Specialist',
    goal='Train accurate regression models to predict annual maintenance costs per vehicle',
    backstory="""You specialize in cost forecasting using machine learning.
    You train RandomForest or GradientBoosting regressors to predict each
    vehicle's annual maintenance costs based on:
    - Age, mileage, service history
    - Make/model characteristics
    - Usage patterns (km/day)
    - Historical cost ratios

    Your models help fleet managers:
    - Budget accurately for maintenance
    - Identify high-cost vehicles for replacement
    - Detect cost anomalies

    You aim for R² > 0.7 and minimize RMSE.
    You have FULL ACCESS to the database via database_access_tool to access
    ALL historical invoices and vehicle data for comprehensive model training.""",
    verbose=True,
    allow_delegation=False,
    tools=[database_access_tool, train_annual_cost_model_tool]
)

# Agent F: Maintenance Predictor (MODEL 2)
maintenance_predictor_agent = Agent(
    role='Next Service Cost Prediction Specialist',
    goal='Train models to predict the cost of the next maintenance service for each vehicle',
    backstory="""You use predictive analytics to forecast the cost of upcoming
    maintenance events. Your models complement the existing rule-based
    PredictiveMaintenanceAgent by providing ML-based cost estimates.

    You train models based on:
    - Average service cost history
    - Days since last service
    - Vehicle age and mileage
    - Service frequency patterns

    You also compare your ML predictions with the rule-based predictions
    to provide hybrid recommendations. You aim for R² > 0.6 and practical
    cost estimates that fleet managers can budget for.
    You have FULL ACCESS to the database via database_access_tool to access
    ALL historical service records, invoice line items, and vehicle maintenance
    history for comprehensive pattern analysis.""",
    verbose=True,
    allow_delegation=False,
    tools=[database_access_tool, train_service_cost_model_tool, generate_model_card_tool]
)


# ===== CREW 3: FLEET MANAGEMENT CREW =====

@tool("Fleet Overview Tool")
def fleet_overview_tool() -> dict:
    """
    מציג סקירה מלאה של כל הצי - כל רכב עם כל הנתונים

    Returns:
        dict עם נתוני הצי המלאים
    """
    from src.fleet_analysis_tools import FleetAnalyzer

    analyzer = FleetAnalyzer()
    fleet_df = analyzer.get_fleet_status_summary()

    return {
        'data': fleet_df.to_dict('records'),
        'total_vehicles': len(fleet_df),
        'active_vehicles': len(fleet_df[fleet_df['status'] == 'active']),
        'near_retirement': len(fleet_df[fleet_df.get('retirement_status', '') == 'near_retirement'])
    }


@tool("Strategic Analysis Tool")
def strategic_analysis_tool() -> dict:
    """
    מנתח את הצי ומספק תובנות אסטרטגיות:
    - אמינות לפי דגם
    - המלצות החלפה
    - רכבים מצטיינים
    - מגמות עלויות

    Returns:
        dict עם כל התובנות
    """
    from src.fleet_analysis_tools import FleetAnalyzer

    analyzer = FleetAnalyzer()
    insights = analyzer.get_strategic_insights()

    return insights


# Agent G: Fleet Overview Agent
fleet_overview_agent = Agent(
    role='Fleet Overview Manager',
    goal='Provide comprehensive real-time overview of entire fleet status',
    backstory="""You are the Fleet Overview Manager responsible for maintaining
    a complete, up-to-date view of all vehicles in the fleet. You track:
    - Vehicle details (make, model, plate)
    - Purchase and assignment information
    - Test dates (last and next)
    - Service history
    - Current mileage
    - Estimated retirement date
    - Annual maintenance costs

    Your reports help managers quickly understand the status of every vehicle
    and make informed decisions about fleet operations.
    You have FULL ACCESS to the database via database_access_tool to retrieve
    ALL vehicle information, maintenance history, and calculated metrics.""",
    verbose=True,
    allow_delegation=False,
    tools=[database_access_tool, fleet_overview_tool]
)

# Agent H: Strategic Business Analyst
strategic_analyst_agent = Agent(
    role='Strategic Fleet Business Analyst',
    goal='Provide high-level business insights and recommendations for fleet optimization',
    backstory="""You are a Strategic Business Analyst specializing in fleet management.
    Your role is to analyze data across the ENTIRE fleet and provide actionable
    business intelligence:

    1. RELIABILITY ANALYSIS: Which vehicle models are most reliable? (fewer breakdowns)
    2. COST EFFICIENCY: Which vehicles are most economical to maintain?
    3. REPLACEMENT RECOMMENDATIONS: Which vehicles should be replaced? (age, cost, mileage)
    4. BEST PERFORMERS: Which vehicles are fleet stars? (low cost, high reliability)
    5. COST TRENDS: How are maintenance costs trending over time?
    6. WORKSHOP ANALYSIS: Which workshops offer best value?

    Your insights guide strategic decisions on:
    - Which models to purchase for fleet expansion
    - When to retire specific vehicles
    - Budget planning for next fiscal year
    - Workshop contract negotiations

    You have FULL ACCESS to the database via database_access_tool to analyze
    ALL historical data and generate comprehensive business intelligence.""",
    verbose=True,
    allow_delegation=False,
    tools=[database_access_tool, strategic_analysis_tool]
)


# ===== AGENT LIST FOR EXPORT =====
ALL_AGENTS = {
    'crew1': {
        'validator': data_validator_agent,
        'explorer': eda_explorer_agent,
        'reporter': report_generator_agent
    },
    'crew2': {
        'feature_engineer': feature_engineer_agent,
        'cost_predictor': cost_predictor_agent,
        'maintenance_predictor': maintenance_predictor_agent
    },
    'crew3': {
        'fleet_overview': fleet_overview_agent,
        'strategic_analyst': strategic_analyst_agent
    }
}


# For easy import
__all__ = [
    'data_validator_agent',
    'eda_explorer_agent',
    'report_generator_agent',
    'feature_engineer_agent',
    'cost_predictor_agent',
    'maintenance_predictor_agent',
    'fleet_overview_agent',
    'strategic_analyst_agent',
    'ALL_AGENTS'
]
