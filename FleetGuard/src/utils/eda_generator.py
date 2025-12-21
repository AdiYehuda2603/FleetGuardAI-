"""
EDA Generator - Agent B/C Logic
Generates comprehensive exploratory data analysis HTML reports
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

try:
    from src.database_manager import DatabaseManager
except ImportError:
    from database_manager import DatabaseManager


class EDAGenerator:
    """
    Generates comprehensive EDA reports for fleet maintenance data
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.insights = {}

    def generate_report(self, df=None, output_path=None, include_profiling=False):
        """
        Generate comprehensive EDA HTML report

        Args:
            df: pandas DataFrame (uses database if None)
            output_path: Path to save HTML report (auto-generates if None)
            include_profiling: Whether to include ydata-profiling report (slower)

        Returns:
            tuple: (report_path, insights_dict)
        """
        # Load data if not provided
        if df is None:
            df_invoices = self.db.get_all_invoices()
            df_vehicles = self.db.get_vehicle_with_stats()
        else:
            df_invoices = df
            df_vehicles = self.db.get_vehicle_with_stats()

        # Perform analysis
        self._analyze_distributions(df_invoices)
        self._identify_anomalies(df_invoices)
        self._workshop_comparison(df_invoices)
        self._temporal_analysis(df_invoices)
        self._vehicle_analysis(df_vehicles)

        # Generate HTML report
        html_content = self._build_html_report(df_invoices, df_vehicles)

        # Save report
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            output_path = os.path.join(base_dir, "data", "reports", f"eda_report_{timestamp}.html")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Optionally add ydata-profiling
        if include_profiling:
            try:
                from ydata_profiling import ProfileReport
                profile = ProfileReport(df_invoices, title="FleetGuard Data Profile", explorative=True)
                profile_path = output_path.replace('.html', '_profile.html')
                profile.to_file(profile_path)
                self.insights['profile_report_path'] = profile_path
            except ImportError:
                self.insights['profile_warning'] = "ydata-profiling not installed - skipping detailed profile"

        return output_path, self.insights

    def _analyze_distributions(self, df):
        """Analyze statistical distributions"""
        self.insights['distributions'] = {
            'total_invoices': len(df),
            'total_cost': df['total'].sum(),
            'mean_cost': df['total'].mean(),
            'median_cost': df['total'].median(),
            'std_cost': df['total'].std(),
            'min_cost': df['total'].min(),
            'max_cost': df['total'].max(),
            'cost_quartiles': df['total'].quantile([0.25, 0.5, 0.75]).to_dict()
        }

        # Odometer stats
        if 'odometer_km' in df.columns:
            self.insights['odometer'] = {
                'mean_km': df['odometer_km'].mean(),
                'median_km': df['odometer_km'].median(),
                'max_km': df['odometer_km'].max()
            }

    def _identify_anomalies(self, df):
        """Identify outliers and anomalies"""
        # Cost outliers using IQR method
        Q1 = df['total'].quantile(0.25)
        Q3 = df['total'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        anomalies = df[(df['total'] < lower_bound) | (df['total'] > upper_bound)]

        self.insights['anomalies'] = {
            'count': len(anomalies),
            'percentage': (len(anomalies) / len(df)) * 100,
            'high_cost_threshold': upper_bound,
            'high_cost_invoices': anomalies[anomalies['total'] > upper_bound].shape[0],
            'samples': anomalies.nlargest(5, 'total')[['invoice_no', 'vehicle_id', 'workshop', 'total']].to_dict('records')
        }

    def _workshop_comparison(self, df):
        """Compare workshops by cost and frequency"""
        workshop_stats = df.groupby('workshop').agg({
            'total': ['count', 'sum', 'mean', 'std'],
            'invoice_no': 'count'
        }).round(2)

        workshop_stats.columns = ['_'.join(col).strip() for col in workshop_stats.columns.values]

        self.insights['workshops'] = {
            'stats': workshop_stats.to_dict(),
            'ranking_by_cost': workshop_stats.sort_values('total_mean', ascending=False).index.tolist(),
            'most_used': workshop_stats.sort_values('total_count', ascending=False).index[0],
            'cheapest_avg': workshop_stats.sort_values('total_mean', ascending=True).index[0],
            'most_expensive_avg': workshop_stats.sort_values('total_mean', ascending=False).index[0]
        }

        # Cost variance analysis
        mean_cost = df['total'].mean()
        for workshop in df['workshop'].unique():
            workshop_mean = df[df['workshop'] == workshop]['total'].mean()
            diff_pct = ((workshop_mean - mean_cost) / mean_cost) * 100
            if abs(diff_pct) > 15:  # More than 15% difference
                if 'pricing_concerns' not in self.insights['workshops']:
                    self.insights['workshops']['pricing_concerns'] = []
                self.insights['workshops']['pricing_concerns'].append({
                    'workshop': workshop,
                    'avg_cost': workshop_mean,
                    'deviation_from_mean': diff_pct
                })

    def _temporal_analysis(self, df):
        """Analyze trends over time"""
        df['date'] = pd.to_datetime(df['date'])

        # Monthly aggregation
        monthly = df.set_index('date').resample('M').agg({
            'total': ['sum', 'count', 'mean']
        }).round(2)

        self.insights['temporal'] = {
            'date_range': f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}",
            'months_covered': len(monthly),
            'monthly_avg_cost': monthly[('total', 'sum')].mean(),
            'busiest_month': monthly[('total', 'count')].idxmax().strftime('%Y-%m'),
            'most_expensive_month': monthly[('total', 'sum')].idxmax().strftime('%Y-%m')
        }

    def _vehicle_analysis(self, df_vehicles):
        """Analyze vehicle fleet statistics"""
        if df_vehicles is None or df_vehicles.empty:
            return

        self.insights['vehicles'] = {
            'total_vehicles': len(df_vehicles),
            'avg_age': (datetime.now().year - df_vehicles['year'].mean()),
            'avg_km': df_vehicles['current_km'].mean() if 'current_km' in df_vehicles.columns else None,
            'total_services': df_vehicles['total_services'].sum() if 'total_services' in df_vehicles.columns else None,
            'high_cost_vehicles': df_vehicles.nlargest(5, 'total_cost')[['vehicle_id', 'make_model', 'total_cost']].to_dict('records') if 'total_cost' in df_vehicles.columns else []
        }

    def _build_html_report(self, df_invoices, df_vehicles):
        """Build HTML report content"""

        html = f"""
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FleetGuard EDA Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            direction: rtl;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }}
        h1 {{
            color: #667eea;
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        h2 {{
            color: #764ba2;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 40px;
        }}
        h3 {{
            color: #555;
            margin-top: 25px;
        }}
        .summary-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .metric {{
            display: inline-block;
            margin: 15px 20px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .insight-box {{
            background: #f8f9fa;
            border-left: 5px solid #667eea;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .warning-box {{
            background: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .danger-box {{
            background: #f8d7da;
            border-left: 5px solid #dc3545;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #888;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚛 FleetGuard - דוח ניתוח נתונים (EDA)</h1>
        <p style="text-align: center; color: #888;">נוצר ב-{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <!-- Summary -->
        <div class="summary-box">
            <div class="metric">
                <div class="metric-value">{self.insights['distributions']['total_invoices']:,}</div>
                <div class="metric-label">סה"כ חשבוניות</div>
            </div>
            <div class="metric">
                <div class="metric-value">₪{self.insights['distributions']['total_cost']:,.0f}</div>
                <div class="metric-label">סה"כ הוצאות</div>
            </div>
            <div class="metric">
                <div class="metric-value">₪{self.insights['distributions']['mean_cost']:,.0f}</div>
                <div class="metric-label">ממוצע לחשבונית</div>
            </div>
            <div class="metric">
                <div class="metric-value">{self.insights['vehicles']['total_vehicles']}</div>
                <div class="metric-label">רכבים בצי</div>
            </div>
        </div>

        <!-- Cost Analysis -->
        <h2>📊 ניתוח עלויות</h2>
        <div class="insight-box">
            <strong>התפלגות עלויות:</strong>
            <ul>
                <li>ממוצע: ₪{self.insights['distributions']['mean_cost']:,.2f}</li>
                <li>חציון: ₪{self.insights['distributions']['median_cost']:,.2f}</li>
                <li>סטיית תקן: ₪{self.insights['distributions']['std_cost']:,.2f}</li>
                <li>טווח: ₪{self.insights['distributions']['min_cost']:,.2f} - ₪{self.insights['distributions']['max_cost']:,.2f}</li>
            </ul>
        </div>

        <!-- Anomalies -->
        <h2>⚠️ חריגות ואנומליות</h2>
        <div class="{"warning-box" if self.insights['anomalies']['count'] > 0 else "insight-box"}">
            <strong>זוהו {self.insights['anomalies']['count']} חריגות ({self.insights['anomalies']['percentage']:.1f}% מהחשבוניות)</strong>
            <p>סף לעלות גבוהה: ₪{self.insights['anomalies']['high_cost_threshold']:,.2f}</p>
            <p>חשבוניות עם עלות חריגה: {self.insights['anomalies']['high_cost_invoices']}</p>
        </div>

        {"".join([f'''
        <div class="danger-box">
            <strong>🔴 חשבונית חריגה:</strong> {sample['invoice_no']} - רכב {sample['vehicle_id']}
            במוסך {sample['workshop']} - סכום: ₪{sample['total']:,.2f}
        </div>
        ''' for sample in self.insights['anomalies']['samples'][:3]])}

        <!-- Workshop Comparison -->
        <h2>🔧 השוואת מוסכים</h2>
        <div class="insight-box">
            <strong>מסקנות:</strong>
            <ul>
                <li>מוסך הכי נפוץ: <strong>{self.insights['workshops']['most_used']}</strong></li>
                <li>מוסך עם ממוצע הכי זול: <strong>{self.insights['workshops']['cheapest_avg']}</strong></li>
                <li>מוסך עם ממוצע הכי יקר: <strong>{self.insights['workshops']['most_expensive_avg']}</strong></li>
            </ul>
        </div>

        {"".join([f'''
        <div class="warning-box">
            <strong>⚡ התראת תמחור:</strong> מוסך "{concern['workshop']}"
            סוטה {concern['deviation_from_mean']:.1f}% מהממוצע (ממוצע: ₪{concern['avg_cost']:,.2f})
        </div>
        ''' for concern in self.insights['workshops'].get('pricing_concerns', [])]) if 'pricing_concerns' in self.insights['workshops'] else ""}

        <h3>סטטיסטיקות מוסכים:</h3>
        <table>
            <thead>
                <tr>
                    <th>מוסך</th>
                    <th>מספר טיפולים</th>
                    <th>סה"כ הוצאות</th>
                    <th>ממוצע לטיפול</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f'''
                <tr>
                    <td>{workshop}</td>
                    <td>{int(stats['total_count'])}</td>
                    <td>₪{stats['total_sum']:,.2f}</td>
                    <td>₪{stats['total_mean']:,.2f}</td>
                </tr>
                ''' for workshop, stats in [(k, {kk.split('_')[1]: v for kk, v in vv.items()}) for k, vv in self.insights['workshops']['stats'].items()]])}
            </tbody>
        </table>

        <!-- Temporal Analysis -->
        <h2>📈 ניתוח זמני</h2>
        <div class="insight-box">
            <strong>טווח תאריכים:</strong> {self.insights['temporal']['date_range']}<br>
            <strong>חודשים מכוסים:</strong> {self.insights['temporal']['months_covered']}<br>
            <strong>ממוצע חודשי:</strong> ₪{self.insights['temporal']['monthly_avg_cost']:,.2f}<br>
            <strong>החודש העמוס ביותר:</strong> {self.insights['temporal']['busiest_month']}<br>
            <strong>החודש היקר ביותר:</strong> {self.insights['temporal']['most_expensive_month']}
        </div>

        <!-- Vehicle Analysis -->
        <h2>🚗 ניתוח רכבים</h2>
        <div class="insight-box">
            <strong>סה"כ רכבים בצי:</strong> {self.insights['vehicles']['total_vehicles']}<br>
            <strong>גיל ממוצע:</strong> {self.insights['vehicles']['avg_age']:.1f} שנים<br>
            {"<strong>קילומטרז' ממוצע:</strong> " + f"{self.insights['vehicles']['avg_km']:,.0f} ק\"מ<br>" if self.insights['vehicles']['avg_km'] else ""}
            {"<strong>סה\"כ טיפולים:</strong> " + f"{int(self.insights['vehicles']['total_services'])}<br>" if self.insights['vehicles']['total_services'] else ""}
        </div>

        <h3>רכבים עם הוצאות גבוהות:</h3>
        <table>
            <thead>
                <tr>
                    <th>רכב</th>
                    <th>דגם</th>
                    <th>סה"כ הוצאות</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f'''
                <tr>
                    <td>{vehicle['vehicle_id']}</td>
                    <td>{vehicle['make_model']}</td>
                    <td>₪{vehicle['total_cost']:,.2f}</td>
                </tr>
                ''' for vehicle in self.insights['vehicles']['high_cost_vehicles']])}
            </tbody>
        </table>

        <!-- Footer -->
        <div class="footer">
            <p>🤖 נוצר אוטומטית על ידי FleetGuard Multi-Agent System (CrewAI)</p>
            <p>דוח זה מבוסס על {self.insights['distributions']['total_invoices']:,} חשבוניות ו-{self.insights['vehicles']['total_vehicles']} רכבים</p>
        </div>
    </div>
</body>
</html>
"""

        return html


# --- Testing ---
if __name__ == "__main__":
    generator = EDAGenerator()
    report_path, insights = generator.generate_report()

    print("\n" + "=" * 80)
    print("EDA REPORT GENERATED")
    print("=" * 80)
    print(f"\nReport saved to: {report_path}")
    print("\nKey Insights:")
    print(f"  Total Invoices: {insights['distributions']['total_invoices']}")
    print(f"  Total Cost: ₪{insights['distributions']['total_cost']:,.2f}")
    print(f"  Anomalies Found: {insights['anomalies']['count']}")
    print(f"  Cheapest Workshop: {insights['workshops']['cheapest_avg']}")
    print(f"  Most Expensive Workshop: {insights['workshops']['most_expensive_avg']}")
    print("\n" + "=" * 80)
