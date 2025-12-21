# FleetGuard Multi-Agent System - CrewAI Implementation Plan

## Overview
This plan upgrades the existing FleetGuard system into a full Multi-Agent System using CrewAI while preserving all existing code and logic.

---

## Architecture Design

### Current State Preservation
- **Keep intact**: `generate_data.py`, base `main.py` structure, all existing logic
- **Wrap, don't replace**: Convert independent agents into CrewAI orchestration
- **Maintain**: All Hebrew/RTL support, existing database schema, GPT-4o-mini integration

### New Directory Structure
```
FleetGuard/
├── src/
│   ├── database_manager.py          # KEEP AS-IS (utility for all agents)
│   ├── ai_engine.py                 # KEEP (will wrap into CrewAI)
│   ├── predictive_agent.py          # KEEP (will wrap into CrewAI)
│   ├── crewai_agents.py             # NEW - CrewAI agent definitions
│   ├── crewai_tasks.py              # NEW - CrewAI task definitions
│   ├── crew_orchestrator.py         # NEW - Crew coordination
│   └── utils/
│       ├── data_validator.py        # NEW - Schema validation
│       ├── eda_generator.py         # NEW - EDA analysis
│       ├── ml_trainer.py            # NEW - ML model training
│       └── file_processor.py        # NEW - PDF/CSV upload handler
├── data/
│   ├── database/fleet.db            # KEEP
│   ├── uploads/                     # NEW - uploaded files
│   ├── reports/                     # NEW - EDA HTML reports
│   └── models/                      # NEW - saved ML models
├── config/
│   └── dataset_contract.json        # NEW - data validation schema
├── main.py                          # MODIFY - add file upload + new tabs
├── generate_data.py                 # KEEP AS-IS
└── requirements.txt                 # UPDATE - add crewai, scikit-learn
```

---

## Phase 1: Setup & Dependencies

### 1.1 Update requirements.txt
Add to existing dependencies:
```
crewai>=0.11.0
scikit-learn>=1.3.0
seaborn>=0.12.0
matplotlib>=3.7.0
pdfplumber>=0.10.0
ydata-profiling>=4.5.0
```

### 1.2 Create dataset_contract.json
Define strict schema with critical fields:
```json
{
  "schema_version": "1.0",
  "critical_fields": [
    "vehicle_id",
    "date",
    "odometer_km",
    "workshop",
    "total"
  ],
  "optional_fields": [
    "plate",
    "make_model",
    "kind"
  ],
  "field_types": {
    "vehicle_id": "string",
    "date": "date",
    "odometer_km": "integer",
    "workshop": "string",
    "total": "float"
  },
  "validation_rules": {
    "odometer_km": {"min": 0, "max": 500000},
    "total": {"min": 0, "max": 50000},
    "date": {"format": "YYYY-MM-DD"}
  }
}
```

---

## Phase 2: Data Processing Utilities

### 2.1 Create src/utils/file_processor.py
**Purpose**: Handle uploaded PDF/CSV files and convert to database format

**Key Functions**:
- `process_uploaded_file(file, file_type)`: Main entry point
- `extract_pdf_invoice(pdf_bytes)`: Extract invoice data from PDF using pdfplumber
- `parse_csv_invoice(csv_df)`: Parse CSV with expected schema
- `convert_to_db_format(raw_data)`: Normalize to invoices/invoice_lines schema

**Logic**:
1. Accept both PDF and CSV uploads
2. Extract invoice metadata (date, vehicle_id, workshop, etc.)
3. Extract line items (description, qty, unit_price)
4. Return standardized dict matching database schema

### 2.2 Create src/utils/data_validator.py
**Purpose**: Enforce dataset_contract.json validation (Agent A logic)

**Key Class**: `DataValidator`

**Methods**:
- `__init__(contract_path)`: Load JSON schema
- `validate_dataframe(df)`: Main validation
- `drop_invalid_rows(df)`: Remove rows missing critical fields
- `log_dropped_rows(dropped_df)`: Generate alert logs

**Validation Logic**:
```python
def validate_dataframe(self, df):
    dropped = []
    alerts = []

    for idx, row in df.iterrows():
        missing_fields = []
        for field in self.critical_fields:
            if pd.isna(row.get(field)):
                missing_fields.append(field)

        if missing_fields:
            dropped.append(idx)
            alerts.append(f"⚠️ Vehicle {row.get('vehicle_id', 'UNKNOWN')} data ignored due to missing fields: {', '.join(missing_fields)}")

    clean_df = df.drop(dropped)
    return clean_df, alerts
```

