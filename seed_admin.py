from tinydb import TinyDB, Query
from werkzeug.security import generate_password_hash
from datetime import datetime

# Connect to DB
db = TinyDB('database.json')
users_table = db.table('users')

# Admin Credentials
username = "you@#2110$ssef"
password = "1357911"
full_name = "System Administrator"

# Check if user exists
User = Query()
existing_user = users_table.search(User.username == username)

if existing_user:
    # Update existing user to be admin with correct password
    print(f"Updating existing user '{username}' to Admin role...")
    users_table.update({
        'role': 'admin',
        'password': generate_password_hash(password),
        'full_name': full_name
    }, User.username == username)
else:
    # Create new admin user
    print(f"Creating new Admin user '{username}'...")
    users_table.insert({
        'username': username,
        'password': generate_password_hash(password),
        'full_name': full_name,
        'phone': '00000000000',
        'role': 'admin',
        'project_location': 'Main Office',
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

print("Admin account setup complete.")
print(f"Username: {username}")
print("Password: [HIDDEN]")
