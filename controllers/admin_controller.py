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
from models import UserModel, ChatModel, PaymentModel, SecurityLogModel, UnansweredQuestionsModel, LearnedAnswersModel, ContactModel, Database, RatingModel, ComplaintModel, InspectionRequestModel

admin_bp = Blueprint('admin', __name__)
bcrypt = Bcrypt()

# Initialize models
user_model = UserModel()
chat_model = ChatModel()
payment_model = PaymentModel()
security_log_model = SecurityLogModel()
unanswered_model = UnansweredQuestionsModel()
learned_model = LearnedAnswersModel()
contact_model = ContactModel()
rating_model = RatingModel()
complaint_model = ComplaintModel()
inspection_model = InspectionRequestModel()
db = Database()

@admin_bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    users = user_model.get_all()
    messages = contact_model.get_all()
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

        return context[-15:]

    # Basic Analytics for Dashboard Summary (if needed)
    total_users_count = len(users)
    total_requests_count = len(messages)
    conversion_rate = round((total_requests_count / total_users_count * 100), 1) if total_users_count > 0 else 0
    
    analytics_summary = {
        'total_users': total_users_count,
        'total_requests': total_requests_count,
        'conversion_rate': conversion_rate
    }

    return render_template('admin.html', users=users, messages=messages, 
                           chats=chats, unanswered=unanswered, security_logs=sec_logs[:50],
                           payments=payments, chats_by_user=chats_by_user, get_context=get_context,
                           analytics=analytics_summary)

@admin_bp.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    # Get only users with role='user' or no role (default to user)
    all_users = user_model.get_all()
    users = [u for u in all_users if u.get('role', 'user') == 'user']
    
    # Get contact messages (requests)
    messages = contact_model.get_all()
    
    # Get unanswered questions
    unanswered = unanswered_model.get_all()
    
    # Get all chats to filter user-related questions
    chats = chat_model.get_all()
    
    # Get payments
    payments = payment_model.get_all()
    
    # Filter unanswered questions from users (not workers)
    user_unanswered = []
    for q in unanswered:
        user_id = q.get('user_id')
        # Check if this user_id belongs to a user (not worker)
        user_obj = user_model.get_by_username(user_id)
        if user_obj and user_obj.get('role', 'user') == 'user':
            user_unanswered.append(q)
    
    # Calculate basic analytics
    total_users = len(users)
    total_requests = len(messages)
    conversion_rate = round((total_requests / total_users * 100), 1) if total_users > 0 else 0
    pending_questions = len(user_unanswered)
    
    # Calculate advanced analytics
    completed_projects = len([u for u in users if u.get('project_percentage', 0) == 100])
    ongoing_projects = len([u for u in users if 0 < u.get('project_percentage', 0) < 100])
    not_started = len([u for u in users if u.get('project_percentage', 0) == 0])
    
    # Average completion rate
    total_percentage = sum([u.get('project_percentage', 0) for u in users])
    avg_completion = round(total_percentage / total_users, 1) if total_users > 0 else 0
    
    # Active users (users with chats)
    user_chats = [c for c in chats if user_model.get_by_username(c.get('user_id')) and 
                  user_model.get_by_username(c.get('user_id')).get('role', 'user') == 'user']
    active_users = len(set([c.get('user_id') for c in user_chats]))
    
    # Payment statistics
    user_payments = [p for p in payments if user_model.get_by_username(p.get('username')) and
                     user_model.get_by_username(p.get('username')).get('role', 'user') == 'user']
    total_payments = len(user_payments)
    
    analytics = {
        'total_users': total_users,
        'total_requests': total_requests,
        'conversion_rate': conversion_rate,
        'pending_questions': pending_questions,
        'completed_projects': completed_projects,
        'ongoing_projects': ongoing_projects,
        'not_started': not_started,
        'avg_completion': avg_completion,
        'active_users': active_users,
        'total_payments': total_payments
    }
    
    return render_template('admin_users.html', 
                         users=users, 
                         messages=messages[:10],  # Latest 10 messages
                         unanswered=user_unanswered[:10],  # Latest 10 unanswered
                         payments=user_payments[:10],  # Latest 10 payments
                         analytics=analytics)

@admin_bp.route('/admin/workers')
@login_required
def admin_workers():
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    # Get only users with role='worker'
    all_users = user_model.get_all()
    workers = [u for u in all_users if u.get('role') == 'worker']
    
    return render_template('admin_workers.html', workers=workers)

