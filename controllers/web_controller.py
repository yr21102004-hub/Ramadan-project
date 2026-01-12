from flask import Blueprint, render_template

web_bp = Blueprint('web', __name__)

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

@web_bp.route('/')
def index():
    return render_template('home.html')

@web_bp.route('/service/<service_id>')
def service_detail(service_id):
    service = SERVICES_DATA.get(service_id)
    if not service:
        return render_template('404.html'), 404
    return render_template('service_detail.html', service=service)

@web_bp.route('/about')
def about():
    return render_template('about.html')

@web_bp.route('/services')
def services():
    return render_template('services.html')

@web_bp.route('/projects')
def projects():
    return render_template('projects.html')

@web_bp.route('/contact')
def contact():
    return render_template('contact.html')
