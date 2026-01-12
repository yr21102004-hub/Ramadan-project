from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from datetime import datetime
import os
import shutil
import io
import base64
import qrcode
import pyotp
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
from models import UserModel, ChatModel, PaymentModel, SecurityLogModel, UnansweredQuestionsModel, LearnedAnswersModel, Database

admin_bp = Blueprint('admin', __name__)
bcrypt = Bcrypt()

# Initialize models
user_model = UserModel()
chat_model = ChatModel()
payment_model = PaymentModel()
security_log_model = SecurityLogModel()
unanswered_model = UnansweredQuestionsModel()
learned_model = LearnedAnswersModel()
db = Database()

@admin_bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    users = user_model.get_all()
    messages = db.contacts.all()
    chats = chat_model.get_all()
    unanswered = unanswered_model.get_all()
    sec_logs = security_log_model.get_all()
    payments = payment_model.get_all()
    
    # Sort
    messages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    chats.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    unanswered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    sec_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    payments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # Chat Context Logic
    chats_by_user = {}
    for c in chats:
        uid = c.get('user_id', 'unknown')
        if uid not in chats_by_user:
            chats_by_user[uid] = []
        chats_by_user[uid].append(c)
    
    for uid in chats_by_user:
        chats_by_user[uid].sort(key=lambda x: x.get('timestamp', ''))

    def get_context(uid, q_time_str):
        full_history = chats_by_user.get(uid, [])
        if not full_history: return []
        try:
            q_time = datetime.strptime(q_time_str, "%Y-%m-%d %H:%M:%S")
        except:
            return full_history[-10:]
            
        context = []
        for h in full_history:
            try:
                h_time = datetime.strptime(h.get('timestamp', ''), "%Y-%m-%d %H:%M:%S")
                diff = (q_time - h_time).total_seconds()
                if 0 <= diff <= 1800:
                    context.append(h)
            except:
                continue
        return context[-15:]

    return render_template('admin.html', users=users, messages=messages, 
                           chats=chats, unanswered=unanswered, security_logs=sec_logs[:50],
                           payments=payments, chats_by_user=chats_by_user, get_context=get_context)

@admin_bp.route('/admin/add_user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        return "Access Denied", 403
        
    username = request.form.get('username')
    full_name = request.form.get('full_name')
    phone = request.form.get('phone')
    email = request.form.get('email', '')
    project_location = request.form.get('project_location')
    project_description = request.form.get('project_description', 'لا يوجد وصف')
    
    profile_image_path = None
    if 'profile_image' in request.files:
        file = request.files['profile_image']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
            unique_filename = f"{username}_{timestamp}.{file_extension}"
            
            upload_folder = os.path.join('static', 'user_images')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            profile_image_path = f"user_images/{unique_filename}"
    
    password = bcrypt.generate_password_hash(username).decode('utf-8') 

    if user_model.get_by_username(username):
        return "User already exists", 400

    user_model.create({
        'username': username,
        'password': password,
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'profile_image': profile_image_path,
        'project_location': project_location,
        'project_description': project_description,
        'project_percentage': 0,
        'role': 'user'
    })
    
    flash(f"تم إضافة المستخدم {username} بنجاح.")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/answer_question', methods=['POST'])
@login_required
def answer_question():
    if current_user.role != 'admin': return "Access Denied", 403
    question = request.form.get('question')
    answer = request.form.get('answer')
    unanswered_model.update_response(question, answer)
    flash("تم حفظ الإجابة بنجاح! سيقوم الذكاء الاصطناعي باستخدامها مستقبلاً.")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/delete_answered_question', methods=['POST'])
@login_required
def delete_answered_question():
    if current_user.role != 'admin': return "Access Denied", 403
    question = request.form.get('question')
    question_record = unanswered_model.get_by_question(question)
    
    if question_record and question_record.get('admin_response'):
        learned_model.create(question=question, answer=question_record.get('admin_response'))
        unanswered_model.delete(question)
        flash("تم نقل السؤال والإجابة إلى قاعدة المعرفة.")
    else:
        unanswered_model.delete(question)
        flash("تم حذف السؤال نهائياً.")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/learned_answers')
@login_required
def learned_answers():
    if current_user.role != 'admin': return "Access Denied", 403
    learned = learned_model.get_all()
    learned.sort(key=lambda x: x.get('learned_at', ''), reverse=True)
    return render_template('admin_learned.html', learned=learned)

@admin_bp.route('/admin/chats')
@login_required
def view_chats():
    if current_user.role != 'admin': return "Access Denied", 403
    chats = chat_model.get_all()
    return render_template('admin_chats.html', chats=chats)

@admin_bp.route('/admin/backup')
@login_required
def manual_backup():
    if current_user.role != 'admin': return "Access Denied", 403
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        if not os.path.exists('backups'): os.makedirs('backups')
        backup_path = f'backups/manual_backup_{timestamp}.json'
        shutil.copy2('database.json', backup_path)
        security_log_model.create("Manual Backup", f"Admin {current_user.username} created a backup", severity="low")
        flash("تم إنشاء النسخة الاحتياطية بنجاح.")
        return send_file(backup_path, as_attachment=True)
    except Exception as e:
        flash(f"فشل إنشاء النسخة الاحتياطية: {str(e)}")
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/setup_2fa')
@login_required
def setup_2fa():
    if not current_user.two_factor_secret:
        secret = pyotp.random_base32()
        user_model.update(current_user.username, {'two_factor_secret': secret})
        current_user.two_factor_secret = secret
    else:
        secret = current_user.two_factor_secret
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=current_user.username, issuer_name="Haj Ramadan Paints")
    img = qrcode.make(otp_uri)
    buf = io.BytesIO()
    img.save(buf)
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return render_template('setup_2fa.html', qr_code=qr_b64, secret=secret)

@admin_bp.route('/admin/toggle_2fa', methods=['POST'])
@login_required
def toggle_2fa():
    action = request.form.get('action')
    if action == 'enable':
        user_model.update(current_user.username, {'two_factor_enabled': True})
        flash('تم تفعيل المصادقة الثنائية بنجاح')
    else:
        user_model.update(current_user.username, {'two_factor_enabled': False})
        flash('تم تعطيل المصادقة الثنائية')
    return redirect(url_for('admin.admin_dashboard'))
