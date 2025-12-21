# Model Card - FleetGuard AI Maintenance Cost Predictor

## Model Details

### Purpose
This model predicts monthly maintenance costs for fleet vehicles to enable proactive budgeting and optimize maintenance resource allocation.

### Model Type
- **Algorithm**: Gradient Boosting Regressor
- **Framework**: scikit-learn 1.8.0
- **Task**: Regression (Continuous Cost Prediction)
- **Created**: December 17, 2025
- **Version**: 1.0

### Developers
- **Organization**: FleetGuard AI
- **Project Type**: Academic Final Project - Data Science and Machine Learning
- **Contact**: [Project Repository]

---

## Training Data Summary

### Dataset Description
- **Source**: Fleet management database with vehicle and invoice records
- **Size**: 86 total records (68 training, 18 test samples)
- **Split Ratio**: 80% training, 20% testing
- **Time Period**: Historical vehicle maintenance data
- **Geographic Scope**: Single fleet organization

### Features (11 total)
1. **vehicle_age_years**: Age of vehicle in years
2. **current_km**: Current odometer reading
3. **total_km_driven**: Total kilometers driven since purchase
4. **total_services**: Cumulative number of maintenance services
5. **avg_cost_per_service**: Historical average service cost per vehicle
6. **service_frequency_rate**: Services per month rate
7. **km_per_month**: Average monthly mileage
8. **days_since_last_service**: Days elapsed since last maintenance
9. **months_since_purchase**: Vehicle tenure in months
10. **make_model_encoded**: Vehicle make/model (label encoded)
11. **assigned_to_encoded**: Driver assignment (label encoded)

### Target Variable
- **monthly_maintenance_cost**: Predicted monthly maintenance cost in ILS (Israeli Shekels)

### Data Processing
- Missing values handled via interpolation and forward-fill
- Outliers detected using IQR method and Z-score analysis
- Features engineered from raw vehicle and invoice data
- Label encoding applied to categorical variables (make_model, assigned_to)

---

## Performance Metrics

### Training Performance
- **R² Score**: 0.9999 (99.99% variance explained)
- **Note**: Near-perfect training performance suggests potential overfitting on small dataset

### Test Performance
- **R² Score**: 0.9688 (96.88% variance explained)
- **RMSE**: ₪16.24 (Root Mean Squared Error)
- **MAE**: ₪11.49 (Mean Absolute Error)

### Interpretation
- The model explains 96.9% of cost variance in unseen data
- Average prediction error: ±₪11.49 per month
- Typical cost predictions are accurate within ±₪16.24 range
- Performance deemed **excellent** for budget planning purposes

### Validation Status
✅ Model ready for production deployment
✅ Suitable for accurate monthly budget allocation
✅ Low extreme errors - stable predictions

---

## Limitations

### Dataset Limitations
1. **Small Sample Size**: Only 86 records may not capture full variability
   - Limited generalization to other fleet types
   - Potential sensitivity to outliers

2. **Single Fleet Scope**: Trained on one organization's data
   - May not generalize to different industries (e.g., construction vs. delivery)
   - Regional differences in parts/labor costs not captured

3. **Temporal Limitations**: Historical data only
   - Cannot predict impacts of future market changes (inflation, parts shortages)
   - No seasonal patterns captured if data spans <12 months

### Model Limitations
4. **Overfitting Risk**: Near-perfect training R² (0.9999) vs test R² (0.9688)
   - 3% performance gap suggests slight overfitting
   - Recommendation: Gather more data for retraining

5. **Feature Engineering Dependencies**:
   - Requires all 11 features to be available at prediction time
   - Label encodings must match training data categories

6. **No Uncertainty Quantification**:
   - Point predictions only (no confidence intervals)
   - Cannot indicate when predictions are unreliable

### Use Case Limitations
7. **Not suitable for**:
   - Individual service cost prediction (only monthly aggregates)
   - Emergency/accident cost prediction (trained on routine maintenance)
   - Real-time decision making (requires batch processing)

---

## Ethical Considerations

### Bias and Fairness

#### Potential Biases Identified
1. **Vehicle Model Bias**:
   - Premium brands may have higher maintenance costs due to expensive parts
   - Risk: Model could perpetuate preference for certain brands even if alternatives are cost-effective
   - Mitigation: Feature importance analysis shows `make_model_encoded` impact

2. **Driver Assignment Bias**:
   - Model includes `assigned_to_encoded` feature
   - Risk: Could unfairly attribute high costs to specific drivers without considering vehicle condition or usage patterns
   - Mitigation: Predictions should not be used for driver performance evaluation without contextual analysis

3. **Historical Bias**:
   - If past data reflects inefficient maintenance practices or poor vendor pricing, model will learn these patterns
   - Risk: Perpetuating suboptimal spending patterns
   - Mitigation: Regular model retraining as maintenance practices improve

#### Fairness Considerations
- **Geographic Fairness**: Model trained on single location's pricing - not fair to apply to regions with different labor/parts costs
- **Vehicle Age Fairness**: May underpredict costs for very old vehicles (if training data skewed toward newer fleet)

### Privacy

#### Data Privacy Measures
1. **Personal Information**:
   - Driver names encoded as integers (not reversible without mapping file)
   - No personally identifiable information (PII) stored in model
   - License plate numbers not included in model features

2. **Data Storage**:
   - Model file (`model.pkl`) contains no raw personal data
   - Training data (`features.csv`) should be access-controlled
   - Metadata files contain only statistical summaries