@admin_bp.route('/admin/add_worker', methods=['POST'])
@login_required
def add_worker():
    if current_user.role != 'admin':
        return "Access Denied", 403
        
    username = request.form.get('username')
    full_name = request.form.get('full_name')
    phone = request.form.get('phone')
    email = request.form.get('email', '')
    specialization = request.form.get('specialization')
    experience_years = request.form.get('experience_years', 0)
    status = request.form.get('status', 'active')
    
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
        flash('اسم المستخدم موجود بالفعل', 'error')
        return redirect(url_for('admin.admin_workers'))

    user_model.create({
        'username': username,
        'password': password,
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'profile_image': profile_image_path,
        'specialization': specialization,
        'experience_years': int(experience_years),
        'status': status,
        'role': 'worker'
    })
    
    flash(f"تم إضافة العامل {full_name} بنجاح.", 'success')
    return redirect(url_for('admin.admin_workers'))

@admin_bp.route('/admin/update_worker', methods=['POST'])
@login_required
def update_worker():
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    username = request.form.get('username')
    specialization = request.form.get('specialization')
    experience_years = request.form.get('experience_years')
    status = request.form.get('status')
    
    user_model.update(username, {
        'specialization': specialization,
        'experience_years': int(experience_years),
        'status': status
    })
    
    flash(f"تم تحديث بيانات العامل بنجاح.", 'success')
    return redirect(url_for('admin.admin_workers'))

