// Theme Management
let currentTheme = localStorage.getItem('theme') || 'light';

function setTheme(theme) {
    currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    // Update theme toggle button
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
}

function toggleTheme() {
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

// Initialize theme
document.addEventListener('DOMContentLoaded', () => {
    setTheme(currentTheme);
    
    // Check system preference if no theme is set
    if (!localStorage.getItem('theme')) {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDark ? 'dark' : 'light');
    }
});

// Mobile Menu
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobileMenu');
    mobileMenu.classList.toggle('active');
}

// Close mobile menu when clicking on links
document.addEventListener('DOMContentLoaded', () => {
    const mobileLinks = document.querySelectorAll('.mobile-nav-link');
    mobileLinks.forEach(link => {
        link.addEventListener('click', () => {
            const mobileMenu = document.getElementById('mobileMenu');
            mobileMenu.classList.remove('active');
        });
    });
});

// Technology Section
let activeTechTab = 0;
const technologies = [
    {
        title: "Natural Language Processing",
        description: "Procesamiento avanzado de lenguaje natural con modelos transformer de última generación",
        features: ["Análisis de sentimientos", "Generación de texto", "Traducción automática", "Chatbots conversacionales"],
        image: "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80"
    },
    {
        title: "Computer Vision",
        description: "Reconocimiento y análisis de imágenes con precisión excepcional mediante deep learning",
        features: ["Detección de objetos", "Reconocimiento facial", "OCR avanzado", "Análisis médico"],
        image: "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80"
    },
    {
        title: "Predictive Analytics",
        description: "Algoritmos de machine learning para predicción y optimización de procesos empresariales",
        features: ["Forecasting", "Detección de anomalías", "Optimización", "Business Intelligence"],
        image: "https://images.unsplash.com/photo-1498050108023-c5249f4df085?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80"
    }
];