#### Privacy Risks
- **Re-identification Risk**: Low - encoded driver IDs alone cannot identify individuals
- **Data Leakage**: Model predictions could indirectly reveal driver identities if combined with external information

### Responsible Use Cases

#### Intended Use Cases ✅
1. **Budget Planning**: Forecasting monthly maintenance expenses for financial planning
2. **Resource Allocation**: Identifying vehicles likely to need higher maintenance budgets
3. **Fleet Optimization**: Informing vehicle replacement decisions based on predicted cost trends
4. **Vendor Negotiation**: Using cost predictions to evaluate service provider pricing

#### Prohibited Use Cases ❌
1. **Driver Discrimination**: DO NOT use predictions to penalize or fire drivers
   - Costs may be due to vehicle age, not driver behavior
   - Requires comprehensive investigation before personnel decisions

2. **Insurance Underwriting**: DO NOT use to deny coverage or adjust premiums
   - Model not calibrated for risk assessment
   - May violate insurance regulations

3. **Punitive Actions**: DO NOT use to justify reduced vehicle maintenance
   - Predictions are for planning, not justification to cut safety spending

4. **Automated Decision-Making**: DO NOT use without human oversight
   - Model has limitations and requires contextual judgment

### Accountability

#### Responsible Parties
1. **Model Developers**: FleetGuard AI team
   - Responsible for documenting limitations and biases
   - Obligation to provide model updates and retraining guidance

2. **Deployment Team**: Fleet Management Organization
   - Responsible for ensuring predictions used ethically
   - Must provide human oversight for all cost-related decisions

3. **End Users**: Fleet Managers and Financial Planners
   - Must understand model limitations
   - Should challenge predictions that seem unreasonable
   - Obligated to report unintended consequences

#### Monitoring and Auditing
- **Performance Monitoring**: Track prediction errors monthly to detect drift
- **Bias Audits**: Quarterly analysis of predictions by vehicle type and driver
- **Feedback Loop**: Collect user reports of unfair or inaccurate predictions
- **Retraining Cadence**: Retrain model every 6 months with new data

#### Dispute Resolution
- Users can request explanation for any prediction
- Feature importance charts provided in dashboard for transparency
- Appeals process: Manual review by fleet manager with domain expertise

### Societal Impact

#### Positive Impacts
- **Cost Efficiency**: Helps organizations optimize budgets, freeing resources for other needs
- **Predictive Maintenance**: Enables proactive maintenance, improving vehicle safety
- **Data-Driven Decisions**: Reduces arbitrary decision-making in fleet management

#### Negative Impacts
- **Job Displacement Risk**: Automation of cost forecasting could reduce demand for manual budget analysts
- **Over-Reliance on AI**: Users may trust predictions blindly without critical thinking
- **Vendor Impact**: Predictive cost models could pressure maintenance providers to lower prices unsustainably

### Transparency Commitments

1. **Model Explainability**:
   - Feature importance charts included in dashboard
   - Users can see which factors drive predictions

2. **Documentation**:
   - This model card provides full transparency on training, performance, and limitations
   - Evaluation reports available in `reports/evaluation_report.md`

3. **Open Questions**:
   - How to handle predictions for new vehicle models not in training data?
   - Should model exclude `assigned_to_encoded` to prevent driver bias?
   - What is acceptable prediction error threshold for financial planning?

---

## How to Use This Model

### Requirements
```bash
pip install scikit-learn==1.8.0 pandas numpy joblib
```

### Loading the Model
```python
import joblib
model = joblib.load('models/model.pkl')
```

### Making Predictions
```python
import pandas as pd

# Prepare input features (must match training features)
features = pd.DataFrame([{
    'vehicle_age_years': 5,
    'current_km': 80000,
    'total_km_driven': 75000,
    'total_services': 12,
    'avg_cost_per_service': 850,
    'service_frequency_rate': 0.4,
    'km_per_month': 1200,
    'days_since_last_service': 45,
    'months_since_purchase': 60,
    'make_model_encoded': 2,
    'assigned_to_encoded': 1
}])

# Predict monthly maintenance cost
prediction = model.predict(features)
print(f"Predicted monthly cost: ₪{prediction[0]:.2f}")
```

### Interpretation Guidelines
1. Compare prediction to historical average for context
2. Consider ±₪11.49 MAE as uncertainty margin
3. Investigate if prediction deviates >30% from historical costs
4. Do not use predictions in isolation - combine with domain expertise

---

## Model Maintenance

### Retraining Triggers
- New data available (recommended: every 6 months)
- Prediction accuracy degrades >20% MAE increase
- Fleet composition changes significantly (new vehicle types)
- Major market changes (e.g., parts price inflation)

### Versioning
- Current version: 1.0 (December 17, 2025)
- Track R² and RMSE for each retrained version
- Document feature changes in model metadata

### Deprecation Policy
- Model will be deprecated if:
  - Test R² falls below 0.85
  - MAE exceeds ₪25
  - Newer model architecture shows >15% improvement

---

## Contact and Feedback

For questions, concerns, or to report unintended model behavior:
- **Technical Issues**: Contact FleetGuard AI development team
- **Ethical Concerns**: Report to project supervisor or ethics committee
- **Data Errors**: Submit feedback via dashboard or data management portal

---

**Last Updated**: December 17, 2025
**Model Card Version**: 1.0
**Compliance**: Follows best practices from Model Cards for Model Reporting (Mitchell et al., 2019)
