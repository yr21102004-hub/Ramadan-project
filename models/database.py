"""
Database Models
Handles all database operations
"""
from tinydb import TinyDB, Query
from datetime import datetime
import os

class Database:
    """Database singleton class"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.db = TinyDB('database.json')
        return cls._instance
    
    def table(self, name):
        """Get a specific table by name"""
        return self.db.table(name)

    @property
    def users(self):
        return self.db.table('users')
    
    @property
    def chats(self):
        return self.db.table('chat_logs')
    
    @property
    def contacts(self):
        return self.db.table('contacts')
    
    @property
    def unanswered(self):
        return self.db.table('unanswered_questions')
    
    @property
    def security_logs(self):
        return self.db.table('security_audit_logs')
    
    @property
    def payments(self):
        return self.db.table('payments')
    
    @property
    def subscriptions(self):
        return self.db.table('subscriptions')
    
    @property
    def learned_answers(self):
        return self.db.table('learned_answers')
    
    @property
    def ratings(self):
        return self.db.table('ratings')
    
    @property
    def complaints(self):
        return self.db.table('complaints')
    
    @property
    def inspection_requests(self):
        return self.db.table('inspection_requests')



class UserModel:
    """User Model - handles user operations"""
    
    def __init__(self):
        self.db = Database()
        self.table = self.db.users
        self.query = Query()
    
    def get_by_username(self, username):
        """Get user by username"""
        return self.table.get(self.query.username == username)
    
    def get_all(self):
        """Get all users"""
        return self.table.all()
    
    def create(self, user_data):
        """Create new user"""
        user_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.table.insert(user_data)
    
    def update(self, username, data):
        """Update user"""
        return self.table.update(data, self.query.username == username)
    
    def delete(self, username):
        """Delete user"""
        return self.table.remove(self.query.username == username)
    
    def get_all_except_admin(self):
        """Get all users except admin"""
        return [u for u in self.table.all() if u.get('role') != 'admin']

    def submit_verification(self, username, data):
        """Submit worker verification documents"""
        update_data = {
            'verification_status': 'pending',
            'id_card_front': data.get('id_card_front'),
            'id_card_back': data.get('id_card_back'),
            'selfie_image': data.get('selfie_image'),
            'work_proof_type': data.get('work_proof_type'),
            'work_proof_files': data.get('work_proof_files', []),
            'verification_submitted_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self.table.update(update_data, self.query.username == username)

    def verify_user(self, username, status='verified', notes=''):
        """Approve or Reject verification"""
        update_data = {
            'verification_status': status,
            'verified_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'admin_notes': notes
        }
        return self.table.update(update_data, self.query.username == username)

    def get_pending_verifications(self):
        """Get all users with pending verification"""
        return self.table.search(self.query.verification_status == 'pending')


class ChatModel:
    """Chat Model - handles chat operations"""
    
    def __init__(self):
        self.db = Database()
        self.table = self.db.chats
        self.query = Query()
    
    def get_all(self):
        """Get all chats"""
        return self.table.all()
    
    def get_by_user(self, user_id):
        """Get chats by user ID"""
        return self.table.search(self.query.user_id == user_id)
    
    def create(self, chat_data):
        """Create new chat log"""
        chat_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.table.insert(chat_data)


class PaymentModel:
    """Payment Model - handles payment operations"""
    
    def __init__(self):
        self.db = Database()
        self.table = self.db.payments
        self.query = Query()
    
    def get_all(self):
        """Get all payments"""
        return self.table.all()
    
    def create(self, payment_data):
        """Create new payment"""
        payment_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.table.insert(payment_data)

    def get_by_user(self, username):
        """Get payments by username"""
        return self.table.search(self.query.username == username)


class SubscriptionModel:
    """Subscription Model"""
    
    def __init__(self):
        self.db = Database()
        self.table = self.db.subscriptions
        self.query = Query()
    
    def get_all(self):
        return self.table.all()
    
    def get_by_user(self, username):
        return self.table.search(self.query.username == username)
    
    def create(self, data):
        data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.table.insert(data)


class SecurityLogModel:
    """Security Log Model"""
    
    def __init__(self):
        self.db = Database()
        self.table = self.db.security_logs
        self.query = Query()
    
    def get_all(self):
        """Get all security logs"""
        return self.table.all()
    
    def create(self, event_type, details, severity="low"):
        """Create security log"""
        log_data = {
            'event': event_type,
            'details': details,
            'severity': severity,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self.table.insert(log_data)

    def truncate(self):
        """Clear all security logs"""
        return self.table.truncate()


class ContactModel:
    """Contact Model - handles contact form submissions"""
    
    def __init__(self):
        self.db = Database()
        self.table = self.db.contacts
        self.query = Query()
    
    def get_all(self):
        """Get all contact messages"""
        return self.table.all()
    
    def create(self, name, phone, message, user_id=None, service=None):
        """Create new contact message"""
        contact_data = {
            'name': name,
            'phone': phone,
            'message': message,
            'user_id': user_id,
            'service': service,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self.table.insert(contact_data)

    def get_by_user(self, user_id):
        """Get messages by user ID"""
        return self.table.search(self.query.user_id == user_id)

    def delete(self, doc_id):
        """Delete contact message by ID"""
        return self.table.remove(doc_ids=[int(doc_id)])


class LearnedAnswersModel:
    """Learned Answers Model - stores Q&A pairs for AI learning"""
    
    def __init__(self):
        self.db = Database()
        self.table = self.db.learned_answers
        self.query = Query()
    
    def get_all(self):
        """Get all learned answers"""
        return self.table.all()
    
    def get_by_question(self, question):
        """Get answer by question"""
        return self.table.get(self.query.question == question)
    
    def create(self, question, answer):
        """Create new learned answer"""
        learned_data = {
            'question': question,
            'answer': answer,
            'learned_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self.table.insert(learned_data)
    
    def search_similar(self, normalized_question):
        """Search for similar questions using normalized text"""
        all_learned = self.table.all()
        for record in all_learned:
            if record.get('question') == normalized_question:
                return record.get('answer')
        return None


class UnansweredQuestionsModel:
    """Unanswered Questions Model"""
    
    def __init__(self):
        self.db = Database()
        self.table = self.db.unanswered
        self.query = Query()
    
    def get_all(self):
        """Get all unanswered questions"""
        return self.table.all()
    
    def get_by_question(self, question):
        """Get question by text"""
        return self.table.get(self.query.question == question)
        
    def get_by_user(self, user_id):
        """Get unanswered by user ID"""
        return self.table.search(self.query.user_id == user_id)
        
    def create(self, question, user_id):
        """Create new unanswered question"""
        msg_clean = question.lower().strip()
        # Upsert: update timestamp if exists, insert if not
        self.table.upsert({
            'question': msg_clean,
            'user_id': user_id,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'admin_response': None
        }, self.query.question == msg_clean)
        
    def update_response(self, question, response):
        """Update admin response"""
        return self.table.update({'admin_response': response}, self.query.question == question)
        
    def delete(self, question):
        """Delete question"""
        return self.table.remove(self.query.question == question)