function switchTech(index) {
    activeTechTab = index;
    
    // Update tab buttons
    const tabs = document.querySelectorAll('.tech-tab');
    tabs.forEach((tab, i) => {
        if (i === index) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
    
    // Update content
    const tech = technologies[index];
    document.querySelector('.tech-title').textContent = tech.title;
    document.querySelector('.tech-description').textContent = tech.description;
    document.querySelector('.tech-image img').src = tech.image;
    
    // Update features
    const features = document.querySelectorAll('.feature span');
    features.forEach((feature, i) => {
        if (tech.features[i]) {
            feature.textContent = tech.features[i];
        }
    });
}

// Business Units Section
let selectedBusinessUnit = 0;
let activeConfigTab = 'features';

const businessUnits = [
    {
        title: "FinTech & Banking",
        features: ["Análisis de Riesgo", "Detección de Fraudes", "Robo-Advisory", "KYC Automatizado"],
        compliance: ["SOX", "PCI-DSS", "GDPR", "Basel III"],
        integrations: ["Core Banking", "Payment Gateways", "CRM Systems", "Regulatory APIs"],
        models: ["Credit Scoring", "Fraud Detection", "Market Analysis", "Risk Assessment"],
        security: ["End-to-End Encryption", "Multi-Factor Auth", "Audit Trails", "Data Masking"]
    },
    {
        title: "Healthcare & Medical",
        features: ["Diagnóstico por IA", "Análisis de Imágenes", "Predicción de Enfermedades", "Telemedicina"],
        compliance: ["HIPAA", "FDA", "CE Marking", "ISO 13485"],
        integrations: ["EMR/EHR", "PACS Systems", "Lab Equipment", "Wearable Devices"],
        models: ["Image Analysis", "Drug Discovery", "Patient Monitoring", "Clinical Decision Support"],
        security: ["PHI Protection", "Secure Messaging", "Access Controls", "Anonymization"]
    },
    {
        title: "Retail & E-commerce",
        features: ["Recomendaciones", "Optimización", "Análisis de Sentimientos", "Chatbots"],
        compliance: ["PCI DSS", "CCPA", "GDPR", "Local Tax Laws"],
        integrations: ["E-commerce Platforms", "CRM", "ERP Systems", "Social Media APIs"],
        models: ["Recommendation Engine", "Price Optimization", "Demand Forecasting", "Customer Segmentation"],
        security: ["Payment Security", "Customer Data Protection", "Fraud Prevention", "API Security"]
    }
];

function selectBusinessUnit(index) {
    selectedBusinessUnit = index;
    
    // Update business cards visual state
    const cards = document.querySelectorAll('.business-card');
    cards.forEach((card, i) => {
        if (i === index) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });
    
    // Update config panel title
    const unit = businessUnits[index];
    document.querySelector('.config-title').textContent = `Configuración Avanzada: ${unit.title}`;
    
    // Update config content
    updateConfigContent();
}

function switchConfigTab(tabId) {
    activeConfigTab = tabId;
    
    // Update tab buttons
    const tabs = document.querySelectorAll('.config-tab');
    tabs.forEach(tab => {
        const tabKey = tab.getAttribute('onclick').match(/'([^']+)'/)[1];
        if (tabKey === tabId) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
    
    // Update content
    updateConfigContent();
}

function updateConfigContent() {
    const unit = businessUnits[selectedBusinessUnit];
    const items = unit[activeConfigTab] || unit.features;
    
    const container = document.querySelector('.config-items');
    container.innerHTML = '';
    
    items.forEach(item => {
        const itemEl = document.createElement('div');
        itemEl.className = 'config-item';
        itemEl.innerHTML = `
            <span class="check-icon">✅</span>
            <span>${item}</span>
        `;
        container.appendChild(itemEl);
    });
}

// Quantum Lab Section
let activeExperiment = 0;

function selectExperiment(index) {
    activeExperiment = index;
    
    const cards = document.querySelectorAll('.experiment-card');
    cards.forEach((card, i) => {
        if (i === index) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });
}

// Metaverse Section
let activeWorld = 0;

function selectWorld(index) {
    activeWorld = index;
    
    const cards = document.querySelectorAll('.world-card');
    cards.forEach((card, i) => {
        if (i === index) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });
}

// Modal Management
function openScheduleModal() {
    const modal = document.getElementById('scheduleModal');
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeScheduleModal() {
    const modal = document.getElementById('scheduleModal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
}

function openGoogleCalendar() {
    // In a real application, this would open the actual Google Calendar booking link
    window.open('https://calendar.google.com/calendar/appointments/schedules/your-link', '_blank', 'width=800,height=600');
    closeScheduleModal();
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('scheduleModal');
    if (e.target === modal) {
        closeScheduleModal();
    }
});

// Canvas Animations
function initParticleSystem() {
    const canvas = document.getElementById('particlesCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    function resizeCanvas() {
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const particles = [];
    
    // Create particles
    for (let i = 0; i < 50; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            dx: (Math.random() - 0.5) * 0.5,
            dy: (Math.random() - 0.5) * 0.5,
            size: Math.random() * 3 + 1,
            color: Math.random() > 0.5 ? '#3b82f6' : '#8b5cf6',
            opacity: Math.random() * 0.5 + 0.3
        });
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw connections
        particles.forEach((particle, i) => {
            particles.slice(i + 1).forEach(otherParticle => {
                const dx = particle.x - otherParticle.x;
                const dy = particle.y - otherParticle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 100) {
                    ctx.beginPath();
                    ctx.moveTo(particle.x, particle.y);
                    ctx.lineTo(otherParticle.x, otherParticle.y);
                    ctx.strokeStyle = `rgba(59, 130, 246, ${0.1 * (1 - distance / 100)})`;
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            });
        });

        // Update and draw particles
        particles.forEach(particle => {
            particle.x += particle.dx;
            particle.y += particle.dy;

            if (particle.x < 0 || particle.x > canvas.width) particle.dx *= -1;
            if (particle.y < 0 || particle.y > canvas.height) particle.dy *= -1;

            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fillStyle = particle.color;
            ctx.globalAlpha = particle.opacity;
            ctx.fill();
            ctx.globalAlpha = 1;
        });

        requestAnimationFrame(animate);
    }

    animate();
}

function initQuantumAnimation() {
    const canvas = document.getElementById('quantumCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    function resizeCanvas() {
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const atoms = [];
    
    // Create quantum atoms
    for (let i = 0; i < 8; i++) {
        atoms.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            radius: Math.random() * 30 + 20,
            angle: Math.random() * Math.PI * 2,
            speed: (Math.random() - 0.5) * 0.02,
            color: ['#3b82f6', '#8b5cf6', '#06b6d4', '#ec4899'][Math.floor(Math.random() * 4)],
            electrons: Array.from({ length: Math.floor(Math.random() * 3) + 2 }, () => ({
                angle: Math.random() * Math.PI * 2,
                distance: Math.random() * 20 + 15,
                speed: Math.random() * 0.1 + 0.05
            }))
        });
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        atoms.forEach(atom => {
            atom.angle += atom.speed;
            
            // Draw atom nucleus
            ctx.beginPath();
            ctx.arc(atom.x, atom.y, 8, 0, Math.PI * 2);
            ctx.fillStyle = atom.color;
            ctx.globalAlpha = 0.8;
            ctx.fill();
            
            // Draw electron orbits and electrons
            atom.electrons.forEach(electron => {
                electron.angle += electron.speed;
                
                // Orbit
                ctx.beginPath();
                ctx.arc(atom.x, atom.y, electron.distance, 0, Math.PI * 2);
                ctx.strokeStyle = atom.color;
                ctx.globalAlpha = 0.2;
                ctx.lineWidth = 1;
                ctx.stroke();
                
                // Electron
                const electronX = atom.x + Math.cos(electron.angle) * electron.distance;
                const electronY = atom.y + Math.sin(electron.angle) * electron.distance;
                
                ctx.beginPath();
                ctx.arc(electronX, electronY, 3, 0, Math.PI * 2);
                ctx.fillStyle = atom.color;
                ctx.globalAlpha = 1;
                ctx.fill();
            });
            
            // Quantum entanglement lines
            atoms.forEach(otherAtom => {
                if (otherAtom !== atom) {
                    const dx = atom.x - otherAtom.x;
                    const dy = atom.y - otherAtom.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    if (distance < 150) {
                        ctx.beginPath();
                        ctx.moveTo(atom.x, atom.y);
                        ctx.lineTo(otherAtom.x, otherAtom.y);
                        ctx.strokeStyle = atom.color;
                        ctx.globalAlpha = 0.1 * (1 - distance / 150);
                        ctx.lineWidth = 2;
                        ctx.stroke();
                    }
                }
            });
        });

        ctx.globalAlpha = 1;
        requestAnimationFrame(animate);
    }

    animate();
}

function initMetaverseAnimation() {
    const canvas = document.getElementById('metaverseCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    function resizeCanvas() {
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const nodes = [];
    
    // Create 3D metaverse nodes
    for (let i = 0; i < 30; i++) {
        nodes.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            z: Math.random() * 200 - 100,
            vx: (Math.random() - 0.5) * 2,
            vy: (Math.random() - 0.5) * 2,
            vz: (Math.random() - 0.5) * 2,
            color: ['#3b82f6', '#8b5cf6', '#06b6d4', '#ec4899', '#f59e0b'][Math.floor(Math.random() * 5)],
            size: Math.random() * 8 + 4,
            connections: []
        });
    }

    // Create connections
    nodes.forEach((node, i) => {
        nodes.forEach((otherNode, j) => {
            if (i !== j) {
                const distance = Math.sqrt(
                    Math.pow(node.x - otherNode.x, 2) + 
                    Math.pow(node.y - otherNode.y, 2) + 
                    Math.pow(node.z - otherNode.z, 2)
                );
                if (distance < 120 && node.connections.length < 3) {
                    node.connections.push(j);
                }
            }
        });
    });

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Update positions
        nodes.forEach(node => {
            node.x += node.vx;
            node.y += node.vy;
            node.z += node.vz;

            if (node.x < 0 || node.x > canvas.width) node.vx *= -1;
            if (node.y < 0 || node.y > canvas.height) node.vy *= -1;
            if (node.z < -100 || node.z > 100) node.vz *= -1;
        });

        // Draw connections
        nodes.forEach((node, i) => {
            node.connections.forEach(connectionIndex => {
                const connectedNode = nodes[connectionIndex];
                
                ctx.beginPath();
                ctx.moveTo(node.x, node.y);
                ctx.lineTo(connectedNode.x, connectedNode.y);
                
                const distance = Math.sqrt(
                    Math.pow(node.x - connectedNode.x, 2) + 
                    Math.pow(node.y - connectedNode.y, 2)
                );
                
                ctx.strokeStyle = node.color;
                ctx.globalAlpha = Math.max(0.1, 1 - distance / 120);
                ctx.lineWidth = 2;
                ctx.stroke();
            });
        });

        // Draw nodes with 3D effect
        nodes.forEach(node => {
            const perspective = 200 / (200 + node.z);
            const size = node.size * perspective;
            
            ctx.beginPath();
            ctx.arc(node.x, node.y, size, 0, Math.PI * 2);
            ctx.fillStyle = node.color;
            ctx.globalAlpha = 0.8 * perspective;
            ctx.fill();
            
            // Glow effect
            ctx.beginPath();
            ctx.arc(node.x, node.y, size * 1.5, 0, Math.PI * 2);
            ctx.fillStyle = node.color;
            ctx.globalAlpha = 0.2 * perspective;
            ctx.fill();
        });

        ctx.globalAlpha = 1;
        requestAnimationFrame(animate);
    }

    animate();
}

