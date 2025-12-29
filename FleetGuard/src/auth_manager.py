"""
Authentication Manager for FleetGuard
Handles user registration, login, and session management
"""

import sqlite3
import hashlib
import os
from datetime import datetime
from src.utils.path_resolver import path_resolver

# Import streamlit only when needed (lazy import)
try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False
    # Create a mock session_state for when Streamlit is not available
    class MockSessionState:
        def __init__(self):
            self._data = {}
        def get(self, key, default=None):
            return self._data.get(key, default)
        def __setitem__(self, key, value):
            self._data[key] = value
        def __contains__(self, key):
            return key in self._data
        def __getitem__(self, key):
            return self._data[key]
    
    class MockStreamlit:
        session_state = MockSessionState()
        def rerun(self):
            pass
    
    st = MockStreamlit()


class AuthManager:
    """Manages user authentication and authorization"""
    
    def __init__(self, db_path=None):
        """Initialize AuthManager with database path"""
        if db_path is None:
            # שימוש ב-PathResolver לקבלת נתיב מוחלט
            # עובד בכל סביבה - local, cloud, tests
            self.db_path = str(path_resolver.get_db_path('users.db'))
        else:
            self.db_path = db_path

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Create users table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, email: str, password: str, full_name: str = "") -> tuple[bool, str]:
        """
        Register a new user
        
        Returns:
            (success: bool, message: str)
        """
        if not username or not email or not password:
            return False, "כל השדות נדרשים"
        
        if len(password) < 6:
            return False, "הסיסמה חייבת להכיל לפחות 6 תווים"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash = self._hash_password(password)
            created_at = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (username, email, password_hash, full_name, created_at))
            
            conn.commit()
            return True, "ההרשמה בוצעה בהצלחה!"
        
        except sqlite3.IntegrityError:
            if "username" in str(sqlite3.IntegrityError):
                return False, "שם המשתמש כבר קיים"
            else:
                return False, "כתובת האימייל כבר קיימת"
        
        except Exception as e:
            return False, f"שגיאה בהרשמה: {str(e)}"
        
        finally:
            conn.close()
    
    def login_user(self, username: str, password: str) -> tuple[bool, str, dict]:
        """
        Authenticate user login
        
        Returns:
            (success: bool, message: str, user_data: dict)
        """
        if not username or not password:
            return False, "נא להזין שם משתמש וסיסמה", {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self._hash_password(password)
        
        cursor.execute("""
            SELECT id, username, email, full_name, is_active
            FROM users
            WHERE username = ? AND password_hash = ?
        """, (username, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return False, "שם משתמש או סיסמה שגויים", {}
        
        if not user[4]:  # is_active
            return False, "החשבון מושבת", {}
        
        # Update last login
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET last_login = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), user[0]))
        conn.commit()
        conn.close()
        
        user_data = {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'full_name': user[3]
        }
        
        return True, "התחברות בוצעה בהצלחה!", user_data
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated in current session"""
        if not _HAS_STREAMLIT:
            return False
        try:
            return st.session_state.get('authenticated', False)
        except:
            return False
    
    def get_current_user(self) -> dict:
        """Get current authenticated user data"""
        if not _HAS_STREAMLIT:
            return {}
        try:
            if self.is_authenticated():
                return st.session_state.get('user_data', {})
        except:
            pass
        return {}
    
    def logout(self):
        """Logout current user"""
        if not _HAS_STREAMLIT:
            return
        try:
            st.session_state['authenticated'] = False
            st.session_state['user_data'] = {}
            st.session_state['openai_api_key'] = None
            st.rerun()
        except:
            pass
    
    def set_api_key(self, api_key: str):
        """Securely store API key in session (not in database)"""
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            if _HAS_STREAMLIT:
                try:
                    st.session_state['openai_api_key'] = api_key
                except:
                    pass
    
    def get_api_key(self) -> str:
        """Get API key from session or environment"""
        # First try session (if Streamlit is available)
        if _HAS_STREAMLIT:
            try:
                if 'openai_api_key' in st.session_state:
                    return st.session_state['openai_api_key']
            except:
                pass
        
        # Then try environment
        return os.environ.get("OPENAI_API_KEY", "")

