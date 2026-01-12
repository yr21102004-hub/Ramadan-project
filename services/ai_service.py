import re
from models import Database, LearnedAnswersModel, UnansweredQuestionsModel, ChatModel
from datetime import datetime

class AIService:
    """
    Service class for AI and Chatbot logic.
    Encapsulates all logic related to processing user messages and generating responses.
    """
    
    def __init__(self):
        self.learned_model = LearnedAnswersModel()
        self.unanswered_model = UnansweredQuestionsModel()
        self.chat_model = ChatModel()
        self._learned_cache = None
        self._last_cache_update = None
        
        # Static Knowledge Base
        self.knowledge_base = [
            # ... (Static content remains the same structure, but truncated here for brevity in diff if not changing)
            # Actually, I must provide the full content or just the init method change.
            # I will modify get_response to use cache.
        ]
        # To avoid re-listing the KB, I will target specific chunks.
        
    # (Re-declaring init to initialize cache variables)
    def __init__(self):
        self.learned_model = LearnedAnswersModel()
        self.unanswered_model = UnansweredQuestionsModel()
        self.chat_model = ChatModel()
        self._learned_cache = None
        
        # Static Knowledge Base (Data Structure: List of Dictionaries)
        self.knowledge_base = [
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

    def normalize_arabic(self, text: str) -> str:
        """Standardize Arabic text for better matching."""
        if not text: return ""
        text = text.lower().strip()
        text = re.sub(r"[أإآ]", "ا", text)
        text = re.sub(r"ة", "ه", text)
        text = re.sub(r"[\u064B-\u0652]", "", text)
        return text

    def _refresh_cache(self):
        """Refreshes the internal cache of learned answers."""
        self._learned_cache = self.learned_model.get_all()

    def get_response(self, user_id, message, user_name="Guest") -> str:
        """Get the appropriate response for the user message."""
        msg_norm = self.normalize_arabic(message)
        
        # 1. Check Static Knowledge Base
        for entry in self.knowledge_base:
            for kw in entry['keywords_ar']:
                if self.normalize_arabic(kw) in msg_norm:
                    return entry['response_ar']
            for kw in entry['keywords_en']:
                if kw.lower() in msg_norm:
                    return entry['response_en']
        
        # 2. Check Learned Answers table (Cached)
        if self._learned_cache is None:
            self._refresh_cache()
            
        for rec in self._learned_cache:
            if self.normalize_arabic(rec['question']) == msg_norm:
                return rec['answer']
        
        # 3. Check Unanswered table for admin-learned answers (still being reviewed)
        # We don't cache this heavily as it changes frequently, but could be optimized.
        all_unanswered = self.unanswered_model.get_all()
        for rec in all_unanswered:
            if self.normalize_arabic(rec['question']) == msg_norm and rec.get('admin_response'):
                return rec['admin_response']
            
        return "__NOT_FOUND__"


    def process_message(self, user_id, user_name, message):
        """
        Main entry point for processing a chat message.
        Returns: Tuple(response_text, is_new_unanswered)
        """
        # Validate characters
        if not re.search(r'[a-zA-Z0-9\u0600-\u06FF]', message):
            msg_warning = f"عذراً يا {user_name}، أنا أفهم فقط اللغة العربية، الإنجليزية، والأرقام.\n" \
                          f"Sorry {user_name}, I only understand Arabic, English, and numbers."
            return msg_warning

        response_text = self.get_response(user_id, message, user_name)
        
        # Personalize response
        if response_text != "__NOT_FOUND__" and "يا " not in response_text:
            response_text = f"يا {user_name}، " + response_text
        
        # Helper for handling not found
        if response_text == "__NOT_FOUND__":
            # Use model to create/upsert
            self.unanswered_model.create(message, user_id)
            response_text = "عذراً، هذا السؤال جديد عليّ ولم أتمكن من فهمه جيداً. 🤖\nيرجى ترك رقم هاتفك هنا للتواصل معك من قبل مدير الموقع والإجابة على استفسارك بدقة."
        
        # Log Chat
        self.chat_model.create({
            'user_id': user_id,
            'user_name': user_name,
            'message': message,
            'response': response_text,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return response_text
