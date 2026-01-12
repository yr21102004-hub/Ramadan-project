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

/* Global Audio Player Logic (Persistent State) */
document.addEventListener('DOMContentLoaded', () => {
    const audio = document.getElementById('quran-audio');
    const toggleBtn = document.getElementById('quran-toggle');
    const icon = toggleBtn ? toggleBtn.querySelector('i') : null;

    if (!audio || !toggleBtn) return;

    // Load State
    const savedTime = localStorage.getItem('quran_time');
    const isPlaying = localStorage.getItem('quran_playing') === 'true';

    if (savedTime) {
        audio.currentTime = parseFloat(savedTime);
    }

    // Attempt Autoplay if it was playing
    if (isPlaying) {
        // Modern browsers block autoplay without interaction.
        // We catch the error and default to paused state if blocked.
        const playPromise = audio.play();
        if (playPromise !== undefined) {
            playPromise.then(() => {
                updateIcon(true);
            }).catch(error => {
                console.log("Autoplay prevented:", error);
                updateIcon(false);
                // Reset state to paused to avoid sync issues
                localStorage.setItem('quran_playing', 'false');
            });
        }
    }

    // Toggle Click Event
    toggleBtn.addEventListener('click', () => {
        if (audio.paused) {
            audio.play().then(() => {
                updateIcon(true);
                localStorage.setItem('quran_playing', 'true');
            });
        } else {
            audio.pause();
            updateIcon(false);
            localStorage.setItem('quran_playing', 'false');
        }
    });

    // Save Position periodically
    audio.addEventListener('timeupdate', () => {
        localStorage.setItem('quran_time', audio.currentTime);
    });

    // Save ended state
    audio.addEventListener('ended', () => {
        localStorage.setItem('quran_playing', 'false');
        updateIcon(false);
    });

    function updateIcon(playing) {
        if (playing) {
            icon.classList.remove('fa-play');
            icon.classList.add('fa-pause');
            toggleBtn.classList.add('playing');
        } else {
            icon.classList.remove('fa-pause');
            icon.classList.add('fa-play');
            toggleBtn.classList.remove('playing');
        }
    }
});
/* Global Audio Player Logic (Persistent State & AutoPlay) */
document.addEventListener('DOMContentLoaded', () => {
    const audio = document.getElementById('quran-audio');
    const toggleBtn = document.getElementById('quran-toggle');
    const icon = toggleBtn ? toggleBtn.querySelector('i') : null;

    if (!audio || !toggleBtn) return;

    // Load State
    const savedTime = localStorage.getItem('quran_time');

    // Default to TRUE for autoplay if not set
    let isPlaying = localStorage.getItem('quran_playing');
    if (isPlaying === null) {
        isPlaying = true; // Default auto play
        localStorage.setItem('quran_playing', 'true');
    } else {
        isPlaying = isPlaying === 'true';
    }

    if (savedTime) {
        audio.currentTime = parseFloat(savedTime);
    }

    // Try to play immediately
    const startAudio = () => {
        if (localStorage.getItem('quran_playing') === 'true') {
            audio.play().then(() => {
                updateIcon(true);
            }).catch(error => {
                console.log("Autoplay blocked. Waiting for interaction.");
                updateIcon(false);
            });
        }
    };

    // First try
    startAudio();

    // Second try on any user interaction (click anywhere) logic
    const enableAudioOnInteraction = () => {
        startAudio();
        // Remove listeners once we tried
        document.removeEventListener('click', enableAudioOnInteraction);
        document.removeEventListener('keydown', enableAudioOnInteraction);
    };

    if (audio.paused && isPlaying) {
        document.addEventListener('click', enableAudioOnInteraction);
        document.addEventListener('keydown', enableAudioOnInteraction);
    }

    // Toggle Click Event
    toggleBtn.addEventListener('click', (e) => {
        // Stop the global interaction listener if user clicks the toggle directly
        document.removeEventListener('click', enableAudioOnInteraction);

        if (audio.paused) {
            audio.play().then(() => {
                updateIcon(true);
                localStorage.setItem('quran_playing', 'true');
            });
        } else {
            audio.pause();
            updateIcon(false);
            localStorage.setItem('quran_playing', 'false');
        }
    });

    // Save Position periodically
    audio.addEventListener('timeupdate', () => {
        localStorage.setItem('quran_time', audio.currentTime);
    });

    // Save ended state
    audio.addEventListener('ended', () => {
        localStorage.setItem('quran_playing', 'false');
        updateIcon(false);
    });

    function updateIcon(playing) {
        if (playing) {
            icon.classList.remove('fa-play');
            icon.classList.add('fa-pause');
            toggleBtn.classList.add('playing');
        } else {
            icon.classList.remove('fa-pause');
            icon.classList.add('fa-play');
            toggleBtn.classList.remove('playing');
        }
    }
});
