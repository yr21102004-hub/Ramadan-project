from flask_login import UserMixin
from models.database import UserModel

class User(UserMixin):
    """
    User class for Flask-Login compatibility.
    Wraps the user dictionary from TinyDB.
    """
    def __init__(self, user_data):
        self.id = user_data.get('username')
        self.username = user_data.get('username')
        self.role = user_data.get('role', 'user')
        self.full_name = user_data.get('full_name')
        self.two_factor_enabled = user_data.get('two_factor_enabled', False)
        self.two_factor_secret = user_data.get('two_factor_secret')

    @staticmethod
    def get(username):
        user_model = UserModel()
        user_data = user_model.get_by_username(username)
        if user_data:
            return User(user_data)
        return None
