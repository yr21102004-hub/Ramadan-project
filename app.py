from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from tinydb import TinyDB, Query
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os
import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, generate_csrf
from dotenv import load_dotenv
import pyotp
import qrcode
import io
import base64

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Basic Secret Key
app.secret_key = os.getenv('SECRET_KEY', 'simple_secret_key')
app.config.update(
    SESSION_COOKIE_SECURE=False, # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Initialize Minimal Extensions
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

# Rate Limiter Setup
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Database Setup
db = TinyDB('database.json')
users_table = db.table('users')
chats_table = db.table('chat_logs')
contacts_table = db.table('contacts')
unanswered_table = db.table('unanswered_questions')
security_logs = db.table('security_audit_logs')
payments_table = db.table('payments')

def auto_backup():
    """Creates an automatic backup of the database."""
    try:
        import shutil
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        if not os.path.exists('backups'):
            os.makedirs('backups')
        shutil.copy2('database.json', f'backups/db_backup_{timestamp}.json')
        # Keep only last 10 backups
        backups = sorted([f for f in os.listdir('backups') if f.endswith('.json')])
        if len(backups) > 10:
            os.remove(os.path.join('backups', backups[0]))
    except Exception as e:
        print(f"Backup failed: {e}")

def log_security_event(event_type, details, severity="low"):
    """Logs security events and triggers protections."""
    security_logs.insert({
        'event': event_type,
        'details': details,
        'severity': severity,
        'ip': request.remote_addr,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    # If high severity or repeated, we could implement auto-blocking here
    if severity == "high":
        auto_backup() # Critical event triggers immediate backup before any potential data loss


# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Class
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data.get('username')
        self.username = user_data.get('username')
        self.role = user_data.get('role', 'user')
        self.full_name = user_data.get('full_name')
        self.two_factor_enabled = user_data.get('two_factor_enabled', False)
        self.two_factor_secret = user_data.get('two_factor_secret')

    @staticmethod
    def get(username):
        UserQuery = Query()
        user_data = users_table.get(UserQuery.username == username)
        if user_data:
            return User(user_data)
        return None

@login_manager.user_loader
def load_user(username):
    return User.get(username)

# Routes
@app.route('/')
def index():
    return render_template('home.html')

# PWA Routes
@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/sw.js')
def service_worker():
    return app.send_static_file('sw.js')

# Data for Services
SERVICES_DATA = {
    'modern-paints': {
        'title': 'دهانات حديثة',
        'description': 'نستخدم أحدث تقنيات الدهانات الديكورية والكمبيوتر لإضفاء لمسة جمالية فريدة على منزلك. لدينا مجموعة واسعة من الألوان والتأثيرات التي تناسب جميع الأذواق، سواء كنت تبحث عن طابع كلاسيكي أو مودرن.',
        'features': [
            'دهانات جوتن وسايبس عالية الجودة',
            'دهانات قطيفة وشمواه',
            'تنسيق ألوان احترافي'
        ],
        'image': 'modern_paints.png'
    },
    'gypsum-board': {
        'title': 'جبس بورد (تشطيب ودهانات)',
        'description': 'نقدم أرقى مستويات التشطيب لأعمال الجبس بورد والأسقف المعلقة. تخصصنا هو إظهار جمال التصميم من خلال مراحل المعجون والدهانات الدقيقة، لضمان سطح ناعم ومثالي يبرز روعة الإضاءة والتصميم. (نحن متخصصون في بند الدهانات والتشطيب وليس التركيب).',
        'features': [
            'معالجة فواصل الجبس بورد بمهارة عالية',
            'تشطيب ناعم (Full Finish) للأسقف ومكتبات الشاشات',
            'تنسيق ألوان الدهانات مع الإضاءة المخفية',
            'دهانات عالية الجودة تدوم طويلاً'
        ],
        'image': 'gypsum_finish.png'
    },
    'integrated-finishing': {
        'title': 'تشطيب متكامل',
        'description': 'خدمة تشطيب ودهانات متكاملة تضمن لك جودة عالية ولمسات فنية راقية. نهتم بأدق التفاصيل لضمان مظهر جمالي يتناسب مع ذوقك الرفيع، سواء للواجهات الخارجية أو الديكورات الداخلية.',
        'features': [
            'تشطيب دهانات بكافة انواعها داخلية و خارجية',
            'أعمال المحارة والجبس',
            'ديكورات وتجاليد حوائط'
        ],
        'image': 'integrated_finishing.png'
    },
    'putty-finishing': {
        'title': 'تشطيب كامل ومعجون',
        'description': 'تعتبر مرحلة المعجون هي الأساس لأي دهان ناجح. نحن نولي اهتماماً خاصاً لهذه المرحلة، حيث نقوم بتجهيز الحوائط بمهارة فائقة لضمان ملمس ناعم كالحرير وخالٍ من العيوب.',
        'features': [
            'سحب طبقات معجون متعددة لتسوية الحوائط',
            'صنفرة ميكانيكية ويدوية لإزالة الشوائب',
            'علاج عيوب المحارة والزوايا',
            'دهانات أساس (سيلر) عالية الجودة'
        ],
        'image': 'putty_finishing.png'
    },
    'wallpaper': {
        'title': 'تركيب ورق حائط',
        'description': 'أضف لمسة من الفخامة إلى غرفتك مع أحدث تشكيلات ورق الحائط. فنيونا محترفون في التركيب لضمان عدم وجود فواصل ظاهرة أو فقاعات هواء، مع الحفاظ على تناسق النقوش.',
        'features': [
            'تركيب جميع أنواع الورق (فينيل، قماش، 3D)',
            'تجهيز الحوائط قبل التركيب لضمان الثبات',
            'دقة متناهية في قص ولصق الأطراف',
            'تصميمات عصرية وكلاسيكية'
        ],
        'image': 'wallpaper.png'
    },
    'renovation': {
        'title': 'تجديد وترميم',
        'description': 'نعيد الحياة للمنازل والمباني القديمة. نقوم بمعالجة كافة مشاكل الرطوبة والشروخ، وتحديث شبكات المرافق، وتغيير الديكور بالكامل ليواكب أحدث الصيحات.',
        'features': [
            'علاج الشروخ وتصدعات الجدران',
            'حلول جذرية لمشاكل الرطوبة والنشع',
            'تحديث الأرضيات والدهانات',
            'إعادة توزيع الكهرباء والسباكة'
        ],
        'image': 'renovation.jpg'
    }
}

@app.route('/service/<service_id>')
def service_detail(service_id):
    service = SERVICES_DATA.get(service_id)
    if not service:
        return render_template('404.html'), 404
    return render_template('service_detail.html', service=service)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return "<h1>500 Internal Server Error</h1><p>Please try again.</p>", 500

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        # Condition: User MUST have an account (be logged in)
        if not current_user.is_authenticated:
            # Handle failure due to no account
            payments_table.insert({
                'username': 'Guest',
                'full_name': 'زائر غير مسجل',
                'amount': request.form.get('amount', '0'),
                'method': request.form.get('method', 'غير معروف'),
                'transaction_id': 'N/A',
                'status': 'failed (No Account)',
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            log_security_event("Unauthenticated Payment", "محاولة دفع بدون حساب", severity="medium")
            flash('لا يمكن إتمام عملية التحويل إلا لمن لديهم حساب على الموقع. يرجى تسجيل الدخول أولاً.')
            return redirect(url_for('login'))
            
        try:
            amount = request.form.get('amount')
            method = request.form.get('method')
            transaction_id = request.form.get('transaction_id')
            
            if not amount or float(amount) <= 0:
                raise ValueError("مبلغ غير صحيح")

            # Successfully logged as pending
            payments_table.insert({
                'username': current_user.username,
                'full_name': current_user.full_name,
                'amount': amount,
                'method': method,
                'transaction_id': transaction_id,
                'status': 'success (Pending Approval)',
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash('تم إرسال بيانات الدفع بنجاح، سيتم مراجعتها من قبل الإدارة.')
        except Exception as e:
            # Log failure
            payments_table.insert({
                'username': current_user.username,
                'full_name': current_user.full_name,
                'amount': request.form.get('amount', '0'),
                'method': request.form.get('method', 'unknown'),
                'transaction_id': request.form.get('transaction_id', 'N/A'),
                'status': f'failed ({str(e)})',
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash('فشلت محاولة تسجيل الدفع. تأكد من إدخال البيانات بشكل صحيح.')
            
        return redirect(url_for('index'))
    
    # GET request check
    if not current_user.is_authenticated:
        flash('يرجى تسجيل الدخول للوصول لصفحة الدفع')
        return redirect(url_for('login'))
        
    return render_template('payment.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        user = User.get(username)
        
        # Security: Fetch raw data to check hash
        UserQuery = Query()
        user_data = users_table.get(UserQuery.username == username)
        
        if user_data and bcrypt.check_password_hash(user_data.get('password', ''), password):
            if user.two_factor_enabled:
                # Store username in session temporarily to verify 2FA
                session['2fa_user'] = username
                return redirect(url_for('verify_2fa'))
            
            login_user(user)
            auto_backup() # Autonomous Resilience: Backup state on successful admin/user session start
            return redirect(url_for('admin' if user.role == 'admin' else 'index'))
        
        # Autonomous Logging: Track and flag failed attempts
        log_security_event("Failed Login", f"Attempt for username: {username}", severity="medium")
        flash('اسم المستخدم أو كلمة المرور غير صحيحة')

    return render_template('login.html', captcha_q=None)

@app.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    if '2fa_user' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        code = request.form.get('code')
        username = session['2fa_user']
        user = User.get(username)
        
        if not user:
            session.pop('2fa_user', None)
            return redirect(url_for('login'))
            
        totp = pyotp.TOTP(user.two_factor_secret)
        if totp.verify(code):
            login_user(user)
            session.pop('2fa_user', None)
            flash('تم تسجيل الدخول بنجاح')
            return redirect(url_for('admin' if user.role == 'admin' else 'index'))
        else:
            flash('رمز التحقق غير صحيح')
            
    return render_template('verify_2fa.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        password = request.form.get('password')
        phone = request.form.get('phone')
        email = request.form.get('email', '')
        project_description = request.form.get('project_description', 'لا يوجد وصف للمشروع')
        
        if User.get(username):
            flash('اسم المستخدم مسجل بالفعل')
            return redirect(url_for('register'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        role = 'user'
        if len(users_table.all()) == 0:
            role = 'admin'
            
        users_table.insert({
            'username': username,
            'password': hashed_password,
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'role': role,
            'project_location': 'غير محدد',
            'project_description': project_description,
            'project_percentage': 0,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        login_user(User.get(username))
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        flash("هذه الميزة غير مفعلة حالياً في النسخة المبسطة.")
    return render_template('forgot_password.html')

@app.route('/verify_code', methods=['GET', 'POST'])
def verify_code():
    return render_template('verify_code.html')

@app.route('/reset_new_password', methods=['GET', 'POST'])
def reset_new_password():
    return render_template('reset_new_password.html')

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return "Access Denied", 403
        
    users = users_table.all()
    messages = contacts_table.all()
    chats = chats_table.all()
    unanswered = unanswered_table.all()
    sec_logs = security_logs.all()
    payments = payments_table.all()
    
    # Sort everything
    messages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    chats.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    unanswered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    sec_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    payments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # Prepare chat history grouped by user_id for context
    chats_by_user = {}
    for c in chats:
        uid = c.get('user_id', 'unknown')
        if uid not in chats_by_user:
            chats_by_user[uid] = []
        chats_by_user[uid].append(c)
    
    # Sort each user's history by time ascending
    for uid in chats_by_user:
        chats_by_user[uid].sort(key=lambda x: x.get('timestamp', ''))

    # Help function to group by "session" (within 30 mins)
    def get_context(uid, q_time_str):
        full_history = chats_by_user.get(uid, [])
        if not full_history: return []
        
        try:
            q_time = datetime.strptime(q_time_str, "%Y-%m-%d %H:%M:%S")
        except:
            return full_history[-10:] # Fallback
            
        # Only show messages within 30 minutes of the question
        # AND limit to the 15 most recent messages in that window.
        context = []
        for h in full_history:
            try:
                h_time = datetime.strptime(h.get('timestamp', ''), "%Y-%m-%d %H:%M:%S")
                diff = (q_time - h_time).total_seconds()
                # If message is within 30 mins (1800s) AND is not in the future (diff >= 0)
                if 0 <= diff <= 1800:
                    context.append(h)
            except:
                continue
                
        return context[-15:]

    return render_template('admin.html', users=users, messages=messages, 
                           chats=chats, unanswered=unanswered, security_logs=sec_logs[:50],
                           payments=payments, chats_by_user=chats_by_user, get_context=get_context)

@app.route('/admin/add_user', methods=['POST'])
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
    
    password = bcrypt.generate_password_hash(username).decode('utf-8') 

    if User.get(username):
        return "User already exists", 400

    users_table.insert({
        'username': username,
        'password': password,
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'project_location': project_location,
        'project_description': project_description,
        'project_percentage': 0,
        'role': 'user',
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    flash(f"تم إضافة المستخدم {username} بنجاح.")
    return redirect(url_for('admin'))

@app.route('/admin/update_project_percentage', methods=['POST'])
@login_required
def update_project_percentage():
    if current_user.role != 'admin':
        return "Access Denied", 403
        
    username = request.form.get('username')
    percentage = request.form.get('percentage')
    
    try:
        percentage = int(percentage)
        if percentage < 0: percentage = 0
        if percentage > 100: percentage = 100
    except:
        percentage = 0
        
    UserQuery = Query()
    users_table.update({'project_percentage': percentage}, UserQuery.username == username)
    flash(f"تم تحديث نسبة الإنجاز للعميل {username} بنجاح.")
    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<username>', methods=['POST'])
@login_required
def delete_user(username):
    if current_user.role != 'admin':
        return "Access Denied", 403

    UserQuery = Query()
    users_table.remove(UserQuery.username == username)
    flash(f"تم حذف المستخدم {username} بنجاح.")
    return redirect(url_for('admin'))

@app.route('/admin/answer_question', methods=['POST'])
@login_required
def answer_question():
    if current_user.role != 'admin': return "Access Denied", 403
    question = request.form.get('question')
    answer = request.form.get('answer')
    
    UQuest = Query()
    unanswered_table.update({'admin_response': answer}, UQuest.question == question)
    flash("تم حفظ الإجابة بنجاح! سيقوم الذكاء الاصطناعي باستخدامها مستقبلاً.")
    return redirect(url_for('admin'))

@app.route('/admin/chats')
@login_required
def admin_chats():
    if current_user.role != 'admin': return "Access Denied", 403
    chats = chats_table.all()
    return render_template('admin_chats.html', chats=chats)

@app.route('/admin/backup')
@login_required
def admin_backup():
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    try:
        import shutil
        from flask import send_file
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        if not os.path.exists('backups'):
            os.makedirs('backups')
        
        backup_path = f'backups/manual_backup_{timestamp}.json'
        shutil.copy2('database.json', backup_path)
        
        # Log the event
        log_security_event("Manual Backup", f"Admin {current_user.username} created a backup", severity="low")
        
        flash("تم إنشاء النسخة الاحتياطية بنجاح.")
        return send_file(backup_path, as_attachment=True)
        
    except Exception as e:
        flash(f"فشل إنشاء النسخة الاحتياطية: {str(e)}")
        return redirect(url_for('admin'))

@app.route('/admin/setup_2fa')
@login_required
def setup_2fa():
    # If already set up but not enabled, we still show the secret
    if not current_user.two_factor_secret:
        secret = pyotp.random_base32()
        UserQuery = Query()
        users_table.update({'two_factor_secret': secret}, UserQuery.username == current_user.username)
        # Re-fetch user to update current_user object attributes if needed
        user_data = users_table.get(UserQuery.username == current_user.username)
        current_user.two_factor_secret = secret
    else:
        secret = current_user.two_factor_secret

    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.username, 
        issuer_name="Ramadan Paints"
    )
    
    # Generate QR Code
    img = qrcode.make(otp_uri)
    buf = io.BytesIO()
    img.save(buf)
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return render_template('setup_2fa.html', qr_code=qr_b64, secret=secret)

@app.route('/admin/toggle_2fa', methods=['POST'])
@login_required
def toggle_2fa():
    action = request.form.get('action') # 'enable' or 'disable'
    UserQuery = Query()
    
    if action == 'enable':
        users_table.update({'two_factor_enabled': True}, UserQuery.username == current_user.username)
        flash('تم تفعيل المصادقة الثنائية بنجاح')
    else:
        users_table.update({'two_factor_enabled': False}, UserQuery.username == current_user.username)
        flash('تم تعطيل المصادقة الثنائية')
        
    return redirect(url_for('admin'))

@app.route('/user/<username>')
@login_required
def user_profile(username):
    if current_user.role != 'admin' and current_user.username != username:
        return "Access Denied", 403
        
    UserQuery = Query()
    user_data = users_table.get(UserQuery.username == username)
    if not user_data:
        return "User not found", 404
        
    user_obj = {
        'full_name': user_data.get('full_name'),
        'username': user_data.get('username'),
        'email': user_data.get('email', 'لا يوجد'),
        'phone': user_data.get('phone'),
        'project_location': user_data.get('project_location', 'غير محدد'),
        'project_description': user_data.get('project_description', 'لا يوجد وصف'),
        'project_percentage': user_data.get('project_percentage', 0),
        'created_at': user_data.get('created_at')
    }
    return render_template('user_dashboard.html', user=user_obj)

# Knowledge Base & Chat
KNOWLEDGE_BASE = [
    {
        "keywords_ar": ["تواصل", "أكلم حد", "رقم تليفون", "تليفونكم", "موبايل", "اتصل", "رقمكم", "كلمني", "اريد التواصل"],
        "keywords_en": ["contact", "call", "phone number", "mobile", "talk to someone", "communicate"],
        "response_ar": "يمكنك التواصل مباشرة مع مدير الموقع عبر الرقم: 01129276218 📞\nأو عبر البريد الإلكتروني: ramadan.mohamed@example.com\nيسعدنا دائماً خدمتك!",
        "response_en": "You can contact the site manager directly at: 01129276218 📞\nor via email: ramadan.mohamed@example.com\nWe are always happy to help!"
    },
    {
        "keywords_ar": ["من انت", "مين انت", "من أنت", "عرفني", "بوت", "روبوت", "مساعد"],
        "keywords_en": ["who are you", "who is this", "bot", "robot", "assistant", "help"],
        "response_ar": "أنا المساعد الذكي لمدير الموقع رمضان محمد جبر. 🤖\nمهمتي مساعدتك في معرفة خدماتنا، تقديم نصائح في الديكور، وتسهيل تواصلك معنا.",
        "response_en": "I am the Smart Assistant for Ramadan Mohamed Gabr. 🤖\nMy mission is to help you explore our services, give decor tips, and connect you with us."
    },
    {
        "keywords_ar": ["من نحن", "عن الشركة", "تاريخ", "خبرة", "مين انتم", "من انتم", "من أنتم", "مين حضراتكم"],
        "keywords_en": ["about us", "who are we", "history", "experience", "site manager info"],
        "response_ar": "نحن فريق 'رمضان محمد جبر للدهانات والديكورات'، رواد في مجال التشطيبات في مصر بخبرة تمتد لأكثر من 30 عاماً تحت إشراف مدير الموقع. 🏆\nتخصصنا تحويل الوحدات السكنية والتجارية إلى تحف فنية باستخدام أحدث الخامات وتقنيات التنفيذ.",
        "response_en": "We are 'Ramadan Mohamed Gabr for Paints & Decor', leaders in finishing in Egypt with over 30 years of experience. 🏆\nWe specialize in transforming residential and commercial units into artistic masterpieces using the latest materials and techniques."
    },
    {
        "keywords_ar": ["خدمات", "بتعملوا ايه", "شغلكم", "انشطة", "مجالات"],
        "keywords_en": ["services", "what do you do", "activities", "scope", "work"],
        "response_ar": "خدماتنا تشمل: 🎨\n1. دهانات حديثة وكلاسيكية.\n2. تشطيبات جبس بورد وأسقف معلقة.\n3. تركيب جميع أنواع ورق الحائط.\n4. تجديد وترميم الشقق القديمة.\n5. تشطيب كامل (على المفتاح).",
        "response_en": "Our services include: 🎨\n1. Modern and Classic Paints.\n2. Gypsum Board and Suspended Ceilings.\n3. Wallpaper Installation.\n4. Renovation of Old Apartments.\n5. Full Turnkey Finishing."
    },
    {
        "keywords_ar": ["مشاريع", "أعمال", "صور", "سابقة اعمال", "نفذتوها", "وريني", "مشارعكم"],
        "keywords_en": ["projects", "portfolio", "works", "gallery", "previous work", "show me"],
        "response_ar": "فخورون بمشاريعنا! 🏗️\nقمنا بتنفيذ مئات الوحدات السكنية والتجارية في القاهرة الكبرى.\nيمكنك مشاهدة صور حية لأعمالنا في صفحة 'مشاريعنا' على الموقع.\nهل تحب أن أصف لك أحدث مشروع قمنا به؟ 😃",
        "response_en": "We are proud of our projects! 🏗️\nWe have executed hundreds of residential and commercial units in Greater Cairo.\nYou can view live photos of our work on the 'Projects' page of the website.\nWould you like me to describe our latest project? 😃"
    },
    {
        "keywords_ar": ["مكان", "عنوان", "موقع", "فين", "مقر", "لوكيشن"],
        "keywords_en": ["location", "address", "where", "office", "hq"],
        "response_ar": "مقر مدير الموقع الرئيسي في القاهرة، ولكننا نقدم خدماتنا في جميع أنحاء الجمهورية (القاهرة، الجيزة، والإسكندرية والمحافظات الأخرى). 🚛",
        "response_en": "Our HQ is in Cairo, but we serve all over Egypt (Cairo, Giza, Alexandria, and other governorates). 🚛"
    },
    {
        "keywords_ar": ["مواعيد", "شغالين", "فاتحين", "وقت"],
        "keywords_en": ["hours", "time", "open", "working hours"],
        "response_ar": "متاحون لخدمتكم طوال أيام الأسبوع من الساعة 9 صباحاً حتى 9 مساءً. 🕘",
        "response_en": "We are available to serve you 7 days a week from 9 AM to 9 PM. 🕘"
    },
    {
        "keywords_ar": ["شروخ", "تنمل", "ترييح", "شرخ"],
        "keywords_en": ["cracks", "fissures", "wall crack", "splitting"],
        "response_ar": "الشروخ أنواع: 🔸 شروخ سطحية: نعالجها بمعجون شروخ مرن. 🔸 شروخ عميقة (إنشائية): نستخدم شريط 'ميش' مع المعجون لضمان تماسك الطبقات.\nلا تقلق، لدينا حلول نهائية! 🛠️",
        "response_en": "Cracks have types:\n🔸 Surface cracks: Treated with flexible crack putty.\n🔸 Deep cracks (structural): We use 'Mesh' tape during putty to ensure layer cohesion.\nDon't worry, we have permanent solutions! 🛠️"
    },
    {
        "keywords_ar": ["اسعار", "سعر", "تكلفة", "بكام", "المتر", "مصنعية"],
        "keywords_en": ["price", "cost", "how much", "rate", "quotation"],
        "response_ar": "الأسعار تختلف حسب نوع التشطيب والمساحة وحالة الحوائط. 💰\nولكن كن واثقاً أننا نقدم أفضل قيمة مقابل سعر في السوق.\nيمكننا تحديد موعد للمعانية لتقديم عرض سعر دقيق ومجاني! 📅",
        "response_en": "Prices vary depending on the finish type, area, and wall condition. 💰\nBut rest assured, we offer the best value for money in the market.\nWe can schedule a visit for a precise and free quotation! 📅"
    },
    {
        "keywords_ar": ["جوتن", "سايبس", "خامات", "انواع دهان", "بلاستيك", "تستخدموا ايه"],
        "keywords_en": ["jotun", "sipes", "materials", "brands", "paint types"],
        "response_ar": "نحن معتمدون لاستخدام كبرى العلامات العالمية مثل 'جوتن' (Jotun) و 'سايبس' (Sipes) و 'جي إل سي' (GLC).\nنضمن لك خامات أصلية تعيش طويلاً وتعطيك ألوان زاهية. 🌈",
        "response_en": "We are certified users of top global brands like 'Jotun', 'Sipes', and 'GLC'.\nWe guarantee authentic materials that last long and provide vibrant colors. 🌈"
    },
    {
        "keywords_ar": ["الوان", "اختار لون", "موضة", "تريند", "بيج\", \"جراي", "لون"],
        "keywords_en": ["colors", "trends", "fashion", "beige", "grey", "choose color"],
        "response_ar": "اختيار اللون محير، صح؟ 🎨\nحالياً الألوان الترابية (Beige, Greige) والأوف وايت هي الأكثر طلباً.\nلدينا مهندسون متخصصون لمساعدتك في تنسيق الألوان مع الأثاث والإضاءة.",
        "response_en": "Choosing a color is tricky, right? 🎨\nCurrently, earthy tones (Beige, Greige) and Off-White are the most requested.\nWe have specialized engineers to help you coordinate colors with furniture and lighting."
    },
    {
        "keywords_ar": ["رطوبة", "نشع", "مياه", "حائط بيقشر"],
        "keywords_en": ["humidity", "moisture", "water leak", "peeling paint"],
        "response_ar": "الرطوبة عدو الدهان الأول! 💧\nالحل ليس في الدهان فوقها، بل في معالجة مصدر المياه أولاً، ثم استخدام 'عازل رطوبة' قوي قبل المعجون.\nهل الرطوبة ناتجة عن تسريب داخلي أم بسبب عوامل الجو؟",
        "response_en": "Humidity is the number one enemy of paint! 💧\nThe solution is not to paint over it, but to treat the water source first, then use a strong 'moisture insulator' before putty.\nIs the humidity caused by an internal leak or weather factors?"
    },
    {
        "keywords_ar": ["شروخ", "تنمل", "ترييح", "شرخ"],
        "keywords_en": ["cracks", "fissures", "wall crack", "splitting"],
        "response_ar": "الشروخ أنواع: 🔸 شروخ سطحية: نعالجها بمعجون شروخ مرن. 🔸 شروخ عميقة (إنشائية): نستخدم شريط 'ميش' مع المعجون لضمان تماسك الطبقات.\nلا تقلق، لدينا حلول نهائية! 🛠️",
        "response_en": "Cracks have types:\n🔸 Surface cracks: Treated with flexible crack putty.\n🔸 Deep cracks (structural): We use 'Mesh' tape during putty to ensure layer cohesion.\nDon't worry, we have permanent solutions! 🛠️"
    },
    {
        "keywords_ar": ["مشكلة", "عندي مشكلة", "استفسار", "سؤال", "مساعدة"],
        "keywords_en": ["problem", "issue", "question", "inquiry", "help"],
        "response_ar": "أهلاً بك! أنا هنا للمساعدة. هل لديك مشكلة معينة تود مناقشتها (رطوبة، شروخ) أم تود الاستفسار عن خدماتنا وأسعارنا؟ 🎨",
        "response_en": "Welcome! I'm here to help. Do you have a specific issue (humidity, cracks) or want to inquire about our services and prices? 🎨"
    },
    {
        "keywords_ar": ["رمضان", "مين رمضان", "من هو رمضان", "الحاج رمضان"],
        "keywords_en": ["ramadan", "who is ramadan"],
        "response_ar": "الحاج رمضان محمد جبر هو مدير الموقع والمشرف العام، خبرة أكثر من 30 سنة في مجال الدهانات والديكور. 🏗️\nأشرف بنفسه على مئات المشاريع الناجحة، واضعاً 'الدقة والأمانة' كشعار دائم.",
        "response_en": "Haj Ramadan Mohamed Gabr is the site manager and general supervisor, with over 30 years of experience in paints and decor. 🏗️\nHe personally supervised hundreds of successful projects, always prioritizing 'Precision and Honesty'."
    },
    {
        "keywords_ar": ["مساحة", "ضيقة", "واسعة", "صغيرة", "كبيرة", "غرفة"],
        "keywords_en": ["space", "small room", "large room", "area", "size"],
        "response_ar": "للمساحات الضيقة، ننصح بالألوان الفاتحة مثل الأوف وايت والبيج لتعطي إحساساً بالاتساع. 📏\nأما المساحات الكبيرة، فيمكننا استخدام ألوان داكنة في حائط واحد (Feature Wall) لإضافة عمق وفخامة.\nما هي مساحة الغرفة التي تفكر في دهانها؟",
        "response_en": "For small spaces, we recommend light colors like Off-White and Beige to create a sense of spaciousness. 📏\nFor large areas, dark colors can be used on a 'Feature Wall' to add depth and luxury.\nWhat is the size of the room you're planning to paint?"
    },
    {
        "keywords_ar": ["إضاءة", "اضاءة", "نور", "شمس", "لمبات"],
        "keywords_en": ["lighting", "light", "sunlight", "lamps", "brightness"],
        "response_ar": "الإضاءة تغير لون الدهان تماماً! 💡\nالإضاءة الصفراء تجعل الألوان تبدو أدفأ، بينما الإضاءة البيضاء (Leds) تظهر اللون الحقيقي.\nهل الغرفة بها إضاءة طبيعية جيدة أم تعتمد على الإضاءة الصناعية؟",
        "response_en": "Lighting completely changes the paint color! 💡\nYellow lighting makes colors look warmer, while white (LED) lighting shows the true color.\nDoes your room have good natural light or does it depend on artificial lighting?"
    },
    {
        "keywords_ar": ["كلاسيك", "مودرن", "حديث", "قديم", "ستايل", "طراز", "نيوكلاسيك"],
        "keywords_en": ["classic", "modern", "style", "vintage", "contemporary", "neoclassic"],
        "response_ar": "الستايل المودرن يعتمد على البساطة والألوان الحيادية (رمادي، أبيض). 🏠\nأما الستايل الكلاسيك، فيميل للكرانيش المذهبة وورق الحائط المنقوش والدهانات القطيفة.\nأما النيوكلاسيك فهو يجمع بين فخامة الماضي وبساطة الحاضر. أيهما تفضل؟",
        "response_en": "Modern style relies on simplicity and neutral colors. Classic style features gilded cornices and patterned wallpaper. Neoclassic combines both. Which do you prefer?"
    },
    {
        "keywords_ar": ["مدة", "وقت", "تخلصوا في قد ايه", "ايام", "يوم", "اسبوع"],
        "keywords_en": ["duration", "time", "how long", "period", "finish date"],
        "response_ar": "مدة العمل تختلف حسب المساحة ونوع التشطيب. ⏱️\nغالباً الغرفة الواحدة تأخذ من 3 إلى 5 أيام (معجون ودهان)، والشقة الكاملة من 3 إلى 6 أسابيع لضمان جودة الجفاف والتنفيذ.\nهل تود إنهاء العمل في وقت محدد؟",
        "response_en": "Work duration depends on the area. Typically, one room takes 3-5 days, and a full apartment takes 3-6 weeks to ensure quality. Do you have a specific deadline?"
    },
    {
        "keywords_ar": ["غسيل", "بيتغسل", "نظافة", "تنظيف", "مية", "صابون"],
        "keywords_en": ["washable", "clean", "cleaning", "water", "soap", "scrub"],
        "response_ar": "نحن نستخدم دهانات بلاستيك نصف لامع ولامع قابلة للغسل تماماً بمواد التنظيف العادية. 🧽\nدهانات جوتن وسايبس التي نستخدمها تتميز بمقاومة عالية بمرور الوقت.\nهل تبحث عن دهانات سهلة التنظيف لغرف الأطفال مثلاً؟",
        "response_en": "We use washable semi-gloss and gloss paints. They are highly resistant and easy to clean. Are you looking for kid-friendly washable paints?"
    },
    {
        "keywords_ar": ["اطفال", "غرفة نوم", "صالة", "ريسيبشن", "مطبخ", "حمام"],
        "keywords_en": ["kids", "bedroom", "living room", "reception", "kitchen", "bathroom"],
        "response_ar": "لكل غرفة خصوصيتها: 🛏️\n- غرف النوم: ألوان هادئة للراحة.\n- الريسيبشن: ألوان فخمة أو ورق حائط.\n- المطبخ والحمام: دهانات مقاومة للرطوبة والبكتيريا.\nما هي الغرفة التي تبحث عن أفكار لها؟",
        "response_en": "Each room is unique: Bedrooms need calm colors, Receptions need luxury, Kitchens/Bathrooms need moisture resistance. Which room are we talking about?"
    },
    {
        "keywords_ar": ["معاينة", "زيارة", "اشوف الموقع", "تجيلي", "رفع مقاسات"],
        "keywords_en": ["visit", "inspection", "survey", "site visit", "measurement"],
        "response_ar": "بالتأكيد! المعاينة هي أول خطوة للنجاح. 📐\nنقوم بزيارة الموقع، رفع المقاسات، وفحص حالة الحوائط لتقديم عرض سعر دقيق ومجاني.\nاترك رقمك وسنتواصل معك لتحديد موعد!",
        "response_en": "Certainly! Inspection is the first step. We visit the site, take measurements, and check walls for a free quote. Leave your number to schedule!"
    },
    {
        "keywords_ar": ["سراميك", "رخام", "باركية", "ارضية", "ارضيات"],
        "keywords_en": ["tiles", "marble", "parquet", "flooring", "floor"],
        "response_ar": "نحن نهتم جداً بتغطية وحماية الأرضيات أثناء العمل. 🛡️\nسواء كان سيراميك أو باركية، نقوم بفرش طبقات حماية لضمان بقائها نظيفة تماماً.\nهل الأرضيات عندك جاهزة أم سيتم تركيبها؟",
        "response_en": "We protect your floors during work using special covers. Whether it's tiles or parquet, we keep it clean. Is your flooring already installed?"
    },
    {
        "keywords_ar": ["سقف", "سقوف", "كرانيش", "فيوتك", "سرر"],
        "keywords_en": ["ceiling", "ceilings", "cornice", "foam", "fyutech"],
        "response_ar": "الأسقف هي 'الحائط الخامس' للمنزل! ☁️\nنبدع في دهانات الأسقف وتركيب ودهان الكرانيش والفيوتك بلمسات حريرية.\nهل تفكر في سقف سادة أم به ديكورات جبسية؟",
        "response_en": "Ceilings are the '5th wall'! We excel in painting ceilings and cornices. Are you looking for a plain ceiling or gypsum decorations?"
    },
    {
        "keywords_ar": ["سلام", "ازيك", "صباح", "مساء", "هاي", "مرحبا"],
        "keywords_en": ["hello", "hi", "hey", "morning", "evening", "greetings"],
        "response_ar": "أهلاً بك! يومك سعيد. 🌸\nأنا خبير الديكور والدهانات لمدير الموقع رمضان محمد جبر، كيف يمكنني تجميل منزلك اليوم؟",
        "response_en": "Hello! Have a great day. I am the Decor expert for site manager Ramadan Mohamed Gabr, how can I help beautify your home today?"
    },
    {
        "keywords_ar": ["شكرا", "تسلم", "جزاك", "تمام", "ماشي"],
        "keywords_en": ["thanks", "thank you", "ok", "great", "nice"],
        "response_ar": "العفو، أنا في خدمتك دائماً! 😊\nهل لديك أي سؤال آخر بخصوص الدهانات أو الديكور؟",
        "response_en": "You're welcome! I'm always here to help. Any other questions about paints or decor?"
    },
    {
        "keywords_ar": ["خارجي", "واجهة", "واجهات", "عمارة", "فيلا", "برة"],
        "keywords_en": ["exterior", "facade", "facades", "villa", "outdoor", "outside"],
        "response_ar": "نحن متخصصون أيضاً في دهانات الواجهات الخارجية! 🏰\nنستخدم دهانات مقاومة للعوامل الجوية وأشعة الشمس لضمان بقاء الألوان لسنوات طويلة.\nهل الواجهة طوب أحمر أم محارة؟",
        "response_en": "We specialize in exterior facades using weather-resistant paints. Is the facade red brick or plastered?"
    },
    {
        "keywords_ar": ["عفش", "موبيليا", "كنبة", "سرير", "دولاب", "خشب", "اثاث"],
        "keywords_en": ["furniture", "sofa", "bed", "closet", "wood"],
        "response_ar": "تنسيق لون الحائط مع العفش هو سر الجمال! 🛋️\n- لو العفش غامق، يفضل حوائط فاتحة.\n- لو العفش مودرن وبسيط، ممكن نستخدم حائط واحد بلون جريء.\nهل العفش عندك موجود فعلاً ولا لسه هتختاره؟",
        "response_en": "Coordinating wall color with furniture is key! If furniture is dark, go for light walls. If modern, try a bold accent wall. Do you already have the furniture?"
    },
    {
        "keywords_ar": ["ملمس", "قطيفة", "خشن", "ناعم", "تكتشر", "بروز"],
        "keywords_en": ["texture", "velvet", "rough", "smooth", "relief"],
        "response_ar": "الدهانات الديكورية مثل (القطيفة، السواحيلي، الاستوكو) تعطي ملمساً رائعاً للحائط. ✨\nنحن محترفون في تنفيذ هذه التأثيرات الفنية بدقة عالية.\nهل تحب الحوائط سادة تماماً أم تود تجربة ملمس ديكوري؟",
        "response_en": "Decorative paints like velvet, Swahili, or Stucco add amazing texture. We are experts in these artistic effects. Do you prefer plain walls or textured ones?"
    },
    {
        "keywords_ar": ["صحي", "حساسية", "ريحة", "رائحة", "اطفال", "نفس"],
        "keywords_en": ["health", "allergy", "smell", "odor", "breath"],
        "response_ar": "صحتكم تهمنا! 🏥\nنستخدم دهانات صديقة للبيئة (Low VOC) عديمة الرائحة تقريباً وآمنة لمرضى الحساسية والأطفال.\nهل هناك أي اعتبارات صحية تود منا مراعاتها أثناء العمل؟",
        "response_en": "Your health matters! We use eco-friendly, low-VOC, odorless paints safe for children and allergy sufferers. Any health considerations we should know?"
    },
    {
        "keywords_ar": ["موضة 2024", "موضة 2025", "تريند", "جديد", "احدث"],
        "keywords_en": ["trends 2024", "trends 2025", "newest", "modern colors"],
        "response_ar": "أحدث صيحات الموضة الآن هي الألوان الطبيعية (Earth Tones) مثل 'Sage Green' و 'Warm Greige'. 🌿\nأيضاً استخدام الأخشاب مع الدهانات (التجاليد) موضة جداً.\nهل تحب الالتزام بالموضة العالمية أم تفضل الذوق الكلاسيكي الثابت؟",
        "response_en": "The latest trends are Earth Tones like Sage Green and Warm Greige, and mixing wood with paint. Do you follow trends or prefer timeless classics?"
    },
    {
        "keywords_ar": ["مساحة واسعة", "صالة كبيرة", "فيلا واسعة"],
        "keywords_en": ["large space", "big hall", "wide villa"],
        "response_ar": "في المساحات الواسعة، لدينا حرية إبداع أكبر! 🏰\nيمكننا استخدام 'بانوهات' كلاسيكية أو تقسيم الحوائط بألوان مختلفة لتعطي فخامة.\nهل تفكر في تقسيم الصالة لعدة أركان (ليفينج، سفرة)؟",
        "response_en": "In large spaces, we have more creative freedom! We can use classic panels or different color zones for luxury. Thinking of dividing the hall into zones?"
    },
    {
        "keywords_ar": ["ورق حائط", "3D", "مناظر", "لزق ورق"],
        "keywords_en": ["wallpaper", "3D wallpaper", "scenery", "wallpaper gluing"],
        "response_ar": "ورق الحائط يعطي روحاً مختلفة للمكان. 🖼️\nنحن متميزون في لزق كافة الأنواع (الرول، 3D، القماش) بدون فواصل ظاهرة.\nهل لديك ورق حائط جاهز للتركيب أم تود أن نرشح لك كتالوجات؟",
        "response_en": "Wallpaper adds soul to a place. We excel in installing all types without visible seams. Do you have the wallpaper or need catalog recommendations?"
    },
    {
        "keywords_ar": ["سعر المتر", "تكلفة الشقة", "بكام الدهان"],
        "keywords_en": ["meter price", "apartment cost", "how much"],
        "response_ar": "التكلفة تعتمد على: (حالة الحوائط، عدد الطبقات، ونوع ماركة الدهان). 💰\nتبدأ أسعارنا من مستويات تنافسية جداً مع ضمان أعلى جودة.\nهل تود أن نرسل لك مهندسًا للمعاينة وعمل مقايسة دقيقة مجاناً؟",
        "response_en": "Cost depends on wall condition, layers, and brand. Our prices are competitive with guaranteed quality. Want a free expert visit for a quote?"
    },
    {
        "keywords_ar": ["جبس بورد", "بيت نور", "سقف معلق"],
        "keywords_en": ["gypsum board", "light cove", "suspended ceiling"],
        "response_ar": "الجبس بورد يحتاج معاملة خاصة في المعجون والدهان لمنع ظهور الشروخ عند الفواصل. 👷\nنحن متخصصون في تشطيب الجبس بورد (معجون ودهان) ليكون قطعة واحدة ملساء.\nهل الجبس بورد عندك فلات (سادة) أم به مستويات وإضاءة؟",
        "response_en": "Gypsum board needs careful putty to prevent cracks. We specialize in finishing it for a smooth look. Is it flat or multilevel with lighting?"
    },
    {
        "keywords_ar": ["ضمان", "تأمين", "صيانة", "بعد الشغل"],
        "keywords_en": ["warranty", "guarantee", "maintenance", "after support"],
        "response_ar": "ثقتكم هي رأسمالنا! 🛡️\nنحن نقدم ضماناً حقيقياً على جودة التنفيذ وعدم تقشير الدهانات بمرور الوقت.\nدائماً نبني علاقة مستمرة مع عملائنا حتى بعد انتهاء المشروع.",
        "response_en": "Trust is our capital! We offer a real warranty on execution and paint durability. We value long-term relationships with our clients."
    },
    {
        "keywords_ar": ["باب", "ببان", "خشب", "شباك", "شبابيك", "لاكيه", "استر"],
        "keywords_en": ["door", "doors", "wood", "window", "windows", "lacquer", "oyster"],
        "response_ar": "أبواب منزلك هي عنوان الفخامة! 🚪\nنقوم بدهانات الأبواب الخشبية بكافة أنواعها (لاكيه مغسول، أستر، أو دهانات حديثة).\nهل الأبواب عندك خشب خام أم تحتاج لتجديد دهان قديم؟",
        "response_en": "Your doors are a statement of luxury! We paint all types of wooden doors (lacquer, oyster, or modern finishes). Are your doors raw wood or do they need renovation?"
    },
    {
        "keywords_ar": ["زيت", "بلاستيك", "فرق", "احسن", "مط", "لامع"],
        "keywords_en": ["oil based", "plastic", "difference", "better", "matt", "glossy"],
        "response_ar": "الفرق الجوهري: ✨\n- البلاستيك: أسرع في الجفاف، بدون رائحة تقريباً، وألوانه مطفية هادئة.\n- الزيت (اللاكيه): أكثر متانة، سهل التنظيف جداً، وله لمعة جذابة.\nأيهما تفضل لمنزلك؟ يمكننا دمج الاثنين حسب طبيعة كل غرفة.",
        "response_en": "The main difference: Plastic is faster drying and odorless with matte tones. Oil (Lacquer) is more durable and very easy to clean with a glossy finish. Which do you prefer?"
    },
    {
        "keywords_ar": ["شتاء", "صيف", "مطر", "رطوبة جو", "وقت مناسب"],
        "keywords_en": ["winter", "summer", "rain", "humidity", "best time"],
        "response_ar": "يمكننا العمل طوال العام بفضل تقنيات الجفاف الحديثة! 🌤️\nلكن يفضل دائماً الأوقات ذات الرطوبة المنخفضة لضمان جفاف طبقات المعجون بعمق.\nهل تخطط للبدء الآن أم تنتظر موسماً معيناً؟",
        "response_en": "We can work year-round thanks to modern drying techniques! However, low-humidity times are always better for deep putty drying. Planning to start now or waiting for a specific season?"
    },
    {
        "keywords_ar": ["فقاقيع", "بقع", "اصفرار", "تقشير"],
        "keywords_en": ["bubbles", "stains", "yellowing", "peeling"],
        "response_ar": "هذه المشاكل لها أسباب علمية: 🧬\n- الفقاقيع: رطوبة محبوسة أو سوء تجهيز.\n- الاصفرار: بسبب نوع دهان رديء أو تدخين.\nنحن نشخص السبب ونعالجه من الجذور قبل إعادة الدهان لضمان عدم تكرار المشكلة.",
        "response_en": "These issues have scientific causes: Bubbles mean trapped moisture; yellowing is often from poor quality paint or smoke. We diagnose and fix the root cause first."
    },
    {
        "keywords_ar": ["نور ابيض", "نور اصفر", "وارم", "كول"],
        "keywords_en": ["white light", "yellow light", "warm", "cool"],
        "response_ar": "نصيحة ذهبية: 💡\n- النور الأصفر (Warm): يبرز جمال ألوان (البيج، البني، الأحمر).\n- النور الأبيض (Cool): مثالي لألوان (الرمادي، الأزرق، الأبيض).\nدائماً جرب عينة اللون تحت إضاءة الغرفة الفعلية قبل البدء!",
        "response_en": "Golden tip: Warm light enhances beiges and browns; cool light is perfect for greys and blues. Always test a color sample under your actual room lights!"
    },
    {
        "keywords_ar": ["سلم", "بلكونة", "منور", "سطح"],
        "keywords_en": ["stairs", "balcony", "lightwell", "roof"],
        "response_ar": "نهتم بكافة تفاصيل المنزل! 🏡\nنستخدم دهانات خاصة للمداخل والبلكونات تتحمل الشمس والأتربة وتظل محتفظة برونقها.\nهل تفكر في تجديد مدخل العمارة أم البلكونة الخاصة بك؟",
        "response_en": "We care about every detail! We use special paints for balconies and entrances that withstand sun and dust. Thinking of renovating your balcony or the building entrance?"
    },
    {
        "keywords_ar": ["وحدي", "بنفسي", "اعمل ايه", "خطوات"],
        "keywords_en": ["myself", "diy", "how to", "steps"],
        "response_ar": "لو حابب تبدأ بنفسك، أهم خطوة هي 'التجهيز'! 🛠️\nصنفرة الحوائط ونظافتها هي 70% من نجاح الدهان. لكن للنتائج الاحترافية والمساحات الكبيرة، فريقنا دائماً جاهز لمساعدتك وتوفير وقتك وجهدك.",
        "response_en": "If you want to DIY, 'preparation' is key! Sanding and cleaning are 70% of success. But for professional results and large areas, our team is ready to save you time and effort."
    },
    {
        "keywords_ar": ["فينوماستيك", "بيرل", "مط", "جوتن", "جوتاشيلد"],
        "keywords_en": ["fenomastic", "pearl", "jotun", "jotashield"],
        "response_ar": "مجموعة جوتن رائعة! 🌈\n- 'فينوماستيك مذهل' يعطي ملمساً حريرياً.\n- 'جوتاشيلد' مثالي للواجهات الخارجية.\n- 'بيرل' يعطي لمعة لؤلؤية خفيفة.\nهل تفكر في ماركة معينة أم نختار لك الأنسب لميزانيتك؟",
        "response_en": "Jotun products are excellent! Fenomastic gives a silk touch, Jotashield is great for exteriors, and Pearl offers a subtle glow. Looking for a specific brand or need budget recommendations?"
    },
    {
        "keywords_ar": ["رول", "فرشة", "سكينة", "صنفرة", "مقص", "ميزان"],
        "keywords_en": ["roller", "brush", "knife", "sandpaper", "scissor", "level"],
        "response_ar": "العدة هي نصف الشغل! 🛠️\nنحن نستخدم أجود أنواع الرولات والفرش لضمان عدم ترك علامات (خطوط) على الحائط.\nهل جربت استخدام رولة النقاشة قبل كده ولا بتستفسر عن الأنواع؟",
        "response_en": "Tools are half the work! We use high-quality rollers and brushes to ensure a smooth finish without streaks. Have you ever used a roller or are you just asking?"
    },
    {
        "keywords_ar": ["تعتيق", "رخامي", "استوكو", "خيال", "روعة"],
        "keywords_en": ["antique", "marble effect", "stucco", "special finish"],
        "response_ar": "الدهانات الديكورية (التعتيق والاستوكو) تحول الحائط لقطعة فنية تشبه الرخام الطبيعي. 🏛️\nهذا النوع يحتاج فني محترف جداً لضمان تناسق العروق واللمعة.\nهل تود تنفيذ حائط واحد (Feature wall) بهذا الستايل؟",
        "response_en": "Special finishes like Stucco can make your wall look like natural marble! It requires a very skilled artisan. Thinking of a featured wall with this style?"
    },
    {
        "keywords_ar": ["سكن", "ايجار", "نقل", "تجديد سريع"],
        "keywords_en": ["rent", "moving", "fast renovation"],
        "response_ar": "لو محتاج تجديد سريع عشان نقل سكن أو شقة إيجار، عندنا حلول 'التجديد السريع'! ⚡\nبألوان مريحة وتكلفة اقتصادية تخلص في وقت قياسي.\nكم عدد الغرف التي تود تجديدها؟",
        "response_en": "Moving or renting? We have fast renovation solutions with comfortable colors and economic costs. How many rooms do you need to refresh?"
    },
    {
        "keywords_ar": ["باركيه", "خشب ارضيات", "HDF", "الوان ارضية"],
        "keywords_en": ["parquet", "wood flooring", "hdf", "floor colors"],
        "response_ar": "الباركيه يحتاج ألوان حوائط دافئة! 🪵\nالأوف وايت، الرمادي الدافئ (Greige)، والكافيه هي أفضل صديق للأرضيات الخشبية.\nما هو لون الباركيه عندك؟ فاتح أم غامق؟",
        "response_en": "Parquet floors pair best with warm wall colors like Off-white and Greige. What's your parquet color, light or dark?"
    },
    {
        "keywords_ar": ["رسم", "تابلوه", "فرسك", "رسم يدوي"],
        "keywords_en": ["drawing", "mural", "fresco", "hand painting"],
        "response_ar": "الرسم اليدوي على الحوائط يعطي طابعاً شخصياً فريداً! 🎨\nسواء كان رسم كلاسيك أو مودرن أو حتى رسومات لغرف الأطفال.\nهل لديك صورة معينة تود رسمها على الحائط؟",
        "response_en": "Hand painting adds a unique personal touch! Whether it's for a classic look or kids' rooms. Do you have a specific image in mind?"
    },
    {
        "keywords_ar": ["ستايل ريفي", "بوهيمي", "اسكندنافي", "مينيماليزم"],
        "keywords_en": ["rustic", "boho", "scandinavian", "minimalism"],
        "response_ar": "كل ستايل وله باليتة ألوان: 🌿\n- الرفي: ألوان ترابية وخشب.\n- البوهيمي: ألوان جريئة ومتداخلة.\n- الاسكندنافي: أبيض ورمادي فاتح.\nأي جو تود أن يسود في منزلك؟",
        "response_en": "Each style has its palette: Rustic is earthy, Boho is bold, Scandi is whites and light greys. What vibe are you aiming for?"
    },
    {
        "keywords_ar": ["مكتب", "شغل", "تركيز", "دراسة"],
        "keywords_en": ["office", "work", "focus", "study"],
        "response_ar": "لأماكن العمل والدراسة، ننصح بالألوان التي تساعد على التركيز مثل الأزرق الهادئ أو الأخضر الفاتح. 📚\nنبتعد عن الألوان الصارخة اللي بتشتت الانتباه.\nهل تود دهان مكتب منزلي أم شركة؟",
        "response_en": "For study and work areas, we recommend colors that aid focus like calm blues or light greens. Are we painting a home office or a corporate space?"
    },
    {
        "keywords_ar": ["سيراميك حمام", "دهان سيراميك", "تغيير لون سيراميك"],
        "keywords_en": ["bathroom tiles", "tile painting", "change tile color"],
        "response_ar": "نعم! يوجد دهانات متخصصة للسيراميك (إيبوكسي) تعطي شكلاً جديداً تماماً بدون تكسير. 🚿\nلكنها تحتاج دقة عالية جداً في التحضير.\nهل تود تجديد لون سيراميك المطبخ أم الحمام؟",
        "response_en": "Yes! Specialize epoxy paints can change tile colors without demolition. Needs high precision. Kitchen or bathroom?"
    },
    {
        "keywords_ar": ["تعتيم", "سينما منزلية", "اسود", "كحلي"],
        "keywords_en": ["darkening", "home cinema", "black", "navy"],
        "response_ar": "للـ Home Cinema، بنستخدم دهانات 'مط' (Matte) تماماً عشان نمنع أي انعكاس للضوء. 🎬\nالألوان الغامقة جداً بتخلي تجربة المشاهدة خيالية.\nهل الغرفة مخصصة للشاشة فقط؟",
        "response_en": "For home cinemas, we use deep matte paints to prevent reflections. It makes the viewing experience amazing. Is the room dedicated to a TV/projector?"
    },
    {
        "keywords_ar": ["نمل", "حشرات", "سوس", "خشب قديم"],
        "keywords_en": ["ants", "insects", "termites", "old wood"],
        "response_ar": "قبل دهان الخشب القديم، لازم نعالجه بمواد مضادة للسوس والحشرات! 🐜\nحماية الخشب هي أساس بقاء الدهان.\nهل تلاحظ وجود أي ثقوب صغيرة في الخشب؟",
        "response_en": "Before painting old wood, we must treat it for insects and termites. Protection is key. Do you see any small holes in the wood?"
    },
    {
        "keywords_ar": ["بروز", "جبس", "بانوهات", "تحديد"],
        "keywords_en": ["frames", "gypsum profiles", "wall frames", "outlining"],
        "response_ar": "البانوهات (Wall Frames) هي قمة الفخامة الكلاسيكية والنيوكلاسيك. ✨\nمهمتنا تنفيذها بأبعاد هندسية دقيقة ودهانها لتظهر كجزء من الحائط.\nهل تفضل البانوهات بلون الحائط أم بلون مختلف؟",
        "response_en": "Wall frames (Panohat) are the peak of classic luxury. We ensure perfect geometric execution. Do you prefer them the same color as the wall or different?"
    },
    {
        "keywords_ar": ["مطعم", "كافيه", "محل", "تجاري"],
        "keywords_en": ["restaurant", "cafe", "shop", "commercial"],
        "response_ar": "الأماكن التجارية تحتاج دهانات تتحمل 'الاحتراف' والتقشير وسهلة التنظيف. ☕\nألوان المطاعم (فاتحة للشهية) تختلف عن الكافيهات (الهادئة).\nما هو نشاط المحل الذي تود تشطيبه؟",
        "response_en": "Commercial spaces need high-durability, easy-to-clean paints. Restaurant colors differ from cafes. What's your business type?"
    }
]

def normalize_arabic(text):
    if not text: return ""
    text = text.lower().strip()
    # Normalize Alef forms
    text = re.sub(r"[أإآ]", "ا", text)
    # Normalize Teh Marbuta and Heh
    text = re.sub(r"ة", "ه", text)
    # Remove Tashkeel (diacritics)
    text = re.sub(r"[\u064B-\u0652]", "", text)
    return text

def get_ai_response(user_id, message, user_name=None):
    msg_norm = normalize_arabic(message)
    
    # 1. Check Static Knowledge Base
    for entry in KNOWLEDGE_BASE:
        # Check if any dynamic keyword match (substring match on normalized text)
        for kw in entry['keywords_ar']:
            if normalize_arabic(kw) in msg_norm:
                return entry['response_ar']
        for kw in entry['keywords_en']:
            if kw.lower() in msg_norm:
                return entry['response_en']
    
    # 2. Check Unanswered table for admin-learned answers
    UQuest = Query()
    # Also check with normalization for learned questions
    all_unanswered = unanswered_table.all()
    for rec in all_unanswered:
        if normalize_arabic(rec['question']) == msg_norm and rec.get('admin_response'):
            return rec['admin_response']
        
    return "__NOT_FOUND__"

@app.route('/api/chat', methods=['POST'])
@limiter.limit("20 per minute")
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        
        # Determine unique user_id
        if current_user.is_authenticated:
            user_id = current_user.username
            user_name = current_user.full_name if current_user.full_name else current_user.username
        else:
            user_id = data.get('user_id', 'anonymous')
            user_name = "Guest"
        
        # Validate characters: Arabic, English, Numbers, and basic punctuation
        # Allowed: \u0600-\u06FF (Arabic), a-zA-Z, 0-9, spaces, and common marks
        if not re.search(r'[a-zA-Z0-9\u0600-\u06FF]', message):
            msg_warning = f"عذراً يا {user_name}، أنا أفهم فقط اللغة العربية، الإنجليزية، والأرقام.\n" \
                          f"Sorry {user_name}, I only understand Arabic, English, and numbers."
            return jsonify({'response': msg_warning})
        
        response_text = get_ai_response(user_id, message, user_name)
        
        # Recognize Contact Request and Log it specifically
        is_contact_req = any(kw in message.lower() for kw in ["تواصل", "أكلم حد", "رقم", "اتصل", "contact", "call", "phone"])
        if is_contact_req:
            log_security_event("Contact Info Requested", f"User {user_name} ({user_id}) requested contact details. Message: {message}", severity="low")

        # Personalize response if it's a normal response (not the "Not Found" or specific warnings)
        if response_text != "__NOT_FOUND__" and "يا " not in response_text:
            response_text = f"يا {user_name}، " + response_text
        
        # Logic for Unanswered Questions
        if response_text == "__NOT_FOUND__":
            msg_clean = message.lower().strip()
            UQuest = Query()
            # Always update the latest user/timestamp for this unanswered question
            # so the admin sees the most recent context.
            unanswered_table.upsert({
                'question': msg_clean,
                'user_id': user_id,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'admin_response': None # It was not found, so we reset answer if it was cleared
            }, UQuest.question == msg_clean)
            
            response_text = "عذراً، هذا السؤال جديد عليّ ولم أتمكن من فهمه جيداً. 🤖\nيرجى ترك رقم هاتفك هنا للتواصل معك من قبل مدير الموقع والإجابة على استفسارك بدقة."
        
        chats_table.insert({
            'user_id': user_id,
            'user_name': user_name,
            'message': message,
            'response': response_text,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return jsonify({'response': response_text})
    except:
        return jsonify({'response': "عذراً، حدث خطأ."})

# API Route
@app.route('/api/contact', methods=['POST'])
@limiter.limit("5 per minute")
def api_contact():
    try:
        data = request.get_json()
        contacts_table.insert({
            "name": data.get('name'),
            "phone": data.get('phone'),
            "message": data.get('message'),
            "created_at": datetime.now().isoformat()
        })
        return jsonify({"status": "success", "message": "Data saved successfully"})
    except:
        return jsonify({"status": "error", "message": "Error"}), 500

@app.errorhandler(403)
def forbidden_error(e):
    log_security_event("Access Denied (403)", f"Attempt to access: {request.path}", severity="medium")
    return "Access Denied", 403

@app.errorhandler(429)
def ratelimit_handler(e):
    log_security_event("Rate Limit Tripped", f"IP hit limit on: {request.path}", severity="high")
    return jsonify(error="Too many requests", message="لقد تجاوزت حد المحاولات المسموح به. يرجى الانتظار قليلاً."), 429

@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0")
