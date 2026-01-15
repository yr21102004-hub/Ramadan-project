from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import random
import string
from models import UserModel, SecurityLogModel
from models.user import User

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()
user_model = UserModel()
security_model = SecurityLogModel()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_sms_otp(phone, code):
    """
    Simulates sending an SMS/WhatsApp OTP.
    Logs the code for the admin to see and flash for the user.
    """
    # In a real scenario, this would call a WhatsApp/SMS API
    print(f"DEBUG: Sending OTP {code} to {phone}")
    security_model.create("OTP Sent", f"Code {code} sent to {phone}", severity="low")
    return True

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        user_data = user_model.get_by_username(username)
        user = User.get(username) if user_data else None
        
        if user_data and bcrypt.check_password_hash(user_data.get('password', ''), password):
            if user.two_factor_enabled:
                otp = generate_otp()
                session['2fa_user'] = username
                session['otp_code'] = otp
                # Send the code
                send_sms_otp(user_data.get('phone'), otp)
                flash('تم إرسال رمز التحقق إلى هاتفك')
                return redirect(url_for('auth.verify_2fa'))
            
            login_user(user)
            return redirect(url_for('admin.admin_dashboard' if user.role == 'admin' else 'user.profile', username=username))
        
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
    # SECURITY BYPASS: SMS not sending, allowing direct login
    if current_user.is_authenticated:
        return redirect(url_for('admin.admin_dashboard' if current_user.role == 'admin' else 'user.profile', username=current_user.username))
    
    if '2fa_user' in session:
        user = User.get(session['2fa_user'])
        login_user(user)
        session.pop('2fa_user', None)
        session.pop('otp_code', None)
        flash('تم تسجيل الدخول (تم تجاوز التحقق لعدم وصول الرسالة)')
        return redirect(url_for('admin.admin_dashboard' if user.role == 'admin' else 'user.profile', username=user.username))
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        
        user_data = user_model.get_by_username(username)
        if user_data and user_data.get('phone') == phone:
            session['reset_user'] = username
            flash('تم تفعيل وضع استعادة الدخول')
            return redirect(url_for('auth.verify_code'))
        else:
            flash('البيانات المدخلة غير صحيحة')
            
    return render_template('forgot_password.html')

@auth_bp.route('/verify_code', methods=['GET', 'POST'])
def verify_code():
    # SECURITY BYPASS: Proceed directly to password reset
    if 'reset_user' in session:
        return redirect(url_for('auth.reset_new_password'))
    return redirect(url_for('auth.forgot_password'))

@auth_bp.route('/reset_new_password', methods=['GET', 'POST'])
def reset_new_password():
    if 'reset_user' not in session:
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user_model.update(session['reset_user'], {'password': hashed})
        session.pop('reset_user', None)
        session.pop('otp_code', None)
        flash('تم تغيير كلمة المرور بنجاح')
        return redirect(url_for('auth.login'))
        
    return render_template('reset_new_password.html')

@auth_bp.route('/verify/worker', methods=['GET', 'POST'])
@login_required
def submit_verification():
    """Submit worker verficiation documents"""
    if current_user.role != 'worker':
        return redirect(url_for('web.home'))
        
    if request.method == 'POST':
        try:
            import os
            from werkzeug.utils import secure_filename
            
            # Helper to save file
            def save_file(file, subfolder):
                if not file: return None
                filename = secure_filename(f"{current_user.username}_{file.filename}")
                path = os.path.join(f"static/uploads/{subfolder}", filename)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                file.save(path)
                return f"uploads/{subfolder}/{filename}"

            data = {
                'id_card_front': save_file(request.files.get('id_front'), 'verification'),
                'id_card_back': save_file(request.files.get('id_back'), 'verification'),
                'selfie_image': save_file(request.files.get('selfie'), 'verification'),
                'work_proof_type': request.form.get('proof_type')
            }
            
            # Proof Files
            proof_files = []
            if 'work_photos' in request.files:
                for f in request.files.getlist('work_photos'):
                    if f.filename:
                        proof_files.append(save_file(f, 'work_proof'))
            
            if 'work_video' in request.files:
                video = request.files.get('work_video')
                if video and video.filename:
                    proof_files.append(save_file(video, 'work_proof'))
            
            data['work_proof_files'] = proof_files
            
            user_model.submit_verification(current_user.username, data)
            return {'success': True}
            
        except Exception as e:
            print(e)
            return {'success': False, 'message': str(e)}

    return render_template('worker_verification.html')
