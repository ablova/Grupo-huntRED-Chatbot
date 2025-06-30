/**
 * Grupo huntRED® - Propuesta Premium Enhancement
 * La mejor propuesta automatizada del planeta
 */

class ProposalEnhancements {
    constructor() {
        this.currentTab = 'summary';
        this.charts = {};
        this.isLoading = false;
        this.theme = 'default';
        this.init();
    }

    init() {
        this.setupLoadingStates();
        this.setupTabs();
        this.setupROICalculator();
        this.setupROIAdvancedFeatures();
        this.setupBookmarks();
        this.setupThemeSwitcher();
        this.setupCharts();
        this.setupAnimations();
        this.setupAccessibility();
        this.setupQRCode();
        this.setupFooterIcons();
        this.setupProgressiveDisclosure();
        this.setupSearch();
        this.setupInteractiveTimeline();
        this.setupEngagementTracking();
        
        this.addROIHistoryTracking();
        
        console.log('Proposal Enhancements initialized successfully');
    }

    // Loading states premium
    setupLoadingStates() {
        const skeletonHTML = `
            <div class="animate-pulse">
                <div class="bg-gray-200 rounded-lg h-48 mb-4"></div>
                <div class="space-y-2">
                    <div class="bg-gray-200 h-4 rounded w-3/4"></div>
                    <div class="bg-gray-200 h-4 rounded w-1/2"></div>
                    <div class="bg-gray-200 h-4 rounded w-5/6"></div>
                </div>
            </div>
        `;

        document.querySelectorAll('canvas[id*="Chart"]').forEach(canvas => {
            const container = canvas.parentElement;
            container.innerHTML = skeletonHTML;
            
            setTimeout(() => {
                container.innerHTML = `<canvas id="${canvas.id}" height="200"></canvas>`;
                this.setupCharts();
            }, 1500);
        });
    }

    // Tabs mejorados con micro-interacciones
    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabPanels = document.querySelectorAll('.tab-panel');

        tabButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e));
            btn.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.switchTab(e);
                }
            });
        });

        document.addEventListener('keydown', (e) => {
            if (e.altKey) {
                switch(e.key) {
                    case '1': this.goToTab('summary'); break;
                    case '2': this.goToTab('details'); break;
                    case '3': this.goToTab('milestones'); break;
                    case '4': this.goToTab('services'); break;
                    case '5': this.goToTab('contacts'); break;
                }
            }
        });
    }

    switchTab(e) {
        e.preventDefault();
        const targetId = e.currentTarget.id.replace('tab-', 'panel-');
        
        const currentPanel = document.querySelector('.tab-panel.active');
        if (currentPanel) {
            currentPanel.style.transform = 'translateX(-20px)';
            currentPanel.style.opacity = '0';
        }
        
        setTimeout(() => {
            document.querySelectorAll('.tab-button').forEach(tab => {
                tab.classList.remove('tab-active', 'text-red-600', 'border-red-600', 'bg-red-50');
                tab.classList.add('border-transparent');
                tab.setAttribute('aria-selected', 'false');
            });
            
            e.currentTarget.classList.add('tab-active', 'text-red-600', 'border-red-600', 'bg-red-50');
            e.currentTarget.classList.remove('border-transparent');
            e.currentTarget.setAttribute('aria-selected', 'true');
            
            document.querySelectorAll('.tab-panel').forEach(panel => {
                panel.classList.remove('active');
                panel.classList.add('hidden');
            });
            
            const targetPanel = document.getElementById(targetId);
            if (targetPanel) {
                targetPanel.classList.add('active');
                targetPanel.classList.remove('hidden');
                
                targetPanel.style.transform = 'translateX(20px)';
                targetPanel.style.opacity = '0';
                
                setTimeout(() => {
                    targetPanel.style.transition = 'all 0.3s ease';
                    targetPanel.style.transform = 'translateX(0)';
                    targetPanel.style.opacity = '1';
                }, 50);
            }
        }, 150);

        this.currentTab = e.currentTarget.id.replace('tab-', '');
        this.updateURL();
        this.trackEngagement('tab_switch', this.currentTab);
    }

    // Calculadora de ROI interactiva mejorada y sincronizada
    setupROICalculator() {
        // Sincronizar con datos reales de la propuesta
        this.syncROIData();
        
        // Configurar sliders con valores reales
        ['salarySlider', 'timeSlider', 'productivitySlider', 'qualitySlider', 'retentionSlider'].forEach(id => {
            const slider = document.getElementById(id);
            const value = document.getElementById(id.replace('Slider', 'Value'));
            
            if (slider && value) {
                slider.addEventListener('input', () => {
                    this.updateROICalculation();
                    value.textContent = this.formatSliderValue(id, slider.value);
                    this.updateROIChart();
                    this.updateROIInsights();
                });
            }
        });

        // Configurar selectores adicionales
        ['industrySelect', 'positionLevelSelect', 'urgencySelect'].forEach(id => {
            const select = document.getElementById(id);
            if (select) {
                select.addEventListener('change', () => {
                    this.updateROICalculation();
                    this.updateROIChart();
                    this.updateROIInsights();
                });
            }
        });

        this.updateROICalculation();
        this.updateROIChart();
        this.updateROIInsights();
    }

    // Sincronizar datos con la propuesta real
    syncROIData() {
        // Obtener datos reales de la propuesta
        const proposalData = this.getProposalData();
        
        // Actualizar sliders con valores reales
        if (proposalData.averageSalary) {
            const salarySlider = document.getElementById('salarySlider');
            if (salarySlider) {
                salarySlider.value = proposalData.averageSalary;
                salarySlider.min = proposalData.averageSalary * 0.5;
                salarySlider.max = proposalData.averageSalary * 2;
            }
        }

        if (proposalData.estimatedTime) {
            const timeSlider = document.getElementById('timeSlider');
            if (timeSlider) {
                timeSlider.value = proposalData.estimatedTime;
            }
        }

        // Actualizar industria si está disponible
        if (proposalData.industry) {
            const industrySelect = document.getElementById('industrySelect');
            if (industrySelect) {
                industrySelect.value = proposalData.industry;
            }
        }

        // Actualizar nivel de posición
        if (proposalData.positionLevel) {
            const levelSelect = document.getElementById('positionLevelSelect');
            if (levelSelect) {
                levelSelect.value = proposalData.positionLevel;
            }
        }
    }

    // Obtener datos reales de la propuesta
    getProposalData() {
        const data = {
            averageSalary: 800000,
            estimatedTime: 45,
            industry: 'technology',
            positionLevel: 'senior',
            urgency: 'medium'
        };

        // Intentar obtener datos reales del DOM
        const salaryElements = document.querySelectorAll('[data-salary]');
        if (salaryElements.length > 0) {
            const salaries = Array.from(salaryElements).map(el => 
                parseInt(el.dataset.salary.replace(/[^\d]/g, ''))
            );
            data.averageSalary = salaries.reduce((a, b) => a + b, 0) / salaries.length;
        }

        // Obtener industria del cliente
        const industryElement = document.querySelector('[data-industry]');
        if (industryElement) {
            data.industry = industryElement.dataset.industry;
        }

        // Obtener nivel de posición
        const levelElements = document.querySelectorAll('[data-level]');
        if (levelElements.length > 0) {
            const levels = Array.from(levelElements).map(el => el.dataset.level);
            data.positionLevel = this.getMostCommonLevel(levels);
        }

        return data;
    }

    getMostCommonLevel(levels) {
        const counts = {};
        levels.forEach(level => {
            counts[level] = (counts[level] || 0) + 1;
        });
        return Object.keys(counts).reduce((a, b) => counts[a] > counts[b] ? a : b);
    }

    updateROICalculation() {
        const salarySlider = document.getElementById('salarySlider');
        const timeSlider = document.getElementById('timeSlider');
        const productivitySlider = document.getElementById('productivitySlider');
        const qualitySlider = document.getElementById('qualitySlider');
        const retentionSlider = document.getElementById('retentionSlider');
        
        if (!salarySlider || !timeSlider || !productivitySlider) return;

        const salary = parseInt(salarySlider.value);
        const time = parseInt(timeSlider.value);
        const productivity = parseInt(productivitySlider.value);
        const quality = parseInt(qualitySlider?.value || 85);
        const retention = parseInt(retentionSlider?.value || 80);

        // Cálculos avanzados
        const dailySalary = salary / 365;
        const vacancyCost = dailySalary * time * (productivity / 100);
        const qualityCost = vacancyCost * (1 - quality / 100);
        const retentionCost = vacancyCost * (1 - retention / 100);
        const totalCost = vacancyCost + qualityCost + retentionCost;
        
        // Costo de nuestro servicio
        const serviceCost = this.getServiceCost();
        
        // ROI mejorado
        const roi = ((totalCost - serviceCost) / serviceCost) * 100;
        const paybackPeriod = serviceCost / (totalCost / 12); // meses

        // Actualizar elementos
        this.updateROIElements({
            vacancyCost,
            qualityCost,
            retentionCost,
            totalCost,
            serviceCost,
            roi,
            paybackPeriod
        });
    }

    getServiceCost() {
        // Obtener costo real del servicio de la propuesta
        const totalElement = document.querySelector('[data-total]');
        if (totalElement) {
            return parseInt(totalElement.dataset.total.replace(/[^\d]/g, ''));
        }
        
        // Valor por defecto
        return 150000;
    }

    updateROIElements(data) {
        const elements = {
            'vacancyCost': `$${data.vacancyCost.toLocaleString()}`,
            'qualityCost': `$${data.qualityCost.toLocaleString()}`,
            'retentionCost': `$${data.retentionCost.toLocaleString()}`,
            'totalCost': `$${data.totalCost.toLocaleString()}`,
            'serviceCost': `$${data.serviceCost.toLocaleString()}`,
            'roiValue': `${Math.max(0, data.roi).toFixed(0)}%`,
            'paybackPeriod': `${data.paybackPeriod.toFixed(1)} meses`
        };

        Object.keys(elements).forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = elements[id];
            }
        });

        // Actualizar indicadores visuales
        this.updateROIIndicators(data);
    }

    updateROIIndicators(data) {
        // Indicador de ROI
        const roiIndicator = document.getElementById('roiIndicator');
        if (roiIndicator) {
            const roi = data.roi;
            let color, icon, text;
            
            if (roi >= 300) {
                color = 'text-green-600';
                icon = 'fa-rocket';
                text = 'ROI Excepcional';
            } else if (roi >= 200) {
                color = 'text-blue-600';
                icon = 'fa-chart-line';
                text = 'ROI Excelente';
            } else if (roi >= 100) {
                color = 'text-yellow-600';
                icon = 'fa-thumbs-up';
                text = 'ROI Bueno';
            } else {
                color = 'text-red-600';
                icon = 'fa-exclamation-triangle';
                text = 'ROI Bajo';
            }
            
            roiIndicator.className = `text-2xl font-bold ${color}`;
            roiIndicator.innerHTML = `<i class="fas ${icon} mr-2"></i>${text}`;
        }

        // Indicador de período de recuperación
        const paybackIndicator = document.getElementById('paybackIndicator');
        if (paybackIndicator) {
            const payback = data.paybackPeriod;
            let color, text;
            
            if (payback <= 3) {
                color = 'text-green-600';
                text = 'Recuperación Rápida';
            } else if (payback <= 6) {
                color = 'text-blue-600';
                text = 'Recuperación Normal';
            } else {
                color = 'text-yellow-600';
                text = 'Recuperación Lenta';
            }
            
            paybackIndicator.className = `text-sm ${color}`;
            paybackIndicator.textContent = text;
        }
    }

    updateROIChart() {
        const chartContainer = document.getElementById('roiChartContainer');
        if (!chartContainer) return;

        const salary = parseInt(document.getElementById('salarySlider')?.value || 800000);
        const time = parseInt(document.getElementById('timeSlider')?.value || 45);
        const productivity = parseInt(document.getElementById('productivitySlider')?.value || 25);

        // Crear gráfico de comparación
        const chartHTML = `
            <canvas id="roiComparisonChart" height="200"></canvas>
        `;
        
        chartContainer.innerHTML = chartHTML;

        // Configurar Chart.js
        const ctx = document.getElementById('roiComparisonChart');
        if (ctx && typeof Chart !== 'undefined') {
            const dailySalary = salary / 365;
            const vacancyCost = dailySalary * time * (productivity / 100);
            const serviceCost = this.getServiceCost();

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Costo de Vacante', 'Nuestro Servicio', 'Ahorro Neto'],
                    datasets: [{
                        label: 'Costo Mensual',
                        data: [vacancyCost / 12, serviceCost / 12, (vacancyCost - serviceCost) / 12],
                        backgroundColor: [
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)'
                        ],
                        borderColor: [
                            'rgba(239, 68, 68, 1)',
                            'rgba(59, 130, 246, 1)',
                            'rgba(16, 185, 129, 1)'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `$${context.parsed.y.toLocaleString()}/mes`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    updateROIInsights() {
        const insightsContainer = document.getElementById('roiInsights');
        if (!insightsContainer) return;

        const salary = parseInt(document.getElementById('salarySlider')?.value || 800000);
        const time = parseInt(document.getElementById('timeSlider')?.value || 45);
        const productivity = parseInt(document.getElementById('productivitySlider')?.value || 25);
        const industry = document.getElementById('industrySelect')?.value || 'general';

        // Generar insights personalizados
        const insights = this.generateROIInsights(salary, time, productivity, industry);
        
        insightsContainer.innerHTML = insights.map(insight => `
            <div class="bg-blue-50 border-l-4 border-blue-400 p-4 mb-3 rounded">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <i class="fas fa-lightbulb text-blue-400"></i>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm text-blue-700">${insight}</p>
                    </div>
                </div>
            </div>
        `).join('');
    }

    generateROIInsights(salary, time, productivity, industry) {
        const insights = [];
        const dailySalary = salary / 365;
        const vacancyCost = dailySalary * time * (productivity / 100);

        // Insights basados en datos
        if (productivity > 30) {
            insights.push(`La alta productividad perdida (${productivity}%) indica una posición crítica que requiere atención inmediata.`);
        }

        if (time > 60) {
            insights.push(`Con ${time} días de búsqueda, el costo de oportunidad es significativo. Nuestro proceso puede reducir este tiempo en un 60%.`);
        }

        if (salary > 1000000) {
            insights.push(`Para posiciones de alto nivel ($${salary.toLocaleString()}), la inversión en un proceso de selección premium se justifica ampliamente.`);
        }

        // Insights por industria
        const industryInsights = {
            'technology': 'En tecnología, la velocidad de contratación es crucial. Cada día de vacante puede costar hasta $5,000 en productividad perdida.',
            'finance': 'En finanzas, la precisión en la selección es fundamental. Un mal contrato puede costar hasta 10x el salario anual.',
            'healthcare': 'En salud, las vacantes prolongadas afectan directamente la calidad del servicio al paciente.',
            'manufacturing': 'En manufactura, las vacantes pueden detener líneas de producción completas.'
        };

        if (industryInsights[industry]) {
            insights.push(industryInsights[industry]);
        }

        // Insight de ROI
        const serviceCost = this.getServiceCost();
        const roi = ((vacancyCost - serviceCost) / serviceCost) * 100;
        
        if (roi > 200) {
            insights.push(`Con un ROI del ${roi.toFixed(0)}%, esta inversión se recupera en menos de 6 meses.`);
        }

        return insights;
    }

    formatSliderValue(id, value) {
        switch(id) {
            case 'salarySlider': return `$${parseInt(value).toLocaleString()}`;
            case 'timeSlider': return `${value} días`;
            case 'productivitySlider': return `${value}%`;
            case 'qualitySlider': return `${value}%`;
            case 'retentionSlider': return `${value}%`;
            default: return value;
        }
    }

    // Timeline interactivo
    setupInteractiveTimeline() {
        const timelineItems = document.querySelectorAll('.timeline-item');
        timelineItems.forEach((item, index) => {
            item.addEventListener('click', () => {
                this.activateTimelineStep(index + 1);
            });
        });
    }

    activateTimelineStep(step) {
        document.querySelectorAll('.timeline-item').forEach((item, index) => {
            if (index < step) {
                item.classList.remove('opacity-50');
                item.classList.add('completed');
                item.querySelector('.w-8').classList.remove('bg-gray-300');
                item.querySelector('.w-8').classList.add('bg-blue-500');
                item.querySelector('.w-4').classList.remove('bg-gray-300');
                item.querySelector('.w-4').classList.add('bg-green-500');
            } else {
                item.classList.add('opacity-50');
                item.classList.remove('completed');
                item.querySelector('.w-8').classList.add('bg-gray-300');
                item.querySelector('.w-8').classList.remove('bg-blue-500');
                item.querySelector('.w-4').classList.add('bg-gray-300');
                item.querySelector('.w-4').classList.remove('bg-green-500');
            }
        });
    }

    // Búsqueda inteligente
    setupSearch() {
        const searchInput = document.getElementById('searchInput');
        const searchResults = document.getElementById('searchResults');

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase();
                if (query.length < 2) {
                    searchResults.classList.add('hidden');
                    return;
                }

                const results = this.searchInDocument(query);
                this.displaySearchResults(results);
            });
        }
    }

    searchInDocument(query) {
        const elements = document.querySelectorAll('h1, h2, h3, h4, h5, p, li, td, th');
        const results = [];

        elements.forEach(el => {
            const text = el.textContent.toLowerCase();
            if (text.includes(query)) {
                results.push({
                    element: el,
                    text: el.textContent.substring(0, 100) + '...',
                    type: el.tagName.toLowerCase()
                });
            }
        });

        return results.slice(0, 10);
    }

    displaySearchResults(results) {
        const searchResults = document.getElementById('searchResults');
        
        if (results.length === 0) {
            searchResults.innerHTML = '<div class="p-4 text-gray-500">No se encontraron resultados</div>';
        } else {
            searchResults.innerHTML = results.map(result => `
                <div class="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100" onclick="this.scrollToElement('${result.element.id || result.element.className}')">
                    <div class="font-medium text-sm text-gray-800">${result.text}</div>
                    <div class="text-xs text-gray-500">${result.type.toUpperCase()}</div>
                </div>
            `).join('');
        }

        searchResults.classList.remove('hidden');
    }

    // Marcadores
    setupBookmarks() {
        const bookmarksBtn = document.getElementById('bookmarksBtn');
        const bookmarksPanel = document.getElementById('bookmarksPanel');

        if (bookmarksBtn) {
            bookmarksBtn.addEventListener('click', () => {
                bookmarksPanel.classList.toggle('hidden');
            });
        }

        document.querySelectorAll('h1, h2, h3, h4').forEach(heading => {
            heading.style.cursor = 'pointer';
            heading.addEventListener('click', () => this.toggleBookmark(heading));
        });
    }

    toggleBookmark(element) {
        const bookmarksList = document.getElementById('bookmarksList');
        const existingBookmark = bookmarksList.querySelector(`[data-id="${element.id}"]`);

        if (existingBookmark) {
            existingBookmark.remove();
            element.classList.remove('text-red-600');
        } else {
            const bookmark = document.createElement('div');
            bookmark.className = 'bookmark-item flex items-center justify-between p-2 bg-gray-50 rounded';
            bookmark.setAttribute('data-id', element.id);
            bookmark.innerHTML = `
                <span class="text-sm text-gray-700">${element.textContent}</span>
                <button onclick="this.removeBookmark('${element.id}')" class="text-red-500 hover:text-red-700">
                    <i class="fas fa-times"></i>
                </button>
            `;
            bookmarksList.appendChild(bookmark);
            element.classList.add('text-red-600');
        }
    }

    // Cambiador de tema
    setupThemeSwitcher() {
        const themeBtn = document.getElementById('themeBtn');
        const themePanel = document.getElementById('themePanel');

        if (themeBtn) {
            themeBtn.addEventListener('click', () => {
                themePanel.classList.toggle('hidden');
            });
        }

        document.querySelectorAll('.theme-option').forEach(option => {
            option.addEventListener('click', () => {
                this.changeTheme(option.dataset.theme);
            });
        });
    }

    changeTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.theme = theme;
        this.trackEngagement('theme_change', theme);
    }

    // Gráficos mejorados con Chart.js
    setupCharts() {
        const talentMarketCanvas = document.getElementById('talentMarketChart');
        if (talentMarketCanvas) {
            this.charts.talentMarket = new Chart(talentMarketCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['Talentos Disponibles', 'Escasez de Talento', 'Talentos Pasivos'],
                    datasets: [{
                        data: [45, 27, 28],
                        backgroundColor: [
                            '#10B981', // Verde
                            '#EF4444', // Rojo
                            '#3B82F6'  // Azul
                        ],
                        borderWidth: 0,
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                usePointStyle: true,
                                font: { size: 12 }
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#E53E3E',
                            borderWidth: 1
                        }
                    },
                    animation: {
                        animateRotate: true,
                        animateScale: true
                    }
                }
            });
        }
    }

    // Animaciones premium
    setupAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in');
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            observer.observe(el);
        });

        document.querySelectorAll('.service-card, .info-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-5px) scale(1.02)';
                card.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) scale(1)';
                card.style.boxShadow = '';
            });
        });
    }

    // Mejoras de accesibilidad
    setupAccessibility() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Saltar al contenido principal';
        skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-red-600 text-white px-4 py-2 rounded z-50';
        document.body.insertBefore(skipLink, document.body.firstChild);

        document.querySelectorAll('.tab-button').forEach((tab, index) => {
            tab.setAttribute('aria-label', `${tab.textContent} (Alt + ${index + 1})`);
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });
    }

    // QR Code mejorado
    setupQRCode() {
        const qrContainer = document.querySelector('.qr-code-container');
        if (qrContainer) {
            const qrUrl = `https://ai.huntred.com/verify/${this.getProposalId()}`;
            const qrImage = qrContainer.querySelector('img');
            if (qrImage) {
                qrImage.src = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(qrUrl)}&color=E53E3E&bgcolor=FFFFFF`;
                qrImage.alt = 'Código QR para verificar propuesta';
            }
        }
    }

    getProposalId() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('id') || 'default';
    }

    // Footer con iconos en lugar de texto
    setupFooterIcons() {
        const footerLinks = document.querySelectorAll('.footer-social-links a');
        footerLinks.forEach(link => {
            const icon = this.getSocialIcon(link.href);
            if (icon) {
                link.innerHTML = `<i class="${icon} text-xl"></i>`;
                link.setAttribute('aria-label', link.textContent);
                link.classList.add('hover:scale-110', 'transition-transform', 'duration-200');
            }
        });
    }

    getSocialIcon(url) {
        if (url.includes('linkedin')) return 'fab fa-linkedin';
        if (url.includes('facebook')) return 'fab fa-facebook';
        if (url.includes('twitter') || url.includes('x.com')) return 'fab fa-twitter';
        if (url.includes('instagram')) return 'fab fa-instagram';
        if (url.includes('wa.me') || url.includes('whatsapp')) return 'fab fa-whatsapp';
        if (url.includes('telegram')) return 'fab fa-telegram';
        return 'fas fa-external-link-alt';
    }

    // Progressive disclosure
    setupProgressiveDisclosure() {
        const sections = document.querySelectorAll('section');
        sections.forEach((section, index) => {
            section.style.opacity = '0';
            section.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                section.style.transition = 'all 0.6s ease';
                section.style.opacity = '1';
                section.style.transform = 'translateY(0)';
            }, index * 200);
        });
    }

    // Toast notifications mejoradas
    showToast(message, type = 'success', duration = 3000) {
        const toast = document.createElement('div');
        const iconClass = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
        const bgColor = type === 'success' ? 'bg-green-500' : 'bg-red-500';
        
        toast.className = `toast fixed bottom-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 transform translate-y-full transition-transform duration-300`;
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${iconClass} mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.remove('translate-y-full');
        }, 100);
        
        setTimeout(() => {
            toast.classList.add('translate-y-full');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    // Tracking de engagement
    setupEngagementTracking() {
        let maxScroll = 0;
        window.addEventListener('scroll', () => {
            const scrollPercent = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
            if (scrollPercent > maxScroll) {
                maxScroll = scrollPercent;
                if (maxScroll % 25 === 0) {
                    this.trackEngagement('scroll_depth', maxScroll);
                }
            }
        });

        let startTime = Date.now();
        setInterval(() => {
            const timeOnPage = Math.floor((Date.now() - startTime) / 1000);
            if (timeOnPage % 30 === 0) {
                this.trackEngagement('time_on_page', timeOnPage);
            }
        }, 1000);
    }

    trackEngagement(action, value) {
        console.log('Engagement:', action, value);
        
        if (typeof gtag !== 'undefined') {
            gtag('event', action, {
                'event_category': 'proposal_engagement',
                'event_label': value
            });
        }
    }

    goToTab(tabName) {
        const tabButton = document.getElementById(`tab-${tabName}`);
        if (tabButton) {
            tabButton.click();
        }
    }

    updateURL() {
        const url = new URL(window.location);
        url.searchParams.set('tab', this.currentTab);
        window.history.replaceState({}, '', url);
    }

    // Funcionalidades adicionales para la calculadora de ROI
    setupROIAdvancedFeatures() {
        // Botones de acción
        this.setupROIActionButtons();
        
        // Comparador de escenarios
        this.setupScenarioComparison();
        
        // Historial de cálculos
        this.setupCalculationHistory();
        
        // Sincronización en tiempo real
        this.setupRealTimeSync();
        
        // Exportación avanzada
        this.setupAdvancedExport();
    }

    setupROIActionButtons() {
        const resetBtn = document.getElementById('roiResetBtn');
        const exportBtn = document.getElementById('roiExportBtn');
        
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetROICalculator();
                this.showToast('Calculadora reiniciada', 'info');
            });
        }
        
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportROIData();
            });
        }
    }

    resetROICalculator() {
        // Restaurar valores por defecto
        const defaultValues = {
            'salarySlider': 800000,
            'timeSlider': 45,
            'productivitySlider': 25,
            'qualitySlider': 85,
            'retentionSlider': 80,
            'industrySelect': 'technology',
            'positionLevelSelect': 'senior',
            'urgencySelect': 'medium'
        };

        Object.keys(defaultValues).forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.value = defaultValues[id];
                const valueElement = document.getElementById(id.replace('Slider', 'Value'));
                if (valueElement) {
                    valueElement.textContent = this.formatSliderValue(id, defaultValues[id]);
                }
            }
        });

        this.updateROICalculation();
        this.updateROIChart();
        this.updateROIInsights();
    }

    exportROIData() {
        const data = this.getCurrentROIData();
        
        // Crear objeto de exportación
        const exportData = {
            timestamp: new Date().toISOString(),
            parameters: data.parameters,
            results: data.results,
            insights: data.insights,
            metadata: {
                client: this.getClientInfo(),
                proposal: this.getProposalInfo()
            }
        };

        // Generar PDF
        this.generateROIPDF(exportData);
        
        // Generar Excel
        this.generateROIExcel(exportData);
        
        this.showToast('Datos exportados exitosamente', 'success');
    }

    getCurrentROIData() {
        const parameters = {
            salary: parseInt(document.getElementById('salarySlider')?.value || 800000),
            time: parseInt(document.getElementById('timeSlider')?.value || 45),
            productivity: parseInt(document.getElementById('productivitySlider')?.value || 25),
            quality: parseInt(document.getElementById('qualitySlider')?.value || 85),
            retention: parseInt(document.getElementById('retentionSlider')?.value || 80),
            industry: document.getElementById('industrySelect')?.value || 'technology',
            positionLevel: document.getElementById('positionLevelSelect')?.value || 'senior',
            urgency: document.getElementById('urgencySelect')?.value || 'medium'
        };

        const results = {
            vacancyCost: this.calculateVacancyCost(parameters),
            qualityCost: this.calculateQualityCost(parameters),
            retentionCost: this.calculateRetentionCost(parameters),
            totalCost: this.calculateTotalCost(parameters),
            serviceCost: this.getServiceCost(),
            roi: this.calculateROI(parameters),
            paybackPeriod: this.calculatePaybackPeriod(parameters)
        };

        return { parameters, results, insights: this.generateROIInsights(parameters.salary, parameters.time, parameters.productivity, parameters.industry) };
    }

    calculateVacancyCost(params) {
        const dailySalary = params.salary / 365;
        return dailySalary * params.time * (params.productivity / 100);
    }

    calculateQualityCost(params) {
        const vacancyCost = this.calculateVacancyCost(params);
        return vacancyCost * (1 - params.quality / 100);
    }

    calculateRetentionCost(params) {
        const vacancyCost = this.calculateVacancyCost(params);
        return vacancyCost * (1 - params.retention / 100);
    }

    calculateTotalCost(params) {
        return this.calculateVacancyCost(params) + 
               this.calculateQualityCost(params) + 
               this.calculateRetentionCost(params);
    }

    calculateROI(params) {
        const totalCost = this.calculateTotalCost(params);
        const serviceCost = this.getServiceCost();
        return ((totalCost - serviceCost) / serviceCost) * 100;
    }

    calculatePaybackPeriod(params) {
        const totalCost = this.calculateTotalCost(params);
        const serviceCost = this.getServiceCost();
        return serviceCost / (totalCost / 12);
    }

    generateROIPDF(data) {
        // Crear contenido HTML para PDF
        const htmlContent = `
            <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .header { text-align: center; margin-bottom: 30px; }
                        .section { margin-bottom: 20px; }
                        .metric { display: flex; justify-content: space-between; margin: 5px 0; }
                        .highlight { background-color: #f0f8ff; padding: 10px; border-radius: 5px; }
                        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        th { background-color: #f2f2f2; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Análisis de ROI - Grupo huntRED®</h1>
                        <p>Generado el: ${new Date().toLocaleDateString()}</p>
                    </div>
                    
                    <div class="section">
                        <h2>Parámetros del Cálculo</h2>
                        <table>
                            <tr><th>Parámetro</th><th>Valor</th></tr>
                            <tr><td>Salario Promedio</td><td>$${data.parameters.salary.toLocaleString()}</td></tr>
                            <tr><td>Tiempo de Vacante</td><td>${data.parameters.time} días</td></tr>
                            <tr><td>Productividad Perdida</td><td>${data.parameters.productivity}%</td></tr>
                            <tr><td>Calidad de Contratación</td><td>${data.parameters.quality}%</td></tr>
                            <tr><td>Tasa de Retención</td><td>${data.parameters.retention}%</td></tr>
                            <tr><td>Industria</td><td>${data.parameters.industry}</td></tr>
                        </table>
                    </div>
                    
                    <div class="section">
                        <h2>Resultados del Análisis</h2>
                        <div class="highlight">
                            <div class="metric"><strong>ROI:</strong> ${data.results.roi.toFixed(0)}%</div>
                            <div class="metric"><strong>Período de Recuperación:</strong> ${data.results.paybackPeriod.toFixed(1)} meses</div>
                        </div>
                        <table>
                            <tr><th>Concepto</th><th>Costo</th></tr>
                            <tr><td>Costo de Vacante</td><td>$${data.results.vacancyCost.toLocaleString()}</td></tr>
                            <tr><td>Costo de Calidad</td><td>$${data.results.qualityCost.toLocaleString()}</td></tr>
                            <tr><td>Costo de Retención</td><td>$${data.results.retentionCost.toLocaleString()}</td></tr>
                            <tr><td><strong>Costo Total</strong></td><td><strong>$${data.results.totalCost.toLocaleString()}</strong></td></tr>
                            <tr><td>Nuestro Servicio</td><td>$${data.results.serviceCost.toLocaleString()}</td></tr>
                        </table>
                    </div>
                    
                    <div class="section">
                        <h2>Insights Inteligentes</h2>
                        ${data.insights.map(insight => `<p>• ${insight}</p>`).join('')}
                    </div>
                </body>
            </html>
        `;

        // Usar jsPDF para generar PDF
        if (typeof jsPDF !== 'undefined') {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            
            doc.html(htmlContent, {
                callback: function (doc) {
                    doc.save('analisis-roi-huntred.pdf');
                },
                x: 10,
                y: 10
            });
        }
    }

    generateROIExcel(data) {
        // Crear datos para Excel
        const excelData = [
            ['Análisis de ROI - Grupo huntRED®'],
            [''],
            ['Parámetros del Cálculo'],
            ['Parámetro', 'Valor'],
            ['Salario Promedio', `$${data.parameters.salary.toLocaleString()}`],
            ['Tiempo de Vacante', `${data.parameters.time} días`],
            ['Productividad Perdida', `${data.parameters.productivity}%`],
            ['Calidad de Contratación', `${data.parameters.quality}%`],
            ['Tasa de Retención', `${data.parameters.retention}%`],
            ['Industria', data.parameters.industry],
            [''],
            ['Resultados del Análisis'],
            ['Concepto', 'Costo'],
            ['Costo de Vacante', `$${data.results.vacancyCost.toLocaleString()}`],
            ['Costo de Calidad', `$${data.results.qualityCost.toLocaleString()}`],
            ['Costo de Retención', `$${data.results.retentionCost.toLocaleString()}`],
            ['Costo Total', `$${data.results.totalCost.toLocaleString()}`],
            ['Nuestro Servicio', `$${data.results.serviceCost.toLocaleString()}`],
            ['ROI', `${data.results.roi.toFixed(0)}%`],
            ['Período de Recuperación', `${data.results.paybackPeriod.toFixed(1)} meses`]
        ];

        // Usar SheetJS para generar Excel
        if (typeof XLSX !== 'undefined') {
            const ws = XLSX.utils.aoa_to_sheet(excelData);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, 'Análisis ROI');
            XLSX.writeFile(wb, 'analisis-roi-huntred.xlsx');
        }
    }

    setupScenarioComparison() {
        // Crear comparador de escenarios
        const comparisonContainer = document.createElement('div');
        comparisonContainer.id = 'scenarioComparison';
        comparisonContainer.className = 'mt-6 bg-white p-4 rounded-lg border border-gray-200';
        comparisonContainer.innerHTML = `
            <h4 class="font-semibold text-gray-800 mb-3">
                <i class="fas fa-balance-scale text-purple-500 mr-2"></i>
                Comparador de Escenarios
            </h4>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="text-center">
                    <h5 class="font-medium text-gray-700 mb-2">Escenario Actual</h5>
                    <div id="currentScenario" class="bg-blue-50 p-3 rounded-lg">
                        <div class="text-lg font-bold text-blue-600" id="currentROI">212%</div>
                        <div class="text-sm text-gray-600">ROI</div>
                    </div>
                </div>
                <div class="text-center">
                    <h5 class="font-medium text-gray-700 mb-2">Escenario Optimista</h5>
                    <div id="optimisticScenario" class="bg-green-50 p-3 rounded-lg">
                        <div class="text-lg font-bold text-green-600" id="optimisticROI">--</div>
                        <div class="text-sm text-gray-600">ROI</div>
                    </div>
                </div>
                <div class="text-center">
                    <h5 class="font-medium text-gray-700 mb-2">Escenario Pesimista</h5>
                    <div id="pessimisticScenario" class="bg-red-50 p-3 rounded-lg">
                        <div class="text-lg font-bold text-red-600" id="pessimisticROI">--</div>
                        <div class="text-sm text-gray-600">ROI</div>
                    </div>
                </div>
            </div>
        `;

        // Insertar después de la calculadora principal
        const calculator = document.querySelector('.bg-gradient-to-br.from-blue-50');
        if (calculator) {
            calculator.parentNode.insertBefore(comparisonContainer, calculator.nextSibling);
        }

        // Actualizar escenarios
        this.updateScenarios();
    }

    updateScenarios() {
        const currentParams = this.getCurrentROIData().parameters;
        
        // Escenario optimista
        const optimisticParams = {
            ...currentParams,
            time: Math.max(15, currentParams.time * 0.6),
            productivity: Math.min(50, currentParams.productivity * 1.2),
            quality: Math.min(95, currentParams.quality + 5),
            retention: Math.min(95, currentParams.retention + 5)
        };
        
        // Escenario pesimista
        const pessimisticParams = {
            ...currentParams,
            time: Math.min(120, currentParams.time * 1.4),
            productivity: Math.max(10, currentParams.productivity * 0.8),
            quality: Math.max(60, currentParams.quality - 10),
            retention: Math.max(50, currentParams.retention - 10)
        };

        const optimisticROI = this.calculateROI(optimisticParams);
        const pessimisticROI = this.calculateROI(pessimisticParams);

        const optimisticEl = document.getElementById('optimisticROI');
        const pessimisticEl = document.getElementById('pessimisticROI');

        if (optimisticEl) optimisticEl.textContent = `${optimisticROI.toFixed(0)}%`;
        if (pessimisticEl) pessimisticEl.textContent = `${pessimisticROI.toFixed(0)}%`;
    }

    setupCalculationHistory() {
        // Crear historial de cálculos
        const historyContainer = document.createElement('div');
        historyContainer.id = 'calculationHistory';
        historyContainer.className = 'mt-6 bg-white p-4 rounded-lg border border-gray-200';
        historyContainer.innerHTML = `
            <h4 class="font-semibold text-gray-800 mb-3">
                <i class="fas fa-history text-gray-500 mr-2"></i>
                Historial de Cálculos
            </h4>
            <div id="historyList" class="space-y-2 max-h-40 overflow-y-auto">
                <!-- Los cálculos se agregarán aquí -->
            </div>
        `;

        // Insertar después del comparador de escenarios
        const comparison = document.getElementById('scenarioComparison');
        if (comparison) {
            comparison.parentNode.insertBefore(historyContainer, comparison.nextSibling);
        }

        // Inicializar historial
        this.calculationHistory = JSON.parse(localStorage.getItem('roiCalculationHistory') || '[]');
        this.updateHistoryDisplay();
    }

    addToHistory(data) {
        const historyEntry = {
            id: Date.now(),
            timestamp: new Date().toISOString(),
            data: data
        };

        this.calculationHistory.unshift(historyEntry);
        
        // Mantener solo los últimos 10 cálculos
        if (this.calculationHistory.length > 10) {
            this.calculationHistory = this.calculationHistory.slice(0, 10);
        }

        localStorage.setItem('roiCalculationHistory', JSON.stringify(this.calculationHistory));
        this.updateHistoryDisplay();
    }

    updateHistoryDisplay() {
        const historyList = document.getElementById('historyList');
        if (!historyList) return;

        historyList.innerHTML = this.calculationHistory.map(entry => `
            <div class="flex justify-between items-center p-2 bg-gray-50 rounded hover:bg-gray-100 cursor-pointer" 
                 onclick="proposalEnhancements.loadHistoryEntry(${entry.id})">
                <div>
                    <div class="text-sm font-medium">ROI: ${entry.data.results.roi.toFixed(0)}%</div>
                    <div class="text-xs text-gray-500">${new Date(entry.timestamp).toLocaleString()}</div>
                </div>
                <button onclick="event.stopPropagation(); proposalEnhancements.deleteHistoryEntry(${entry.id})" 
                        class="text-red-500 hover:text-red-700">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
    }

    loadHistoryEntry(id) {
        const entry = this.calculationHistory.find(e => e.id === id);
        if (!entry) return;

        // Restaurar valores
        Object.keys(entry.data.parameters).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                element.value = entry.data.parameters[key];
                const valueElement = document.getElementById(key.replace('Slider', 'Value'));
                if (valueElement) {
                    valueElement.textContent = this.formatSliderValue(key, entry.data.parameters[key]);
                }
            }
        });

        this.updateROICalculation();
        this.updateROIChart();
        this.updateROIInsights();
        this.updateScenarios();
        
        this.showToast('Cálculo restaurado del historial', 'info');
    }

    deleteHistoryEntry(id) {
        this.calculationHistory = this.calculationHistory.filter(e => e.id !== id);
        localStorage.setItem('roiCalculationHistory', JSON.stringify(this.calculationHistory));
        this.updateHistoryDisplay();
        this.showToast('Entrada eliminada del historial', 'info');
    }

    setupRealTimeSync() {
        // Sincronizar con cambios en la propuesta
        const observer = new MutationObserver(() => {
            this.syncROIData();
            this.updateROICalculation();
        });

        // Observar cambios en elementos de la propuesta
        const proposalElements = document.querySelectorAll('[data-salary], [data-industry], [data-level]');
        proposalElements.forEach(element => {
            observer.observe(element, { attributes: true, subtree: true });
        });
    }

    setupAdvancedExport() {
        // Agregar botones de exportación avanzada
        const exportButtons = document.querySelectorAll('[id*="Export"]');
        exportButtons.forEach(button => {
            button.addEventListener('click', () => {
                const data = this.getCurrentROIData();
                this.addToHistory(data);
                this.exportROIData();
            });
        });
    }

    getClientInfo() {
        // Obtener información del cliente de la propuesta
        const clientName = document.querySelector('[data-client-name]')?.dataset.clientName || 'Cliente';
        const clientIndustry = document.querySelector('[data-industry]')?.dataset.industry || 'General';
        
        return {
            name: clientName,
            industry: clientIndustry,
            date: new Date().toLocaleDateString()
        };
    }

    getProposalInfo() {
        // Obtener información de la propuesta
        const proposalId = document.querySelector('[data-proposal-id]')?.dataset.proposalId || 'N/A';
        const proposalTotal = document.querySelector('[data-total]')?.dataset.total || 'N/A';
        
        return {
            id: proposalId,
            total: proposalTotal,
            generated: new Date().toISOString()
        };
    }

    addROIHistoryTracking() {
        // Agregar tracking automático de cambios en ROI
        const roiElements = document.querySelectorAll('#salarySlider, #timeSlider, #productivitySlider, #qualitySlider, #retentionSlider, #industrySelect, #positionLevelSelect, #urgencySelect');
        
        let debounceTimer;
        roiElements.forEach(element => {
            element.addEventListener('change', () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    const data = this.getCurrentROIData();
                    this.addToHistory(data);
                    this.updateScenarios();
                }, 2000); // Esperar 2 segundos después del último cambio
            });
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.proposalEnhancements = new ProposalEnhancements();
    
    // Cargar Chart.js si no está disponible
    if (typeof Chart === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        script.onload = () => {
            window.proposalEnhancements.setupCharts();
        };
        document.head.appendChild(script);
    }
});

// Exportar para uso global
window.ProposalEnhancements = ProposalEnhancements;
