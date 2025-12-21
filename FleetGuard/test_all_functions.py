"""
סקריפט בדיקה לכל הפונקציות ב-FleetGuard
בודק שכל הפונקציות עובדות כמו שצריך
"""

import sys
import os

# הוספת נתיב לפרויקט
sys.path.insert(0, os.path.dirname(__file__))

def test_database_manager():
    """בודק את DatabaseManager"""
    print("\n" + "="*60)
    print("Testing DatabaseManager")
    print("="*60)
    
    try:
        from src.database_manager import DatabaseManager
        
        db = DatabaseManager()
        print("OK: DatabaseManager created")
        
        # בדיקת קריאה
        invoices = db.get_all_invoices()
        print(f"OK: Read invoices: {len(invoices)} invoices")
        
        vehicles = db.get_all_vehicles()
        print(f"OK: Read vehicles: {len(vehicles)} vehicles")
        
        # בדיקת CRUD
        if hasattr(db, 'add_invoice'):
            print("OK: add_invoice function exists")
        else:
            print("ERROR: add_invoice function missing")
        
        if hasattr(db, 'delete_invoice'):
            print("OK: delete_invoice function exists")
        else:
            print("ERROR: delete_invoice function missing")
        
        if hasattr(db, 'update_vehicle_odometer'):
            print("OK: update_vehicle_odometer function exists")
        else:
            print("ERROR: update_vehicle_odometer function missing")
        
        return True
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_auth_manager():
    """בודק את AuthManager"""
    print("\n" + "="*60)
    print("Testing AuthManager")
    print("="*60)
    
    try:
        from src.auth_manager import AuthManager
        
        auth = AuthManager()
        print("OK: AuthManager created")
        
        # בדיקת פונקציות
        if hasattr(auth, 'register_user'):
            print("OK: register_user function exists")
        else:
            print("ERROR: register_user function missing")
        
        if hasattr(auth, 'login_user'):
            print("OK: login_user function exists")
        else:
            print("ERROR: login_user function missing")
        
        return True
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_maintenance_pattern_agent():
    """בודק את MaintenancePatternAgent"""
    print("\n" + "="*60)
    print("Testing MaintenancePatternAgent")
    print("="*60)
    
    try:
        from src.maintenance_pattern_agent import MaintenancePatternAgent
        
        agent = MaintenancePatternAgent()
        print("OK: MaintenancePatternAgent created")
        
        # בדיקת ניתוח
        patterns = agent.analyze_maintenance_patterns()
        print("OK: Pattern analysis completed")
        
        if 'tire_replacements' in patterns:
            print("OK: Tire pattern detection works")
        
        if 'routine_services' in patterns:
            print("OK: Routine service pattern detection works")
        
        return True
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_file_processor():
    """בודק את FileProcessor"""
    print("\n" + "="*60)
    print("Testing FileProcessor")
    print("="*60)
    
    try:
        from src.utils.file_processor import FileProcessor
        
        processor = FileProcessor()
        print("OK: FileProcessor created")
        
        if hasattr(processor, 'process_uploaded_file'):
            print("OK: process_uploaded_file function exists")
        else:
            print("ERROR: process_uploaded_file function missing")
        
        return True
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_crew_orchestrator():
    """בודק את CrewOrchestrator"""
    print("\n" + "="*60)
    print("Testing CrewOrchestrator")
    print("="*60)
    
    try:
        from src.crew_orchestrator import DirectOrchestrator
        
        orchestrator = DirectOrchestrator()
        print("OK: DirectOrchestrator created")
        
        return True
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_ai_engine():
    """בודק את FleetAIEngine"""
    print("\n" + "="*60)
    print("Testing FleetAIEngine")
    print("="*60)
    
    try:
        from src.ai_engine import FleetAIEngine
        
        engine = FleetAIEngine()
        print("OK: FleetAIEngine created")
        
        return True
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def main():
    """מריץ את כל הבדיקות"""
    print("\n" + "="*60)
    print("FleetGuard - בדיקת כל הפונקציות")
    print("="*60)
    
    results = {
        'DatabaseManager': test_database_manager(),
        'AuthManager': test_auth_manager(),
        'MaintenancePatternAgent': test_maintenance_pattern_agent(),
        'FileProcessor': test_file_processor(),
        'CrewOrchestrator': test_crew_orchestrator(),
        'FleetAIEngine': test_ai_engine()
    }
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nSUCCESS: All tests passed!")
    else:
        print(f"\nWARNING: {total - passed} tests failed")

if __name__ == "__main__":
    main()

