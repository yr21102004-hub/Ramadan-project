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


    // Theme Toggle
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = themeToggle.querySelector('i');

    function updateThemeIcon(isLight) {
        if (isLight) {
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
        } else {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        }
    }

    // Check saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-mode');
        updateThemeIcon(true);
    } else {
        updateThemeIcon(false);
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
            const isLight = document.body.classList.contains('light-mode');

            updateThemeIcon(isLight);
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
        });
    }

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
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        // Attempt to save to DB (NoSQL)
        const response = await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            // Success
            alert("تم استلام طلبك بنجاح! سيتم الرد عليك في خلال 48 ساعة.");
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

/* Chat Widget Logic */
document.addEventListener('DOMContentLoaded', () => {
    const chatWidget = document.getElementById('chat-widget');
    const chatToggle = document.getElementById('chat-toggle-btn');
    const closeChat = document.getElementById('close-chat');
    const sendBtn = document.getElementById('send-chat-btn');
    const chatInput = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');

    if (!chatWidget || !chatToggle) return;

    // Toggle Chat
    function toggleChat() {
        chatWidget.classList.toggle('active');
        if (chatWidget.classList.contains('active')) {
            setTimeout(() => chatInput.focus(), 100);
        }
    }

    chatToggle.addEventListener('click', toggleChat);
    closeChat.addEventListener('click', toggleChat);

    // Send Message
    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // Add User Message
        appendMessage(text, 'user-message');
        chatInput.value = '';

        // Add Loading Indicator
        const loadingId = 'loading-' + Date.now();
        appendMessage('<i class="fas fa-ellipsis-h fa-fade"></i>', 'bot-message', loadingId);

        try {
            // Persistent ID for Chat Grouping
            let chatUserId = localStorage.getItem('chat_user_id');
            if (!chatUserId || chatUserId === 'anonymous') {
                chatUserId = 'user_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
                localStorage.setItem('chat_user_id', chatUserId);
            }

            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    message: text,
                    user_id: chatUserId
                })
            });

            const data = await response.json();

            // Remove Loading
            removeMessage(loadingId);

            // Add Bot Message
            appendMessage(data.response, 'bot-message');

        } catch (error) {
            console.error(error);
            removeMessage(loadingId);
            appendMessage('عذراً، حدث خطأ في الاتصال.', 'bot-message');
        }
    }

    // Helper: Append Message
    function appendMessage(text, className, id = null) {
        const div = document.createElement('div');
        div.className = `message ${className}`;
        div.innerHTML = text; // Allow HTML
        if (id) div.id = id;

        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return id;
    }

    function removeMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }
});