### 2.3 Create src/utils/eda_generator.py
**Purpose**: Generate comprehensive EDA HTML report (Agent B/C logic)

**Key Class**: `EDAGenerator`

**Methods**:
- `generate_report(df, output_path)`: Main report generation
- `_analyze_distributions()`: Statistical summaries
- `_identify_anomalies()`: Outlier detection
- `_workshop_comparison()`: Cost comparison by workshop
- `_temporal_analysis()`: Time series patterns

**Technology**:
- Use `ydata-profiling` for automated EDA
- Custom sections for fleet-specific insights
- Save as HTML to `data/reports/eda_report_{timestamp}.html`

### 2.4 Create src/utils/ml_trainer.py
**Purpose**: Train ML models for cost and maintenance prediction (Agent E/F logic)

**Key Class**: `FleetMLTrainer`

**Models**:
1. **Annual Cost Predictor** (Regression)
   - Features: vehicle age, current_km, make_model (encoded), total_services, avg_service_cost
   - Target: predicted annual maintenance cost
   - Algorithm: RandomForestRegressor or GradientBoostingRegressor

2. **Next Maintenance Predictor** (Regression)
   - Features: days_since_service, current_km, km_per_day, service_history
   - Target: days until next maintenance event
   - Algorithm: RandomForestRegressor

**Methods**:
- `prepare_features(df)`: Feature engineering
- `train_cost_model(X, y)`: Train annual cost predictor
- `train_maintenance_model(X, y)`: Train maintenance predictor
- `save_models(cost_model, maint_model)`: Pickle models
- `generate_model_card()`: Create model_card.md with metrics

**Feature Engineering Logic**:
```python
def prepare_features(self, df):
    # Calculate vehicle age
    df['age'] = datetime.now().year - df['year']

    # Encode categorical
    df['make_model_encoded'] = LabelEncoder().fit_transform(df['make_model'])

    # Time-based features
    df['days_since_last_service'] = (datetime.now() - pd.to_datetime(df['last_service_date'])).dt.days

    # Cost ratios
    df['cost_vs_fleet_avg'] = df['avg_service_cost'] / df['avg_service_cost'].mean()

    return df
```

---

## Phase 3: CrewAI Agent Definitions

### 3.1 Create src/crewai_agents.py

**Crew 1: Data Analyst Crew**

```python
from crewai import Agent
from src.utils.data_validator import DataValidator
from src.utils.eda_generator import EDAGenerator

# Agent A: Data Validator
validator_agent = Agent(
    role='Data Quality Enforcer',
    goal='Validate incoming fleet data against strict schema and drop invalid rows',
    backstory='''You are a meticulous data validator with zero tolerance for
    incomplete records. You enforce the dataset_contract.json schema and log
    every dropped row with specific reasons.''',
    verbose=True,
    allow_delegation=False,
    tools=[DataValidator]  # Custom tool wrapping validation logic
)

# Agent B: EDA Explorer
eda_explorer = Agent(
    role='Fleet Data Analyst',
    goal='Perform comprehensive exploratory data analysis on fleet maintenance data',
    backstory='''You are an expert data scientist specializing in vehicle fleet
    analysis. You identify patterns, anomalies, and cost-saving opportunities
    through statistical analysis.''',
    verbose=True,
    allow_delegation=False,
    tools=[EDAGenerator]
)

# Agent C: Report Generator
reporter = Agent(
    role='Technical Report Writer',
    goal='Generate professional HTML reports with actionable insights',
    backstory='''You transform statistical findings into clear, actionable
    reports for fleet managers. Your reports are visual, comprehensive, and
    highlight critical issues.''',
    verbose=True,
    allow_delegation=False
)
```

**Crew 2: Data Scientist Crew**

