"""
Flask Application with MVC Architecture and WebSocket Support
"""
from flask import Flask, render_template
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from dotenv import load_dotenv
import os

# Import WebSocket
from websockets import init_socketio

# Import Blueprints
from controllers.web_controller import web_bp
from controllers.auth_controller import auth_bp
from controllers.user_controller import user_bp
from controllers.admin_controller import admin_bp
from controllers.inspection_controller import inspection_bp
from controllers.chat_controller import chat_bp
from controllers.payment_controller import payment_bp
from controllers.rating_controller import rating_bp

# Import Models
from models.user import User

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'simple_secret_key')
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Initialize extensions
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Initialize WebSocket
socketio = init_socketio(app)

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(username):
    return User.get(username)

# Register Blueprints
app.register_blueprint(web_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(inspection_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(rating_bp)

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return "<h1>500 Internal Server Error</h1><p>Please try again.</p>", 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
