
from flask_bcrypt import Bcrypt
from flask import Flask
from werkzeug.security import check_password_hash as werkzeug_check_password_hash
import logging

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Hash from database.json for user "Jo"
stored_hash = "scrypt:32768:8:1$GUSHr2jikAnv6FqE$273dae64d8da69b085d7cdeb754bb8c24c160921f0979062653f00438d546e27bf9c6799f4dd12a9ea3d9db812e45f632cc8315193dd4d771753bb6418780584"
password_attempt = "admin123" # Guessing from context or trying a dummy. 
# actually the user said "admin123" was the password for the FIRST user in comments, maybe Jo is different.
# But the error is "Invalid Salt" (500), which happens BEFORE password verification result (True/False) is returned usually?
# No, invalid salt usually means verify() couldn't parse the hash format.

print(f"Testing hash: {stored_hash}")

try:
    print("Attempting Bcrypt...")
    bcrypt.check_password_hash(stored_hash, password_attempt)
    print("Bcrypt Success (Result doesn't matter, just no crash)")
except Exception as e:
    print(f"Bcrypt Failed with {type(e).__name__}: {e}")
    try:
        print("Attempting Werkzeug fallback...")
        res = werkzeug_check_password_hash(stored_hash, password_attempt)
        print(f"Werkzeug Success. Match: {res}")
    except Exception as ew:
        print(f"Werkzeug Failed with {type(ew).__name__}: {ew}")