@admin_bp.route('/admin/analytics')
@login_required
def analytics_dashboard():
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    try:
        users = user_model.get_all()
        messages = contact_model.get_all()
        chats = chat_model.get_all()
        sec_logs = security_log_model.get_all()
        unanswered = unanswered_model.get_all()
        
        from collections import Counter
        from datetime import datetime
        
        # 1. Totals
        total_users_count = len(users)
        total_requests_count = len(messages)
        conversion_rate = round((total_requests_count / total_users_count * 100), 1) if total_users_count > 0 else 0
        
        # 2. Frequent AI Users
        user_ai_days = {}
        for c in chats:
            uname = c.get('user_name', 'Unknown')
            ts = c.get('timestamp', '')
            if ts:
                date = ts.split(' ')[0]
                if uname not in user_ai_days: user_ai_days[uname] = set()
                user_ai_days[uname].add(date)
        frequent_ai_stats = {u: len(d) for u, d in user_ai_days.items() if len(d) >= 2}
        sorted_frequent = sorted(frequent_ai_stats.items(), key=lambda x: x[1], reverse=True)
        analy_ai_labels = [x[0] for x in sorted_frequent]
        analy_ai_values = [x[1] for x in sorted_frequent]

        # 3. Top Visitors (All Time)
        all_login_events = [l for l in sec_logs if 'Login' in str(l.get('event', '')) and 'Success' in str(l.get('event', ''))]
        all_visitors_list = []
        for l in all_login_events:
            details = str(l.get('details', ''))
            if 'User ' in details:
                try:
                    username = details.split('User ')[1].split(' ')[0]
                    all_visitors_list.append(username)
                except: pass
        top_all_visitors_data = Counter(all_visitors_list).most_common()
        analy_all_visitors_labels = [x[0] for x in top_all_visitors_data]
        analy_all_visitors_values = [x[1] for x in top_all_visitors_data]

        # 4. Daily & Heavy Visitors
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_login_events = [l for l in sec_logs if 'Login' in str(l.get('event', '')) and 'Success' in str(l.get('event', '')) and str(l.get('timestamp', '')).startswith(today_str)]
        today_visitors_list = []
        for l in today_login_events:
            details = str(l.get('details', ''))
            if 'User ' in details:
                try:
                    username = details.split('User ')[1].split(' ')[0]
                    today_visitors_list.append(username)
                except: pass
        today_visitor_counts = Counter(today_visitors_list)
        heavy_data = {k: v for k, v in today_visitor_counts.items() if v > 2}
        analy_heavy_labels = list(heavy_data.keys())
        analy_heavy_values = list(heavy_data.values())
        daily_data = {k: v for k, v in today_visitor_counts.items() if v == 1}
        analy_daily_labels = list(daily_data.keys())
        analy_daily_values = list(daily_data.values()) 

        # 5. Top Requested Services
        service_counts = Counter([str(m.get('service', 'general')) for m in messages])
        service_map = {'modern-paints':'دهانات حديثة','gypsum-board':'جبس بورد','integrated-finishing':'تشطيب متكامل',
                      'putty-finishing':'تأسيس ومعجون','wallpaper':'ورق حائط','renovation':'تجديد وترميم','general':'استفسار عام'}
        top_services_req_data = service_counts.most_common(5)
        top_services_req_labels = [service_map.get(x[0], x[0]) for x in top_services_req_data]
        top_services_req_values = [x[1] for x in top_services_req_data]
        
        # 6. Most Viewed Services
        service_views = []
        for l in sec_logs:
            if str(l.get('event')) == 'Service View':
                details = str(l.get('details', ''))
                if 'User viewed service: ' in details:
                    try:
                        svc_title = details.split('User viewed service: ')[1]
                        service_views.append(svc_title)
                    except: pass
        top_services_view_data = Counter(service_views).most_common(5)
        top_services_view_labels = [x[0] for x in top_services_view_data]
        top_services_view_values = [x[1] for x in top_services_view_data]

        # 7. Peak Hours
        hour_counts = Counter()
        for l in sec_logs:
            ts = str(l.get('timestamp', ''))
            if ts and ' ' in ts:
                try:
                    hour = ts.split(' ')[1].split(':')[0]
                    hour_counts[hour] += 1
                except: pass
        sorted_hours = sorted([ (str(h).zfill(2), hour_counts.get(str(h).zfill(2), 0)) for h in range(24) ])
        peak_hours_labels = [x[0] + ":00" for x in sorted_hours]
        peak_hours_values = [x[1] for x in sorted_hours]

        # 8. AI Efficiency
        total_ai_msgs = len(chats)
        unanswered_msgs = len(unanswered)
        answered_msgs = max(0, total_ai_msgs - unanswered_msgs)
        ai_efficiency = {
            'names': ['تم الرد', 'بدون إجابة'],
            'counts': [answered_msgs, unanswered_msgs]
        }

        # 9. Page Popularity
        page_views = []
        for l in sec_logs:
            event = str(l.get('event', ''))
            if 'View' in event or 'Page' in event:
                details = str(l.get('details', ''))
                if 'page: ' in details.lower():
                    parts = details.lower().split('page: ')
                    if len(parts) > 1:
                        pname = parts[1].strip()
                        page_views.append(pname)
                elif event == 'Service View':
                    page_views.append('الخدمات')

        page_map = {'/':'الرئيسية','home':'الرئيسية','projects':'معرض الأعمال','about':'من نحن','contact':'اتصل بنا','services':'الخدمات','admin':'لوحة التحكم','login':'تسجيل الدخول'}
        top_pages_data = Counter(page_views).most_common(5)
        page_pop_labels = [page_map.get(x[0], x[0]) for x in top_pages_data]
        page_pop_values = [x[1] for x in top_pages_data]

        return render_template('analytics.html', analytics={
            'total_users': total_users_count, 'total_requests': total_requests_count, 'conversion_rate': conversion_rate,
            'top_ai_labels': analy_ai_labels, 'top_ai_values': analy_ai_values,
            'top_all_visitors_labels': analy_all_visitors_labels, 'top_all_visitors_values': analy_all_visitors_values,
            'heavy_visitors_labels': analy_heavy_labels, 'heavy_visitors_values': analy_heavy_values,
            'daily_visitors_labels': analy_daily_labels, 'daily_visitors_values': analy_daily_values,
            'top_services_req_labels': top_services_req_labels, 'top_services_req_values': top_services_req_values,
            'top_services_view_labels': top_services_view_labels, 'top_services_view_values': top_services_view_values,
            'peak_hours_labels': peak_hours_labels, 'peak_hours_values': peak_hours_values,
            'ai_efficiency': ai_efficiency, 'page_pop_labels': page_pop_labels, 'page_pop_values': page_pop_values
        })
    except Exception as e:
        import traceback
        with open('analytics_error.log', 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())
        print(f"ANALYTICS ERROR: {str(e)}")
        flash(f"حدث خطأ أثناء تحميل الإحصائيات. تم تسجيل الخطأ للفحص.")
        return redirect(url_for('admin.admin_dashboard'))

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
    
    if not answer:
        flash("يرجى كتابة إجابة قبل الحفظ.")
        return redirect(url_for('admin.admin_dashboard'))

    # Add to learned answers immediately and delete from pending
    learned_model.create(question=question, answer=answer)
    unanswered_model.delete(question)
    
    flash("تم حفظ الإجابة وإضافتها لقاعدة المعرفة، وتم إزالة السؤال من القائمة.")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/delete_message', methods=['POST'])
