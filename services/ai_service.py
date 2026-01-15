import re
import difflib

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
        
        # Static Knowledge Base (Data Structure: List of Dictionaries)
        self.knowledge_base = [
            {
                "keywords_ar": [
                    "تواصل", "اتواصل", "نتواصل", "التواصل", "اكلم", "أكلم", "كلم", "اكلمكم", "كلمكم", "اكلم حد", 
                    "رقم", "ارقام", "تليفون", "تلفون", "موبايل", "محمول", "هاتف", "جوال",
                    "اتصل", "اتصال", "كلمني", "كلموني", "كلمنا", "اتصلوا", "اتصلو",
                    "ابعت", "ابعتلي", "ارسل", "ارسلوا", "بعت", "رسالة", "مراسلة",
                    "واتس", "واتساب", "whatsapp", "ايميل", "بريد", "ميل", "email",
                    "عاوز اكلم", "محتاج اتواصل", "ازاي اوصلكم", "ازاي اكلمكم", "طريقة التواصل",
                    "وسيلة تواصل", "للتواصل", "للاتصال"
                ],
                "keywords_en": [
                    "contact", "contacts", "call", "calls", "phone", "telephone", "number", "mobile", "cell",
                    "talk", "speak", "reach", "communicate", "communication", "get in touch", "touch",
                    "whatsapp", "email", "mail", "message", "messaging", "send message",
                    "how to contact", "how to reach", "contact info", "contact information",
                    "reach out", "get hold"
                ],
                "response_ar": "يمكنك التواصل مباشرة مع مدير الموقع عبر الرقم: 01129276218 📞\nأو عبر البريد الإلكتروني: ramadan.mohamed@example.com\nيسعدنا دائماً خدمتك!",
                "response_en": "You can contact the site manager directly at: 01129276218 📞\nor via email: ramadan.mohamed@example.com\nWe are always happy to help!"
            },
            {
                "keywords_ar": [
                    "انت", "انتو", "مين", "من", "منو", "مين انت", "من انت", "انت مين",
                    "عرفني", "عرف نفسك", "عرفنا", "قولي مين انت", "اعرفك", "تعريف",
                    "بوت", "روبوت", "مساعد", "مساعد ذكي", "ذكاء", "اصطناعي", "شات بوت", "chatbot",
                    "الذكاء الاصطناعي", "ai", "مين بيكلمني", "بتكلم مين", "انت ايه", "وظيفتك ايه"
                ],
                "keywords_en": [
                    "who are you", "who is this", "who r u", "what are you", "what r u",
                    "introduce", "introduce yourself", "tell me about you", "your name",
                    "bot", "robot", "assistant", "virtual assistant", "ai", "artificial intelligence",
                    "chatbot", "chat bot", "automated", "automation", "smart assistant"
                ],
                "response_ar": "أنا المساعد الذكي لمدير الموقع الحاج رمضان محمد جبر. 🤖\nمهمتي مساعدتك في معرفة خدماتنا، تقديم نصائح في الديكور، وتسهيل تواصلك معنا.",
                "response_en": "I am the Smart Assistant for Haj Ramadan Mohamed Gabr. 🤖\nMy mission is to help you explore our services, give decor tips, and connect you with us."
            },
            {
                "keywords_ar": [
                    "نحن", "احنا", "انتم", "انتو", "حضراتكم", "حضرتكم",
                    "الشركة", "الموقع", "المؤسسة", "الفريق", "الشغل",
                    "تاريخ", "خبرة", "خبرتكم", "سنين", "سنوات", "تجربة", "تجربتكم",
                    "معلومات", "نبذة", "تعريف", "عن الشركة", "عنكم", "عنكو",
                    "من نحن", "من احنا", "مين انتم", "مين انتو", "اعرف عنكم",
                    "قولولي عنكم", "ايه قصتكم", "بتشتغلوا من امتى"
                ],
                "keywords_en": [
                    "about", "about us", "about you", "who are we", "who are you",
                    "company", "business", "firm", "organization", "team",
                    "history", "experience", "background", "info", "information",
                    "years", "profile", "story", "your story", "tell me about",
                    "how long", "since when", "established"
                ],
                "response_ar": "نحن فريق 'الحاج رمضان محمد جبر للدهانات والديكورات'، رواد في مجال التشطيبات في مصر بخبرة تمتد لأكثر من 30 عاماً تحت إشراف مدير الموقع. 🏆\nتخصصنا تحويل الوحدات السكنية والتجارية إلى تحف فنية باستخدام أحدث الخامات وتقنيات التنفيذ.",
                "response_en": "We are 'Haj Ramadan Mohamed Gabr for Paints & Decor', leaders in finishing in Egypt with over 30 years of experience. 🏆\nWe specialize in transforming residential and commercial units into artistic masterpieces using the latest materials and techniques."
            },
            {
                "keywords_ar": [
                    "خدمات", "خدمة", "خدماتكم", "الخدمات", "ايه الخدمات",
                    "بتعملوا", "تعملوا", "بتشتغلوا", "تشتغلوا", "بتقدموا", "تقدموا",
                    "شغل", "شغلكم", "الشغل", "انشطة", "نشاط", "مجالات", "مجال",
                    "تخصص", "تخصصكم", "اعمال", "اعمالكم", "نوع الشغل",
                    "ايه اللي بتعملوه", "بتشتغلوا في ايه", "ممكن تعملوا ايه",
                    "عندكم ايه", "بتوفروا ايه"
                ],
                "keywords_en": [
                    "services", "service", "what services", "your services",
                    "what do you do", "what you do", "what do you offer", "what you offer",
                    "activities", "activity", "scope", "work", "works", "offerings",
                    "specialization", "specialty", "specialize", "field", "fields",
                    "what can you do", "what are you offering", "provide", "available services"
                ],
                "response_ar": "خدماتنا تشمل: 🎨\n1. دهانات حديثة وكلاسيكية.\n2. تشطيبات جبس بورد وأسقف معلقة.\n3. تركيب جميع أنواع ورق الحائط.\n4. تجديد وترميم الشقق القديمة.\n5. تشطيب كامل (على المفتاح).",
                "response_en": "Our services include: 🎨\n1. Modern and Classic Paints.\n2. Gypsum Board and Suspended Ceilings.\n3. Wallpaper Installation.\n4. Renovation of Old Apartments.\n5. Full Turnkey Finishing."
            },
            {
                "keywords_ar": [
                    "مشاريع", "مشروع", "مشاريعكم", "المشاريع",
                    "اعمال", "اعمالكم", "الاعمال", "شغل", "شغلكم",
                    "صور", "صورة", "الصور", "فيديو", "فيديوهات",
                    "سابقة", "سابقة اعمال", "اعمال سابقة", "شغل سابق",
                    "نفذتوها", "عملتوها", "خلصتوها", "اتعملت",
                    "وريني", "شوفني", "اشوف", "عاوز اشوف", "ممكن اشوف",
                    "معرض", "معرض اعمال", "بورتفوليو", "portfolio",
                    "انجازات", "انجازاتكم", "نماذج", "امثلة", "مثال"
                ],
                "keywords_en": [
                    "projects", "project", "works", "work", "jobs", "job",
                    "portfolio", "gallery", "photos", "pictures", "images", "videos",
                    "previous", "previous work", "past work", "past projects",
                    "show me", "let me see", "can i see", "examples", "example",
                    "achievements", "accomplishments", "completed", "finished",
                    "samples", "showcase"
                ],
                "response_ar": "فخورون بمشاريعنا! 🏗️\nقمنا بتنفيذ مئات الوحدات السكنية والتجارية في القاهرة الكبرى.\nيمكنك مشاهدة صور حية لأعمالنا في صفحة 'مشاريعنا' على الموقع.\nهل تحب أن أصف لك أحدث مشروع قمنا به؟ 😃",
                "response_en": "We are proud of our projects! 🏗️\nWe have executed hundreds of residential and commercial units in Greater Cairo.\nYou can view live photos of our work on the 'Projects' page of the website.\nWould you like me to describe our latest project? 😃"
            },
            {
                "keywords_ar": [
                    "مكان", "مكانكم", "المكان", "فين", "وين", "فينكم", "وينكم",
                    "عنوان", "العنوان", "عنوانكم", "موقع", "الموقع", "موقعكم",
                    "مقر", "المقر", "مقركم", "لوكيشن", "location",
                    "محل", "المحل", "محلكم", "مكتب", "المكتب", "مكتبكم",
                    "تواجد", "تواجدكم", "موجودين فين", "بتشتغلوا فين",
                    "ازاي اجيلكم", "ازاي اوصلكم", "الطريق", "ازاي اروح"
                ],
                "keywords_en": [
                    "location", "locations", "address", "where", "where are you",
                    "place", "office", "offices", "hq", "headquarters", "head office",
                    "situated", "located", "based", "where located", "where based",
                    "how to get", "how to reach", "directions", "find you"
                ],
                "response_ar": "مقر مدير الموقع الرئيسي في القاهرة، ولكننا نقدم خدماتنا في جميع أنحاء الجمهورية (القاهرة، الجيزة، والإسكندرية والمحافظات الأخرى). 🚛",
                "response_en": "Our HQ is in Cairo, but we serve all over Egypt (Cairo, Giza, Alexandria, and other governorates). 🚛"
            },
            {
                "keywords_ar": [
                    "مواعيد", "ميعاد", "المواعيد", "الميعاد", "مواعيدكم",
                    "شغالين", "فاتحين", "مفتوحين", "بتشتغلوا", "بتفتحوا",
                    "وقت", "اوقات", "الوقت", "ساعات", "الساعات", "ساعات العمل",
                    "دوام", "الدوام", "دوامكم", "امتى", "متى", "توقيت", "التوقيت",
                    "من امتى لامتى", "بتفتحوا الساعة كام", "بتقفلوا الساعة كام",
                    "شغالين كل يوم", "ايام العمل", "ايام الشغل"
                ],
                "keywords_en": [
                    "hours", "hour", "time", "times", "timing", "timings",
                    "open", "opening", "opening hours", "opening times",
                    "working", "working hours", "working times", "work hours",
                    "schedule", "when", "when open", "availability", "available",
                    "business hours", "office hours", "what time", "close", "closing"
                ],
                "response_ar": "متاحون لخدمتكم طوال أيام الأسبوع من الساعة 9 صباحاً حتى 4 مساءً. 🕘",
                "response_en": "We are available to serve you 7 days a week from 9 AM to 4 PM. 🕘"
            },
            {
                "keywords_ar": [
                    "شروخ", "شرخ", "الشروخ", "شرخ في الحيطة", "شروخ في الحائط",
                    "تشقق", "تشققات", "التشققات", "متشققة", "مشروخة",
                    "تنمل", "ترييح", "كسر", "كسور", "مكسورة",
                    "تصدع", "تصدعات", "صدع", "صدوع", "متصدعة",
                    "حيطة مشروخة", "جدار مشروخ", "الحائط فيه شروخ",
                    "عندي شرخ", "في شروخ", "مشكلة شروخ", "علاج الشروخ"
                ],
                "keywords_en": [
                    "cracks", "crack", "cracking", "cracked",
                    "fissures", "fissure", "wall crack", "wall cracks",
                    "splitting", "split", "fracture", "fractures", "fractured",
                    "broken", "broken wall", "damaged wall",
                    "crack problem", "fix cracks", "repair cracks"
                ],
                "response_ar": "الشروخ أنواع: 🔸 شروخ سطحية: نعالجها بمعجون شروخ مرن. 🔸 شروخ عميقة (إنشائية): نستخدم شريط 'ميش' مع المعجون لضمان تماسك الطبقات.\nلا تقلق، لدينا حلول نهائية! 🛠️",
                "response_en": "Cracks have types:\n🔸 Surface cracks: Treated with flexible crack putty.\n🔸 Deep cracks (structural): We use 'Mesh' tape during putty to ensure layer cohesion.\nDon't worry, we have permanent solutions! 🛠️"
            },
            {
                "keywords_ar": [
                    "اسعار", "سعر", "الاسعار", "السعر", "اسعاركم", "سعركم",
                    "تكلفة", "تكاليف", "التكلفة", "التكاليف",
                    "بكام", "كام", "بكم", "ب كام", "بكام المتر",
                    "المتر", "متر", "للمتر", "سعر المتر",
                    "مصنعية", "المصنعية", "اجر", "الاجر",
                    "فلوس", "الفلوس", "ثمن", "الثمن", "قيمة", "القيمة",
                    "عرض سعر", "تسعيرة", "التسعيرة", "الاسعار عندكم",
                    "كام هيكلفني", "هيكلف كام", "التكلفة كام", "الميزانية"
                ],
                "keywords_en": [
                    "price", "prices", "pricing", "cost", "costs", "costing",
                    "how much", "how much does it cost", "rate", "rates",
                    "quotation", "quote", "estimate", "estimation",
                    "budget", "fee", "fees", "charge", "charges",
                    "per meter", "per square meter", "what's the price",
                    "price list", "cost estimate"
                ],
                "response_ar": "الأسعار تختلف حسب نوع التشطيب والمساحة وحالة الحوائط. 💰\nولكن كن واثقاً أننا نقدم أفضل قيمة مقابل سعر في السوق.\nيمكننا تحديد موعد للمعاينة لتقديم عرض سعر دقيق ومجاني! 📅",
                "response_en": "Prices vary depending on the finish type, area, and wall condition. 💰\nBut rest assured, we offer the best value for money in the market.\nWe can schedule a visit for a precise and free quotation! 📅"
            },
            {
                "keywords_ar": [
                    "جوتن", "سايبس", "sipes", "jotun", "جي ال سي", "glc",
                    "خامات", "خامة", "الخامات", "خاماتكم",
                    "انواع", "نوع", "الانواع", "النوع",
                    "دهان", "دهانات", "الدهان", "الدهانات",
                    "بلاستيك", "زيت", "دهان بلاستيك", "دهان زيت",
                    "ماركات", "ماركة", "براند", "البراند", "علامة تجارية",
                    "تستخدموا", "بتستخدموا", "تستعملوا", "بتستعملوا",
                    "جودة", "الجودة", "نوعية", "النوعية", "كويس", "اصلي",
                    "ايه اللي بتستخدموه", "بتشتغلوا بايه", "المواد"
                ],
                "keywords_en": [
                    "jotun", "sipes", "glc", "materials", "material",
                    "brands", "brand", "paint brands", "paint types",
                    "quality", "high quality", "type", "types", "kind", "kinds",
                    "what you use", "what do you use", "which brands",
                    "plastic paint", "oil paint", "emulsion", "original", "genuine"
                ],
                "response_ar": "نحن معتمدون لاستخدام كبرى العلامات العالمية مثل 'جوتن' (Jotun) و 'سايبس' (Sipes) و 'جي إل سي' (GLC).\nنضمن لك خامات أصلية تعيش طويلاً وتعطيك ألوان زاهية. 🌈",
                "response_en": "We are certified users of top global brands like 'Jotun', 'Sipes', and 'GLC'.\nWe guarantee authentic materials that last long and provide vibrant colors. 🌈"
            },
            {
                "keywords_ar": [
                    "رطوبة", "رطوبه", "الرطوبة", "رطوبة في الحيطة",
                    "نداوة", "ندى", "الندى", "نداوه",
                    "مياه", "ميه", "المياه", "الميه", "مية",
                    "تسرب", "تسريب", "التسرب", "تسرب مياه", "تسريب ميه",
                    "عفن", "العفن", "فطريات", "الفطريات", "عفونة",
                    "ريحة", "رايحة", "الريحة", "ريحة وحشة", "رايحة عفن",
                    "مشكلة", "مشكله", "المشكلة", "عندي مشكلة", "في مشكلة",
                    "حلول", "حل", "الحل", "الحلول", "علاج", "معالجة",
                    "ازاي اعالج", "ايه الحل", "عاوز حل", "محتاج حل",
                    "الحيطة مبلولة", "الجدار فيه ميه", "في تسريب"
                ],
                "keywords_en": [
                    "humidity", "moisture", "dampness", "damp", "wet", "wetness",
                    "water", "water problem", "leak", "leakage", "leaking",
                    "mold", "mould", "fungus", "mildew",
                    "smell", "bad smell", "odor", "odour",
                    "problem", "issue", "solution", "fix", "repair",
                    "how to fix", "need solution", "wet wall", "damp wall"
                ],
                "response_ar": "مشكلة الرطوبة لها حلول جذرية! 💧\n\n🔹 **الأسباب الشائعة:**\n• تسرب مياه من السباكة أو الأسطح\n• سوء التهوية\n• عزل ضعيف للحوائط الخارجية\n\n🔹 **الحلول المهنية:**\n1️⃣ **كشف المصدر:** نحدد مصدر التسرب بدقة\n2️⃣ **العزل المائي:** نستخدم مواد عزل حديثة (سيكا، بيتومين)\n3️⃣ **المعالجة:** إزالة الطبقات المتضررة وتطهير الحائط\n4️⃣ **الدهان المضاد:** استخدام دهانات مقاومة للرطوبة\n\n✅ نضمن لك حل نهائي مع ضمان على العمل!\nتواصل معنا للمعاينة المجانية: 01129276218 📞",
                "response_en": "Humidity problems have permanent solutions! 💧\n\n🔹 **Common Causes:**\n• Water leakage from plumbing or roofs\n• Poor ventilation\n• Weak insulation of external walls\n\n🔹 **Professional Solutions:**\n1️⃣ **Source Detection:** We accurately identify the leak source\n2️⃣ **Waterproofing:** Using modern insulation materials (Sika, Bitumen)\n3️⃣ **Treatment:** Removing damaged layers and sanitizing the wall\n4️⃣ **Anti-Moisture Paint:** Using humidity-resistant paints\n\n✅ We guarantee a permanent solution with work warranty!\nContact us for free inspection: 01129276218 📞"
            }
        ]

    def normalize_text(self, text: str) -> str:
        """Standardize text (Arabic & English) for better matching."""
        if not text: return ""
        text = text.lower().strip()
        
        # Remove special characters and punctuation
        text = re.sub(r'[?؟!.،,]', '', text)
        
        # Arabic-specific normalization (Alif, Ta-Marbuta, etc.)
        text = re.sub(r"[أإآ]", "ا", text)
        text = re.sub(r"ة", "ه", text)
        text = re.sub(r"ى", "ي", text)
        text = re.sub(r"ؤ", "و", text)
        text = re.sub(r"ئ", "ي", text)
        text = re.sub(r"[\u064B-\u0652]", "", text) # Remove Harakat
        
        # Common Egyptian/Slang variants to Standard mapping
        dialect_map = {
            "عايز": "اريد", "عاوز": "اريد", "محتاج": "اريد",
            "عايزين": "نريد", "عاوزين": "نريد",
            "بكام": "سعر", "كام": "سعر", "تكلفه": "سعر",
            "فين": "اين", "فينكم": "مكانكم",
            "شغلكم": "اعمالكم", "شغل": "عمل", "صور": "اعمال", "مشاريع": "اعمال",
            "مين": "من", "بلدي": "مصر",
            "حضرتك": "", "باشا": "", "يا": "", "ممكن": "", "لو": "", "سمحت": "",
            "مشكله": "مشكلة", "عندي": "لدي", "توجد": "موجود",
            "حلول": "حل", "علاج": "حل", "ايه": "ما",
        }
        
        words = text.split()
        normalized_words = [dialect_map.get(w, w) for w in words]
        return " ".join([w for w in normalized_words if w]).strip()

    def normalize_arabic(self, text: str) -> str:
        """Legacy shim for normalize_text."""
        return self.normalize_text(text)

    def calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity ratio."""
        return difflib.SequenceMatcher(None, s1, s2).ratio()

    def extract_keywords(self, text: str) -> set:
        """Extract core keywords by removing common fillers."""
        # Simple stop words for both Arabic and English
        stop_words = {
            "ما", "من", "هل", "كيف", "اين", "متي", "كم", "في", "علي", "الي", "عن", "بس", "هو", "هي", "انتم", 
            "the", "a", "an", "is", "are", "what", "how", "where", "who", "can", "you", "tell", "me"
        }
        words = self.normalize_text(text).split()
        return {w for w in words if len(w) > 2 and w not in stop_words}

    def _refresh_cache(self):
        """Refreshes the internal cache of learned answers."""
        self._learned_cache = self.learned_model.get_all()

    def get_response(self, user_id, message, user_name="Guest") -> str:
        """Get the appropriate response for the user message with fuzzy logic."""
        msg_norm = self.normalize_text(message)
        msg_keywords = self.extract_keywords(message)
        
        # 1. Check Static Knowledge Base (Keyword-based high priority)
        for entry in self.knowledge_base:
            # Check Arabic keywords
            for kw in entry['keywords_ar']:
                kw_norm = self.normalize_text(kw)
                if kw_norm in msg_norm or (kw_norm in msg_keywords):
                    return entry['response_ar']
            # Check English keywords
            for kw in entry['keywords_en']:
                if kw.lower() in message.lower() or (kw.lower() in msg_keywords):
                    return entry['response_en']
        
        # 2. Check Learned Answers table (Cached with Fuzzy Matching)
        if self._learned_cache is None:
            self._refresh_cache()
            
        best_match = None
        highest_score = 0
        
        for rec in self._learned_cache:
            stored_question = rec['question']
            stored_norm = self.normalize_text(stored_question)
            
            # Technique A: Exact Normalized Match
            if stored_norm == msg_norm:
                return rec['answer']
            
            # Technique B: Fuzzy Similarity (Levenshtein-like)
            score = self.calculate_similarity(stored_norm, msg_norm)
            
            # Technique C: Keyword Overlap (Weighted)
            stored_keywords = self.extract_keywords(stored_question)
            if stored_keywords and msg_keywords:
                overlap = len(stored_keywords.intersection(msg_keywords))
                overlap_score = overlap / max(len(stored_keywords), len(msg_keywords))
                # Boost the fuzzy score if keywords match well
                score = max(score, overlap_score)

            if score > highest_score:
                highest_score = score
                best_match = rec['answer']
        
        # If we have a reasonably strong match (threshold 0.65 for fuzzy/keyword mix)
        if highest_score > 0.65:
            return best_match
        
        # 3. Check Unanswered table for admin-learned answers
        all_unanswered = self.unanswered_model.get_all()
        for rec in all_unanswered:
            if self.calculate_similarity(self.normalize_text(rec['question']), msg_norm) > 0.8:
                if rec.get('admin_response'):
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
