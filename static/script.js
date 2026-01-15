// Mobile Menu & Theme Toggler Logic
document.addEventListener('DOMContentLoaded', () => {
    // Mobile Menu Logic
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');

    if (hamburger && navLinks) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navLinks.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!hamburger.contains(e.target) && !navLinks.contains(e.target) && navLinks.classList.contains('active')) {
                hamburger.classList.remove('active');
                navLinks.classList.remove('active');
            }
        });

        // Close menu when clicking a link
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navLinks.classList.remove('active');
            });
        });
    }

    // Theme Toggler Logic
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const icon = themeToggle.querySelector('i');

    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        body.classList.add('light-mode');
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }

    themeToggle.addEventListener('click', () => {
        body.classList.toggle('light-mode');

        if (body.classList.contains('light-mode')) {
            localStorage.setItem('theme', 'light');
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            localStorage.setItem('theme', 'dark');
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    });
});

// Contact Form Submission (Global Function)
async function submitContactForm() {
    const nameInput = document.getElementById("name");
    const phoneInput = document.getElementById("phone");
    const messageInput = document.getElementById("message");
    const submitBtn = document.querySelector('button[type="submit"]');

    if (!nameInput || !phoneInput || !messageInput) {
        alert("يرجى ملء جميع البيانات");
        return;
    }

    const name = nameInput.value;
    const phone = phoneInput.value;
    const message = messageInput.value;
    const service = document.getElementById("service") ? document.getElementById("service").value : "general";

    // Change button state
    let originalText = "ارسال الرسالة";
    if (submitBtn) {
        originalText = submitBtn.innerText;
        submitBtn.innerText = 'جاري الحفظ...';
        submitBtn.disabled = true;
    }

    // Database Payload
    const formData = { name, phone, message, service };

    let isSuccess = false;

    try {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (!meta) throw new Error("رمز الأمان (CSRF) مفقود - يرجى تحديث الصفحة");
        const csrfToken = meta.getAttribute('content');

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
            isSuccess = true;
            // Success
            alert("تم استلام طلبك بنجاح! سيتم الرد عليك في خلال 48 ساعة.");
            // Safe Reset
            try {
                if (nameInput) nameInput.value = "";
                if (phoneInput) phoneInput.value = "";
                if (messageInput) messageInput.value = "";
            } catch (e) { console.log("Form reset minor error", e); }
        } else {
            alert("حدث خطأ أثناء الإرسال، يرجى المحاولة مرة أخرى.");
        }

    } catch (error) {
        if (!isSuccess) {
            console.error('Error saving to DB:', error);
            alert("حدث خطأ في الاتصال: " + error.message);
        }
    } finally {
        if (submitBtn) {
            submitBtn.innerText = originalText;
            submitBtn.disabled = false;
        }
    }
}

/* Chat Widget Logic */
document.addEventListener('DOMContentLoaded', () => {
    const chatWidget = document.getElementById('chat-widget');
    const chatToggle = document.getElementById('chat-toggle-btn'); // Fixed ID
    const closeChat = document.getElementById('close-chat');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-chat-btn'); // Fixed ID
    const chatMessages = document.getElementById('chat-messages');

    let chatUserId = localStorage.getItem('chat_user_id');
    if (!chatUserId) {
        chatUserId = 'user_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
        localStorage.setItem('chat_user_id', chatUserId);
    }

    if (chatToggle && chatWidget && closeChat) {
        chatToggle.addEventListener('click', () => {
            chatWidget.classList.add('active');
            chatToggle.style.display = 'none';
            if (chatInput) chatInput.focus();
        });

        closeChat.addEventListener('click', () => {
            chatWidget.classList.remove('active');
            setTimeout(() => {
                chatToggle.style.display = 'flex';
            }, 300);
        });
    }

    // Auto-resize textarea
    if (chatInput) {
        chatInput.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            if (this.value === '') {
                this.style.height = '40px';
            }
        });

        // Send on Enter (shift+enter for new line)
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    function addMessage(text, type) {
        const div = document.createElement('div');
        div.className = `message ${type}`;
        div.textContent = text;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage() {
        if (!chatInput) return;

        const text = chatInput.value.trim();
        if (!text) return;

        // Visual update
        addMessage(text, 'user');
        chatInput.value = '';
        chatInput.style.height = '40px';

        // Add loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot loading';
        loadingDiv.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({
                    message: text,
                    user_id: chatUserId
                })
            });

            const data = await response.json();

            // Remove loading
            loadingDiv.remove();

            if (data.response) {
                addMessage(data.response, 'bot');
            } else {
                addMessage('عذراً، حدث خطأ في النظام.', 'bot');
            }

        } catch (error) {
            loadingDiv.remove();
            console.error('Chat Error:', error);
            addMessage('عذراً، لا يمكن الاتصال بالخادم حالياً.', 'bot');
        }
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
});

/* Global Audio Player Logic (Persistent State & AutoPlay) */
document.addEventListener('DOMContentLoaded', () => {
    const audio = document.getElementById('quran-audio');
    const toggleBtn = document.getElementById('audio-toggle');
    const icon = toggleBtn ? toggleBtn.querySelector('i') : null;

    if (!audio || !toggleBtn) return;

    // Check localStorage for playing state
    // Default to 'true' if not set (AutoPlay)
    let isPlaying = localStorage.getItem('quran_playing');

    // Attempt Autoplay
    if (isPlaying === null || isPlaying === 'true') {
        const playPromise = audio.play();
        if (playPromise !== undefined) {
            playPromise.then(() => {
                isPlaying = 'true';
                localStorage.setItem('quran_playing', 'true');
                updateIcon(true);
            }).catch(error => {
                // Auto-play was prevented
                console.log("Autoplay prevented:", error);
                isPlaying = 'false';
                localStorage.setItem('quran_playing', 'false');
                updateIcon(false);
            });
        }
    } else {
        updateIcon(false);
    }

    toggleBtn.addEventListener('click', () => {
        if (audio.paused) {
            audio.play().then(() => {
                localStorage.setItem('quran_playing', 'true');
                updateIcon(true);
            }).catch(e => console.error("Play error:", e));
        } else {
            audio.pause();
            localStorage.setItem('quran_playing', 'false');
            updateIcon(false);
        }
    });

    function updateIcon(playing) {
        if (!icon) return;
        if (playing) {
            icon.classList.remove('fa-volume-mute');
            icon.classList.add('fa-volume-up');
            toggleBtn.classList.add('playing'); // Optional pulse effect
        } else {
            icon.classList.remove('fa-volume-up');
            icon.classList.add('fa-volume-mute');
            toggleBtn.classList.remove('playing');
        }
    }
});