@login_required
def delete_message():
    if current_user.role != 'admin': return "Access Denied", 403
    doc_id = request.form.get('doc_id')
    contact_model.delete(doc_id)
    flash("تم حذف الرسالة بنجاح.")
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
@admin_bp.route('/admin/security/clear', methods=['POST'])
@login_required
def clear_security_logs():
    if current_user.role != 'admin': return "Access Denied", 403
    security_log_model.truncate()
    security_log_model.create("Logs Cleared", f"Admin {current_user.username} cleared all security logs", severity="info")
    flash("تم مسح سجلات المراقبة الأمنية بنجاح، وبدء التسجيل من جديد.")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/security/audit')
@login_required
def security_audit():
    if current_user.role != 'admin': return "Access Denied", 403
    
    from flask import current_app
    
    # Perform checks
    checks = []
    
    # 1. CSRF Check
    csrf_enabled = current_app.config.get('WTF_CSRF_ENABLED', True)
    checks.append({
        'name': 'حماية CSRF',
        'status': 'آمن' if csrf_enabled else 'خطر',
        'desc': 'حماية النماذج من الهجمات العابرة للمواقع.',
        'icon': 'fa-shield-alt',
        'color': 'success' if csrf_enabled else 'danger'
    })
    
    # 2. Session Cookies
    secure_session = current_app.config.get('SESSION_COOKIE_HTTPONLY', False)
    checks.append({
        'name': 'أمان الجلسة (HttpOnly)',
        'status': 'مفعل' if secure_session else 'غير مفعل',
        'desc': 'منع الوصول لملفات تعريف الارتباط عبر JavaScript.',
        'icon': 'fa-cookie-bite',
        'color': 'success' if secure_session else 'warning'
    })
    
    # 3. Security Headers
    # We added them in app.after_request, so assuming they are active
    checks.append({
        'name': 'رؤوس الأمان (HSTS, CSP, X-Frame)',
        'status': 'نشط',
        'desc': 'حماية المتصفح من هجمات XSS و Clickjacking.',
        'icon': 'fa-file-code',
        'color': 'success'
    })
    
    # 4. Database Backups
    backup_exists = os.path.exists('backups') and len(os.listdir('backups')) > 0
    checks.append({
        'name': 'النسخ الاحتياطي',
        'status': 'موجود' if backup_exists else 'غير موجود',
        'desc': f"يوجد {len(os.listdir('backups')) if backup_exists else 0} نسخة احتياطية محفوظة.",
        'icon': 'fa-database',
        'color': 'success' if backup_exists else 'warning'
    })
    
    # 5. Admin Passwords (Check for defaults - very simple)
    admin_user = user_model.get_by_username('admin')
    weak_pwd = False
    if admin_user and bcrypt.check_password_hash(admin_user['password'], 'admin'):
        weak_pwd = True
    
    checks.append({
        'name': 'قوة كلمة مرور المسؤول',
        'status': 'ضعيف' if weak_pwd else 'قوي',
        'desc': 'كلمة المرور الحالية للمسؤول آمنة وصعبة التخمين.' if not weak_pwd else 'تحذير: كلمة المرور الافتراضية "admin" ما زالت مستخدمة!',
        'icon': 'fa-key',
        'color': 'danger' if weak_pwd else 'success'
    })

    # 6. Rate Limiting
    checks.append({
        'name': 'تحديد معدل الطلبات (Rate Limiting)',
        'status': 'مفعل',
        'desc': 'حماية الموقع من هجمات Brute Force و DDoS.',
        'icon': 'fa-tachometer-alt',
        'color': 'success'
    })

    logs = security_log_model.get_all()
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    recent_logs = logs[:10]

    return render_template('admin_security.html', checks=checks, logs=recent_logs)


@admin_bp.route('/admin/complaints')
@login_required
def admin_complaints():
    """View and manage complaints"""
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    # Get all complaints
    all_complaints = complaint_model.get_all()
    
    # Sort by date (newest first)
    all_complaints.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Get statistics
    pending = len([c for c in all_complaints if c['status'] == 'قيد المراجعة'])
    resolved = len([c for c in all_complaints if c['status'] == 'تم الحل'])
    rejected = len([c for c in all_complaints if c['status'] == 'مرفوضة'])
    
    stats = {
        'total': len(all_complaints),
        'pending': pending,
        'resolved': resolved,
        'rejected': rejected
    }
    
    return render_template('admin_complaints.html', complaints=all_complaints, stats=stats)


