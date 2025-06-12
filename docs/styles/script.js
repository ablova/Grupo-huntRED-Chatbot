
// Theme Toggle Functionality
function initTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeToggleMobile = document.getElementById('theme-toggle-mobile');
    const html = document.documentElement;
    
    // Check for saved theme preference or default to 'light'
    const savedTheme = localStorage.getItem('theme') || 'light';
    html.classList.toggle('dark', savedTheme === 'dark');
    
    function toggleTheme() {
        const isDark = html.classList.contains('dark');
        html.classList.toggle('dark', !isDark);
        localStorage.setItem('theme', !isDark ? 'dark' : 'light');
        updateThemeIcons();
    }
    
    function updateThemeIcons() {
        const isDark = html.classList.contains('dark');
        const sunIcon = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707"></path>
        </svg>`;
        
        const moonIcon = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path>
        </svg>`;
        
        if (themeToggle) {
            themeToggle.innerHTML = isDark ? sunIcon : moonIcon;
        }
        if (themeToggleMobile) {
            themeToggleMobile.innerHTML = isDark ? sunIcon : moonIcon;
        }
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    if (themeToggleMobile) {
        themeToggleMobile.addEventListener('click', toggleTheme);
    }
    
    // Initialize icons
    updateThemeIcons();
}

// Mobile Menu Functionality
function initMobileMenu() {
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
        
        // Close mobile menu when clicking on links
        const mobileLinks = mobileMenu.querySelectorAll('a');
        mobileLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileMenu.classList.add('hidden');
            });
        });
    }
}

// Smooth Scrolling for Navigation Links
function initSmoothScrolling() {
    const navLinks = document.querySelectorAll('a[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const headerHeight = 80; // Account for fixed header
                const targetPosition = targetElement.offsetTop - headerHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Intersection Observer for Animations
function initAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in-up');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    animatedElements.forEach(el => observer.observe(el));
}

// Header Background on Scroll
function initHeaderScroll() {
    const header = document.querySelector('header');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('backdrop-blur-xl');
        } else {
            header.classList.remove('backdrop-blur-xl');
        }
    });
}

// CTA Button Interactions
function initCTAButtons() {
    const ctaButtons = document.querySelectorAll('a[href*="#"], button');
    
    ctaButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const buttonText = button.textContent.trim();
            
            // Verificar si es un botón de demo o agendamiento
            if (buttonText.match(/(Agendar|Demo|Solicitar Demo|Agendar Cita)/i)) {
                e.preventDefault();
                window.open('https://calendar.app.google/63XsoSPhKfntRns19', '_blank');
                return false;
            }
            
            // Manejar otros tipos de botones si es necesario
            if (buttonText.includes('Cotización')) {
                console.log('Opening quote request form...');
                // Aquí podrías agregar la lógica para el formulario de cotización
            }
        });
    });
}

// Form Interactions
function initForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            console.log('Form submitted:', new FormData(form));
            // Handle form submission
        });
    });
}

// Keyboard Navigation
function initKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
        // ESC key closes mobile menu
        if (e.key === 'Escape') {
            const mobileMenu = document.getElementById('mobile-menu');
            if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                mobileMenu.classList.add('hidden');
            }
        }
    });
}

// Initialize all functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initMobileMenu();
    initSmoothScrolling();
    initAnimations();
    initHeaderScroll();
    initCTAButtons();
    initForms();
    initKeyboardNavigation();
    
    console.log('TechAI website initialized successfully!');
});

// Performance monitoring
window.addEventListener('load', () => {
    console.log('Page loaded in:', performance.now(), 'ms');
});