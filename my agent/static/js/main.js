// ============================================
// NOVA BRIEF - Main JavaScript
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    setupSmoothScroll();
    setupMobileMenu();
    setupIntersectionObserver();
    
    // Load initial stats if on index
    if (document.getElementById('heroSubscribers')) {
        loadStatistics();
    }
});

// Smooth scroll logic
function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({ behavior: 'smooth' });
                // Close mobile menu if open
                const mobileMenu = document.getElementById('mobileMenu');
                if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                    mobileMenu.classList.add('hidden');
                }
            }
        });
    });
}

// Mobile Menu
function setupMobileMenu() {
    const btn = document.getElementById('mobileMenuBtn');
    const menu = document.getElementById('mobileMenu');
    if (btn && menu) {
        btn.addEventListener('click', () => {
            menu.classList.toggle('hidden');
        });
    }
}

// Scroll animation observer
function setupIntersectionObserver() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('opacity-100', 'translate-y-0');
                entry.target.classList.remove('opacity-0', 'translate-y-4');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    // Apply to feature cards and other elements
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        el.classList.add('opacity-0', 'translate-y-4', 'transition', 'duration-700', 'ease-out');
        observer.observe(el);
    });
}

// Stats Animation
async function loadStatistics() {
    try {
        const response = await fetch('/api/statistics');
        if (!response.ok) return;
        const data = await response.json();
        
        animateCounter('heroSubscribers', data.active_users || 0);
        animateCounter('heroArticles', data.total_articles || 0);
    } catch (e) {
        console.error('Stats load failed', e);
    }
}

function animateCounter(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    
    const duration = 2000;
    const steps = 60;
    const stepTime = duration / steps;
    const increment = Math.max(1, Math.ceil(target / steps));
    let current = 0;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        el.textContent = current.toLocaleString();
    }, stepTime);
}

// Notification system
function showNotification(message, isError = false) {
    const div = document.createElement('div');
    div.className = `fixed bottom-4 right-4 z-50 px-6 py-3 rounded-xl shadow-2xl text-sm font-bold transition-all duration-300 transform translate-y-20 opacity-0 flex items-center gap-2 ${isError ? 'bg-red-500 text-white' : 'bg-emerald-500 text-white'}`;
    div.innerHTML = `<i class="fas fa-${isError ? 'exclamation-circle' : 'check-circle'}"></i> ${message}`;
    
    document.body.appendChild(div);
    
    // Animate in
    setTimeout(() => {
        div.classList.remove('translate-y-20', 'opacity-0');
    }, 10);
    
    // Animate out
    setTimeout(() => {
        div.classList.add('translate-y-20', 'opacity-0');
        setTimeout(() => div.remove(), 300);
    }, 4000);
}