```python
from src.utils.ml_trainer import FleetMLTrainer
from src.predictive_agent import PredictiveMaintenanceAgent

# Agent D: Feature Engineer
feature_engineer = Agent(
    role='ML Feature Engineer',
    goal='Prepare and transform fleet data for machine learning models',
    backstory='''You are a feature engineering expert who creates powerful
    predictive features from raw fleet data. You understand vehicle lifecycles
    and cost drivers.''',
    verbose=True,
    allow_delegation=False
)

# Agent E: Cost Predictor
cost_predictor = Agent(
    role='Cost Prediction Specialist',
    goal='Train accurate regression models to predict annual maintenance costs',
    backstory='''You specialize in cost forecasting using machine learning.
    Your models help fleet managers budget effectively and identify high-cost vehicles.''',
    verbose=True,
    allow_delegation=False,
    tools=[FleetMLTrainer]
)

# Agent F: Maintenance Predictor
maintenance_predictor = Agent(
    role='Maintenance Forecasting Specialist',
    goal='Predict when vehicles will need their next maintenance or breakdown',
    backstory='''You use predictive analytics to forecast maintenance events,
    helping prevent breakdowns and optimize service scheduling.''',
    verbose=True,
    allow_delegation=False,
    tools=[FleetMLTrainer, PredictiveMaintenanceAgent]  # Wrap existing logic
)
```

### 3.2 Create src/crewai_tasks.py

```python
from crewai import Task

# Crew 1 Tasks
validate_task = Task(
    description='''Validate the uploaded fleet data against dataset_contract.json:
    1. Check for missing critical fields (vehicle_id, date, odometer_km, workshop, total)
    2. Drop rows with missing critical data
    3. Log specific alerts: "Vehicle [ID] data ignored due to missing fields: [field_list]"
    4. Return cleaned DataFrame and alert list

    Input: {uploaded_df}
    Output: (clean_df, alerts)
    ''',
    agent=validator_agent,
    expected_output='Cleaned DataFrame and list of validation alerts'
)

eda_task = Task(
    description='''Perform comprehensive EDA on the validated fleet data:
    1. Statistical summaries (mean, median, std for costs and mileage)
    2. Distribution analysis (cost distributions by workshop, vehicle model)
    3. Anomaly detection (outliers in costs, unusual mileage patterns)
    4. Temporal patterns (cost trends over time)
    5. Workshop comparison (pricing differences, service frequency)

    Input: {clean_df}
    Output: EDA insights dictionary
    ''',
    agent=eda_explorer,
    expected_output='Dictionary containing EDA insights and statistics'
)

report_task = Task(
    description='''Generate professional HTML EDA report:
    1. Use ydata-profiling for automated report
    2. Add custom sections for fleet-specific insights
    3. Highlight anomalies and recommendations
    4. Save to data/reports/eda_report_{timestamp}.html

    Input: {eda_insights}
    Output: Path to generated HTML report
    ''',
    agent=reporter,
    expected_output='File path to generated HTML report'
)

# Crew 2 Tasks
feature_eng_task = Task(
    description='''Engineer features for ML models:
    1. Calculate vehicle age from year
    2. Encode categorical variables (make_model, workshop)
    3. Create time-based features (days_since_last_service, km_per_day)
    4. Generate cost ratios (cost_vs_fleet_avg)
    5. Create service frequency metrics

    Input: {clean_df}
    Output: Feature-engineered DataFrame ready for modeling
    ''',
    agent=feature_engineer,
    expected_output='DataFrame with engineered features'
)

cost_model_task = Task(
    description='''Train annual cost prediction model:
    1. Split data into train/test (80/20)
    2. Train RandomForestRegressor or GradientBoostingRegressor
    3. Evaluate using RMSE, MAE, R²
    4. Save model to data/models/cost_predictor.pkl
    5. Generate feature importance analysis

    Input: {features_df}
    Target: Annual maintenance cost (sum of vehicle costs per year)
    Output: Trained model and evaluation metrics
    ''',
    agent=cost_predictor,
    expected_output='Trained cost prediction model and metrics dictionary'
)

maintenance_model_task = Task(
    description='''Train next maintenance prediction model:
    1. Use existing PredictiveMaintenanceAgent logic as baseline
    2. Train ML model to predict days until next service
    3. Incorporate km_per_day and service history patterns
    4. Save model to data/models/maintenance_predictor.pkl
    5. Compare ML predictions with rule-based predictions

    Input: {features_df}
    Target: Days until next maintenance event
    Output: Trained maintenance model and comparison report
    ''',
    agent=maintenance_predictor,
    expected_output='Trained maintenance model and comparison with existing logic'
)

model_card_task = Task(
    description='''Generate model_card.md documentation:
    1. Model descriptions (architecture, features, target)
    2. Performance metrics (RMSE, MAE, R² for both models)
    3. Feature importance rankings
    4. Usage instructions
    5. Limitations and assumptions

    Input: {cost_metrics}, {maintenance_metrics}
    Output: data/models/model_card.md
    ''',
    agent=cost_predictor,  # Can use either predictor agent
    expected_output='Markdown file with complete model documentation'
)
```

