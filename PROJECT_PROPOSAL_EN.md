# 📋 FleetGuard AI - Final Project Proposal

## 🎯 Project Mission

**FleetGuard AI** is an intelligent fleet management system designed to optimize operational costs, predict vehicle maintenance needs, and improve strategic decision-making through advanced data analytics and machine learning.

The system combines multi-agent architecture (CrewAI) with predictive models to deliver actionable insights for fleet managers.

---

## 🏢 Business Background

### The Challenge
Organizations managing vehicle fleets face significant challenges:
- **High maintenance costs** without proper prediction tools
- **Unplanned downtime** due to unexpected failures
- **Suboptimal decisions** about vehicle replacement timing
- **Inefficient workshop selection** leading to budget overruns
- **Poor driver performance** without tracking metrics

### Our Solution
FleetGuard AI analyzes historical maintenance data, vehicle performance, and operational patterns to:
- Predict monthly maintenance costs per vehicle
- Identify vehicles requiring replacement
- Recommend optimal workshops based on cost and quality
- Track driver performance and identify training needs
- Generate strategic reports (quarterly, annual, retirement planning)

### Business Value
- **Cost Reduction:** 15-25% savings through predictive maintenance
- **Downtime Prevention:** Early failure detection reduces unplanned stops
- **Data-Driven Decisions:** Replace emotion-based decisions with analytics
- **Resource Optimization:** Efficient workshop and driver management

---

## 🤖 System Architecture - Two Crew System

### **Crew 1 — Data Analyst Crew** (3 Agents)

**Purpose:** Data ingestion, cleaning, exploration, and business intelligence

#### Agent A: Data Ingestion Specialist
- **Role:** Data Collection & Validation Expert
- **Goal:** Load and validate all fleet data from multiple sources
- **Tasks:**
  - Load data from `vehicles.csv` and `invoices.csv`
  - Validate data integrity (nulls, duplicates, type mismatches)
  - Create dataset contract (JSON schema with constraints)
  - Generate data quality report
- **Tools:** `pandas`, `jsonschema`, custom validation functions

#### Agent B: Exploratory Data Analyst
- **Role:** Statistical Analysis & Pattern Recognition Expert
- **Goal:** Perform comprehensive EDA and identify insights
- **Tasks:**
  - Generate `eda_report.html` using ydata-profiling
  - Identify correlations, outliers, and trends
  - Analyze cost distributions by workshop, vehicle model, age
  - Detect seasonal patterns in maintenance
- **Tools:** `ydata-profiling`, `matplotlib`, `seaborn`, `plotly`

#### Agent C: Business Insights Generator
- **Role:** Strategic Business Analyst
- **Goal:** Transform data findings into business recommendations
- **Tasks:**
  - Identify top 5 most/least reliable vehicle models
  - Calculate cost per kilometer for each vehicle
  - Recommend vehicles for retirement (age + cost criteria)
  - Compare workshop efficiency and pricing
  - Generate executive dashboard metrics
- **Tools:** Custom analytics functions, strategic algorithms

---

### **Crew 2 — Data Scientist Crew** (3 Agents)

**Purpose:** Feature engineering, model training, and predictive analytics

#### Agent D: Feature Engineer
- **Role:** Feature Creation & Selection Expert
- **Goal:** Engineer optimal features for maintenance cost prediction
- **Tasks:**
  - Create derived features:
    - `vehicle_age_years` (from purchase date)
    - `avg_cost_per_service`
    - `days_since_last_service`
    - `service_frequency_rate`
    - `km_per_month`
  - Perform feature selection (correlation analysis, VIF)
  - Handle categorical encoding (workshop names, vehicle models)
  - Export `features.csv` for model training
- **Tools:** `pandas`, `scikit-learn.preprocessing`, feature engineering libraries

#### Agent E: Model Trainer
- **Role:** Machine Learning Model Developer
- **Goal:** Train and optimize predictive models
- **Tasks:**
  - Train multiple models:
    - **Random Forest Regressor**
    - **Gradient Boosting Regressor**
    - **XGBoost Regressor**
  - Hyperparameter tuning using GridSearchCV
  - Cross-validation (K-Fold, 5 folds)
  - Select best model based on validation metrics
  - Export `model.pkl` (serialized trained model)
