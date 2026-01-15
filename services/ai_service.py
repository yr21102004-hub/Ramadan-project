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
                    "السلام", "سلام", "مرحبا", "اهلا", "هاي", "هلو", "صباح", "مساء",
                    "ازيك", "ازيكم", "عامل ايه", "اخبارك", "كيفك", "كيف حالك",
                    "تمام", "الحمد لله", "بخير", "كويس", "تشرفنا", "اهلين"
                ],
                "keywords_en": [
                    "hi", "hello", "hey", "hai", "hay", "hii", "helo",
                    "good morning", "good evening", "good afternoon",
                    "how are you", "how r u", "how are u", "whats up", "what's up",
                    "how do you do", "nice to meet", "greetings", "sup"
                ],
                "response_ar": "أهلاً وسهلاً! 👋\nأنا المساعد الذكي لـ الحاج رمضان محمد جبر للدهانات والديكورات.\nكيف يمكنني مساعدتك اليوم؟ 😊\n\nيمكنني الإجابة عن:\n• مشاكل الرطوبة والشروخ\n• الأسعار والخدمات\n• المشاريع والأعمال السابقة\n• معلومات التواصل",
                "response_en": "Hello! 👋\nI'm the Smart Assistant for Haj Ramadan Mohamed Gabr Paints & Decor.\nHow can I help you today? 😊\n\nI can answer about:\n• Humidity and crack problems\n• Prices and services\n• Projects and previous work\n• Contact information"
            },
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
                    "خارجي", "خارجية", "الخارجي", "الخارجية", "واجهات", "وجهات", "الواجهات", "واجهة", 
                    "بروفايل", "جرافيتو", "سفيتو", "حجر", "هاشمي", "فرعوني", "مايكا", "طوب", 
                    "سور", "اسوار", "بلكونة من بره", "شباك من بره", "دهان العمارة"
                ],
                "keywords_en": [
                    "external", "exterior", "outside", "outdoor", "facade", "facades", "front", 
                    "profile", "grafito", "saveto", "stone", "fence", "balcony outside", "building paint"
                ],
                "response_ar": "أهلاً بك! نحن حالياً متخصصون في **الدهانات والديكورات الداخلية فقط** (الشقق، الفلل، والمكاتب من الداخل). 🏠\nلا ننفذ أعمال الواجهات الخارجية في الوقت الحالي.\nهل يمكنني مساعدتك في أي شيء يخص الديكور الداخلي؟ 😊",
                "response_en": "Welcome! We currently specialize in **Interior Paints & Decor only** (Apartments, Villas, Offices inside). 🏠\nWe do not execute exterior facades at the moment.\nCan I help you with anything regarding interior decor? 😊"
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
                    "1", "١", "تقشر", "بيقشر", "مقشر", "الدهان بيقع", "قشرة", "قشور", "تساقط", "بيسقط", "واقع", 
                    "الدهان بيتشال", "طبقات بتقع", "تقشير", "ازالة الدهان", "الدهان بيفك", "بيفك", 
                    "بيفرول", "بيطلع", "بيتقلع", "دهان قديم بيقع", "الحيطة بتقشر", "السقف بيقشر",
                    "نقشر", "تقشيط", "سقوط الدهان", "انفصال الدهان", "البيت بيقشر"
                ],
                "keywords_en": [
                    "peeling", "paint peeling", "flaking", "flakes", "falling off", "paint coming off", 
                    "strips", "layers peeling", "detachment", "loose paint", "paint lifting", "scaling", 
                    "blistering and peeling", "paint stripping", "old paint falling", "wall peeling", 
                    "ceiling peeling", "paint separation", "coat peeling", "paint chip", "chipping"
                ],
                "response_ar": "1️⃣ تقشّر الدهان\n\n🔹 الأسباب من الأصل:\n• وجود رطوبة أو تسريب مياه\n• دهان فوق سطح مترب أو دهان قديم\n• عدم استخدام برايمر (الأساس)\n\n🔹 الحلول:\n• إزالة الدهان المتقشّر تمامًا\n• معالجة الرطوبة أو التسريب\n• تنظيف وصنفرة السطح\n• وضع برايمر مناسب ثم إعادة الدهان\n\n🔧 نصيحة مهمة\n70٪ من مشاكل الدهانات سببها تجهيز السطح الخاطئ وليس الدهان نفسه.",
                "response_en": "Peeling paint is annoying, but fixable! 🏚️\n\n🔹 **Cause:** Often due to moisture, dirty surface before painting, or poor putty.\n🔹 **Solution:**\n1. Scrape off all old paint.\n2. Sand and clean the wall thoroughly.\n3. Apply a strong Primer to ensure adhesion.\n4. Repaint with high-quality materials.\n\nContact us to handle it for you! 01129276218 📞"
            },
            {
                "keywords_ar": [
                    "2", "٢", "شروخ", "شرخ", "تشقق", "تشققات", "تنميل", "تنميلات", "نمملة", "منملة", "ترييح", 
                    "الحيطة مريحة", "صدع", "تصدع", "شق", "شقوق", "كسر", "كسور", "الحيطة مشروخة", 
                    "الجدار مشروخ", "السقف مشروخ", "شرخ في الحائط", "شرخ عمودي", "شرخ افقي", "شروخ شعرية",
                    "شرخ في الزاوية", "شروخ سطحية", "شروخ عميقة", "حيطتي مشققة"
                ],
                "keywords_en": [
                    "cracks", "crack", "cracking", "fissure", "fissures", "hairline cracks", "wall cracked", 
                    "split", "fracture", "fractured", "broken wall", "structural cracks", "settlement cracks", 
                    "plaster cracks", "ceiling cracks", "wall splitting", "gap in wall", "deep crack", 
                    "surface crack", "spider web cracks", "cracked paint"
                ],
                "response_ar": "2️⃣ تشققات الدهان\n\n🔹 الأسباب:\n• دهان طبقات سميكة مرة واحدة\n• استخدام دهان رديء الجودة\n• تمدد وانكماش الجدار بسبب الحرارة\n\n🔹 الحلول:\n• كشط المناطق المتشققة\n• ملء الشروخ بالمعجون\n• دهان بطبقات خفيفة ومتعددة\n• اختيار دهان مرن وجيد\n\n🔧 نصيحة مهمة\n70٪ من مشاكل الدهانات سببها تجهيز السطح الخاطئ وليس الدهان نفسه.",
                "response_en": "Cracks vary, but we have the cure! 🧱\n\n🔹 **Surface Cracks:** Treated with flexible crack putty and new paint.\n🔹 **Deep Cracks (Structural):** Need opening the crack, applying 'Mesh Tape' with premium putty to bind parts.\n\nDon't ignore cracks, request a free inspection now: 01129276218 📞"
            },
            {
                "keywords_ar": [
                    "3", "٣", "فقاعات", "فقاقيع", "بقللة", "مبقلل", "الدهان مبقع", "منفوخ", "نفخ", "انتفاخ", 
                    "الدهان منفوخ", "بالونات", "بلالين", "هوا تحت الدهان", "ميه تحت الدهان", "تقبب", 
                    "قبة", "معبي هوا", "طرطشة", "حبوب", "محبب", "الدهان محبب", "بشابيش", "فقاعة"
                ],
                "keywords_en": [
                    "bubbles", "bubbling", "blisters", "blistering", "paint bubbles", "swollen paint", 
                    "swelling", "air pockets", "trapped air", "paint puffing", "ballooning", "paint lifting", 
                    "uneven surface", "bumps", "lumps in paint", "paint rising", "water blisters", 
                    "solvent blisters", "heat blisters", "moisture blisters", "bubbled"
                ],
                "response_ar": "3️⃣ فقاعات الدهان\n\n🔹 الأسباب:\n• دهان على سطح رطب\n• الدهان في جو حار جدًا\n• استخدام رولة أو فرشة غير نظيفة\n\n🔹 الحلول:\n• ترك السطح يجف تمامًا\n• إزالة الفقاعات بعد الجفاف\n• إعادة الدهان في درجة حرارة معتدلة\n\n🔧 نصيحة مهمة\n70٪ من مشاكل الدهانات سببها تجهيز السطح الخاطئ وليس الدهان نفسه.",
                "response_en": "Bubbles mean the paint isn't breathing or moisture is trapped! 🫧\n\n🔹 **Solution:**\n1. Scrape bubbles and remove swollen paint.\n2. Let the wall dry completely (if moisture is the cause).\n3. Sand and smooth the surface.\n4. Use high-quality breathable paint.\n\nWe are here to help! 😊"
            },
            {
                "keywords_ar": [
                    "5", "٥", "بهتان", "باهت", "لون متغير", "تغير اللون", "اللون راح", "اللون طار", "اصفرار", 
                    "مصفر", "اللون بيغير", "مش نفس اللون", "اللون اختلف", "تلطيش", "ملطش", "بقع لون", 
                    "لون مش موحد", "الوان مش متجانسة", "اللون طفى", "مطفي", "لمعة راحت", "تباين في اللون",
                    "اللون جرب", "لون الحيطة اتغير", "الدهان غير"
                ],
                "keywords_en": [
                    "fading", "faded", "discoloration", "discolouration", "yellowing", "color change", 
                    "colour change", "losing color", "dull paint", "paint dulled", "uneven color", 
                    "patchy color", "color mismatch", "bleaching", "sun damage", "chalking", "staining", 
                    "uneven shade", "loss of gloss", "flat spots"
                ],
                "response_ar": "5️⃣ بهتان أو تغيّر لون الدهان\n\n🔹 الأسباب:\n• التعرض المباشر للشمس\n• دهان غير مقاوم للأشعة فوق البنفسجية\n• استخدام لون ضعيف الثبات\n\n🔹 الحلول:\n• اختيار دهان مقاوم للشمس\n• إضافة طبقة حماية شفافة\n• استخدام ألوان خارجية مخصصة\n\n🔧 نصيحة مهمة\n70٪ من مشاكل الدهانات سببها تجهيز السطح الخاطئ وليس الدهان نفسه.",
                "response_en": "Discoloration ruins your home's beauty! 🎨\nOften caused by direct sunlight or cheap paints.\n\n✅ **Our Advice:** We use UV-resistant paints (Jotun/GLC) that last for years vividly.\nRefresh your home colors with us using the best materials! ✨"
            },
            {
                "keywords_ar": [
                    "4", "٤", "رطوبة", "عفن", "فطريات", "بقع خضراء", "بقع سوداء", "الحيطة مرشحة", "نشع", 
                    "بتنشع", "مياه في الحيطة", "ميه", "تمليح", "املاح", "ريحة عفن", "ريحة كمكمة", 
                    "كمكمة", "الحيطة منشعة", "الجدار مبلول", "ساقعة", "الحيطة بتجيب ميه", "تسريب مياه",
                    "الحيطة معرقة", "تعريق", "مايه", "حائط رطب", "رشح"
                ],
                "keywords_en": [
                    "humidity", "moisture", "damp", "dampness", "mold", "mould", "mildew", "fungus", 
                    "fungi", "green spots", "black spots", "wet wall", "water stain", "salt deposits", 
                    "efflorescence", "musty smell", "water seeping", "wall sweating", "condensation", 
                    "water leak", "leaking water", "wet spots", "damp patch"
                ],
                "response_ar": "4️⃣ بقع الرطوبة والعفن\n\n🔹 الأسباب:\n• تسريب مياه أو تكثف بخار\n• ضعف التهوية\n• عدم استخدام دهان مقاوم للرطوبة\n\n🔹 الحلول:\n• معالجة مصدر الرطوبة أولًا\n• تنظيف العفن بمحلول مطهر\n• استخدام دهان مقاوم للرطوبة والعفن\n\n🔧 نصيحة مهمة\n70٪ من مشاكل الدهانات سببها تجهيز السطح الخاطئ وليس الدهان نفسه.",
                "response_en": "Humidity problems have permanent solutions! 💧\n\n🔹 **Common Causes:** Water leakage or poor ventilation.\n🔹 **Professional Solution:**\n1️⃣ **Detect & Fix** the source.\n2️⃣ **Waterproofing** with specialized materials (Sika/Bitumen).\n3️⃣ **Anti-Moisture Paint**.\n\nContact us for free inspection: 01129276218 📞"
            },
            {
                "keywords_ar": [
                    "6", "٦", "اثار الفرشاة", "اثار الرولة", "خطوط", "مخطط", "الدهان مخطط", "مش ناعم", "خشن", 
                    "تسييل", "ممسح", "علامات الرولة", "علامات الفرشاة", "ريجة", "خطوط طولية", "خطوط عرضية", 
                    "عيوب فرد", "الدهان مش مفرود", "تكتل", "مكلكع", "كلكعة", "الدهان سايل", "تلطيخ", 
                    "الرولة معلمة", "الفرشة معلمة"
                ],
                "keywords_en": [
                    "brush marks", "roller marks", "brush strokes", "roller strokes", "streaks", "streaking", 
                    "lines in paint", "ridges", "uneven texture", "running paint", "drips", "sagging", 
                    "lap marks", "stippling", "orange peel", "poor flow", "leveling issues", "application marks", 
                    "tool marks", "bumpy finish"
                ],
                "response_ar": "6️⃣ آثار الفرشاة أو الرولة\n\n🔹 الأسباب:\n• دهان ثقيل وغير مخفف\n• أدوات سيئة الجودة\n• دهان غير متساوٍ\n\n🔹 الحلول:\n• تخفيف الدهان حسب تعليمات الشركة\n• استخدام رولة وفرش جيدة\n• الدهان باتجاه واحد وبهدوء\n\n🔧 نصيحة مهمة\n70٪ من مشاكل الدهانات سببها تجهيز السطح الخاطئ وليس الدهان نفسه.",
                "response_en": "Brush and roller marks indicate lack of experience or improper paint thinning. 🖌️\nFor a silk-smooth finish:\n• Wall must be sanded flat.\n• Apply a new coat using high-quality roller and professional technique.\n\nTry the professional touch with us! 👌"
            },
            {
                "keywords_ar": [
                    "7", "٧", "شفافية", "شفاف", "الدهان شفاف", "الحيطة باينة", "اللون القديم باين", "تغطية ضعيفة", 
                    "مش مغطي", "خفيف", "دهان خفيف", "وش واحد", "محتاج وش تاني", "مش ساتر", "كشف", 
                    "كاشف", "اللون ماغطاش", "مسيل", "تسييل خفيف", "تغطية سيئة", "عيوب تغطية", "باهت جدا",
                    "الدهان مش كاسي", "اللون كاشف"
                ],
                "keywords_en": [
                    "transparency", "transparent", "see-through", "poor coverage", "not covering", 
                    "hiding power", "low opacity", "wall showing through", "old color showing", "thin paint", 
                    "watery paint", "sheer", "translucent", "need more coats", "coverage issues", "paint too thin", 
                    "bleed through", "underlying surface visible", "weak color", "insufficient coverage"
                ],
                "response_ar": "7️⃣ الدهان غير ساتر (ضعف التغطية)\n\n🔹 الأسباب:\n• لون أساس داكن\n• دهان منخفض الجودة\n• عدم استخدام برايمر\n• طبقة واحدة فقط\n\n🔹 الحلول:\n• استخدام برايمر مناسب\n• زيادة عدد الطبقات\n• اختيار دهان عالي التغطية\n• توحيد لون السطح قبل الدهان\n\n🔧 نصيحة مهمة\n70٪ من مشاكل الدهانات سببها تجهيز السطح الخاطئ وليس الدهان نفسه.",
                "response_en": "If paint is transparent, it's too thin or coats are insufficient. 📉\n\n🔹 **Solution:**\n• Apply an additional coat.\n• Use paints with high 'Hiding Power' like Jotun Fenomastic.\nWe'll make your walls solid and rich in color! 🌈"
            },
            {
                "keywords_ar": [
                    "مشكلة", "مشكله", "المشكلة", "عندي مشكلة", "في مشكلة", 
                    "واجهتني مشكلة", "صادفتني مشكلة", "خطأ", "غلط", "help", "مساعدة"
                ],
                "keywords_en": [
                    "problem", "issue", "i have a problem", "there is a problem",
                    "trouble", "error", "bug", "wrong", "help me"
                ],
                "response_ar": "قل لي ما هي المشكلة بالتحديد؟ 🤔 هل هي:\n1) تقشّر الدهان؟\n2) تشققات الدهان 🧱\n3) ظهور فقاعات 🫧\n4) تغيّر اللون أو بهتانه 🎨\n5) بقع الرطوبة والعفن 💧\n6) آثار الفرشاة أو الرولة 🖌️\n7) شفافية الدهان\n\nاكتب لي تفاصيل أكتر وهساعدك فوراً!",
                "response_en": "Tell me, what is the problem exactly? 🤔 Is it:\n1) Peeling paint?\n2) Cracks? 🧱\n3) Bubbles? 🫧\n4) Discoloration? 🎨\n5) Humidity & Mold? 💧\n6) Brush marks? 🖌️\n7) Transparency?\n\nPlease provide more details so I can help you!"
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

    def detect_language(self, text: str) -> str:
        """Detect if the message is primarily Arabic or English."""
        # Count Arabic characters vs English characters
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        # If more Arabic characters, it's Arabic
        if arabic_chars > english_chars:
            return 'ar'
        elif english_chars > 0:
            return 'en'
        else:
            # Default to Arabic if no clear indication
            return 'ar'

    def get_response(self, user_id, message, user_name="Guest") -> str:
        """Get the appropriate response for the user message with fuzzy logic."""
        msg_norm = self.normalize_text(message)
        msg_keywords = self.extract_keywords(message)
        
        # Detect user's language
        user_language = self.detect_language(message)
        
        # 1. Check Static Knowledge Base (Keyword-based high priority)
        for entry in self.knowledge_base:
            matched = False
            
            # Check Arabic keywords
            msg_words = set(msg_norm.split())
            for kw in entry['keywords_ar']:
                kw_norm = self.normalize_text(kw)
                # Smart Match: Simple/Short keywords must be exact words (to avoid matching '1' in '010..')
                if len(kw_norm) < 3:
                    if kw_norm in msg_words:
                        matched = True
                        break
                elif kw_norm in msg_norm or (kw_norm in msg_keywords):
                    matched = True
                    break
            
            # If no Arabic match, check English keywords
            if not matched:
                msg_lower_words = set(message.lower().split())
                for kw in entry['keywords_en']:
                    kw_lower = kw.lower()
                    if len(kw_lower) < 3:
                        if kw_lower in msg_lower_words:
                            matched = True
                            break
                    elif kw_lower in message.lower() or (kw_lower in msg_keywords):
                        matched = True
                        break
            
            # If matched, return response in user's language
            if matched:
                if user_language == 'ar':
                    return entry['response_ar']
                else:
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
