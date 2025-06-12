// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize counters when they come into view
    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                if (entry.target.classList.contains('counter')) {
                    animateCounter(entry.target);
                }
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe all counter elements
    document.querySelectorAll('.counter').forEach(counter => {
        observer.observe(counter);
    });

    // Animate counter function
    function animateCounter(counterElement) {
        const target = parseInt(counterElement.getAttribute('data-target'));
        const duration = 2000; // Animation duration in ms
        const frameDuration = 1000 / 60; // 60fps
        const totalFrames = Math.round(duration / frameDuration);
        const easeOutQuad = t => t * (2 - t);
        
        let frame = 0;
        const countTo = target;
        
        // If counter already has a value (from a previous animation), start from there
        const startValue = parseInt(counterElement.innerText.replace(/[^0-9]/g, '')) || 0;
        
        const counter = setInterval(() => {
            frame++;
            
            // Calculate progress (0 to 1)
            const progress = Math.min(frame / totalFrames, 1);
            
            // Apply easing
            const easeProgress = easeOutQuad(progress);
            
            // Calculate current value
            const currentValue = Math.round(startValue + (countTo - startValue) * easeProgress);
            
            // Update the display
            if (counterElement.textContent.includes('%')) {
                counterElement.textContent = currentValue + '%';
            } else if (counterElement.textContent.includes('+')) {
                counterElement.textContent = currentValue.toLocaleString() + '+';
            } else {
                counterElement.textContent = currentValue.toLocaleString();
            }
            
            // Stop the animation
            if (progress === 1) {
                clearInterval(counter);
            }
        }, frameDuration);
    }

    // Add smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Add animation on scroll for elements with 'animate-on-scroll' class
    const animateOnScroll = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fadeInUp');
                animateOnScroll.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });

    // Observe all elements with animate-on-scroll class
    document.querySelectorAll('.animate-on-scroll').forEach(element => {
        animateOnScroll.observe(element);
    });

    // Initialize tooltips if needed
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (typeof bootstrap !== 'undefined') {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

// Theme switcher functionality
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    // Update the theme
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update the button icon
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        themeIcon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Check for saved user preference, if any, on page load
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 
                      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Update the theme toggle button icon
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        themeIcon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Initialize theme when the page loads
initializeTheme();
