import sqlite3
import pandas as pd
import os

class DatabaseManager:
    def __init__(self, db_path=None):
        """
        מאתחל את החיבור לדאטה בייס.
        אם לא התקבל נתיב, הוא מנסה למצוא אותו אוטומטית לפי המבנה שלנו.
        """
        if db_path is None:
            # מציאת הנתיב הנכון - משתמש ב-__file__ כדי למצוא את תיקיית FleetGuard
            # __file__ הוא הנתיב של הקובץ הנוכחי (database_manager.py)
            current_file = os.path.abspath(__file__)
            # current_file = .../FleetGuard/src/database_manager.py
            # נרצה להגיע ל-.../FleetGuard/data/database/fleet.db
            
            # עלה 2 רמות: src -> FleetGuard
            base_dir = os.path.dirname(os.path.dirname(current_file))
            # base_dir = .../FleetGuard
            
            self.db_path = os.path.join(base_dir, "data", "database", "fleet.db")
            
            # אם עדיין לא נמצא, נסה נתיבים נוספים
            if not os.path.exists(self.db_path):
                # נסה נתיבים חלופיים
                alt_paths = [
                    # אם רץ מתוך FleetGuard
                    os.path.join(os.getcwd(), "data", "database", "fleet.db"),
                    # אם רץ מתוך FleetGuardAI
                    os.path.join(os.getcwd(), "FleetGuard", "data", "database", "fleet.db"),
                    # אם רץ מתוך src
                    os.path.join(os.path.dirname(os.getcwd()), "data", "database", "fleet.db"),
                ]
                for alt_path in alt_paths:
                    if os.path.exists(alt_path):
                        self.db_path = alt_path
                        break
        else:
            self.db_path = db_path

    def get_connection(self):
        """יוצר חיבור ל-SQLite"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"❌ Database not found at: {self.db_path}")
        return sqlite3.connect(self.db_path)

    def get_all_invoices(self):
        """שולף את כל החשבוניות כ-DataFrame"""
        conn = self.get_connection()
        query = "SELECT * FROM invoices"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_invoice_lines(self):
        """שולף את כל שורות הפירוט (פריטים)"""
        conn = self.get_connection()
        query = "SELECT * FROM invoice_lines"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_full_view(self):
        """
        מחבר בין החשבוניות לשורות הפירוט (Join)
        כדי לקבל תמונה מלאה: מי עשה מה, מתי וכמה עלה.
        """
        conn = self.get_connection()
        query = """
        SELECT 
            i.invoice_no, 
            i.date, 
            i.workshop, 
            i.vehicle_id, 
            i.plate, 
            i.make_model, 
            i.odometer_km, 
            l.description, 
            l.qty, 
            l.unit_price, 
            l.line_total
        FROM invoices i
        JOIN invoice_lines l ON i.invoice_no = l.invoice_no
        ORDER BY i.date DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_vehicle_history(self, vehicle_id):
        """שולף היסטוריה ספציפית לרכב"""
        conn = self.get_connection()
        query = f"SELECT * FROM invoices WHERE vehicle_id = '{vehicle_id}' ORDER BY date DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_all_vehicles(self):
        """שולף את כל הרכבים בצי"""
        conn = self.get_connection()
        query = "SELECT * FROM vehicles"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_vehicle_info(self, vehicle_id):
        """שולף מידע על רכב ספציפי"""
        conn = self.get_connection()
        query = f"SELECT * FROM vehicles WHERE vehicle_id = '{vehicle_id}'"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_vehicle_with_stats(self):
        """
        שולף מידע על כל רכב עם סטטיסטיקות מעודכנות:
        - קילומטרז' נוכחי (מהחשבונית האחרונה)
        - תאריך טיפול אחרון
        - סה"כ הוצאות
        - מספר טיפולים
        """
        conn = self.get_connection()
        query = """
        SELECT
            v.*,
            MAX(i.date) as last_service_date,
            MAX(i.odometer_km) as current_km,
            COUNT(i.invoice_no) as total_services,
            SUM(i.total) as total_cost,
            AVG(i.total) as avg_service_cost
        FROM vehicles v
        LEFT JOIN invoices i ON v.vehicle_id = i.vehicle_id
        GROUP BY v.vehicle_id
        ORDER BY v.vehicle_id
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    # ===== CRUD Operations =====
    
    def add_invoice(self, invoice_data, invoice_lines_data):
        """מוסיף חשבונית חדשה למסד הנתונים"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO invoices (
                    invoice_no, date, workshop, vehicle_id, plate, make_model,
                    odometer_km, kind, subtotal, vat, total, pdf_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_data.get('invoice_no'),
                invoice_data.get('date'),
                invoice_data.get('workshop'),
                invoice_data.get('vehicle_id'),
                invoice_data.get('plate'),
                invoice_data.get('make_model'),
                invoice_data.get('odometer_km'),
                invoice_data.get('kind', 'routine'),
                invoice_data.get('subtotal', 0),
                invoice_data.get('vat', 0),
                invoice_data.get('total', 0),
                invoice_data.get('pdf_file', '')
            ))
            
            for line in invoice_lines_data:
                cursor.execute("""
                    INSERT INTO invoice_lines (
                        invoice_no, line_no, description, type, qty, unit_price, line_total
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_data.get('invoice_no'),
                    line.get('line_no'),
                    line.get('description'),
                    line.get('type'),
                    line.get('qty'),
                    line.get('unit_price'),
                    line.get('line_total')
                ))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"שגיאה בהוספת חשבונית: {str(e)}")
        finally:
            conn.close()
    
    def delete_invoice(self, invoice_no):
        """מוחק חשבונית מהמסד נתונים"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM invoice_lines WHERE invoice_no = ?", (invoice_no,))
            cursor.execute("DELETE FROM invoices WHERE invoice_no = ?", (invoice_no,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f"שגיאה במחיקת חשבונית: {str(e)}")
        finally:
            conn.close()
    
    def update_vehicle_odometer(self, vehicle_id, new_km, update_date=None):
        """מעדכן קילומטראז' ידני לרכב"""
        from datetime import datetime
        if update_date is None:
            update_date = datetime.now().strftime("%Y-%m-%d")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT vehicle_id FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
            if not cursor.fetchone():
                raise ValueError(f"רכב {vehicle_id} לא נמצא")
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"שגיאה בעדכון קילומטראז': {str(e)}")
        finally:
            conn.close()
    
    def get_invoice_by_no(self, invoice_no):
        """שולף חשבונית ספציפית לפי מספר"""
        conn = self.get_connection()
        query = "SELECT * FROM invoices WHERE invoice_no = ?"
        df = pd.read_sql_query(query, conn, params=(invoice_no,))
        conn.close()
        return df
    
    def search_invoices(self, vehicle_id=None, workshop=None, date_from=None, date_to=None):
        """חיפוש חשבוניות לפי קריטריונים"""
        conn = self.get_connection()
        conditions = []
        params = []

        if vehicle_id:
            conditions.append("vehicle_id = ?")
            params.append(vehicle_id)
        if workshop:
            conditions.append("workshop = ?")
            params.append(workshop)
        if date_from:
            conditions.append("date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("date <= ?")
            params.append(date_to)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM invoices WHERE {where_clause} ORDER BY date DESC"
        df = pd.read_sql_query(query, conn, params=params if params else None)
        conn.close()
        return df

    # ===== Fleet Management Functions =====

    def add_vehicle(self, vehicle_data):
        """
        מוסיף רכב בודד לצי

        Args:
            vehicle_data: dict עם:
                - vehicle_id (חובה)
                - plate (חובה)
                - make_model (חובה)
                - year (חובה)
                - initial_km (חובה)
                - purchase_date (חובה)
                - assigned_to (אופציונלי)
                - last_test_date (אופציונלי)
                - next_test_date (אופציונלי)
                - status (default: active)

        Returns:
            bool: True אם הצליח
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO vehicles (
                    vehicle_id, plate, make_model, year, initial_km,
                    purchase_date, assigned_to, last_test_date, next_test_date,
                    estimated_retirement_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vehicle_data.get('vehicle_id'),
                vehicle_data.get('plate'),
                vehicle_data.get('make_model'),
                vehicle_data.get('year'),
                vehicle_data.get('initial_km', 0),
                vehicle_data.get('purchase_date'),
                vehicle_data.get('assigned_to', ''),
                vehicle_data.get('last_test_date', ''),
                vehicle_data.get('next_test_date', ''),
                vehicle_data.get('estimated_retirement_date', ''),
                vehicle_data.get('status', 'active')
            ))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"שגיאה בהוספת רכב: {str(e)}")
        finally:
            conn.close()

    def bulk_add_vehicles(self, vehicles_df):
        """
        מוסיף מספר רכבים בבת אחת (מ-Excel)

        Args:
            vehicles_df: DataFrame עם כל הרכבים

        Returns:
            dict: {'success': int, 'failed': int, 'errors': list}
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        success_count = 0
        failed_count = 0
        errors = []

        for idx, row in vehicles_df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO vehicles (
                        vehicle_id, plate, make_model, year, initial_km,
                        purchase_date, assigned_to, last_test_date, next_test_date,
                        estimated_retirement_date, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('vehicle_id'),
                    row.get('plate'),
                    row.get('make_model'),
                    row.get('year'),
                    row.get('initial_km', 0),
                    row.get('purchase_date'),
                    row.get('assigned_to', ''),
                    row.get('last_test_date', ''),
                    row.get('next_test_date', ''),
                    row.get('estimated_retirement_date', ''),
                    row.get('status', 'active')
                ))
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"שורה {idx + 2}: {str(e)}")

        conn.commit()
        conn.close()

        return {
            'success': success_count,
            'failed': failed_count,
            'errors': errors
        }

    def get_fleet_overview(self):
        """
        שולף תצוגה מלאה של כל הצי עם כל הנתונים:
        - פרטי רכב
        - סטטיסטיקות תחזוקה
        - תאריכי טסט
        - תאריך גריטה משוער
        - סטטוס
        """
        conn = self.get_connection()
        query = """
        SELECT
            v.vehicle_id,
            v.plate,
            v.make_model,
            v.year,
            v.initial_km,
            v.purchase_date,
            v.assigned_to,
            v.last_test_date,
            v.next_test_date,
            v.estimated_retirement_date,
            v.status,
            MAX(i.date) as last_service_date,
            MAX(i.odometer_km) as current_km,
            COUNT(i.invoice_no) as total_services,
            SUM(i.total) as total_cost,
            AVG(i.total) as avg_service_cost
        FROM vehicles v
        LEFT JOIN invoices i ON v.vehicle_id = i.vehicle_id
        GROUP BY v.vehicle_id
        ORDER BY v.vehicle_id
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    # ===== Chat History & Project Templates Functions =====

    def save_conversation(self, conversation_id, title, project_template_id=None):
        """שומר שיחה חדשה"""
        from datetime import datetime
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO conversations
                (conversation_id, title, created_at, last_updated, message_count, project_template_id)
                VALUES (?, ?, ?, ?, 0, ?)
            """, (
                conversation_id,
                title,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                project_template_id
            ))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"שגיאה בשמירת שיחה: {str(e)}")
        finally:
            conn.close()

    def save_message(self, conversation_id, role, content):
        """שומר הודעה בשיחה"""
        from datetime import datetime
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # הוספת ההודעה
            cursor.execute("""
                INSERT INTO chat_messages
                (conversation_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (conversation_id, role, content, datetime.now().isoformat()))

            # עדכון מספר ההודעות והזמן
            cursor.execute("""
                UPDATE conversations
                SET message_count = message_count + 1,
                    last_updated = ?
                WHERE conversation_id = ?
            """, (datetime.now().isoformat(), conversation_id))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"שגיאה בשמירת הודעה: {str(e)}")
        finally:
            conn.close()

    def get_conversation_history(self, conversation_id):
        """מחזיר את כל ההודעות בשיחה"""
        conn = self.get_connection()
        query = """
        SELECT role, content, timestamp
        FROM chat_messages
        WHERE conversation_id = ?
        ORDER BY message_id ASC
        """
        df = pd.read_sql_query(query, conn, params=(conversation_id,))
        conn.close()
        return df

    def get_all_conversations(self, limit=50):
        """מחזיר רשימת כל השיחות"""
        conn = self.get_connection()
        query = """
        SELECT
            c.conversation_id,
            c.title,
            c.created_at,
            c.last_updated,
            c.message_count,
            c.project_template_id,
            p.template_name
        FROM conversations c
        LEFT JOIN project_templates p ON c.project_template_id = p.template_id
        ORDER BY c.last_updated DESC
        LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df

    def delete_conversation(self, conversation_id):
        """מוחק שיחה והודעות שלה"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM chat_messages WHERE conversation_id = ?", (conversation_id,))
            cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"שגיאה במחיקת שיחה: {str(e)}")
        finally:
            conn.close()

    # ===== Project Templates Functions =====

    def get_all_templates(self):
        """מחזיר את כל תבניות הפרויקטים"""
        conn = self.get_connection()
        query = "SELECT * FROM project_templates ORDER BY template_name"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_template(self, template_id):
        """מחזיר תבנית ספציפית"""
        conn = self.get_connection()
        query = "SELECT * FROM project_templates WHERE template_id = ?"
        df = pd.read_sql_query(query, conn, params=(template_id,))
        conn.close()
        return df.iloc[0] if len(df) > 0 else None

    def save_template(self, template_data):
        """שומר או מעדכן תבנית"""
        from datetime import datetime
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO project_templates
                (template_id, template_name, description, template_type, configuration, created_at, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                template_data.get('template_id'),
                template_data.get('template_name'),
                template_data.get('description'),
                template_data.get('template_type'),
                template_data.get('configuration'),
                template_data.get('created_at', datetime.now().isoformat()),
                template_data.get('last_used', '')
            ))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"שגיאה בשמירת תבנית: {str(e)}")
        finally:
            conn.close()

    def update_template_last_used(self, template_id):
        """מעדכן מתי התבנית נוצלה לאחרונה"""
        from datetime import datetime
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE project_templates
                SET last_used = ?
                WHERE template_id = ?
            """, (datetime.now().isoformat(), template_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"שגיאה בעדכון תבנית: {str(e)}")
        finally:
            conn.close()

    def delete_template(self, template_id):
        """מוחק תבנית"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM project_templates WHERE template_id = ?", (template_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f"שגיאה במחיקת תבנית: {str(e)}")
        finally:
            conn.close()

    # =====================================
    # Email Invoice Fetcher Methods
    # =====================================

    def create_email_sync_table(self):
        """
        Create email_sync_log table if it doesn't exist.

        This table tracks email sync attempts and results.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_sync_log (
                    sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_message_id TEXT UNIQUE,
                    subject TEXT,
                    sender TEXT,
                    received_date TEXT,
                    processed_date TEXT,
                    invoice_numbers TEXT,
                    status TEXT CHECK(status IN ('success', 'failed'))
                )
            """)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"שגיאה ביצירת טבלת סנכרון אימייל: {str(e)}")
        finally:
            conn.close()

    def log_email_sync(self, sync_data):
        """
        Log email sync attempt to database.

        Args:
            sync_data: Dict with keys:
                - email_message_id: Unique email ID
                - subject: Email subject
                - sender: Email sender
                - received_date: When email was received
                - processed_date: When email was processed
                - invoice_numbers: Comma-separated invoice numbers found
                - status: 'success' or 'failed'

        Returns:
            bool: True if logged successfully
        """
        # Ensure table exists
        self.create_email_sync_table()

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO email_sync_log
                (email_message_id, subject, sender, received_date, processed_date, invoice_numbers, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                sync_data.get('email_message_id'),
                sync_data.get('subject'),
                sync_data.get('sender'),
                sync_data.get('received_date'),
                sync_data.get('processed_date'),
                sync_data.get('invoice_numbers', ''),
                sync_data.get('status', 'failed')
            ))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"שגיאה בלוג סנכרון: {str(e)}")
            return False
        finally:
            conn.close()

    def get_email_sync_history(self, limit=20):
        """
        Get email sync history for display.

        Args:
            limit: Maximum number of records to return (default: 20)

        Returns:
            DataFrame with sync history, ordered by processed_date DESC
        """
        # Ensure table exists
        self.create_email_sync_table()

        conn = self.get_connection()

        try:
            query = """
                SELECT
                    sync_id,
                    email_message_id,
                    subject,
                    sender,
                    received_date,
                    processed_date,
                    invoice_numbers,
                    status
                FROM email_sync_log
                ORDER BY processed_date DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(limit,))
            return df
        except Exception as e:
            print(f"שגיאה בשליפת היסטוריית סנכרון: {str(e)}")
            return pd.DataFrame()
        finally:
            conn.close()

    def check_duplicate_invoice(self, invoice_no):
        """
        Check if invoice number already exists in database.

        Args:
            invoice_no: Invoice number to check

        Returns:
            bool: True if invoice exists (is duplicate), False otherwise
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT COUNT(*) FROM invoices WHERE invoice_no = ?
            """, (invoice_no,))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"שגיאה בבדיקת כפילות: {str(e)}")
            return False
        finally:
            conn.close()

    def get_last_email_sync(self):
        """
        Get details of the last successful email sync.

        Returns:
            Dict with last sync info or None if no syncs exist
        """
        history = self.get_email_sync_history(limit=1)

        if history.empty:
            return None

        last_sync = history.iloc[0]
        return {
            'processed_date': last_sync['processed_date'],
            'status': last_sync['status'],
            'invoice_count': len(last_sync['invoice_numbers'].split(',')) if last_sync['invoice_numbers'] else 0,
            'subject': last_sync['subject']
        }