- **Tools:** `scikit-learn`, `xgboost`, `joblib`

#### Agent F: Model Evaluator
- **Role:** Model Performance & Quality Assurance Expert
- **Goal:** Evaluate model performance and generate reports
- **Tasks:**
  - Calculate evaluation metrics:
    - **RMSE** (Root Mean Squared Error)
    - **MAE** (Mean Absolute Error)
    - **R²** (R-squared score)
    - **MAPE** (Mean Absolute Percentage Error)
  - Generate `evaluation_report.md` with:
    - Model comparison table
    - Feature importance analysis
    - Residual plots
    - Business impact projections
  - Create `model_card.md` documenting:
    - Model architecture
    - Training data specifications
    - Performance benchmarks
    - Limitations and ethical considerations
- **Tools:** `scikit-learn.metrics`, visualization libraries

---

## 🔄 CrewAI Flow - Orchestration Layer

The **Flow** coordinates execution between the two crews with validation checkpoints:

```
┌─────────────────────────────────────────────────────────────┐
│                    FleetGuard AI Flow                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  PHASE 1: Data Analyst Crew           │
        │  ┌─────────────────────────────────┐  │
        │  │ Agent A: Data Ingestion         │  │
        │  │ → Load & validate data          │  │
        │  │ → Create dataset_contract.json  │  │
        │  └─────────────────────────────────┘  │
        │               ▼                       │
        │  ┌─────────────────────────────────┐  │
        │  │ Agent B: EDA                    │  │
        │  │ → Generate eda_report.html      │  │
        │  │ → Identify patterns             │  │
        │  └─────────────────────────────────┘  │
        │               ▼                       │
        │  ┌─────────────────────────────────┐  │
        │  │ Agent C: Business Insights      │  │
        │  │ → Strategic recommendations     │  │
        │  │ → Dashboard metrics             │  │
        │  └─────────────────────────────────┘  │
        └───────────────────────────────────────┘
                            │
                   ✓ Validation Checkpoint
                   (Dataset Contract)
                            ▼
        ┌───────────────────────────────────────┐
        │  PHASE 2: Data Scientist Crew         │
        │  ┌─────────────────────────────────┐  │
        │  │ Agent D: Feature Engineering    │  │
        │  │ → Create features.csv           │  │
        │  │ → Feature selection             │  │
        │  └─────────────────────────────────┘  │
        │               ▼                       │
        │  ┌─────────────────────────────────┐  │
        │  │ Agent E: Model Training         │  │
        │  │ → Train RF, GBM, XGBoost        │  │
        │  │ → Export model.pkl              │  │
        │  └─────────────────────────────────┘  │
        │               ▼                       │
        │  ┌─────────────────────────────────┐  │
        │  │ Agent F: Model Evaluation       │  │
        │  │ → Generate evaluation_report.md │  │
        │  │ → Create model_card.md          │  │
        │  └─────────────────────────────────┘  │
        └───────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  Final Outputs:       │
                │  • Trained model      │
                │  • Reports            │
                │  • Predictions        │
                └───────────────────────┘
```

### Flow Implementation (Pseudocode)

```python
from crewai_tools import Flow

class FleetGuardFlow(Flow):

    @start()
    def run_data_analysis(self):
        """Phase 1: Data Analyst Crew"""
        analyst_crew = DataAnalystCrew()
        results = analyst_crew.kickoff()

        # Validate dataset contract
        if not self.validate_contract(results['dataset_contract']):
            raise Exception("Dataset contract validation failed")

        return results

    @listen("run_data_analysis")
    def run_data_science(self, analyst_results):
        """Phase 2: Data Scientist Crew"""
        scientist_crew = DataScientistCrew(
            input_data=analyst_results['cleaned_data']
        )
        results = scientist_crew.kickoff()

        # Validate model performance
        if results['model_metrics']['r2'] < 0.7:
            self.log_warning("Model R² below threshold")

        return results

    @listen("run_data_science")
    def generate_final_report(self, science_results):
        """Generate comprehensive report"""
        return {
            'model': science_results['model'],
            'metrics': science_results['model_metrics'],
            'business_impact': self.calculate_business_impact(science_results)
        }
```

