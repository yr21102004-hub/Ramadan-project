document.addEventListener('DOMContentLoaded', () => {
    // Mobile Menu
    const hamburger = document.querySelector('.hamburger');
    const mobileMenu = document.querySelector('.mobile-menu');
    const closeMenu = document.querySelector('.close-menu');
    const mobileLinks = document.querySelectorAll('.mobile-menu a');

    function toggleMenu() {
        mobileMenu.classList.toggle('active');
        document.body.style.overflow = mobileMenu.classList.contains('active') ? 'hidden' : 'auto';
    }

    hamburger.addEventListener('click', toggleMenu);
    closeMenu.addEventListener('click', toggleMenu);

    mobileLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (mobileMenu.classList.contains('active')) toggleMenu();
        });
    });

    // Scroll Animation Observer
    const observerOptions = {
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Select elements to animate
    document.querySelectorAll('.service-card, .project-item, .info-item, .stat-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
        observer.observe(el);
    });



});

// Contact Form Submission (Global Function)
// Contact Form Submission (Global Function)
async function submitContactForm() {
    const name = document.getElementById("name").value;
    const phone = document.getElementById("phone").value;
    const message = document.getElementById("message").value;
    const submitBtn = document.querySelector('button[type="submit"]');

    if (!name || !phone || !message) {
        alert("يرجى ملء جميع البيانات");
        return;
    }

    // Change button state
    const originalText = submitBtn.innerText;
    submitBtn.innerText = 'جاري الحفظ...';
    submitBtn.disabled = true;

    // Database Payload
    const formData = { name, phone, message };

    try {
        // Attempt to save to DB (NoSQL)
        const response = await fetch('/api/contact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            // Success
            alert("تم استلام طلبك بنجاح! سيتم التواصل معك قريباً.");
            document.querySelector('.contact-form').reset();
        } else {
            alert("حدث خطأ أثناء الإرسال، يرجى المحاولة مرة أخرى.");
        }

    } catch (error) {
        console.error('Error saving to DB:', error);
        alert("حدث خطأ في الاتصال، يرجى المحاولة لاحقاً.");
    } finally {
        submitBtn.innerText = originalText;
        submitBtn.disabled = false;
    }
}