// Initialize animations when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all canvas animations with a small delay
    setTimeout(() => {
        initParticleSystem();
        initQuantumAnimation();
        initMetaverseAnimation();
    }, 100);
    
    // Initialize default states
    updateConfigContent();
});

// Smooth scrolling for navigation links
document.addEventListener('DOMContentLoaded', () => {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            const targetId = link.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const headerHeight = document.querySelector('.header').offsetHeight;
                const targetPosition = targetElement.offsetTop - headerHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
});

// LLM Capabilities Section
let activeLLMCapability = 0;

const llmCapabilities = [
    {
        title: "Neural Language Understanding",
        description: "Comprensión profunda del lenguaje humano con contexto semántico avanzado",
        metrics: ["99.8% Precisión", "150+ Idiomas", "Tiempo Real"],
        color: "from-blue-500 to-purple-600"
    },
    {
        title: "Conversational AI",
        description: "Diálogos naturales con memoria contextual y personalidad adaptable",
        metrics: ["Memoria 128K", "Contexto Infinito", "Multimodal"],
        color: "from-purple-500 to-pink-600"
    },
    {
        title: "Code Generation",
        description: "Generación de código en 200+ lenguajes con optimización automática",
        metrics: ["200+ Lenguajes", "Auto-Debug", "Optimización"],
        color: "from-green-500 to-blue-600"
    },
    {
        title: "Vision & Analysis",
        description: "Análisis visual avanzado con comprensión de contexto y objetos",
        metrics: ["4K Resolution", "OCR Avanzado", "Análisis Scene"],
        color: "from-orange-500 to-red-600"
    },
    {
        title: "Real-time Processing",
        description: "Procesamiento en tiempo real con latencia ultra-baja",
        metrics: ["<10ms Latencia", "Escalable", "Edge Computing"],
        color: "from-cyan-500 to-blue-600"
    },
    {
        title: "Creative AI",
        description: "Generación creativa de contenido multimedia y artístico",
        metrics: ["Arte Digital", "Música", "Video"],
        color: "from-pink-500 to-purple-600"
    }
];

