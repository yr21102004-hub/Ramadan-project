"""
Database Models (SQLite Version)
Handles all database operations using SQL for better reliability.
"""
import sqlite3
import os
from datetime import datetime

class Database:
    """SQLite Database singleton class"""
    _instance = None
    DB_NAME = 'ramadan_company.db'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance
    
    def _init_db(self):
        """Initialize SQLite database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Users Table (Comprehensive)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                role TEXT DEFAULT 'user',
                profile_image TEXT,
                project_location TEXT,
                project_description TEXT,
                project_percentage INTEGER DEFAULT 0,
                two_factor_enabled BOOLEAN DEFAULT 0,
                two_factor_secret TEXT,
                specialization TEXT,
                experience_years INTEGER,
                status TEXT,
                created_at TEXT
            )
        ''')
        
        # 2. Chat Logs Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                user_name TEXT,
                message TEXT,
                response TEXT,
                timestamp TEXT
            )
        ''')
        
        # 3. Contacts Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                message TEXT,
                user_id TEXT,
                service TEXT,
                created_at TEXT
            )
        ''')
        
        # 4. Unanswered Questions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unanswered_questions (
                question TEXT PRIMARY KEY,
                user_id TEXT,
                timestamp TEXT,
                admin_response TEXT
            )
        ''')
        
        # 5. Security Audit Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT,
                details TEXT,
                severity TEXT,
                timestamp TEXT
            )
        ''')
        
        # 6. Payments Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                full_name TEXT,
                amount REAL,
                method TEXT,
                timestamp TEXT,
                status TEXT DEFAULT 'Pending'
            )
        ''')
        
        # 7. Learned Answers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT UNIQUE,
                answer TEXT,
                learned_at TEXT
            )
        ''')
        
        # 8. Subscriptions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                email TEXT,
                created_at TEXT
            )
        ''')
        
        # 9. Ratings Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                worker_id TEXT,
                user_id TEXT,
                quality_rating INTEGER,
                behavior_rating INTEGER,
                comment TEXT,
                timestamp TEXT,
                created_at TEXT
            )
        ''')

        # 10. Complaints Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                subject TEXT,
                message TEXT,
                status TEXT DEFAULT 'قيد المراجعة',
                admin_notes TEXT,
                created_at TEXT
            )
        ''')

        # 11. Inspection Requests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inspection_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                location TEXT,
                date TEXT,
                status TEXT DEFAULT 'new_request',
                worker_id TEXT,
                admin_notes TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_connection(self):
        conn = sqlite3.connect(self.DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    @property
    def users(self): return UserModel()

    def table(self, name):
        """Proxy for TinyDB table() method"""
        return GenericSQLiteModel(name)
    
    @property
    def chats(self): return ChatModel()
    
    @property
    def contacts(self): return ContactModel()
    
    @property
    def unanswered(self): return UnansweredQuestionsModel()
    
    @property
    def security_logs(self): return SecurityLogModel()
    
    @property
    def payments(self): return PaymentModel()
    
    @property
    def learned_answers(self): return LearnedAnswersModel()
    
    @property
    def subscriptions(self): return SubscriptionModel()
    
    @property
    def ratings(self): return GenericSQLiteModel('ratings')
    
    @property
    def complaints(self): return GenericSQLiteModel('complaints')
    
    @property
    def inspection_requests(self): return GenericSQLiteModel('inspection_requests')

class SQLiteModel:
    """Base SQL Model"""
    def __init__(self, table):
        self.db_mgr = Database()
        self.table = table

    def _dict_from_row(self, row):
        if row is None: return None
        d = dict(row)
        if 'id' in d:
             d['doc_id'] = d['id']
        return d

    def _get_columns(self):
        conn = self.db_mgr.get_connection()
        try:
            cursor = conn.execute(f"PRAGMA table_info({self.table})")
            cols = [col[1] for col in cursor.fetchall()]
            return cols
        finally:
            conn.close()

    def _filter_data(self, data):
        """Filter input dict to only include keys that are columns in the table"""
        cols = self._get_columns()
        return {k: v for k, v in data.items() if k in cols}

class GenericSQLiteModel(SQLiteModel):
    """Fallback for tables without dedicated model classes yet"""
    def __init__(self, table):
        super().__init__(table)
    
    def all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table}").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def insert(self, data):
        filtered_data = self._filter_data(data)
        cols = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?'] * len(filtered_data))
        sql = f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})"
        conn = self.db_mgr.get_connection()
        try:
            cursor = conn.execute(sql, list(filtered_data.values()))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def search(self, query=None):
        # Very basic search shim for TinyDB compatibility
        # In practice, the caller should be updated to use SQL
        return self.all()

    def get(self, query=None):
        all_data = self.all()
        return all_data[0] if all_data else None

class UserModel(SQLiteModel):
    def __init__(self):
        super().__init__('users')
    
    def get_by_username(self, username):
        conn = self.db_mgr.get_connection()
        row = conn.execute(f"SELECT * FROM {self.table} WHERE username = ?", (username,)).fetchone()
        conn.close()
        return self._dict_from_row(row)
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table}").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, user_data):
        if 'created_at' not in user_data:
            user_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        filtered_data = self._filter_data(user_data)
        cols = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?'] * len(filtered_data))
        sql = f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})"
        
        conn = self.db_mgr.get_connection()
        try:
            conn.execute(sql, list(filtered_data.values()))
            conn.commit()
        finally:
            conn.close()
    
    def update(self, username, data):
        filtered_data = self._filter_data(data)
        if not filtered_data: return
        
        set_clause = ', '.join([f"{k} = ?" for k in filtered_data.keys()])
        values = list(filtered_data.values())
        values.append(username)
        sql = f"UPDATE {self.table} SET {set_clause} WHERE username = ?"
        
        conn = self.db_mgr.get_connection()
        try:
            conn.execute(sql, values)
            conn.commit()
        finally:
            conn.close()
    
    def delete(self, username):
        conn = self.db_mgr.get_connection()
        conn.execute(f"DELETE FROM {self.table} WHERE username = ?", (username,))
        conn.commit()
        conn.close()

class ChatModel(SQLiteModel):
    def __init__(self):
        super().__init__('chat_logs')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY timestamp DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def get_by_user(self, user_id):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} WHERE user_id = ? ORDER BY timestamp DESC", (user_id,)).fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, chat_data):
        if 'timestamp' not in chat_data:
            chat_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        filtered_data = self._filter_data(chat_data)
        cols = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?'] * len(filtered_data))
        sql = f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})"
        
        conn = self.db_mgr.get_connection()
        conn.execute(sql, list(filtered_data.values()))
        conn.commit()
        conn.close()

class PaymentModel(SQLiteModel):
    def __init__(self):
        super().__init__('payments')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY timestamp DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def get_by_user(self, username):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} WHERE username = ? ORDER BY timestamp DESC", (username,)).fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, payment_data):
        if 'timestamp' not in payment_data:
            payment_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        filtered_data = self._filter_data(payment_data)
        cols = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?'] * len(filtered_data))
        sql = f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})"
        
        conn = self.db_mgr.get_connection()
        conn.execute(sql, list(filtered_data.values()))
        conn.commit()
        conn.close()

    def update_status(self, doc_id, status):
        conn = self.db_mgr.get_connection()
        conn.execute(f"UPDATE {self.table} SET status = ? WHERE id = ?", (status, doc_id))
        conn.commit()
        conn.close()

class SecurityLogModel(SQLiteModel):
    def __init__(self):
        super().__init__('security_audit_logs')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY timestamp DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, event, details, severity="low"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self.db_mgr.get_connection()
        conn.execute(f"INSERT INTO {self.table} (event, details, severity, timestamp) VALUES (?, ?, ?, ?)", 
                     (event, details, severity, timestamp))
        conn.commit()
        conn.close()

    def truncate(self):
        conn = self.db_mgr.get_connection()
        conn.execute(f"DELETE FROM {self.table}")
        conn.commit()
        conn.close()

class ContactModel(SQLiteModel):
    def __init__(self):
        super().__init__('contacts')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY created_at DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def get_by_user(self, user_id):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]

    def create(self, name, phone, message, user_id=None, service=None):
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self.db_mgr.get_connection()
        conn.execute(f"INSERT INTO {self.table} (name, phone, message, user_id, service, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                     (name, phone, message, user_id, service, created_at))
        conn.commit()
        conn.close()

    def delete(self, doc_id):
        conn = self.db_mgr.get_connection()
        conn.execute(f"DELETE FROM {self.table} WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()

class LearnedAnswersModel(SQLiteModel):
    def __init__(self):
        super().__init__('learned_answers')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY learned_at DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, question, answer):
        learned_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg_clean = question.lower().strip()
        conn = self.db_mgr.get_connection()
        try:
            conn.execute(f"INSERT OR REPLACE INTO {self.table} (question, answer, learned_at) VALUES (?, ?, ?)",
                         (msg_clean, answer, learned_at))
            conn.commit()
        finally:
            conn.close()

class UnansweredQuestionsModel(SQLiteModel):
    def __init__(self):
        super().__init__('unanswered_questions')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY timestamp DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, question, user_id):
        msg_clean = question.lower().strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self.db_mgr.get_connection()
        try:
            conn.execute(f"INSERT OR REPLACE INTO {self.table} (question, user_id, timestamp, admin_response) VALUES (?, ?, ?, NULL)",
                         (msg_clean, user_id, timestamp))
            conn.commit()
        finally:
            conn.close()

    def delete(self, question):
        conn = self.db_mgr.get_connection()
        conn.execute(f"DELETE FROM {self.table} WHERE question = ?", (question.lower().strip(),))
        conn.commit()
        conn.close()

    def get_by_user(self, user_id):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]

class SubscriptionModel(SQLiteModel):
    def __init__(self):
        super().__init__('subscriptions')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table}").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def get_by_user(self, username):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} WHERE username = ?", (username,)).fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, data):
        if 'created_at' not in data:
            data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filtered_data = self._filter_data(data)
        cols = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?'] * len(filtered_data))
        sql = f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})"
        conn = self.db_mgr.get_connection()
        conn.execute(sql, list(filtered_data.values()))
        conn.commit()
        conn.close()
