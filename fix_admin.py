from tinydb import TinyDB, Query
from flask_bcrypt import Bcrypt
from flask import Flask

app = Flask(__name__)
bcrypt = Bcrypt(app)
db = TinyDB('database.json')
users_table = db.table('users')

def add_admin():
    username = "you@#2110$ssef"
    password = "1357911"
    
    # Check if exists
    UserQuery = Query()
    existing = users_table.get(UserQuery.username == username)
    if existing:
        print(f"User {username} already exists. Updating password...")
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_table.update({'password': hashed_password}, UserQuery.username == username)
    else:
        print(f"Creating admin user: {username}")
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_table.insert({
            'username': username,
            'password': hashed_password,
            'full_name': 'Youssef Admin',
            'phone': '01129276218',
            'role': 'admin',
            'project_percentage': 100
        })
    print("Done!")

if __name__ == "__main__":
    with app.app_context():
        add_admin()
