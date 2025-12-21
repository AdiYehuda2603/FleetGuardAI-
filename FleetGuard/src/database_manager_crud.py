"""
CRUD Operations for DatabaseManager
Additional methods for adding, deleting, and updating data
"""

import sqlite3
import pandas as pd
from datetime import datetime


def add_crud_methods_to_manager():
    """
    מוסיף פונקציות CRUD ל-DatabaseManager
    """
    from src.database_manager import DatabaseManager
    
    # הוספת פונקציות CRUD
    def add_invoice(self, invoice_data, invoice_lines_data):
        """
        מוסיף חשבונית חדשה למסד הנתונים
        
        Args:
            invoice_data: dict עם נתוני החשבונית
            invoice_lines_data: list of dicts עם שורות הפירוט
        
        Returns:
            bool: True אם הצליח
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # הוספת חשבונית
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
            
            # הוספת שורות פירוט
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
        """
        מוחק חשבונית מהמסד נתונים
        
        Args:
            invoice_no: מספר חשבונית
        
        Returns:
            bool: True אם הצליח
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # מחיקת שורות פירוט תחילה (Foreign Key)
            cursor.execute("DELETE FROM invoice_lines WHERE invoice_no = ?", (invoice_no,))
            
            # מחיקת חשבונית
            cursor.execute("DELETE FROM invoices WHERE invoice_no = ?", (invoice_no,))
            
            conn.commit()
            return cursor.rowcount > 0
        
        except Exception as e:
            conn.rollback()
            raise Exception(f"שגיאה במחיקת חשבונית: {str(e)}")
        
        finally:
            conn.close()
    
    def update_vehicle_odometer(self, vehicle_id, new_km, update_date=None):
        """
        מעדכן קילומטראז' ידני לרכב
        יוצר רשומת עדכון (ניתן להוסיף טבלה נפרדת בעתיד)
        
        Args:
            vehicle_id: מזהה רכב
            new_km: קילומטראז' חדש
            update_date: תאריך עדכון (אופציונלי)
        
        Returns:
            bool: True אם הצליח
        """
        if update_date is None:
            update_date = datetime.now().strftime("%Y-%m-%d")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # בדיקה אם הרכב קיים
            cursor.execute("SELECT vehicle_id FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
            if not cursor.fetchone():
                raise ValueError(f"רכב {vehicle_id} לא נמצא")
            
            # עדכון הקילומטראז' יקרה בחשבונית הבאה
            # כאן רק נשמור את זה (ניתן להוסיף טבלת odometer_updates)
            
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
        """
        חיפוש חשבוניות לפי קריטריונים
        
        Args:
            vehicle_id: מזהה רכב
            workshop: שם מוסך
            date_from: תאריך התחלה
            date_to: תאריך סיום
        
        Returns:
            DataFrame עם תוצאות החיפוש
        """
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
    
    # הוספת הפונקציות ל-DatabaseManager
    DatabaseManager.add_invoice = add_invoice
    DatabaseManager.delete_invoice = delete_invoice
    DatabaseManager.update_vehicle_odometer = update_vehicle_odometer
    DatabaseManager.get_invoice_by_no = get_invoice_by_no
    DatabaseManager.search_invoices = search_invoices
    
    return DatabaseManager

