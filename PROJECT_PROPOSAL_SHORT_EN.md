# 📋 FleetGuard AI - Final Project Proposal

**Student:** [Full Name]
**Institution:** [University/College Name]
**Course:** Data Science & AI - Final Project
**Date:** December 2025

---

## 🎯 Project Objective

**FleetGuard AI** - An intelligent fleet management system combining Data Analytics and Machine Learning to optimize maintenance costs and enable strategic decision-making.

**Predictive Model:** Forecasting monthly maintenance costs per vehicle (`monthly_maintenance_cost`)

---

## 🏢 Business Background

### The Problem
Organizations manage vehicle fleets without predictive capabilities, leading to:
- 💸 Unexpected maintenance costs
- ⚠️ Sudden failures and downtime
- ❓ Vehicle replacement decisions without data

### The Solution
Historical analysis of maintenance invoices, vehicle characteristics, and driver performance using:
- **Crew 1 (Data Analyst)** - Data analysis and business insights
- **Crew 2 (Data Scientist)** - ML model for cost prediction
- **CrewAI Flow** - Automated coordination between crews

### Business Value
✅ 15-25% savings in maintenance costs
✅ Prevention of unexpected failures
✅ Data-driven decisions

---

## 🤖 System Architecture

### **Crew 1 — Data Analyst Crew (3 Agents)**

| Agent | Role | Key Tasks |
|-------|------|-----------|
| **Agent A** | Data Ingestion Specialist | Load data, validation, create Dataset Contract |
| **Agent B** | Exploratory Data Analyst | EDA, generate `eda_report.html`, identify patterns |
| **Agent C** | Business Insights Generator | Business recommendations, model rankings, identify vehicles for replacement |

### **Crew 2 — Data Scientist Crew (3 Agents)**

| Agent | Role | Key Tasks |
|-------|------|-----------|
| **Agent D** | Feature Engineer | Create features (vehicle age, mileage, failure frequency) |
| **Agent E** | Model Trainer | Train models (Random Forest, XGBoost), Hyperparameter Tuning |
| **Agent F** | Model Evaluator | Performance evaluation (RMSE, R², MAE), generate reports |

### **CrewAI Flow - Workflow**

```
┌──────────────────────────────────────────────┐
│           FleetGuard AI Flow                 │
└──────────────────────────────────────────────┘
                    │
        ┌───────────▼────────────┐
        │  Crew 1: Data Analyst  │
        │  • Data Ingestion      │
        │  • EDA & Validation    │
        │  • Business Insights   │
        └───────────┬────────────┘
                    │
            ✓ Dataset Contract
                    │
        ┌───────────▼─────────────┐
        │ Crew 2: Data Scientist  │
        │  • Feature Engineering  │
        │  • Model Training       │
        │  • Model Evaluation     │
        └───────────┬─────────────┘
                    │
        ┌───────────▼─────────────┐
        │  Outputs:               │
        │  • model.pkl            │
        │  • Reports & Metrics    │
        └─────────────────────────┘
```

---

## 📊 Model Specification

**Problem:** Regression - Predict monthly maintenance costs

**Target Variable:** `monthly_maintenance_cost` (ILS ₪)

**Key Features:**
- `vehicle_age_years` - Vehicle age
- `total_km` - Total mileage
- `avg_cost_per_service` - Average cost per service
- `service_frequency_rate` - Service frequency
- `workshop_encoded` - Workshop encoding
- `vehicle_model_encoded` - Vehicle model encoding

**Models:**
1. Random Forest Regressor
2. Gradient Boosting Regressor
3. XGBoost (Recommended)

**Success Metrics:**
- R² > 0.75 (explains 75%+ variance)
- RMSE < ₪500 (prediction error)
- MAE < ₪400 (average error)

---

## 📁 Repository Structure

```
FleetGuardAI/
├── data/
│   ├── raw/                      # Raw data (vehicles.csv, invoices.csv)
│   ├── processed/
│   │   ├── features.csv          # Processed features
│   │   └── dataset_contract.json # Data schema
│   └── database/fleet.db         # SQLite DB
│
├── src/
│   ├── crews/
│   │   ├── data_analyst_crew.py      # Crew 1
│   │   ├── data_scientist_crew.py    # Crew 2 [NEW]
│   │   └── crew_flow.py              # Flow Orchestrator [NEW]
│   ├── agents/                       # 6 agents (3 existing + 3 new)
│   └── tools/                        # Shared tools
│
├── models/
│   ├── model.pkl                 # Trained model
│   └── model_card.md             # Documentation
│
├── reports/
│   ├── eda_report.html           # Automated EDA report
│   ├── evaluation_report.md      # Model evaluation
│   └── business_impact.pdf       # Business summary
│
├── tests/                        # Unit tests
├── main.py                       # Streamlit App
├── requirements.txt
└── README.md
```