---

## 📊 Predictive Model Specification

### Problem Statement
**Predict monthly maintenance cost per vehicle** to enable:
- Proactive budget planning
- Early identification of problematic vehicles
- Optimal timing for vehicle replacement

### Target Variable
`monthly_maintenance_cost` (continuous, in ₪)

### Features (Engineered)
1. **vehicle_age_years** - Vehicle age in years
2. **total_km** - Total kilometers driven
3. **avg_cost_per_service** - Average cost per maintenance visit
4. **service_frequency_rate** - Number of services per month
5. **km_per_month** - Average monthly kilometers
6. **days_since_last_service** - Recency indicator
7. **workshop_encoded** - Categorical encoding of workshop
8. **vehicle_model_encoded** - Categorical encoding of model
9. **season** - Time-based feature (winter has higher costs)

### Model Candidates
1. **Random Forest Regressor**
   - Handles non-linear relationships
   - Robust to outliers
   - Feature importance built-in

2. **Gradient Boosting Regressor**
   - Higher accuracy potential
   - Better for complex patterns
   - Sequential error correction

3. **XGBoost**
   - Optimized gradient boosting
   - Fast training
   - Regularization to prevent overfitting

### Evaluation Metrics
- **RMSE** < ₪500 (acceptable prediction error)
- **R²** > 0.75 (explains 75%+ variance)
- **MAE** < ₪400 (average error tolerance)
- **MAPE** < 15% (relative error threshold)

### Success Criteria
- Model achieves R² > 0.75 on test set
- Predictions enable 20% reduction in budget surprises
- Feature importance aligns with business intuition

---

## 🛠️ Technology Stack

### Core Frameworks
- **CrewAI** (>= 0.86.0) - Multi-agent orchestration
- **CrewAI Tools** - Flow coordination
- **Python 3.11+** - Development language

### Data Processing
- **pandas** - Data manipulation
- **numpy** - Numerical operations
- **ydata-profiling** - Automated EDA reports

### Machine Learning
- **scikit-learn** - Model training, preprocessing, metrics
- **xgboost** - Gradient boosting implementation
- **joblib** - Model serialization

### Visualization
- **plotly** - Interactive dashboards
- **matplotlib** - Static plots
- **seaborn** - Statistical visualizations

### Web Interface
- **Streamlit** - User interface
- **streamlit-option-menu** - Navigation

### Database & Storage
- **SQLite** - Data persistence
- **JSON** - Dataset contracts

### API Integration
- **OpenAI API** (GPT-4o-mini) - Agent intelligence
- **python-dotenv** - Configuration management

---

## 📁 Repository Structure

```
FleetGuardAI/
├── data/
│   ├── raw/
│   │   ├── vehicles.csv              # Vehicle master data
│   │   ├── invoices.csv              # Maintenance invoices
│   │   └── vehicle_template.csv      # Import template
│   ├── processed/
│   │   ├── features.csv              # Engineered features
│   │   └── dataset_contract.json     # Data schema & constraints
│   └── database/
│       └── fleet.db                  # SQLite database
│
├── src/
│   ├── crews/
│   │   ├── data_analyst_crew.py      # Crew 1 (3 agents)
│   │   ├── data_scientist_crew.py    # Crew 2 (3 agents) [NEW]
│   │   └── crew_flow.py              # Flow orchestrator [NEW]
│   │
│   ├── agents/
│   │   ├── data_ingestion_agent.py   # Agent A [NEW]
│   │   ├── eda_agent.py              # Agent B [NEW]
│   │   ├── insights_agent.py         # Agent C [NEW]
│   │   ├── feature_engineer_agent.py # Agent D [NEW]
│   │   ├── model_trainer_agent.py    # Agent E [NEW]
│   │   └── model_evaluator_agent.py  # Agent F [NEW]
│   │
│   ├── tools/
│   │   ├── data_validation_tool.py   # Schema validation
│   │   ├── feature_engineering_tool.py
│   │   └── model_evaluation_tool.py
│   │
│   ├── database_manager.py           # Database operations
│   ├── ai_engine.py                  # Chatbot engine
│   ├── chat_manager.py               # Conversation management
│   └── retirement_calculator.py      # Vehicle retirement logic
│
├── models/
│   ├── model.pkl                     # Trained model [OUTPUT]
│   └── model_card.md                 # Model documentation [OUTPUT]
│
├── reports/
│   ├── eda_report.html               # Exploratory data analysis [OUTPUT]
│   ├── evaluation_report.md          # Model performance [OUTPUT]
│   └── business_impact_summary.pdf   # Executive summary
│
├── docs/
│   ├── CHATBOT_UPGRADE_GUIDE.md      # Chatbot documentation
│   ├── QUICK_START_GUIDE.md          # User guide
│   └── API_DOCUMENTATION.md          # API reference
│
├── tests/
│   ├── test_data_validation.py
│   ├── test_model_training.py
│   └── test_flow_orchestration.py
│
├── main.py                           # Streamlit application
├── requirements.txt                  # Dependencies
├── .env.example                      # Environment template
├── README.md                         # Project overview
├── PROJECT_PROPOSAL_HE.md            # Hebrew proposal
└── PROJECT_PROPOSAL_EN.md            # English proposal (this file)
```

