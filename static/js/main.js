
// TechAI Interactive Features for Django

class TechAIApp {
    constructor() {
      this.init();
    }
  
    init() {
      this.setupThemeToggle();
      this.setupCapabilityCards();
      this.setupMLPipeline();
      this.setupFloatingParticles();
      this.setupScrollAnimations();
    }
  
    setupThemeToggle() {
      const toggleButton = document.querySelector('[data-theme-toggle]');
      if (!toggleButton) return;
  
      toggleButton.addEventListener('click', () => {
        document.documentElement.classList.toggle('dark');
        const isDark = document.documentElement.classList.contains('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
      });
  
      // Load saved theme
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
      }
    }
  
    setupCapabilityCards() {
      const cards = document.querySelectorAll('.llm-capability-card');
      cards.forEach(card => {
        card.addEventListener('click', () => {
          cards.forEach(c => c.classList.remove('active'));
          card.classList.add('active');
        });
      });
    }
  
    setupMLPipeline() {
      const startButton = document.querySelector('[data-pipeline-start]');
      const resetButton = document.querySelector('[data-pipeline-reset]');
      
      if (startButton) {
        startButton.addEventListener('click', () => this.runPipeline());
      }
      
      if (resetButton) {
        resetButton.addEventListener('click', () => this.resetPipeline());
      }
    }
  
    runPipeline() {
      const steps = document.querySelectorAll('.pipeline-step');
      const container = document.querySelector('.ml-pipeline-container');
      
      if (container) {
        container.classList.add('pipeline-running');
      }
  
      steps.forEach((step, index) => {
        setTimeout(() => {
          step.classList.add('active');
          
          setTimeout(() => {
            step.classList.remove('active');
            step.classList.add('completed');
          }, 2000);
        }, index * 1000);
      });
    }
  
    resetPipeline() {
      const steps = document.querySelectorAll('.pipeline-step');
      const container = document.querySelector('.ml-pipeline-container');
      
      if (container) {
        container.classList.remove('pipeline-running');
      }
  
      steps.forEach(step => {
        step.classList.remove('active', 'completed');
      });
    }
  
    setupFloatingParticles() {
      const containers = document.querySelectorAll('[data-particles]');
      
      containers.forEach(container => {
        for (let i = 0; i < 20; i++) {
          const particle = document.createElement('div');
          particle.className = 'neural-particle';
          particle.style.left = Math.random() * 100 + '%';
          particle.style.top = Math.random() * 100 + '%';
          particle.style.animationDelay = Math.random() * 3 + 's';
          container.appendChild(particle);
        }
      });
    }
  
    setupScrollAnimations() {
      const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
      };
  
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
          }
        });
      }, observerOptions);
  
      // Observe elements with animation classes
      document.querySelectorAll('.animate-fade-in-up, .animate-slide-in-left, .animate-slide-in-right').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        observer.observe(el);
      });
    }
  }
  
  // Initialize when DOM is loaded
  document.addEventListener('DOMContentLoaded', () => {
    new TechAIApp();
  });
  
  // For Django - expose globally if needed
  window.TechAIApp = TechAIApp;