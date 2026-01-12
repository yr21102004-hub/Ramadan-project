"""
Flask Application with MVC Architecture and WebSocket Support
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, generate_csrf
from dotenv import load_dotenv
import os
from datetime import datetime
import re

# Import WebSocket
from websockets import init_socketio, notify_admins, broadcast_percentage_update

# Import Models
# Import Models
from models import UserModel, ChatModel, PaymentModel, SecurityLogModel, UnansweredQuestionsModel, LearnedAnswersModel, Database

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

# Initialize models
user_model = UserModel()
chat_model = ChatModel()
payment_model = PaymentModel()
security_log_model = SecurityLogModel()
unanswered_model = UnansweredQuestionsModel()
learned_model = LearnedAnswersModel()
db = Database() # For direct access if needed, or better use contact model if we create one

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
        user_data = user_model.get_by_username(username)
        if user_data:
            return User(user_data)
        return None

@login_manager.user_loader
def load_user(username):
    return User.get(username)

# ============================================
# ROUTES - Using MVC Pattern
# ============================================

# Home & Static Pages
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/sw.js')
def service_worker():
    return app.send_static_file('sw.js')

# Import controllers
from controllers.user_controller import (
    register_user,
    get_user_profile,
    update_user_percentage,
    delete_user
)

# User Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    return register_user()

@app.route('/user/<username>')
@login_required
def user_profile(username):
    return get_user_profile(username)

@app.route('/admin/update_project_percentage', methods=['POST'])
@login_required
def update_project_percentage():
    return update_user_percentage()

@app.route('/admin/delete_user/<username>', methods=['POST'])
@login_required
def delete_user_route(username):
    return delete_user(username)

# Login/Logout (keeping in main app for now)
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        user = User.get(username)
        
        user_data = user_model.get_by_username(username)
        
        if user_data and bcrypt.check_password_hash(user_data.get('password', ''), password):
            if user.two_factor_enabled:
                session['2fa_user'] = username
                return redirect(url_for('verify_2fa'))
            
            login_user(user)
            return redirect(url_for('admin' if user.role == 'admin' else 'index'))
        
        security_log_model.create("Failed Login", f"Attempt for username: {username}", severity="medium")
        flash('اسم المستخدم أو كلمة المرور غير صحيحة')

    return render_template('login.html', captcha_q=None)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Admin Dashboard
@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    users = user_model.get_all()
    # Use direct DB access for tables without specific model methods yet, or use the models
    messages = db.contacts.all()
    chats = chat_model.get_all()
    unanswered = unanswered_model.get_all()
    sec_logs = security_log_model.get_all()
    payments = payment_model.get_all()
    
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

    # Pass learned answers count for the badge if needed, though template uses `unanswered|length`
    # We might want to pass 'learned' count if we add it to dashboard stats later
    
    return render_template('admin.html', users=users, messages=messages, 
                           chats=chats, unanswered=unanswered, security_logs=sec_logs[:50],
                           payments=payments, chats_by_user=chats_by_user, get_context=get_context)


@app.route('/admin/answer_question', methods=['POST'])
@login_required
def answer_question():
    if current_user.role != 'admin': return "Access Denied", 403
    question = request.form.get('question')
    answer = request.form.get('answer')
    
    unanswered_model.update_response(question, answer)
    flash("تم حفظ الإجابة بنجاح! سيقوم الذكاء الاصطناعي باستخدامها مستقبلاً.")
    return redirect(url_for('admin'))


@app.route('/admin/delete_answered_question', methods=['POST'])
@login_required
def delete_answered_question():
    if current_user.role != 'admin': 
        return "Access Denied", 403
    
    question = request.form.get('question')
    
    # First, verify that this question has an answer
    question_record = unanswered_model.get_by_question(question)
    
    if question_record and question_record.get('admin_response'):
        # Move the question and answer to learned_answers table
        learned_model.create(
            question=question,
            answer=question_record.get('admin_response')
        )
        # Note: learned_model.create sets learned_at to now. 
        # If we want to preserve original timestamp, we might need to modify create or add manually.
        # But keeping it simple for MVC migration is fine.
        
        # Now remove it from unanswered_questions table
        unanswered_model.delete(question)
        
        flash("تم نقل السؤال والإجابة إلى قاعدة المعرفة. الذكاء الاصطناعي سيستخدمها للتعلم.")
    else:
        # Case 2: No answer provided. Just delete it (cleaning up spam/unwanted questions)
        unanswered_model.delete(question)
        flash("تم حذف السؤال نهائياً (لم يتم حفظه لأنه بدون إجابة).")
    
    return redirect(url_for('admin'))


@app.route('/admin/learned_answers')
@login_required
def admin_learned_answers():
    if current_user.role != 'admin': 
        return "Access Denied", 403
    
    learned = learned_model.get_all()
    learned.sort(key=lambda x: x.get('learned_at', ''), reverse=True)
    
    return render_template('admin_learned.html', learned=learned)

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return "<h1>500 Internal Server Error</h1><p>Please try again.</p>", 500

# ============================================
# CHATBOT LOGIC & KNOWLEDGE BASE
# ============================================

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
        "response_ar": "أنا المساعد الذكي لمدير الموقع الحاج رمضان محمد جبر. 🤖\nمهمتي مساعدتك في معرفة خدماتنا، تقديم نصائح في الديكور، وتسهيل تواصلك معنا.",
        "response_en": "I am the Smart Assistant for Haj Ramadan Mohamed Gabr. 🤖\nMy mission is to help you explore our services, give decor tips, and connect you with us."
    },
    {
        "keywords_ar": ["من نحن", "عن الشركة", "تاريخ", "خبرة", "مين انتم", "من انتم", "من أنتم", "مين حضراتكم"],
        "keywords_en": ["about us", "who are we", "history", "experience", "site manager info"],
        "response_ar": "نحن فريق 'الحاج رمضان محمد جبر للدهانات والديكورات'، رواد في مجال التشطيبات في مصر بخبرة تمتد لأكثر من 30 عاماً تحت إشراف مدير الموقع. 🏆\nتخصصنا تحويل الوحدات السكنية والتجارية إلى تحف فنية باستخدام أحدث الخامات وتقنيات التنفيذ.",
        "response_en": "We are 'Haj Ramadan Mohamed Gabr for Paints & Decor', leaders in finishing in Egypt with over 30 years of experience. 🏆\nWe specialize in transforming residential and commercial units into artistic masterpieces using the latest materials and techniques."
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
        for kw in entry['keywords_ar']:
            if normalize_arabic(kw) in msg_norm:
                return entry['response_ar']
        for kw in entry['keywords_en']:
            if kw.lower() in msg_norm:
                return entry['response_en']
    
    # 2. Check Learned Answers table (highest priority for admin-taught answers)
    all_learned = learned_model.get_all()
    for rec in all_learned:
        if normalize_arabic(rec['question']) == msg_norm:
            return rec['answer']
    
    # 3. Check Unanswered table for admin-learned answers (still being reviewed)
    all_unanswered = unanswered_model.get_all()
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
        
        # Validate characters
        if not re.search(r'[a-zA-Z0-9\u0600-\u06FF]', message):
            msg_warning = f"عذراً يا {user_name}، أنا أفهم فقط اللغة العربية، الإنجليزية، والأرقام.\n" \
                          f"Sorry {user_name}, I only understand Arabic, English, and numbers."
            return jsonify({'response': msg_warning})
        
        response_text = get_ai_response(user_id, message, user_name)
        
        # Recognize Contact Request
        is_contact_req = any(kw in message.lower() for kw in ["تواصل", "أكلم حد", "رقم", "اتصل", "contact", "call", "phone"])
        if is_contact_req:
            security_log_model.create("Contact Info Requested", f"User {user_name} ({user_id}) requested contact details. Message: {message}", severity="low")

        # Personalize response
        if response_text != "__NOT_FOUND__" and "يا " not in response_text:
            response_text = f"يا {user_name}، " + response_text
        
        # Logic for Unanswered Questions
        if response_text == "__NOT_FOUND__":
            # Use model to create/upsert
            unanswered_model.create(message, user_id)
            
            response_text = "عذراً، هذا السؤال جديد عليّ ولم أتمكن من فهمه جيداً. 🤖\nيرجى ترك رقم هاتفك هنا للتواصل معك من قبل مدير الموقع والإجابة على استفسارك بدقة."
        
        # Log Chat
        chat_model.create({
            'user_id': user_id,
            'user_name': user_name,
            'message': message,
            'response': response_text,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return jsonify({'response': response_text})
        
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({'error': 'An error occurred'}), 500

# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    # Use socketio.run instead of app.run for WebSocket support
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