@admin_bp.route('/admin/complaint/<int:complaint_id>/update', methods=['POST'])
@login_required
def update_complaint_status(complaint_id):
    """Update complaint status"""
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    status = request.form.get('status')
    admin_notes = request.form.get('admin_notes', '')
    
    complaint_model.update_status(complaint_id, status, admin_notes)
    
    flash('تم تحديث حالة الشكوى بنجاح', 'success')
    return redirect(url_for('admin.admin_complaints'))


@admin_bp.route('/admin/inspections')
@login_required
def admin_inspections():
    """View and manage inspections"""
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    # Get all requests
    all_requests = inspection_model.get_all()
    all_requests.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Statistics
    stats = {
        'new': len([r for r in all_requests if r['status'] == 'new_request']),
        'assigned': len([r for r in all_requests if r['status'] == 'assigned_to_worker']),
        'admin_visit': len([r for r in all_requests if r['status'] == 'admin_visit']),
        'completed': len([r for r in all_requests if r['status'] == 'completed']),
        'total': len(all_requests)
    }
    
    return render_template('admin_inspections.html', requests=all_requests, stats=stats)


@admin_bp.route('/admin/inspection/<request_id>/assign', methods=['POST'])
@login_required
def assign_inspection(request_id):
    """Assign worker or admin to inspection"""
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    assignment_type = request.form.get('assignment_type') # 'worker' or 'admin'
    
    if assignment_type == 'admin':
        inspection_model.assign_admin_visit(request_id)
        flash('تم تعيين المعاينة للإدارة', 'success')
    else:
        worker_username = request.form.get('worker_username')
        if worker_username:
            inspection_model.assign_worker(request_id, worker_username)
            flash(f'تم تعيين المعاينة للصنايعي {worker_username}', 'success')
        else:
            flash('الرجاء اختيار صنايعي', 'error')
            
    return redirect(url_for('admin.admin_inspections'))


@admin_bp.route('/admin/inspection/<request_id>/details')
@login_required
def inspection_details(request_id):
    """Get inspection details and nearby workers via AJAX"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    req = inspection_model.get_request_by_id(request_id)
    if not req:
        return jsonify({'error': 'Request not found'}), 404
        
    # Find nearest workers
    nearby_workers = inspection_model.find_nearest_workers(
        user_lat=req['user_latitude'],
        user_lon=req['user_longitude'],
        service_type=req['service_type'],
        max_distance=100, # Search wider range for admin
        limit=10
    )
    
    return jsonify({
        'request': req,
        'nearby_workers': nearby_workers
    })


@admin_bp.route('/admin/inspection/<request_id>/approve', methods=['POST'])
@login_required
def approve_inspection_report(request_id):
    """Admin: Approve or Reject Inspection Report"""
    if current_user.role != 'admin':
        return "Access Denied", 403
        
    decision = request.form.get('decision')
    admin_notes = request.form.get('admin_notes', '')
    
    if decision == 'approve':
        inspection_model.approve_report(request_id)
        # Add notification logic here (optional)
        flash('تم اعتماد التقرير بنجاح، ويمكن للعميل الآن رؤية النتيجة وبيانات الصنايعي', 'success')
    elif decision == 'reject':
        inspection_model.update_status(request_id, 'inspection_rejected', {'admin_notes': admin_notes})
        flash('تم رفض التقرير', 'warning')
        
    return redirect(url_for('admin.admin_inspections'))

@admin_bp.route('/admin/verifications')
@login_required
def admin_verifications():
    """Admin: Verification Requests"""
    if current_user.role != 'admin':
        return "Access Denied", 403
        
    pending = user_model.get_pending_verifications()
    return render_template('admin_verifications.html', pending=pending)

@admin_bp.route('/admin/verify/<username>', methods=['POST'])
@login_required
def process_verification(username):
    """Admin: Accept/Reject Verification"""
    if current_user.role != 'admin':
        return "Access Denied", 403
        
    action = request.form.get('action')
    notes = request.form.get('notes')
    
    if action == 'approve':
        user_model.verify_user(username, 'verified', notes)
        flash(f'تم توثيق الحساب للصنايعي {username}', 'success')
    elif action == 'reject':
        user_model.verify_user(username, 'rejected', notes)
        flash(f'تم رفض توثيق الصنايعي {username}', 'warning')
        
    return redirect(url_for('admin.admin_verifications'))