function selectLLMCapability(index) {
    activeLLMCapability = index;
    
    // Update capability cards
    const cards = document.querySelectorAll('.llm-capability-card');
    cards.forEach((card, i) => {
        if (i === index) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });
}

// ML Pipeline Section
let pipelineRunning = false;
let currentPipelineStep = 0;
let pipelineMetrics = {
    accuracy: 0,
    loss: 1.0,
    epoch: 0,
    throughput: 0
};

function togglePipeline() {
    pipelineRunning = !pipelineRunning;
    const button = document.getElementById('pipeline-toggle');
    const body = document.body;
    
    if (pipelineRunning) {
        button.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg><span>Pausar Pipeline</span>';
        button.className = 'pipeline-control-btn bg-red-500 hover:bg-red-600 text-white';
        body.classList.add('pipeline-running');
        
        // Start pipeline animation
        startPipelineAnimation();
    } else {
        button.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1"/></svg><span>Iniciar Pipeline</span>';
        button.className = 'pipeline-control-btn bg-green-500 hover:bg-green-600 text-white';
        body.classList.remove('pipeline-running');
        
        // Stop pipeline animation
        stopPipelineAnimation();
    }
}

function resetPipeline() {
    pipelineRunning = false;
    currentPipelineStep = 0;
    pipelineMetrics = { accuracy: 0, loss: 1.0, epoch: 0, throughput: 0 };
    
    const button = document.getElementById('pipeline-toggle');
    button.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1"/></svg><span>Iniciar Pipeline</span>';
    button.className = 'pipeline-control-btn bg-green-500 hover:bg-green-600 text-white';
    
    document.body.classList.remove('pipeline-running');
    updatePipelineSteps();
    updatePipelineMetrics();
}