---

## 🎯 Expected Deliverables

### Code & Implementation
- ✅ `data_scientist_crew.py` - Complete Crew 2
- ✅ `crew_flow.py` - Crew coordination
- ✅ 6 documented agent files
- ✅ Unit tests

### Output Files
- ✅ `dataset_contract.json` - Data contract
- ✅ `features.csv` - Processed features
- ✅ `model.pkl` - Trained model
- ✅ `eda_report.html` - EDA report (ydata-profiling)
- ✅ `evaluation_report.md` - Model performance
- ✅ `model_card.md` - Model documentation

### Documentation
- ✅ Detailed README with setup instructions
- ✅ Technical documentation for all agents
- ✅ GitHub with PR workflow (at least 3 PRs)

### Presentation & Demo
- ✅ **Presentation:** 10-12 slides (problem, solution, architecture, results)
- ✅ **Video:** ≤5 minutes (live demo + results)

---

## 🛠️ Technology Stack

**Frameworks:**
- CrewAI (>= 0.86.0) - Agent orchestration
- Python 3.11+

**Data Science:**
- pandas, numpy - Data processing
- scikit-learn, xgboost - ML
- ydata-profiling - Automated EDA

**Visualization:**
- Streamlit - User interface
- plotly, seaborn - Visualizations

**Database:**
- SQLite - Data storage

**AI:**
- OpenAI API (GPT-4o-mini) - Agent intelligence

---

## 📅 Timeline (4 Weeks)

| Week | Tasks | Outputs |
|------|-------|---------|
| **1** | Develop Crew 2 (3 agents) | Agents D, E, F + tests |
| **2** | Flow Integration + Dataset Contract | `crew_flow.py`, `dataset_contract.json` |
| **3** | Model training + reports | `model.pkl`, all reports |
| **4** | Documentation + presentation + video | Ready for submission |

---

## 🎯 Success Criteria

**Technical:**
- ✅ All 6 agents execute without errors
- ✅ Flow coordinates successfully (Crew 1 → Crew 2)
- ✅ R² > 0.75, RMSE < ₪500
- ✅ All required files generated

**Business:**
- ✅ Accurate cost prediction (±₪500)
- ✅ Identify 90%+ vehicles for replacement
- ✅ Expected 20% cost savings

**Academic:**
- ✅ Meet 100% instructor requirements
- ✅ Demonstrate multi-agent coordination
- ✅ Complete and professional ML workflow
- ✅ GitHub with PRs and code reviews

---

## 📋 Dataset Contract (Example)

```json
{
  "contract_version": "1.0.0",
  "dataset_name": "fleet_maintenance_data",
  "schema": {
    "vehicles": {
      "vehicle_id": {"type": "string", "pattern": "^VH-\\d{2}$"},
      "total_km": {"type": "integer", "min": 0, "max": 500000},
      "purchase_date": {"type": "date", "format": "YYYY-MM-DD"}
    },
    "invoices": {
      "amount": {"type": "float", "min": 0, "max": 50000, "currency": "ILS"},
      "vehicle_id": {"foreign_key": "vehicles.vehicle_id"}
    }
  },
  "constraints": {
    "max_null_percentage": 5,
    "vehicle_retirement_age_years": 7
  }
}
```

---

## 🌟 Unique Selling Points

1. **Real business problem** - Not an academic dataset
2. **6 specialized agents** - Clear role separation
3. **Complete ML pipeline** - Raw data to production model
4. **Interactive interface** - Streamlit Dashboard for non-technical users
5. **Strategic AI chatbot** - Natural language queries (Hebrew)

---

## 📞 Submission Details

**Repository:** `https://github.com/[username]/FleetGuardAI`
**Documentation:** `/docs` folder
**Demo Video:** [YouTube link]

**Created by:** [Full Name]
**Instructor:** [Instructor Name]
**Date:** December 2025

---

**END OF PROPOSAL**