---

## Phase 4: Crew Orchestration

### 4.1 Create src/crew_orchestrator.py

```python
from crewai import Crew, Process
from src.crewai_agents import (
    validator_agent, eda_explorer, reporter,
    feature_engineer, cost_predictor, maintenance_predictor
)
from src.crewai_tasks import (
    validate_task, eda_task, report_task,
    feature_eng_task, cost_model_task, maintenance_model_task, model_card_task
)
from src.database_manager import DatabaseManager

class CrewOrchestrator:
    def __init__(self):
        self.db = DatabaseManager()

        # Crew 1: Data Analyst Crew
        self.analyst_crew = Crew(
            agents=[validator_agent, eda_explorer, reporter],
            tasks=[validate_task, eda_task, report_task],
            process=Process.sequential,  # Sequential execution
            verbose=True
        )

        # Crew 2: Data Scientist Crew
        self.scientist_crew = Crew(
            agents=[feature_engineer, cost_predictor, maintenance_predictor],
            tasks=[feature_eng_task, cost_model_task, maintenance_model_task, model_card_task],
            process=Process.sequential,
            verbose=True
        )

    def run_analyst_crew(self, uploaded_df):
        """Execute Data Analyst Crew"""
        result = self.analyst_crew.kickoff(inputs={'uploaded_df': uploaded_df})
        return result

    def run_scientist_crew(self, clean_df):
        """Execute Data Scientist Crew"""
        result = self.scientist_crew.kickoff(inputs={'clean_df': clean_df})
        return result

    def run_full_pipeline(self, uploaded_df):
        """Execute both crews sequentially"""
        # Step 1: Analyst Crew
        analyst_result = self.run_analyst_crew(uploaded_df)
        clean_df = analyst_result['clean_df']
        alerts = analyst_result['alerts']
        report_path = analyst_result['report_path']

        # Step 2: Scientist Crew
        scientist_result = self.run_scientist_crew(clean_df)
        models = scientist_result['models']
        metrics = scientist_result['metrics']

        return {
            'alerts': alerts,
            'report_path': report_path,
            'models': models,
            'metrics': metrics
        }
```

---

## Phase 5: Dashboard Integration

### 5.1 Modify main.py

**Changes**:

1. **Add File Uploader to Sidebar**:
```python
with st.sidebar:
    st.header("⚙️ הגדרות וסינון")

    # NEW: File Upload Section
    st.markdown("---")
    st.subheader("📤 העלאת נתונים")
    uploaded_file = st.file_uploader(
        "העלה חשבונית (PDF/CSV)",
        type=['pdf', 'csv'],
        help="העלה קובץ PDF או CSV עם חשבוניות חדשות"
    )

    if uploaded_file is not None:
        with st.spinner("מעבד קובץ..."):
            # Process file
            from src.utils.file_processor import process_uploaded_file
            from src.crew_orchestrator import CrewOrchestrator

            processed_data = process_uploaded_file(uploaded_file, uploaded_file.type)

            # Trigger CrewAI pipeline
            orchestrator = CrewOrchestrator()
            result = orchestrator.run_full_pipeline(processed_data)

            # Store results in session state
            st.session_state['crew_result'] = result
            st.success("✅ קובץ עובד בהצלחה!")
```

2. **Add New Tab for EDA Report**:
```python
# Change from 4 tabs to 5 tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 לוח בקרה (Dashboard)",
    "🤖 צ'אט אנליסט (AI)",
    "🔮 חיזויים וטיפולים",
    "📄 דוח EDA",  # NEW TAB
    "📋 נתונים גולמיים"
])

# NEW: Tab 4 - EDA Report
with tab4:
    st.header("📄 דוח ניתוח נתונים (EDA)")

    if 'crew_result' in st.session_state:
        report_path = st.session_state['crew_result']['report_path']

        # Display HTML report
        with open(report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=800, scrolling=True)

        # Download button
        st.download_button(
            label="📥 הורד דוח HTML",
            data=html_content,
            file_name=f"eda_report_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html"
        )
    else:
        st.info("💡 העלה קובץ נתונים כדי ליצור דוח EDA")
```

