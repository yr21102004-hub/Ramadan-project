from tinydb import TinyDB, Query
from flask_bcrypt import Bcrypt
from flask import Flask
from datetime import datetime

# Initialize minimal app for Bcrypt context
app = Flask(__name__)
bcrypt = Bcrypt(app)

db = TinyDB('database.json')
users_table = db.table('users')
UserQuery = Query()

# USER REQUESTED CREDENTIALS
target_username = "you@#2110$ssef"
target_password = "1357911"

print(f"Creating fresh Admin user: {target_username}")
hashed_password = bcrypt.generate_password_hash(target_password).decode('utf-8')

users_table.insert({
    'username': target_username,
    'password': hashed_password,
    'full_name': 'Ramadan Admin',
    'phone': '01000000000',
    'role': 'admin',
    'project_location': 'HQ',
    'project_description': 'System Administrator',
    'project_percentage': 0,
    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
})

print("Database rebuilt successfully.")
