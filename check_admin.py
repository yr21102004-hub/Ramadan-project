from tinydb import TinyDB, Query
db = TinyDB('database.json')
users = db.table('users')
admin = users.search(Query().username == 'admin')
if admin:
    print(f"Admin Hash: {admin[0]['password']}")
else:
    print("Admin not found")
