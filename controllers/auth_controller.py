from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import pyotp
from models import UserModel, SecurityLogModel
from models.user import User

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()
user_model = UserModel()
security_model = SecurityLogModel()
# Note: Limiter is usually attached to app. We can use decorators if limiter is initialized with app later or use global limiter.
# For simplicity in this refactor, we omit limiter decorator here or we need to import the global limiter object.

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        user_data = user_model.get_by_username(username)
        # Use User class to wrap data
        user = User.get(username) if user_data else None
        
        if user_data and bcrypt.check_password_hash(user_data.get('password', ''), password):
            if user.two_factor_enabled:
                session['2fa_user'] = username
                return redirect(url_for('auth.verify_2fa'))
            
            login_user(user)
            return redirect(url_for('admin.admin_dashboard' if user.role == 'admin' else 'web.index'))
        
        security_model.create("Failed Login", f"Attempt for username: {username}", severity="medium")
        flash('اسم المستخدم أو كلمة المرور غير صحيحة')

    return render_template('login.html', captcha_q=None)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('web.index'))

@auth_bp.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    if '2fa_user' not in session:
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        code = request.form.get('code')
        username = session['2fa_user']
        user = User.get(username)
        
        if not user:
            session.pop('2fa_user', None)
            return redirect(url_for('auth.login'))
            
        totp = pyotp.TOTP(user.two_factor_secret)
        if totp.verify(code):
            login_user(user)
            session.pop('2fa_user', None)
            flash('تم تسجيل الدخول بنجاح')
            return redirect(url_for('admin.admin_dashboard' if user.role == 'admin' else 'web.index'))
        else:
            flash('رمز التحقق غير صحيح')
            
    return render_template('verify_2fa.html')
@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        flash("هذه الميزة غير مفعلة حالياً في النسخة المبسطة.")
    return render_template('forgot_password.html')

@auth_bp.route('/verify_code', methods=['GET', 'POST'])
def verify_code():
    return render_template('verify_code.html')

@auth_bp.route('/reset_new_password', methods=['GET', 'POST'])
def reset_new_password():
    return render_template('reset_new_password.html')