function startPipelineAnimation() {
    const interval = setInterval(() => {
        if (!pipelineRunning) {
            clearInterval(interval);
            return;
        }
        
        currentPipelineStep = (currentPipelineStep + 1) % 5;
        
        // Update metrics
        pipelineMetrics.accuracy = Math.min(0.99, pipelineMetrics.accuracy + Math.random() * 0.05);
        pipelineMetrics.loss = Math.max(0.001, pipelineMetrics.loss - Math.random() * 0.1);
        pipelineMetrics.epoch = pipelineMetrics.epoch + 1;
        pipelineMetrics.throughput = 1000 + Math.random() * 500;
        
        updatePipelineSteps();
        updatePipelineMetrics();
        updateNeuralCanvas();
    }, 2000);
}

function stopPipelineAnimation() {
    // Animation will stop automatically when pipelineRunning becomes false
}

function updatePipelineSteps() {
    const steps = document.querySelectorAll('.pipeline-step');
    steps.forEach((step, index) => {
        step.classList.remove('active', 'completed');
        
        if (pipelineRunning && index === currentPipelineStep) {
            step.classList.add('active');
        } else if (index < currentPipelineStep || !pipelineRunning) {
            step.classList.add('completed');
        }
    });
}

function updatePipelineMetrics() {
    document.getElementById('accuracy-metric').textContent = (pipelineMetrics.accuracy * 100).toFixed(1);
    document.getElementById('accuracy-progress').style.width = `${pipelineMetrics.accuracy * 100}%`;
    
    document.getElementById('loss-metric').textContent = pipelineMetrics.loss.toFixed(3);
    document.getElementById('loss-progress').style.width = `${(1 - pipelineMetrics.loss) * 100}%`;
    
    document.getElementById('epoch-metric').textContent = pipelineMetrics.epoch;
    document.getElementById('throughput-metric').textContent = Math.floor(pipelineMetrics.throughput);
}

function updateNeuralCanvas() {
    const canvas = document.getElementById('neural-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    if (pipelineRunning) {
        // Draw neural sparks
        for (let i = 0; i < 20; i++) {
            const x = Math.random() * canvas.width;
            const y = Math.random() * canvas.height;
            const opacity = Math.random() * 0.6 + 0.4;
            
            ctx.beginPath();
            ctx.arc(x, y, 1, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(59, 130, 246, ${opacity})`;
            ctx.fill();
        }
    }
}

// Initialize Neural Canvas
function initNeuralCanvas() {
    const canvas = document.getElementById('neural-canvas');
    if (!canvas) return;
    
    function resizeCanvas() {
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
}

// Initialize LLM Capabilities interactions
function initLLMCapabilities() {
    const cards = document.querySelectorAll('.llm-capability-card');
    cards.forEach((card, index) => {
        card.addEventListener('click', () => selectLLMCapability(index));
    });
}

// Initialize ML Pipeline interactions
function initMLPipeline() {
    const toggleBtn = document.getElementById('pipeline-toggle');
    const resetBtn = document.getElementById('pipeline-reset');
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', togglePipeline);
    }
    
    if (resetBtn) {
        resetBtn.addEventListener('click', resetPipeline);
    }
    
    // Initialize metrics
    updatePipelineMetrics();
}

// Initialize new sections when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all canvas animations with a small delay
    setTimeout(() => {
        initParticleSystem();
        initQuantumAnimation();
        initMetaverseAnimation();
    }, 100);
    
    // Initialize default states
    updateConfigContent();
    
    // Initialize new vanguard sections
    initLLMCapabilities();
    initMLPipeline();
    initNeuralCanvas();
});