---

## 📋 Dataset Contract Example

**File:** `data/processed/dataset_contract.json`

```json
{
  "contract_version": "1.0.0",
  "created_at": "2025-12-15T10:00:00Z",
  "dataset_name": "fleet_maintenance_data",

  "schema": {
    "vehicles": {
      "vehicle_id": {
        "type": "string",
        "pattern": "^VH-\\d{2}$",
        "nullable": false,
        "description": "Unique vehicle identifier"
      },
      "plate": {
        "type": "string",
        "nullable": false,
        "description": "License plate number"
      },
      "model": {
        "type": "string",
        "enum": ["Toyota Corolla", "Ford Transit", "Hyundai i20", "Mazda CX-5"],
        "nullable": false
      },
      "purchase_date": {
        "type": "date",
        "format": "YYYY-MM-DD",
        "nullable": false
      },
      "total_km": {
        "type": "integer",
        "min": 0,
        "max": 500000,
        "nullable": false
      },
      "assigned_to": {
        "type": "string",
        "nullable": true,
        "description": "Driver name"
      }
    },

    "invoices": {
      "invoice_no": {
        "type": "string",
        "nullable": false,
        "unique": true
      },
      "date": {
        "type": "date",
        "format": "YYYY-MM-DD",
        "nullable": false
      },
      "vehicle_id": {
        "type": "string",
        "foreign_key": "vehicles.vehicle_id",
        "nullable": false
      },
      "workshop": {
        "type": "string",
        "nullable": false
      },
      "amount": {
        "type": "float",
        "min": 0,
        "max": 50000,
        "nullable": false,
        "currency": "ILS"
      },
      "service_type": {
        "type": "string",
        "nullable": false
      }
    }
  },

  "constraints": {
    "data_quality": {
      "max_null_percentage": 5,
      "max_duplicate_percentage": 1
    },
    "business_rules": {
      "vehicle_retirement_age_years": 7,
      "max_monthly_cost_threshold": 3000,
      "min_records_per_vehicle": 3
    }
  },

  "assumptions": {
    "currency": "ILS (Israeli Shekel)",
    "date_range": "2019-01-01 to 2024-12-31",
    "geographic_scope": "Israel",
    "maintenance_includes": ["repairs", "regular_service", "parts_replacement"],
    "excluded_costs": ["fuel", "insurance", "tolls"]
  },

  "validation_rules": [
    {
      "rule": "purchase_date must be before first invoice date",
      "severity": "error"
    },
    {
      "rule": "total_km should increase over time for each vehicle",
      "severity": "warning"
    },
    {
      "rule": "vehicle_id in invoices must exist in vehicles table",
      "severity": "error"
    }
  ]
}
```

---

## 🎯 Expected Deliverables

### ✅ Code & Implementation
- [ ] `src/crews/data_scientist_crew.py` - Crew 2 implementation
- [ ] `src/crew_flow.py` - Flow orchestrator
- [ ] 6 agent files (3 new for Crew 2)
- [ ] `tests/` directory with unit tests
- [ ] Clean, documented, PEP8-compliant code

