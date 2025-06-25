/**
 * SUPER ADMIN DASHBOARD - BRUCE ALMIGHTY MODE 🚀
 * JavaScript para funcionalidades interactivas del Super Admin Dashboard
 */

class SuperAdminDashboard {
    constructor() {
        this.currentTab = 'overview';
        this.updateInterval = null;
        this.charts = {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.startRealTimeUpdates();
        this.setupAnimations();
        console.log('🚀 Bruce Almighty Mode - Super Admin Dashboard inicializado');
    }

    setupEventListeners() {
        // Navegación por pestañas
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                this.currentTab = e.target.getAttribute('href').substring(1);
                this.loadTabData(this.currentTab);
                this.animateTabContent();
            });
        });

        // Botones de acción
        document.querySelectorAll('.btn-bruce').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleBruceAction(e);
            });
        });

        // Formularios
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                this.handleFormSubmit(e);
            });
        });

        // Modales
        document.querySelectorAll('[data-bs-toggle="modal"]').forEach(modal => {
            modal.addEventListener('show.bs.modal', (e) => {
                this.handleModalShow(e);
            });
        });
    }

    initializeCharts() {
        // Inicializar gráficos si existen
        const chartElements = document.querySelectorAll('canvas');
        chartElements.forEach(canvas => {
            this.createChart(canvas);
        });
    }

    createChart(canvas) {
        const ctx = canvas.getContext('2d');
        const chartId = canvas.id;

        // Configuración base para todos los gráficos
        const baseConfig = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: 'white',
                        font: {
                            size: 12
                        }
                    }
                }
            },
            scales: {
                y: {
                    ticks: {
                        color: 'white',
                        font: {
                            size: 11
                        }
                    },
                    grid: {
                        color: 'rgba(255,255,255,0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: 'white',
                        font: {
                            size: 11
                        }
                    },
                    grid: {
                        color: 'rgba(255,255,255,0.1)'
                    }
                }
            }
        };

        // Crear gráfico según el tipo
        switch(chartId) {
            case 'systemHealthChart':
                this.charts[chartId] = this.createSystemHealthChart(ctx, baseConfig);
                break;
            case 'performanceChart':
                this.charts[chartId] = this.createPerformanceChart(ctx, baseConfig);
                break;
            case 'trendChart':
                this.charts[chartId] = this.createTrendChart(ctx, baseConfig);
                break;
            default:
                console.log(`Gráfico no configurado: ${chartId}`);
        }
    }

    createSystemHealthChart(ctx, config) {
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['AURA', 'GenIA', 'ML', 'Database', 'API'],
                datasets: [{
                    data: [95, 87, 92, 98, 94],
                    backgroundColor: [
                        '#28a745',
                        '#17a2b8',
                        '#ffc107',
                        '#6f42c1',
                        '#fd7e14'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                ...config,
                cutout: '70%',
                plugins: {
                    ...config.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.parsed}%`;
                            }
                        }
                    }
                }
            }
        });
    }

    createPerformanceChart(ctx, config) {
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                datasets: [{
                    label: 'Rendimiento del Sistema',
                    data: [85, 82, 88, 95, 92, 89],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                ...config,
                plugins: {
                    ...config.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Rendimiento: ${context.parsed.y}%`;
                            }
                        }
                    }
                }
            }
        });
    }

    createTrendChart(ctx, config) {
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
                datasets: [{
                    label: 'Candidatos',
                    data: [120, 135, 142, 158, 165, 180],
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderRadius: 5
                }]
            },
            options: {
                ...config,
                plugins: {
                    ...config.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Candidatos: ${context.parsed.y}`;
                            }
                        }
                    }
                }
            }
        });
    }

    loadTabData(tabId) {
        console.log(`Cargando datos para pestaña: ${tabId}`);
        
        // Simular carga de datos
        this.showLoading(tabId);
        
        setTimeout(() => {
            this.hideLoading(tabId);
            this.updateTabContent(tabId);
        }, 1000);
    }

    showLoading(tabId) {
        const tabContent = document.querySelector(`#${tabId}`);
        if (tabContent) {
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading-overlay';
            loadingDiv.innerHTML = `
                <div class="spinner-border text-light" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-2 text-light">Cargando datos de ${tabId}...</p>
            `;
            tabContent.appendChild(loadingDiv);
        }
    }

    hideLoading(tabId) {
        const loadingDiv = document.querySelector(`#${tabId} .loading-overlay`);
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    updateTabContent(tabId) {
        // Actualizar contenido según la pestaña
        switch(tabId) {
            case 'overview':
                this.updateOverviewData();
                break;
            case 'consultants':
                this.updateConsultantsData();
                break;
            case 'clients':
                this.updateClientsData();
                break;
            case 'candidates':
                this.updateCandidatesData();
                break;
            case 'business-units':
                this.updateBusinessUnitsData();
                break;
            case 'proposals':
                this.updateProposalsData();
                break;
            case 'opportunities':
                this.updateOpportunitiesData();
                break;
            case 'process-management':
                this.updateProcessManagementData();
                break;
            case 'aura':
                this.updateAuraData();
                break;
            case 'genia':
                this.updateGeniaData();
                break;
            case 'scraping':
                this.updateScrapingData();
                break;
            case 'sexsi':
                this.updateSexsiData();
                break;
            case 'gpt-jd':
                this.updateGptJdData();
                break;
            case 'salary-comparator':
                this.updateSalaryComparatorData();
                break;
        }
    }

    updateOverviewData() {
        // Actualizar métricas del overview
        this.animateMetrics();
        this.updateSystemHealth();
    }

    updateConsultantsData() {
        // Cargar datos de consultores
        this.loadConsultantsData();
    }

    updateClientsData() {
        // Cargar datos de clientes
        this.loadClientsData();
    }

    updateCandidatesData() {
        // Cargar datos de candidatos
        this.loadCandidatesData();
    }

    updateBusinessUnitsData() {
        // Cargar datos de unidades de negocio
        this.loadBusinessUnitsData();
    }

    updateProposalsData() {
        // Cargar datos de propuestas
        this.loadProposalsData();
    }

    updateOpportunitiesData() {
        // Cargar datos de oportunidades
        this.loadOpportunitiesData();
    }

    updateProcessManagementData() {
        // Cargar datos de gestión de procesos
        this.loadProcessManagementData();
    }

    updateAuraData() {
        // Cargar datos de AURA
        this.loadAuraData();
    }

    updateGeniaData() {
        // Cargar datos de GenIA
        this.loadGeniaData();
    }

    updateScrapingData() {
        // Cargar datos de scraping
        this.loadScrapingData();
    }

    updateSexsiData() {
        // Cargar datos de SEXSI
        this.loadSexsiData();
    }

    updateGptJdData() {
        // Cargar datos del generador GPT
        this.loadGptJdData();
    }

    updateSalaryComparatorData() {
        // Cargar datos del comparador de salarios
        this.loadSalaryComparatorData();
    }

    // Funciones de carga de datos específicas
    async loadConsultantsData() {
        try {
            const response = await fetch('/dashboard/api/super-admin/consultants/');
            const data = await response.json();
            if (data.success) {
                this.renderConsultantsData(data.data);
            }
        } catch (error) {
            console.error('Error cargando datos de consultores:', error);
        }
    }

    async loadClientsData() {
        try {
            const response = await fetch('/dashboard/api/super-admin/clients/');
            const data = await response.json();
            if (data.success) {
                this.renderClientsData(data.data);
            }
        } catch (error) {
            console.error('Error cargando datos de clientes:', error);
        }
    }

    async loadCandidatesData() {
        try {
            const response = await fetch('/dashboard/api/super-admin/candidates/');
            const data = await response.json();
            if (data.success) {
                this.renderCandidatesData(data.data);
            }
        } catch (error) {
            console.error('Error cargando datos de candidatos:', error);
        }
    }

    async loadBusinessUnitsData() {
        try {
            const response = await fetch('/dashboard/api/super-admin/business-units/');
            const data = await response.json();
            if (data.success) {
                this.renderBusinessUnitsData(data.data);
            }
        } catch (error) {
            console.error('Error cargando datos de unidades de negocio:', error);
        }
    }

    async loadProposalsData() {
        try {
            const response = await fetch('/dashboard/api/super-admin/proposals/');
            const data = await response.json();
            if (data.success) {
                this.renderProposalsData(data.data);
            }
        } catch (error) {
            console.error('Error cargando datos de propuestas:', error);
        }
    }

    async loadOpportunitiesData() {
        try {
            const response = await fetch('/dashboard/api/super-admin/opportunities/');
            const data = await response.json();
            if (data.success) {
                this.renderOpportunitiesData(data.data);
            }
        } catch (error) {
            console.error('Error cargando datos de oportunidades:', error);
        }
    }

    async loadProcessManagementData() {
        try {
            const response = await fetch('/dashboard/api/super-admin/process-management/');
            const data = await response.json();
            if (data.success) {
                this.renderProcessManagementData(data.data);
            }
        } catch (error) {
            console.error('Error cargando datos de gestión de procesos:', error);
        }
    }

    async loadAuraData() {
        try {
            const response = await fetch('/dashboard/api/super-admin/aura/');
            const data = await response.json();
            if (data.success) {
                this.renderAuraData(data.data);
            }
        } catch (error) {
            console.error('Error cargando datos de AURA:', error);
        }
    }

    async loadGeniaData() {
        try {
            const response = await fetch('/dashboard/api/super-admin/genia/');
            const data = await response.json();
            if (data.success) {
                this.renderGeniaData(data.data);
            }
        } catch (error) {
            console.error('Error cargando datos de GenIA:', error);
        }
    }

    async loadScrapingData() {
        try {
            const response = await fetch('/dashboard/api/super-admin/scraping/');
            const data = await response.json();
            if (data.success) {
                this.renderScrapingData(data.data);
            }
        } catch (error) {
            console.error('Error cargando datos de scraping:', error);
        }
    }

    async loadSexsiData() {
        try {
            const response = await fetch('/dashboard/api/super-admin/sexsi/');
            const data = await response.json();
            if (data.success) {
                this.renderSexsiData(data.data);
            }
        } catch (error) {
            console.error('Error cargando datos de SEXSI:', error);
        }
    }

    async loadGptJdData() {
        try {
            const response = await fetch('/dashboard/api/super-admin/gpt-jd/');
            const data = await response.json();
            if (data.success) {
                this.renderGptJdData(data.data);
            }
        } catch (error) {
            console.error('Error cargando datos del generador GPT:', error);
        }
    }

    async loadSalaryComparatorData() {
        try {
            const response = await fetch('/dashboard/api/super-admin/salary-comparator/');
            const data = await response.json();
            if (data.success) {
                this.renderSalaryComparatorData(data.data);
            }
        } catch (error) {
            console.error('Error cargando datos del comparador de salarios:', error);
        }
    }

    // Funciones de renderizado
    renderConsultantsData(data) {
        const container = document.getElementById('consultantsData');
        if (container) {
            container.innerHTML = this.generateConsultantsHTML(data);
        }
    }

    renderClientsData(data) {
        const container = document.getElementById('clientsData');
        if (container) {
            container.innerHTML = this.generateClientsHTML(data);
        }
    }

    renderCandidatesData(data) {
        const container = document.getElementById('candidatesData');
        if (container) {
            container.innerHTML = this.generateCandidatesHTML(data);
        }
    }

    renderBusinessUnitsData(data) {
        const container = document.getElementById('businessUnitsData');
        if (container) {
            container.innerHTML = this.generateBusinessUnitsHTML(data);
        }
    }

    renderProposalsData(data) {
        const container = document.getElementById('proposalsData');
        if (container) {
            container.innerHTML = this.generateProposalsHTML(data);
        }
    }

    renderOpportunitiesData(data) {
        const container = document.getElementById('opportunitiesData');
        if (container) {
            container.innerHTML = this.generateOpportunitiesHTML(data);
        }
    }

    renderProcessManagementData(data) {
        const container = document.getElementById('processManagementData');
        if (container) {
            container.innerHTML = this.generateProcessManagementHTML(data);
        }
    }

    renderAuraData(data) {
        const container = document.getElementById('auraData');
        if (container) {
            container.innerHTML = this.generateAuraHTML(data);
        }
    }

    renderGeniaData(data) {
        const container = document.getElementById('geniaData');
        if (container) {
            container.innerHTML = this.generateGeniaHTML(data);
        }
    }

    renderScrapingData(data) {
        const container = document.getElementById('scrapingData');
        if (container) {
            container.innerHTML = this.generateScrapingHTML(data);
        }
    }

    renderSexsiData(data) {
        const container = document.getElementById('sexsiData');
        if (container) {
            container.innerHTML = this.generateSexsiHTML(data);
        }
    }

    renderGptJdData(data) {
        const container = document.getElementById('gptJdData');
        if (container) {
            container.innerHTML = this.generateGptJdHTML(data);
        }
    }

    renderSalaryComparatorData(data) {
        const container = document.getElementById('salaryComparatorData');
        if (container) {
            container.innerHTML = this.generateSalaryComparatorHTML(data);
        }
    }

    // Generadores de HTML
    generateConsultantsHTML(data) {
        return `
            <div class="row">
                <div class="col-md-12">
                    <h5>Consultores Activos: ${data.consultants.length}</h5>
                    <div class="list-group">
                        ${data.consultants.map(consultant => `
                            <div class="list-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6>${consultant.name}</h6>
                                        <small>${consultant.business_unit}</small>
                                    </div>
                                    <div class="text-end">
                                        <div class="badge bg-success">${consultant.performance.score}%</div>
                                        <br>
                                        <small>${consultant.recent_activity}</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    generateClientsHTML(data) {
        return `
            <div class="row">
                <div class="col-md-12">
                    <h5>Clientes Activos: ${data.clients.length}</h5>
                    <div class="list-group">
                        ${data.clients.map(client => `
                            <div class="list-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6>${client.name}</h6>
                                        <small>${client.business_unit}</small>
                                    </div>
                                    <div class="text-end">
                                        <div class="badge bg-primary">$${client.metrics.revenue_generated.toLocaleString()}</div>
                                        <br>
                                        <small>${client.metrics.total_vacancies} vacantes</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    generateCandidatesHTML(data) {
        return `
            <div class="row">
                <div class="col-md-12">
                    <h5>Candidatos Totales: ${data.candidates.length}</h5>
                    <div class="list-group">
                        ${data.candidates.slice(0, 10).map(candidate => `
                            <div class="list-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6>${candidate.name}</h6>
                                        <small>${candidate.current_state}</small>
                                    </div>
                                    <div class="text-end">
                                        <div class="badge bg-info">${candidate.aura_score}</div>
                                        <br>
                                        <small>${candidate.last_activity}</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    generateBusinessUnitsHTML(data) {
        return `
            <div class="row">
                <div class="col-md-12">
                    <h5>Unidades de Negocio: ${data.business_units.length}</h5>
                    <div class="list-group">
                        ${data.business_units.map(bu => `
                            <div class="list-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6>${bu.name}</h6>
                                        <small>${bu.description}</small>
                                    </div>
                                    <div class="text-end">
                                        <div class="badge bg-success">${bu.health_score}%</div>
                                        <br>
                                        <small>${bu.metrics.active_vacancies} vacantes activas</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    generateProposalsHTML(data) {
        return `
            <div class="row">
                <div class="col-md-12">
                    <h5>Propuestas Recientes: ${data.recent_proposals.length}</h5>
                    <div class="list-group">
                        ${data.recent_proposals.slice(0, 10).map(proposal => `
                            <div class="list-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6>${proposal.candidate}</h6>
                                        <small>${proposal.vacancy}</small>
                                    </div>
                                    <div class="text-end">
                                        <div class="badge bg-primary">$${proposal.salary.toLocaleString()}</div>
                                        <br>
                                        <small>${proposal.status}</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    generateOpportunitiesHTML(data) {
        return `
            <div class="row">
                <div class="col-md-12">
                    <h5>Oportunidades Activas: ${data.active_opportunities.length}</h5>
                    <div class="list-group">
                        ${data.active_opportunities.map(opportunity => `
                            <div class="list-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6>${opportunity.title}</h6>
                                        <small>${opportunity.client}</small>
                                    </div>
                                    <div class="text-end">
                                        <div class="badge bg-warning">${opportunity.probability}%</div>
                                        <br>
                                        <small>$${opportunity.value.toLocaleString()}</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    generateProcessManagementHTML(data) {
        return `
            <div class="row">
                <div class="col-md-12">
                    <h5>Procesos Activos: ${data.active_processes.length}</h5>
                    <div class="list-group">
                        ${data.active_processes.map(process => `
                            <div class="list-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6>${process.name}</h6>
                                        <small>${process.stage}</small>
                                    </div>
                                    <div class="text-end">
                                        <div class="badge bg-info">${process.candidates} candidatos</div>
                                        <br>
                                        <small>${process.progress}% completado</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    generateAuraHTML(data) {
        return `
            <div class="row">
                <div class="col-md-12">
                    <h5>Estado de AURA</h5>
                    <div class="metric-card">
                        <div class="metric-value">${data.aura_score_avg}%</div>
                        <div class="metric-label">Score Promedio</div>
                    </div>
                    <div class="list-group">
                        ${data.insights.map(insight => `
                            <div class="list-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6>${insight.title}</h6>
                                        <small>${insight.description}</small>
                                    </div>
                                    <div class="text-end">
                                        <div class="badge bg-success">${insight.confidence}%</div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    generateGeniaHTML(data) {
        return `
            <div class="row">
                <div class="col-md-12">
                    <h5>Estado de GenIA</h5>
                    <div class="metric-card">
                        <div class="metric-value">${data.genia_usage}%</div>
                        <div class="metric-label">Uso del Sistema</div>
                    </div>
                    <div class="list-group">
                        ${data.predictions.map(prediction => `
                            <div class="list-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6>${prediction.title}</h6>
                                        <small>${prediction.description}</small>
                                    </div>
                                    <div class="text-end">
                                        <div class="badge bg-info">${prediction.accuracy}%</div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    generateScrapingHTML(data) {
        return `
            <div class="row">
                <div class="col-md-12">
                    <h5>Estado del Scraping</h5>
                    <div class="metric-card">
                        <div class="metric-value">${data.scraping_status.success_rate}%</div>
                        <div class="metric-label">Tasa de Éxito</div>
                    </div>
                    <div class="list-group">
                        ${data.data_sources.map(source => `
                            <div class="list-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6>${source.name}</h6>
                                        <small>${source.status}</small>
                                    </div>
                                    <div class="text-end">
                                        <div class="badge bg-success">${source.success_rate}%</div>
                                        <br>
                                        <small>${source.records_scraped} registros</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    generateSexsiHTML(data) {
        return `
            <div class="row">
                <div class="col-md-12">
                    <h5>Estado de SEXSI</h5>
                    <div class="metric-card">
                        <div class="metric-value">${data.sexsi_status.sync_success_rate}%</div>
                        <div class="metric-label">Tasa de Sincronización</div>
                    </div>
                    <div class="list-group">
                        ${data.sexsi_integrations.map(integration => `
                            <div class="list-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6>${integration.name}</h6>
                                        <small>${integration.status}</small>
                                    </div>
                                    <div class="text-end">
                                        <div class="badge bg-success">${integration.records_synced}</div>
                                        <br>
                                        <small>Última sincronización</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    generateGptJdHTML(data) {
        return `
            <div class="row">
                <div class="col-md-12">
                    <h5>Generador de JD con GPT</h5>
                    <div class="metric-card">
                        <div class="metric-value">${data.usage_stats.total_generated}</div>
                        <div class="metric-label">JDs Generadas</div>
                    </div>
                    <div class="list-group">
                        ${data.generated_examples.map(example => `
                            <div class="list-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6>${example.role}</h6>
                                        <small>Template: ${example.template_used}</small>
                                    </div>
                                    <div class="text-end">
                                        <div class="badge bg-warning">${example.user_rating}/5</div>
                                        <br>
                                        <small>${example.generated_at}</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    generateSalaryComparatorHTML(data) {
        return `
            <div class="row">
                <div class="col-md-12">
                    <h5>Comparador de Salarios</h5>
                    <div class="metric-card">
                        <div class="metric-value">$${data.market_data.market_averages.developer.toLocaleString()}</div>
                        <div class="metric-label">Salario Promedio Developer</div>
                    </div>
                    <div class="list-group">
                        ${Object.entries(data.market_data.market_averages).map(([role, salary]) => `
                            <div class="list-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6>${role.charAt(0).toUpperCase() + role.slice(1)}</h6>
                                        <small>Salario de mercado</small>
                                    </div>
                                    <div class="text-end">
                                        <div class="badge bg-primary">$${salary.toLocaleString()}</div>
                                        <br>
                                        <small>Promedio anual</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    animateTabContent() {
        const activeTab = document.querySelector('.tab-pane.active');
        if (activeTab) {
            activeTab.classList.add('fade-in');
            setTimeout(() => {
                activeTab.classList.remove('fade-in');
            }, 500);
        }
    }

    animateMetrics() {
        const metrics = document.querySelectorAll('.metric-value');
        metrics.forEach(metric => {
            const value = metric.textContent;
            if (value.includes('$') || value.includes('%')) {
                this.animateValue(metric, 0, parseFloat(value.replace(/[$,%]/g, '')), 2000);
            }
        });
    }

    animateValue(element, start, end, duration) {
        const startTime = performance.now();
        const startValue = start;
        const endValue = end;
        
        function updateValue(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const currentValue = startValue + (endValue - startValue) * progress;
            
            if (element.textContent.includes('$')) {
                element.textContent = '$' + Math.floor(currentValue).toLocaleString();
            } else if (element.textContent.includes('%')) {
                element.textContent = currentValue.toFixed(1) + '%';
            } else {
                element.textContent = Math.floor(currentValue);
            }
            
            if (progress < 1) {
                requestAnimationFrame(updateValue);
            }
        }
        
        requestAnimationFrame(updateValue);
    }

    updateSystemHealth() {
        // Actualizar indicadores de salud del sistema
        const healthIndicators = document.querySelectorAll('.status-indicator');
        healthIndicators.forEach(indicator => {
            const randomHealth = Math.random() * 100;
            if (randomHealth > 80) {
                indicator.className = 'status-indicator status-healthy';
            } else if (randomHealth > 60) {
                indicator.className = 'status-indicator status-warning';
            } else {
                indicator.className = 'status-indicator status-critical';
            }
        });
    }

    startRealTimeUpdates() {
        this.updateInterval = setInterval(() => {
            this.updateRealTimeData();
        }, 30000); // Cada 30 segundos
    }

    updateRealTimeData() {
        // Actualizar datos en tiempo real
        this.updateSystemHealth();
        this.updateRealTimeUpdates();
    }

    updateRealTimeUpdates() {
        const updatesContainer = document.getElementById('realTimeUpdates');
        if (updatesContainer) {
            const newUpdate = document.createElement('div');
            newUpdate.className = 'update-item';
            newUpdate.innerHTML = `
                <span>Sistema funcionando perfectamente</span>
                <span class="update-time">Ahora</span>
            `;
            updatesContainer.insertBefore(newUpdate, updatesContainer.firstChild);
            
            // Mantener solo los últimos 5 updates
            if (updatesContainer.children.length > 5) {
                updatesContainer.removeChild(updatesContainer.lastChild);
            }
        }
    }

    setupAnimations() {
        // Configurar animaciones CSS
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, observerOptions);

        // Observar elementos para animación
        document.querySelectorAll('.metric-card, .list-item, .super-admin-card').forEach(el => {
            observer.observe(el);
        });
    }

    handleBruceAction(event) {
        const action = event.target.getAttribute('data-action');
        console.log(`Bruce Almighty Action: ${action}`);
        
        switch(action) {
            case 'send-message':
                this.showSendMessageModal();
                break;
            case 'control-aura':
                this.showAuraControlModal();
                break;
            case 'control-genia':
                this.showGeniaControlModal();
                break;
            case 'emergency':
                this.showEmergencyModal();
                break;
        }
    }

    handleFormSubmit(event) {
        const form = event.target;
        const formData = new FormData(form);
        
        // Mostrar loading
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';
        }
        
        // Simular envío
        setTimeout(() => {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Enviar';
            }
            this.showSuccessMessage('Acción ejecutada exitosamente');
        }, 2000);
    }

    handleModalShow(event) {
        const modal = event.target;
        modal.classList.add('scale-in');
    }

    showSendMessageModal() {
        const modal = new bootstrap.Modal(document.getElementById('sendMessageModal'));
        modal.show();
    }

    showAuraControlModal() {
        const modal = new bootstrap.Modal(document.getElementById('auraControlModal'));
        modal.show();
    }

    showGeniaControlModal() {
        const modal = new bootstrap.Modal(document.getElementById('geniaControlModal'));
        modal.show();
    }

    showEmergencyModal() {
        const modal = new bootstrap.Modal(document.getElementById('emergencyActionsModal'));
        modal.show();
    }

    showSuccessMessage(message) {
        // Crear notificación de éxito
        const notification = document.createElement('div');
        notification.className = 'alert alert-success alert-dismissible fade show position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Remover después de 5 segundos
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    showErrorMessage(message) {
        // Crear notificación de error
        const notification = document.createElement('div');
        notification.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Remover después de 5 segundos
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    destroy() {
        // Limpiar intervalos y event listeners
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        // Destruir gráficos
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });
        
        console.log('Super Admin Dashboard destruido');
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.superAdminDashboard = new SuperAdminDashboard();
});

// Limpiar al salir de la página
window.addEventListener('beforeunload', function() {
    if (window.superAdminDashboard) {
        window.superAdminDashboard.destroy();
    }
});

// Exportar para uso global
window.SuperAdminDashboard = SuperAdminDashboard;

// Buscador Inteligente Avanzado
function initializeIntelligentSearch() {
    const searchForm = document.getElementById('intelligent-search-form');
    const searchTypeBtns = document.querySelectorAll('.search-type-btn');
    const searchTypeInput = document.getElementById('search_type');
    const loadingSpinner = document.getElementById('loading-spinner');
    const searchInput = document.querySelector('.search-input');
    
    if (!searchForm) return;
    
    // Search type selector
    searchTypeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            searchTypeBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            searchTypeInput.value = this.dataset.type;
        });
    });

    // Form submission with loading
    searchForm.addEventListener('submit', function(e) {
        if (loadingSpinner) {
            loadingSpinner.style.display = 'block';
        }
        
        // Remove existing results
        const existingResults = document.querySelector('.results-container');
        if (existingResults) {
            existingResults.remove();
        }
        
        // Add loading animation
        document.body.style.cursor = 'wait';
    });

    // Real-time search suggestions
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length > 3) {
                searchTimeout = setTimeout(() => {
                    // Show real-time suggestions
                    showSearchSuggestions(query);
                }, 500);
            }
        });
        
        // Auto-complete functionality
        setupAutoComplete(searchInput);
    }
}

function showSearchSuggestions(query) {
    const suggestions = [
        'Market Researcher para PEPSI',
        'CFO en Querétaro',
        'Developer senior en CDMX',
        'Manager de Marketing',
        'Analista de Datos',
        'Consultant de Negocios',
        'Ingeniero de Software',
        'Director de Ventas',
        'HR Manager',
        'Product Manager',
        'UX Designer',
        'Data Scientist'
    ];
    
    const matches = suggestions.filter(s => 
        s.toLowerCase().includes(query.toLowerCase())
    );
    
    if (matches.length > 0) {
        console.log('Suggestions for:', query, matches);
        // Here you could show a dropdown with suggestions
    }
}

function setupAutoComplete(searchInput) {
    const suggestions = [
        'Market Researcher para PEPSI',
        'CFO en Querétaro',
        'Developer senior en CDMX',
        'Manager de Marketing',
        'Analista de Datos',
        'Consultant de Negocios',
        'Ingeniero de Software',
        'Director de Ventas'
    ];
    
    searchInput.addEventListener('input', function() {
        const query = this.value.toLowerCase();
        const matches = suggestions.filter(s => s.toLowerCase().includes(query));
        
        if (matches.length > 0 && query.length > 2) {
            console.log('Auto-complete suggestions:', matches);
        }
    });
}

function setSearchQuery(query) {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.value = query;
        searchInput.focus();
    }
}

// Real-time search API
async function performRealTimeSearch(query, searchType = 'all') {
    try {
        const response = await fetch('/dashboard/super-admin/intelligent-search/api/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                query: query,
                type: searchType
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('Error in real-time search:', error);
        return { error: error.message };
    }
}

// Utility function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize intelligent search when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeIntelligentSearch();
}); 