// huntRED® Demo Complete - JavaScript Avanzado

class HuntREDDemo {
    constructor() {
        this.usdToMxn = 17.5; // Tasa de cambio aproximada
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupScrollEffects();
        this.updatePricing();
        this.setupAnimations();
    }

    setupEventListeners() {
        // Smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Pricing calculator
        document.querySelectorAll('input, select').forEach(element => {
            element.addEventListener('change', () => this.updatePricing());
            element.addEventListener('input', () => this.updatePricing());
        });

        // Tab switching
        const tabButtons = document.querySelectorAll('[data-tab]');
        tabButtons.forEach(button => {
            button.addEventListener('click', () => this.switchTab(button));
        });

        // Form submissions
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        });
    }

    setupScrollEffects() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                }
            });
        }, observerOptions);

        document.querySelectorAll('.reveal-on-scroll').forEach(el => {
            observer.observe(el);
        });
    }

    setupAnimations() {
        // Floating elements
        const floatingElements = document.querySelectorAll('.floating-element');
        floatingElements.forEach((el, index) => {
            el.style.animationDelay = `${index * 2}s`;
        });

        // Counter animations
        this.animateCounters();
    }

    updatePricing() {
        const salaryInput = document.querySelector('input[type="number"]');
        const positionsInput = document.querySelectorAll('input[type="number"]')[1];
        
        if (!salaryInput || !positionsInput) return;

        const salary = parseFloat(salaryInput.value) || 800000;
        const positions = parseInt(positionsInput.value) || 1;
        
        // huntRED pricing (in MXN)
        const huntredAI = 95000; // Solo IA - precio más bajo
        const huntredHybrid = salary * 0.15; // 15% del salario
        const huntredHuman = salary * 0.20; // 20% del salario
        
        // Competitor pricing (converted to MXN)
        const smartrecruiters = 2388 * this.usdToMxn; // $2,388 USD
        const bullhorn = 7388 * this.usdToMxn; // $7,388 USD
        const mya = 100000 * this.usdToMxn; // $100,000 USD
        
        // Update huntRED display
        const huntredPriceElement = document.querySelector('.text-4xl.font-bold.text-red-600');
        if (huntredPriceElement) {
            huntredPriceElement.textContent = `$${huntredAI.toLocaleString()}`;
        }
        
        // Update competitor prices
        const competitorPrices = document.querySelectorAll('.text-4xl.font-bold.text-gray-600');
        if (competitorPrices.length >= 3) {
            competitorPrices[0].textContent = `$${smartrecruiters.toLocaleString()}`;
            competitorPrices[1].textContent = `$${bullhorn.toLocaleString()}`;
            competitorPrices[2].textContent = `$${mya.toLocaleString()}`;
        }

        // Update savings calculation
        this.updateSavings(huntredAI, smartrecruiters, bullhorn, mya);
    }

    updateSavings(huntredPrice, smartrecruiters, bullhorn, mya) {
        const savingsElement = document.getElementById('savings-calculation');
        if (!savingsElement) return;

        const competitors = [smartrecruiters, bullhorn, mya];
        const minCompetitor = Math.min(...competitors);
        const savings = minCompetitor - huntredPrice;
        const savingsPercentage = ((savings / minCompetitor) * 100).toFixed(1);

        savingsElement.innerHTML = `
            <div class="bg-green-50 p-4 rounded-xl border border-green-200">
                <div class="text-lg font-bold text-green-600 mb-2">
                    <i class="fas fa-piggy-bank mr-2"></i>
                    Ahorro con huntRED®
                </div>
                <div class="text-2xl font-bold text-green-600">
                    $${savings.toLocaleString()} MXN
                </div>
                <div class="text-sm text-green-600">
                    ${savingsPercentage}% menos que la competencia
                </div>
            </div>
        `;
    }

    switchTab(activeButton) {
        const tabContainer = activeButton.closest('.tab-container');
        if (!tabContainer) return;

        // Remove active class from all buttons
        tabContainer.querySelectorAll('[data-tab]').forEach(btn => {
            btn.classList.remove('bg-white', 'text-gray-900', 'shadow-lg');
            btn.classList.add('text-gray-600', 'hover:text-gray-900');
        });

        // Add active class to clicked button
        activeButton.classList.remove('text-gray-600', 'hover:text-gray-900');
        activeButton.classList.add('bg-white', 'text-gray-900', 'shadow-lg');

        // Show corresponding content
        const tabId = activeButton.getAttribute('data-tab');
        tabContainer.querySelectorAll('[data-tab-content]').forEach(content => {
            content.classList.add('hidden');
        });
        
        const activeContent = tabContainer.querySelector(`[data-tab-content="${tabId}"]`);
        if (activeContent) {
            activeContent.classList.remove('hidden');
        }
    }

    animateCounters() {
        const counters = document.querySelectorAll('[data-counter]');
        counters.forEach(counter => {
            const target = parseInt(counter.getAttribute('data-counter'));
            const duration = 2000; // 2 seconds
            const step = target / (duration / 16); // 60fps
            let current = 0;

            const timer = setInterval(() => {
                current += step;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                counter.textContent = Math.floor(current).toLocaleString();
            }, 16);
        });
    }

    handleFormSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        
        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.textContent = 'Enviando...';
        submitButton.disabled = true;

        // Simulate form submission
        setTimeout(() => {
            this.showNotification('¡Formulario enviado con éxito!', 'success');
            submitButton.textContent = originalText;
            submitButton.disabled = false;
            form.reset();
        }, 2000);
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-xl shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' : 
            type === 'error' ? 'bg-red-500 text-white' : 
            'bg-blue-500 text-white'
        }`;
        notification.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation' : 'info'}"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // API methods for future integration
    async fetchExchangeRate() {
        try {
            const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
            const data = await response.json();
            this.usdToMxn = data.rates.MXN;
            this.updatePricing();
        } catch (error) {
            console.log('Using default exchange rate');
        }
    }

    async submitDemoRequest(formData) {
        // Future integration with backend
        console.log('Demo request:', formData);
        return { success: true };
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.huntREDDemo = new HuntREDDemo();
    
    // Fetch real exchange rate
    window.huntREDDemo.fetchExchangeRate();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HuntREDDemo;
} 