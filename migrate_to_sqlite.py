from tinydb import TinyDB
import sqlite3
import os
from models.database import Database, UserModel, ChatModel, PaymentModel, SecurityLogModel, ContactModel, LearnedAnswersModel, UnansweredQuestionsModel

def migrate():
    if not os.path.exists('database.json'):
        print("No database.json found to migrate.")
        return

    print("Starting migration from TinyDB to SQLite...")
    tdb = TinyDB('database.json')
    
    # 1. Migrate Users
    print("- Migrating Users...")
    users_table = tdb.table('users')
    user_model = UserModel()
    for u in users_table.all():
        try:
            # Add missing fields with defaults if necessary
            if 'two_factor_enabled' not in u: u['two_factor_enabled'] = 0
            if 'two_factor_secret' not in u: u['two_factor_secret'] = None
            if 'project_percentage' not in u: u['project_percentage'] = 0
            user_model.create(u)
        except Exception as e:
            print(f"  Error migrating user {u.get('username')}: {e}")

    # 2. Migrate Chats
    print("- Migrating Chat Logs...")
    chats_table = tdb.table('chat_logs')
    chat_model = ChatModel()
    for c in chats_table.all():
        chat_model.create(c)

    # 3. Migrate Contacts
    print("- Migrating Contacts...")
    contacts_table = tdb.table('contacts')
    contact_model = ContactModel()
    for c in contacts_table.all():
        # ContactModel.create takes args, while others take dict
        # Name: name, phone, message, user_id=None, service=None
        contact_model.create(
            name=c.get('name'), 
            phone=c.get('phone'), 
            message=c.get('message'),
            user_id=c.get('user_id'),
            service=c.get('service')
        )

    # 4. Migrate Payments
    print("- Migrating Payments...")
    payments_table = tdb.table('payments')
    payment_model = PaymentModel()
    for p in payments_table.all():
        payment_model.create(p)

    # 5. Migrate Security Logs
    print("- Migrating Security Logs...")
    sec_table = tdb.table('security_audit_logs')
    sec_model = SecurityLogModel()
    for s in sec_table.all():
        sec_model.create(s.get('event'), s.get('details'), s.get('severity'))

    # 6. Migrate Learned Answers
    print("- Migrating Learned Answers...")
    learned_table = tdb.table('learned_answers')
    learned_model = LearnedAnswersModel()
    for l in learned_table.all():
        learned_model.create(l.get('question'), l.get('answer'))

    # 7. Migrate Unanswered
    print("- Migrating Unanswered...")
    un_table = tdb.table('unanswered_questions')
    un_model = UnansweredQuestionsModel()
    for u in un_table.all():
        un_model.create(u.get('question'), u.get('user_id'))

    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
