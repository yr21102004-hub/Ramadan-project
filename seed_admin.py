from models.database import UserModel
from flask_bcrypt import Bcrypt
from datetime import datetime
import os

# Initialize
user_model = UserModel()
bcrypt = Bcrypt()

# Admin Credentials
username = os.environ.get('ADMIN_USERNAME', "you@#2110$ssef")
password = os.environ.get('ADMIN_PASSWORD', "1357911")
full_name = "System Administrator"

# Check if user exists
existing_user = user_model.get_by_username(username)

# Use bcrypt for consistency with the app
hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

if existing_user:
    # Update existing user to be admin with correct password
    print(f"Updating existing user '{username}' to Admin role...")
    user_model.update(username, {
        'role': 'admin',
        'password': hashed_password,
        'full_name': full_name
    })
else:
    # Create new admin user
    print(f"Creating new Admin user '{username}'...")
    user_model.create({
        'username': username,
        'password': hashed_password,
        'full_name': full_name,
        'phone': '00000000000',
        'role': 'admin',
        'project_location': 'Main Office',
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

print("Admin account setup complete.")
print(f"Username: {username}")
print("Password: [HIDDEN]")
