# -*- coding: utf-8 -*-
"""
Chat History & Project Templates Schema
הוספת טבלאות להיסטוריית שיחות ותבניות פרויקטים
"""

import sqlite3
import os
from datetime import datetime


class ChatHistorySchemaManager:
    def __init__(self, db_path=None):
        if db_path is None:
            current_file = os.path.abspath(__file__)
            base_dir = os.path.dirname(os.path.dirname(current_file))
            self.db_path = os.path.join(base_dir, "data", "database", "fleet.db")
        else:
            self.db_path = db_path

    def create_tables(self):
        """יוצר את הטבלאות החדשות"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # טבלה 1: שיחות (Conversations)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT,
            last_updated TEXT,
            message_count INTEGER DEFAULT 0,
            project_template_id TEXT,
            FOREIGN KEY (project_template_id) REFERENCES project_templates(template_id)
        )
        """)

        # טבלה 2: הודעות בשיחה (Messages)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
        )
        """)

        # טבלה 3: תבניות פרויקטים (Project Templates)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_templates (
            template_id TEXT PRIMARY KEY,
            template_name TEXT,
            description TEXT,
            template_type TEXT,
            configuration TEXT,
            created_at TEXT,
            last_used TEXT
        )
        """)

        conn.commit()
        conn.close()
        print("[SUCCESS] Chat history & project templates tables created!")

    def populate_default_templates(self):
        """ממלא תבניות ברירת מחדל"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        default_templates = [
            {
                'template_id': 'TPL-QUARTERLY',
                'template_name': 'דוח רבעוני',
                'description': 'דוח מקיף לרבעון - עלויות, תחזוקה, המלצות',
                'template_type': 'quarterly_report',
                'configuration': '''{
                    "date_range": "last_3_months",
                    "sections": [
                        "cost_summary",
                        "workshop_comparison",
                        "top_expenses",
                        "reliability_analysis",
                        "replacement_recommendations"
                    ],
                    "filters": {},
                    "prompt": "תן לי דוח רבעוני מלא: סיכום עלויות, השוואת מוסכים, 5 ההוצאות הגבוהות ביותר, ניתוח אמינות דגמים, והמלצות החלפה."
                }''',
                'created_at': datetime.now().isoformat(),
                'last_used': ''
            },
            {
                'template_id': 'TPL-ANNUAL',
                'template_name': 'דוח שנתי',
                'description': 'דוח שנתי מלא עם תובנות אסטרטגיות',
                'template_type': 'annual_report',
                'configuration': '''{
                    "date_range": "last_12_months",
                    "sections": [
                        "annual_cost_summary",
                        "cost_trends",
                        "vehicle_performance",
                        "workshop_analysis",
                        "strategic_recommendations",
                        "budget_forecast"
                    ],
                    "filters": {},
                    "prompt": "תן לי דוח שנתי מקיף: סיכום עלויות שנתי, מגמות לאורך זמן, ביצועי רכבים, ניתוח מוסכים, המלצות אסטרטגיות, ותחזית תקציב לשנה הבאה."
                }''',
                'created_at': datetime.now().isoformat(),
                'last_used': ''
            },
            {
                'template_id': 'TPL-MAINTENANCE',
                'template_name': 'דוח תחזוקה חודשי',
                'description': 'דוח תחזוקה מפורט לחודש',
                'template_type': 'monthly_maintenance',
                'configuration': '''{
                    "date_range": "last_month",
                    "sections": [
                        "maintenance_summary",
                        "by_vehicle",
                        "by_workshop",
                        "urgent_issues"
                    ],
                    "filters": {},
                    "prompt": "תן לי דוח תחזוקה חודשי: סיכום טיפולים, פירוט לפי רכב, פירוט לפי מוסך, ובעיות דחופות שדורשות טיפול."
                }''',
                'created_at': datetime.now().isoformat(),
                'last_used': ''
            },
            {
                'template_id': 'TPL-RETIREMENT',
                'template_name': 'תכנון גריטה',
                'description': 'ניתוח רכבים לגריטה והחלפה',
                'template_type': 'retirement_planning',
                'configuration': '''{
                    "date_range": "all",
                    "sections": [
                        "retirement_status",
                        "near_retirement_vehicles",
                        "replacement_budget",
                        "recommended_models"
                    ],
                    "filters": {},
                    "prompt": "תן לי ניתוח מלא לתכנון גריטה: סטטוס גריטה של הצי, רכבים קרובים לגריטה, תקציב מוערך להחלפה, ודגמים מומלצים לרכישה."
                }''',
                'created_at': datetime.now().isoformat(),
                'last_used': ''
            },
            {
                'template_id': 'TPL-COST-ANALYSIS',
                'template_name': 'ניתוח עלויות מעמיק',
                'description': 'ניתוח עלויות ואופטימיזציה',
                'template_type': 'cost_optimization',
                'configuration': '''{
                    "date_range": "last_6_months",
                    "sections": [
                        "cost_breakdown",
                        "cost_per_km",
                        "workshop_efficiency",
                        "optimization_opportunities"
                    ],
                    "filters": {},
                    "prompt": "תן לי ניתוח עלויות מעמיק: פירוט עלויות, עלות לקילומטר, יעילות מוסכים, והזדמנויות לחיסכון."
                }''',
                'created_at': datetime.now().isoformat(),
                'last_used': ''
            }
        ]

        for template in default_templates:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO project_templates
                    (template_id, template_name, description, template_type, configuration, created_at, last_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    template['template_id'],
                    template['template_name'],
                    template['description'],
                    template['template_type'],
                    template['configuration'],
                    template['created_at'],
                    template['last_used']
                ))
                print(f"[OK] Added template: {template['template_name']}")
            except Exception as e:
                print(f"[ERROR] Failed to add template {template['template_name']}: {e}")

        conn.commit()
        conn.close()
        print(f"[SUCCESS] Added {len(default_templates)} default templates!")


if __name__ == "__main__":
    manager = ChatHistorySchemaManager()
    print("Creating chat history & project templates tables...")
    manager.create_tables()
    print("\nAdding default project templates...")
    manager.populate_default_templates()
    print("\nAll done!")
