// ============================================
// NOVA BRIEF - Main JavaScript
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    loadStatistics();
    setupEventListeners();
});

// Initialize app
function initializeApp() {
    console.log('Nova Brief initialized');
    setupSmoothScroll();
    setupMobileMenu();
}

// Setup smooth scroll for navigation links
function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && document.querySelector(href)) {
                e.preventDefault();
                const element = document.querySelector(href);
                element.scrollIntoView({ behavior: 'smooth' });
                closeMobileMenu();
            }
        });
    });
}

// Setup mobile menu toggle
function setupMobileMenu() {
    const menuToggle = document.getElementById('menuToggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            const navLinks = document.querySelector('.nav-links');
            navLinks.classList.toggle('active');
        });
    }
}

// Close mobile menu
function closeMobileMenu() {
    const navLinks = document.querySelector('.nav-links');
    if (navLinks) {
        navLinks.classList.remove('active');
    }
}

// Scroll to section
function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

// Load statistics from API
async function loadStatistics() {
    try {
        const response = await fetch('/api/statistics');
        if (!response.ok) throw new Error('Failed to load statistics');
        
        const data = await response.json();
        
        // Update subscriber count
        const subscriberElement = document.getElementById('subscriberCount');
        if (subscriberElement && data.total_users) {
            animateCounter(subscriberElement, data.total_users);
        }
        
        // Update article count
        const articleElement = document.getElementById('articleCount');
        if (articleElement && data.total_articles) {
            animateCounter(articleElement, data.total_articles);
        }
    } catch (error) {
        console.log('Could not load statistics:', error);
    }
}

// Animate counter
function animateCounter(element, target) {
    const current = parseInt(element.textContent) || 0;
    const increment = Math.ceil((target - current) / 20);
    let count = current;
    
    const interval = setInterval(() => {
        count += increment;
        if (count >= target) {
            count = target;
            clearInterval(interval);
        }
        element.textContent = count.toLocaleString();
    }, 30);
}

// Handle subscription form
async function handleSubscribe(event) {
    event.preventDefault();
    
    const name = document.getElementById('subName').value.trim();
    const email = document.getElementById('subEmail').value.trim();
    const form = event.target;
    const messageBox = document.getElementById('subscribeMessage');
    const submitBtn = form.querySelector('.btn-submit');
    
    // Disable button and show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Subscribing...';
    
    try {
        const response = await fetch('/api/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, email })
        });
        
        const data = await response.json();
        messageBox.style.display = 'block';
        
        if (response.ok && data.status !== 'error') {
            messageBox.className = 'message-box success';
            messageBox.innerHTML = '<i class="fas fa-check-circle"></i> ' + 
                (data.already_registered 
                    ? 'You\'re already subscribed! Check your inbox for our daily briefings.'
                    : 'Welcome! Check your email for a welcome message. First briefing arrives tomorrow at 8 AM!');
            form.reset();
            
            // Clear message after 5 seconds
            setTimeout(() => {
                messageBox.style.display = 'none';
            }, 5000);
        } else {
            messageBox.className = 'message-box error';
            messageBox.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + 
                (data.message || 'Something went wrong. Please try again.');
        }
    } catch (error) {
        messageBox.className = 'message-box error';
        messageBox.innerHTML = '<i class="fas fa-exclamation-circle"></i> An error occurred. Please try again later.';
        messageBox.style.display = 'block';
        console.error('Subscription error:', error);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-check"></i> Subscribe Now';
    }
}

// Handle contact form
async function handleContactForm(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    
    // Disable button and show loading state
    submitBtn.disabled = true;
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    
    try {
        const response = await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: form.querySelector('input[type="text"]').value,
                email: form.querySelector('input[type="email"]').value,
                subject: form.querySelector('select').value,
                message: form.querySelector('textarea').value
            })
        });
        
        if (response.ok) {
            showNotification('success', 'Message sent successfully! We\'ll get back to you soon.');
            form.reset();
        } else {
            showNotification('error', 'Failed to send message. Please try again.');
        }
    } catch (error) {
        showNotification('error', 'An error occurred. Please try again later.');
        console.error('Contact form error:', error);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// Show notification
function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        ${message}
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

// Toggle FAQ items
function toggleFAQ(button) {
    const item = button.closest('.faq-item');
    const isOpen = item.classList.contains('open');
    
    // Close all other FAQs
    document.querySelectorAll('.faq-item').forEach(faqItem => {
        faqItem.classList.remove('open');
    });
    
    // Toggle current FAQ
    if (!isOpen) {
        item.classList.add('open');
    }
}

// Setup event listeners
function setupEventListeners() {
    // Newsletter signup on arrow
    const subscribeBtn = document.querySelector('[onclick="scrollToSection(\'subscribe\')"]');
    if (subscribeBtn) {
        subscribeBtn.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                scrollToSection('subscribe');
            }
        });
    }
}

// Add notification styles dynamically
if (!document.querySelector('style[data-notifications]')) {
    const style = document.createElement('style');
    style.setAttribute('data-notifications', 'true');
    style.textContent = `
        .notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 600;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
            max-width: 400px;
        }

        .notification.show {
            opacity: 1;
        }

        .notification-success {
            background: rgba(52, 211, 153, 0.9);
            color: white;
            border: 1px solid rgba(52, 211, 153, 1);
        }

        .notification-error {
            background: rgba(248, 113, 113, 0.9);
            color: white;
            border: 1px solid rgba(248, 113, 113, 1);
        }

        .notification i {
            font-size: 1.25rem;
        }

        @media (max-width: 480px) {
            .notification {
                bottom: 10px;
                right: 10px;
                left: 10px;
                max-width: none;
            }
        }
    `;
    document.head.appendChild(style);
}

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
        }
    });
}, observerOptions);

document.querySelectorAll('.feature-card, .faq-item').forEach(el => {
    observer.observe(el);
});

// Add animation keyframes
if (!document.querySelector('style[data-animations]')) {
    const style = document.createElement('style');
    style.setAttribute('data-animations', 'true');
    style.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);
}

console.log('Nova Brief scripts loaded successfully');
