// Efectos visuales mejorados para huntRED con Tailwind

// Efecto de partículas mejorado
class ParticleEffect {
    constructor() {
        this.canvas = document.getElementById('particlesCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.mouse = { x: 0, y: 0 };
        this.init();
    }

    init() {
        this.resize();
        this.createParticles();
        this.animate();
        this.addEventListeners();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    createParticles() {
        const numberOfParticles = Math.min(window.innerWidth * window.innerHeight / 10000, 100);
        for (let i = 0; i < numberOfParticles; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                size: Math.random() * 3 + 1,
                speedX: Math.random() * 2 - 1,
                speedY: Math.random() * 2 - 1,
                opacity: Math.random() * 0.5 + 0.1,
                color: `rgba(0, 188, 242, ${Math.random() * 0.5 + 0.1})`
            });
        }
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.particles.forEach(particle => {
            particle.x += particle.speedX;
            particle.y += particle.speedY;

            if (particle.x < 0 || particle.x > this.canvas.width) particle.speedX *= -1;
            if (particle.y < 0 || particle.y > this.canvas.height) particle.speedY *= -1;

            const dx = this.mouse.x - particle.x;
            const dy = this.mouse.y - particle.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < 100) {
                const angle = Math.atan2(dy, dx);
                const force = (100 - distance) / 100;
                particle.speedX -= Math.cos(angle) * force * 0.2;
                particle.speedY -= Math.sin(angle) * force * 0.2;
            }

            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fillStyle = particle.color;
            this.ctx.fill();

            this.particles.forEach(otherParticle => {
                const dx = particle.x - otherParticle.x;
                const dy = particle.y - otherParticle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 100) {
                    this.ctx.beginPath();
                    this.ctx.strokeStyle = `rgba(0, 188, 242, ${0.1 * (1 - distance / 100)})`;
                    this.ctx.lineWidth = 0.5;
                    this.ctx.moveTo(particle.x, particle.y);
                    this.ctx.lineTo(otherParticle.x, otherParticle.y);
                    this.ctx.stroke();
                }
            });
        });

        requestAnimationFrame(() => this.animate());
    }

    addEventListeners() {
        window.addEventListener('resize', () => this.resize());
        window.addEventListener('mousemove', (e) => {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
        });
    }
}

// Efecto de revelación al scroll mejorado
class ScrollReveal {
    constructor() {
        this.elements = document.querySelectorAll('.scroll-reveal');
        this.threshold = 0.1;
        this.init();
    }

    init() {
        this.checkVisibility();
        window.addEventListener('scroll', () => this.checkVisibility());
        window.addEventListener('resize', () => this.checkVisibility());
    }

    checkVisibility() {
        this.elements.forEach(element => {
            const rect = element.getBoundingClientRect();
            const windowHeight = window.innerHeight;
            
            const isVisible = (
                rect.top <= windowHeight * (1 - this.threshold) &&
                rect.bottom >= windowHeight * this.threshold
            );

            if (isVisible) {
                element.classList.add('opacity-100', 'translate-y-0');
                element.classList.remove('opacity-0', 'translate-y-8');
            }
        });
    }
}

// Cursor personalizado mejorado
class CustomCursor {
    constructor() {
        this.cursor = document.createElement('div');
        this.cursor.className = 'custom-cursor';
        document.body.appendChild(this.cursor);
        this.init();
    }

    init() {
        this.addEventListeners();
        this.hideDefaultCursor();
    }

    addEventListeners() {
        document.addEventListener('mousemove', (e) => {
            this.cursor.style.left = e.clientX + 'px';
            this.cursor.style.top = e.clientY + 'px';
        });

        document.addEventListener('mousedown', () => {
            this.cursor.classList.add('active');
        });

        document.addEventListener('mouseup', () => {
            this.cursor.classList.remove('active');
        });

        // Efectos en elementos interactivos
        const interactiveElements = document.querySelectorAll('a, button, .business-card, .division-card, .config-item');
        interactiveElements.forEach(element => {
            element.addEventListener('mouseenter', () => {
                this.cursor.classList.add('active');
                element.classList.add('cursor-hover');
            });

            element.addEventListener('mouseleave', () => {
                this.cursor.classList.remove('active');
                element.classList.remove('cursor-hover');
            });
        });
    }

    hideDefaultCursor() {
        document.body.style.cursor = 'none';
        const style = document.createElement('style');
        style.textContent = `
            * {
                cursor: none !important;
            }
            .custom-cursor {
                pointer-events: none;
            }
        `;
        document.head.appendChild(style);
    }
}

// Efecto de hover en tarjetas mejorado
class CardHoverEffect {
    constructor() {
        this.cards = document.querySelectorAll('.group');
        this.init();
    }

    init() {
        this.cards.forEach(card => {
            card.addEventListener('mousemove', (e) => this.handleMouseMove(e, card));
            card.addEventListener('mouseleave', (e) => this.handleMouseLeave(e, card));
        });
    }

    handleMouseMove(e, card) {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = (y - centerY) / 20;
        const rotateY = (centerX - x) / 20;

        card.style.transform = `
            perspective(1000px)
            rotateX(${rotateX}deg)
            rotateY(${rotateY}deg)
            scale3d(1.02, 1.02, 1.02)
        `;

        const glare = card.querySelector('.glare') || this.createGlare(card);
        const glareX = (x / rect.width) * 100;
        const glareY = (y / rect.height) * 100;
        glare.style.background = `radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255,255,255,0.1) 0%, transparent 50%)`;
    }

    handleMouseLeave(e, card) {
        card.style.transform = '';
        const glare = card.querySelector('.glare');
        if (glare) glare.remove();
    }

    createGlare(card) {
        const glare = document.createElement('div');
        glare.className = 'glare absolute inset-0 pointer-events-none';
        card.appendChild(glare);
        return glare;
    }
}

// Inicialización de efectos
document.addEventListener('DOMContentLoaded', () => {
    new ParticleEffect();
    new ScrollReveal();
    new CustomCursor();
    new CardHoverEffect();
}); 