3. **Refine Main Dashboard (Tab 1)**:
```python
with tab1:
    st.header("📊 לוח בקרה ראשי")

    # Show alerts from validation (if exists)
    if 'crew_result' in st.session_state:
        alerts = st.session_state['crew_result']['alerts']

        if alerts:
            st.subheader("⚠️ התראות ואנומליות")
            for alert in alerts:
                st.warning(alert)

        # Show ML model recommendations
        metrics = st.session_state['crew_result']['metrics']

        st.subheader("🎯 המלצות מבוססות AI")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("דיוק חיזוי עלויות (R²)", f"{metrics['cost_model_r2']:.2%}")
            st.caption("מודל ML לחיזוי עלויות שנתיות")

        with col2:
            st.metric("דיוק חיזוי טיפולים (R²)", f"{metrics['maintenance_model_r2']:.2%}")
            st.caption("מודל ML לחיזוי טיפול הבא")

    # Continue with existing dashboard KPIs and charts...
    # (Keep all existing visualizations)
```

4. **Update Tab 3 (Predictions) to Include ML Models**:
```python
with tab3:
    st.header("🔮 חיזוי טיפולים והחלפת רכבים")

    # Add ML-based predictions alongside rule-based
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧮 חיזוי מבוסס כללים")
        # Existing PredictiveMaintenanceAgent logic
        # (Keep as-is)

    with col2:
        st.subheader("🤖 חיזוי מבוסס ML")
        if 'crew_result' in st.session_state:
            models = st.session_state['crew_result']['models']

            # Load ML models and make predictions
            # Show comparison with rule-based predictions
```

---

## Phase 6: Integration & Testing

### 6.1 Integration Checklist
- [ ] All existing code preserved (generate_data.py, base logic)
- [ ] CrewAI agents wrap existing logic (ai_engine.py, predictive_agent.py)
- [ ] File upload triggers CrewAI pipeline automatically
- [ ] Validation agent drops invalid rows with specific logs
- [ ] EDA report generates HTML successfully
- [ ] ML models train and save to data/models/
- [ ] Dashboard displays alerts and recommendations
- [ ] Hebrew/RTL support maintained throughout

### 6.2 Testing Strategy
1. **Unit Tests**: Test each utility module independently
2. **Integration Tests**: Test crew orchestration with sample data
3. **UI Tests**: Test file upload and report rendering in Streamlit
4. **Data Validation Tests**: Test dataset_contract.json enforcement
5. **Model Performance Tests**: Validate ML model metrics (R² > 0.5)

---

## Phase 7: Documentation

### 7.1 Update README.md
Add sections:
- CrewAI architecture diagram
- How to upload files
- How to interpret EDA reports
- ML model usage instructions

### 7.2 Create ARCHITECTURE.md
Document:
- Crew 1 and Crew 2 agent roles
- Task dependencies
- Data flow diagram
- Integration points with existing code

---

## Implementation Order

1. **Phase 1**: Setup dependencies (15 min)
2. **Phase 2**: Create all utility modules (2 hours)
   - file_processor.py
   - data_validator.py
   - eda_generator.py
   - ml_trainer.py
3. **Phase 3**: Define CrewAI agents (1 hour)
4. **Phase 4**: Define CrewAI tasks and orchestrator (1.5 hours)
5. **Phase 5**: Modify main.py dashboard (1 hour)
6. **Phase 6**: Testing and refinement (1 hour)
7. **Phase 7**: Documentation (30 min)

**Total Estimated Time**: 7.25 hours

---

## Success Criteria (Academic Grade: 100/100)

✅ **Preservation**: All existing code intact, no deletions
✅ **CrewAI Integration**: Formal Crews with Agents and Tasks
✅ **Real-time Ingestion**: File upload triggers automatic processing
✅ **Strict Validation**: dataset_contract.json enforced with specific logs
✅ **EDA Report**: Professional HTML report with insights
✅ **ML Models**: Two regression models (cost + maintenance) with model card
✅ **Dashboard Refinement**: Clean UI showing only conclusions/recommendations
✅ **Hebrew Support**: RTL maintained throughout new features

---

## Notes

- Existing `ai_engine.py` (GPT-4o-mini analyst) remains functional and can be used by agents
- Existing `predictive_agent.py` logic serves as baseline for ML model comparison
- `generate_data.py` creates biased data (workshop pricing differences) - ML should detect this
- All new code follows existing Hebrew comment style where appropriate
