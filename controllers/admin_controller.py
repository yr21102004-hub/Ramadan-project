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
from models import UserModel, ChatModel, PaymentModel, SecurityLogModel, UnansweredQuestionsModel, LearnedAnswersModel, ContactModel, Database

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

@admin_bp.route('/admin/analytics')
@login_required
def analytics_dashboard():
    if current_user.role != 'admin':
        return "Access Denied", 403
        
    users = user_model.get_all()
    messages = contact_model.get_all()
    chats = chat_model.get_all()
    sec_logs = security_log_model.get_all()
    
    # Analytics Logic
    from collections import Counter
    
    # 1. Totals
    total_users_count = len(users)
    total_requests_count = len(messages)
    conversion_rate = round((total_requests_count / total_users_count * 100), 1) if total_users_count > 0 else 0
    
    # 2. Frequent AI Users (Almost Daily Activity)
    # Count unique days each user interacted
    user_ai_days = {} # user_name -> set of dates
    for c in chats:
        uname = c.get('user_name', 'Unknown')
        ts = c.get('timestamp', '')
        if ts:
            date = ts.split(' ')[0]
            if uname not in user_ai_days:
                user_ai_days[uname] = set()
            user_ai_days[uname].add(date)
            
    # Filter users active on 2 or more distinct days
    frequent_ai_stats = {u: len(d) for u, d in user_ai_days.items() if len(d) >= 2}
    # Sort by most active days
    sorted_frequent = sorted(frequent_ai_stats.items(), key=lambda x: x[1], reverse=True)
    
    analy_ai_labels = [x[0] for x in sorted_frequent]
    analy_ai_values = [x[1] for x in sorted_frequent]

    # 3. Top Visitors (All Time - Original Chart) [Keep limit for this one or remove as well?]
    # The user asked for AI chat specifically, but let's remove limit for visitors too if requested. 
    # For now, sticking to AI chat request.
    all_login_events = [l for l in sec_logs if 'Login' in l.get('event', '') and 'Success' in l.get('event', '')]
    all_visitors_list = []
    for l in all_login_events:
        details = l.get('details', '')
        if 'User ' in details:
            try:
                username = details.split('User ')[1].split(' ')[0]
                all_visitors_list.append(username)
            except: pass
    top_all_visitors_data = Counter(all_visitors_list).most_common() # Removed limit
    analy_all_visitors_labels = [x[0] for x in top_all_visitors_data]
    analy_all_visitors_values = [x[1] for x in top_all_visitors_data]

    # 4. Daily & Heavy Visitors (Today)
    from datetime import datetime
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_login_events = [l for l in sec_logs 
                          if 'Login' in l.get('event', '') 
                          and 'Success' in l.get('event', '')
                          and l.get('timestamp', '').startswith(today_str)]
    today_visitors_list = []
    for l in today_login_events:
        details = l.get('details', '')
        if 'User ' in details:
            try:
                username = details.split('User ')[1].split(' ')[0]
                today_visitors_list.append(username)
            except: pass
            
    today_visitor_counts = Counter(today_visitors_list)
    
    # Heavy Visitors (> 2 visits today)
    heavy_data = {k: v for k, v in today_visitor_counts.items() if v > 2}
    analy_heavy_labels = list(heavy_data.keys())
    analy_heavy_values = list(heavy_data.values())
    
    # Daily Visitors (Exactly 1 visit today)
    daily_data = {k: v for k, v in today_visitor_counts.items() if v == 1}
    analy_daily_labels = list(daily_data.keys())
    analy_daily_values = list(daily_data.values()) 
    
    # 5. Top Requested Services
    service_counts = Counter([m.get('service', 'general') for m in messages])
    service_map = {
        'modern-paints': 'دهانات حديثة',
        'gypsum-board': 'جبس بورد',
        'integrated-finishing': 'تشطيب متكامل',
        'putty-finishing': 'تأسيس ومعجون',
        'wallpaper': 'ورق حائط',
        'renovation': 'تجديد وترميم',
        'general': 'استفسار عام'
    }
    top_services_req_data = service_counts.most_common(5)
    top_services_req_labels = [service_map.get(x[0], x[0]) for x in top_services_req_data]
    top_services_req_values = [x[1] for x in top_services_req_data]
    
    # 6. Most Viewed Services
    service_views = []
    for l in sec_logs:
        if l.get('event') == 'Service View':
            details = l.get('details', '')
            if 'User viewed service: ' in details:
                svc_title = details.split('User viewed service: ')[1]
                service_views.append(svc_title)
    top_services_view_data = Counter(service_views).most_common(5)
    top_services_view_labels = [x[0] for x in top_services_view_data]
    top_services_view_values = [x[1] for x in top_services_view_data]

    # 7. Peak Hours (Activity by hour of day)
    hour_counts = Counter()
    for l in sec_logs:
        ts = l.get('timestamp', '')
        if ts and ' ' in ts:
            try:
                hour = ts.split(' ')[1].split(':')[0]
                hour_counts[hour] += 1
            except: pass
    # Ensure all 24 hours are represented
    sorted_hours = sorted([ (str(h).zfill(2), hour_counts.get(str(h).zfill(2), 0)) for h in range(24) ])
    peak_hours_labels = [x[0] + ":00" for x in sorted_hours]
    peak_hours_values = [x[1] for x in sorted_hours]

    # 8. AI Efficiency (Answered vs Unanswered)
    total_ai_msgs = len(chats)
    unanswered_msgs = len(unanswered)
    answered_msgs = max(0, total_ai_msgs - unanswered_msgs)
    ai_efficiency = {
        'labels': ['تم الرد', 'بدون إجابة'],
        'values': [answered_msgs, unanswered_msgs]
    }

    # 9. Page Popularity (General views)
    page_views = []
    for l in sec_logs:
        event = l.get('event', '')
        if 'View' in event or 'Page' in event:
            details = l.get('details', '')
            # Try to extract page name from details like "User viewed page: ..."
            if 'page: ' in details.lower():
                pname = details.lower().split('page: ')[1]
                page_views.append(pname)
            elif event == 'Service View':
                page_views.append('الخدمات')

    page_map = {
        '/': 'الرئيسية',
        'home': 'الرئيسية',
        'projects': 'معرض الأعمال',
        'about': 'من نحن',
        'contact': 'اتصل بنا',
        'services': 'الخدمات',
        'admin': 'لوحة التحكم',
        'login': 'تسجيل الدخول'
    }
    top_pages_data = Counter(page_views).most_common(5)
    page_pop_labels = [page_map.get(x[0], x[0]) for x in top_pages_data]
    page_pop_values = [x[1] for x in top_pages_data]

    return render_template('analytics.html', analytics={
                               'total_users': total_users_count,
                               'total_requests': total_requests_count,
                               'conversion_rate': conversion_rate,
                               
                               'top_ai_labels': analy_ai_labels,
                               'top_ai_values': analy_ai_values,
                               'top_all_visitors_labels': analy_all_visitors_labels,
                               'top_all_visitors_values': analy_all_visitors_values,
                               
                               'heavy_visitors_labels': analy_heavy_labels,
                               'heavy_visitors_values': analy_heavy_values,
                               'daily_visitors_labels': analy_daily_labels,
                               'daily_visitors_values': analy_daily_values,
                               
                               'top_services_req_labels': top_services_req_labels,
                               'top_services_req_values': top_services_req_values,
                               'top_services_view_labels': top_services_view_labels,
                               'top_services_view_values': top_services_view_values,
                               
                               'peak_hours_labels': peak_hours_labels,
                               'peak_hours_values': peak_hours_values,
                               'ai_efficiency': ai_efficiency,
                               'page_pop_labels': page_pop_labels,
                               'page_pop_values': page_pop_values
                           })

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
