// AI Engine Visualization Component
class AIEngineVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.skillsCount = 43000;
        this.currentModel = 'gpt-4';
        this.models = {
            'gpt-4': { name: 'GPT-4', provider: 'OpenAI', color: '#10A37F' },
            'claude-3': { name: 'Claude 3', provider: 'Anthropic', color: '#90C6F7' },
            'gemini-pro': { name: 'Gemini Pro', provider: 'Google', color: '#FF6D00' },
            'grok': { name: 'Grok', provider: 'xAI', color: '#000000' },
            'llama-3': { name: 'Llama 3', provider: 'Meta', color: '#FF6B35' }
        };
        this.init();
    }

    init() {
        this.createDOM();
        this.setupEventListeners();
        this.animateSkillsCounter();
        this.startParticleAnimation();
    }

    createDOM() {
        // Main container
        this.container.innerHTML = `
            <div class="relative bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 overflow-hidden">
                <!-- Background elements -->
                <div class="absolute inset-0 opacity-20" id="particles-ai"></div>
                
                <!-- Header -->
                <div class="relative z-10">
                    <h2 class="text-4xl font-bold text-white mb-2">Motor de IA Avanzado</h2>
                    <p class="text-gray-300 mb-8 max-w-3xl">
                        Potenciado por una red neuronal que analiza <span class="font-bold text-white" id="skills-counter">0</span>+ habilidades 
                        y se integra con los modelos de lenguaje más avanzados del mercado.
                    </p>
                </div>

                <!-- Model Selector -->
                <div class="relative z-10 mb-8">
                    <div class="flex flex-wrap gap-3 mb-6">
                        ${Object.entries(this.models).map(([id, model]) => `
                            <button 
                                class="px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${this.currentModel === id ? 'bg-white text-gray-900' : 'bg-gray-800 text-white hover:bg-gray-700'}"
                                data-model="${id}"
                            >
                                ${model.name}
                            </button>
                        `).join('')}
                    </div>
                    <div id="model-details" class="bg-gray-800 bg-opacity-50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
                        <!-- Dynamic content will be inserted here -->
                    </div>
                </div>

                <!-- Capabilities Grid -->
                <div class="grid md:grid-cols-3 gap-6 relative z-10">
                    ${this.createCapabilityCard(
                        'NLP Avanzado', 
                        'Procesamiento de lenguaje natural con soporte multilingüe y análisis de sentimientos.',
                        '🧠',
                        'from-purple-500 to-indigo-600'
                    )}
                    ${this.createCapabilityCard(
                        'Análisis Predictivo', 
                        'Modelos predictivos para evaluar el éxito de contratación y desempeño futuro.',
                        '📊',
                        'from-blue-500 to-cyan-600'
                    )}
                    ${this.createCapabilityCard(
                        'Matchmaking Inteligente', 
                        'Algoritmos avanzados que conectan candidatos ideales con oportunidades perfectas.',
                        '✨',
                        'from-pink-500 to-rose-600'
                    )}
                </div>
            </div>
        `;

        this.updateModelDetails(this.currentModel);
    }

    createCapabilityCard(title, description, icon, gradient) {
        return `
            <div class="bg-gray-800 bg-opacity-50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 hover:border-gray-600 transition-all duration-300 hover:transform hover:-translate-y-1">
                <div class="w-16 h-16 rounded-full bg-gradient-to-r ${gradient} flex items-center justify-center text-2xl mb-4">
                    ${icon}
                </div>
                <h3 class="text-xl font-bold text-white mb-2">${title}</h3>
                <p class="text-gray-300">${description}</p>
            </div>
        `;
    }

    updateModelDetails(modelId) {
        const model = this.models[modelId];
        if (!model) return;

        const detailsContainer = this.container.querySelector('#model-details');
        detailsContainer.innerHTML = `
            <div class="flex flex-col md:flex-row md:items-center justify-between">
                <div>
                    <div class="flex items-center mb-2">
                        <span class="inline-block w-3 h-3 rounded-full mr-2" style="background-color: ${model.color}"></span>
                        <span class="text-sm font-medium text-gray-300">${model.provider}</span>
                    </div>
                    <h3 class="text-2xl font-bold text-white">${model.name}</h3>
                    <p class="text-gray-400 mt-1">Modelo de lenguaje avanzado para análisis de talento</p>
                </div>
                <div class="mt-4 md:mt-0">
                    <div class="flex items-center space-x-2">
                        <span class="px-3 py-1 bg-gray-700 bg-opacity-50 rounded-full text-sm text-gray-200">Multilingüe</span>
                        <span class="px-3 py-1 bg-gray-700 bg-opacity-50 rounded-full text-sm text-gray-200">Contexto amplio</span>
                        <span class="px-3 py-1 bg-gray-700 bg-opacity-50 rounded-full text-sm text-gray-200">Razonamiento avanzado</span>
                    </div>
                </div>
            </div>
        `;
    }

    setupEventListeners() {
        // Model selection
        this.container.querySelectorAll('[data-model]').forEach(button => {
            button.addEventListener('click', (e) => {
                const modelId = e.currentTarget.getAttribute('data-model');
                this.currentModel = modelId;
                this.updateModelDetails(modelId);
                
                // Update active state
                this.container.querySelectorAll('[data-model]').forEach(btn => {
                    btn.classList.remove('bg-white', 'text-gray-900');
                    btn.classList.add('bg-gray-800', 'text-white', 'hover:bg-gray-700');
                });
                e.currentTarget.classList.remove('bg-gray-800', 'text-white', 'hover:bg-gray-700');
                e.currentTarget.classList.add('bg-white', 'text-gray-900');
            });
        });
    }

    animateSkillsCounter() {
        const counter = this.container.querySelector('#skills-counter');
        const duration = 3000; // 3 seconds
        const start = 0;
        const end = this.skillsCount;
        const range = end - start;
        const minDuration = 2000;
        let startTime = null;

        const updateCounter = (timestamp) => {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);
            
            // Ease out function for smooth deceleration
            const easeOutQuad = t => t * (2 - t);
            const current = Math.floor(start + (range * easeOutQuad(progress)));
            
            counter.textContent = current.toLocaleString();
            
            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            } else {
                // Ensure we show the final number
                counter.textContent = end.toLocaleString();
            }
        };

        requestAnimationFrame(updateCounter);
    }

    startParticleAnimation() {
        const canvas = document.createElement('canvas');
        const container = this.container.querySelector('#particles-ai');
        if (!container) return;
        
        container.appendChild(canvas);
        const ctx = canvas.getContext('2d');
        
        // Set canvas size
        const resizeCanvas = () => {
            const rect = container.getBoundingClientRect();
            canvas.width = rect.width;
            canvas.height = rect.height;
        };
        
        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();
        
        // Particle system
        const particles = [];
        const particleCount = Math.floor((canvas.width * canvas.height) / 10000); // Density based on size
        
        // Create particles
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                size: Math.random() * 2 + 1,
                speedX: Math.random() * 1 - 0.5,
                speedY: Math.random() * 1 - 0.5,
                color: `rgba(255, 255, 255, ${Math.random() * 0.1})`
            });
        }
        
        // Animation loop
        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Update and draw particles
            particles.forEach(particle => {
                // Update position
                particle.x += particle.speedX;
                particle.y += particle.speedY;
                
                // Bounce off edges
                if (particle.x < 0 || particle.x > canvas.width) particle.speedX *= -1;
                if (particle.y < 0 || particle.y > canvas.height) particle.speedY *= -1;
                
                // Draw particle
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                ctx.fillStyle = particle.color;
                ctx.fill();
                
                // Draw connections
                particles.forEach(otherParticle => {
                    const dx = particle.x - otherParticle.x;
                    const dy = particle.y - otherParticle.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    if (distance < 100) {
                        ctx.beginPath();
                        ctx.strokeStyle = `rgba(255, 255, 255, ${0.1 - (distance / 1000)})`;
                        ctx.lineWidth = 0.5;
                        ctx.moveTo(particle.x, particle.y);
                        ctx.lineTo(otherParticle.x, otherParticle.y);
                        ctx.stroke();
                    }
                });
            });
            
            requestAnimationFrame(animate);
        };
        
        animate();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('ai-engine-section');
    if (container) {
        new AIEngineVisualizer('ai-engine-section');
    }
});