### ✅ Output Files
- [ ] `data/processed/dataset_contract.json` - Data schema
- [ ] `data/processed/features.csv` - Engineered features
- [ ] `models/model.pkl` - Trained model
- [ ] `reports/eda_report.html` - EDA report (ydata-profiling)
- [ ] `reports/evaluation_report.md` - Model metrics
- [ ] `models/model_card.md` - Model documentation

### ✅ Repository Quality
- [ ] Organized folder structure (as specified above)
- [ ] `README.md` with setup instructions
- [ ] `requirements.txt` with all dependencies
- [ ] `.env.example` for configuration
- [ ] Clear commit messages
- [ ] Feature branches + Pull Requests (at least 3 PRs)
- [ ] Code reviews documented in PR comments

### ✅ Documentation
- [ ] Technical documentation for all agents
- [ ] Flow execution guide
- [ ] Dataset contract explanation
- [ ] Model usage instructions
- [ ] Business impact summary

### ✅ Presentation Materials
- [ ] **Slide Deck** (10-12 slides):
  1. Title + Team
  2. Business Problem
  3. Solution Overview
  4. System Architecture (2 Crews)
  5. CrewAI Flow Diagram
  6. Data Pipeline
  7. Model Performance
  8. Business Impact
  9. Demo Screenshots
  10. Future Roadmap
  11. Q&A

- [ ] **Demo Video** (≤5 minutes):
  - Problem introduction (30 sec)
  - Live system walkthrough (2 min)
  - Agent execution demonstration (1 min)
  - Model prediction showcase (1 min)
  - Business value summary (30 sec)

---

## 📅 Project Timeline

### Week 1: Crew 2 Foundation
- **Days 1-2:** Implement Agents D, E, F
- **Days 3-4:** Build `data_scientist_crew.py`
- **Days 5-7:** Testing and validation

### Week 2: Flow Integration
- **Days 1-3:** Implement `crew_flow.py`
- **Days 4-5:** Integration testing (Crew 1 → Crew 2)
- **Days 6-7:** Dataset contract creation

### Week 3: Model Development
- **Days 1-3:** Feature engineering and model training
- **Days 4-5:** Model evaluation and tuning
- **Days 6-7:** Generate reports (EDA, evaluation, model card)

### Week 4: Documentation & Presentation
- **Days 1-2:** Code cleanup and documentation
- **Days 3-4:** Create slide deck
- **Days 5-6:** Record demo video
- **Day 7:** Final review and submission

---

## 🎯 Success Criteria

### Technical Metrics
- ✅ All 6 agents execute successfully
- ✅ Flow completes without errors
- ✅ Model achieves R² > 0.75
- ✅ All required files generated
- ✅ Code passes 90%+ test coverage
- ✅ Dataset contract validates without errors

### Business Metrics
- ✅ Predicts maintenance costs within ±₪500
- ✅ Identifies 90%+ of vehicles needing replacement
- ✅ Reduces budget surprises by 20%
- ✅ Dashboard used daily by fleet managers

### Academic Metrics
- ✅ Meets 100% of instructor requirements
- ✅ Demonstrates CrewAI multi-agent coordination
- ✅ Shows proper ML workflow (train/test split, validation)
- ✅ Professional documentation and presentation
- ✅ GitHub repository with proper PR workflow

---

## 🌟 Unique Selling Points

1. **Real-World Business Impact:** Solves actual fleet management pain points, not a toy dataset
2. **Advanced Multi-Agent System:** 6 specialized agents with clear role separation
3. **Full ML Pipeline:** From data ingestion to deployed model with monitoring
4. **Production-Ready:** Includes validation, error handling, and data contracts
5. **Interactive Dashboard:** Streamlit UI for non-technical users
6. **Strategic AI Chatbot:** Natural language interface for fleet insights

---

## 📞 Support & Contact

**Project Repository:** `https://github.com/[username]/FleetGuardAI`
**Documentation:** See `/docs` folder
**Demo Video:** [YouTube link to be added]

---

## 📄 License

This project is submitted as part of **[Course Name]** final project requirements.

**Created by:** [Your Name]
**Instructor:** [Instructor Name]
**Institution:** [University/College Name]
**Date:** December 2025

---

**END OF PROPOSAL**
