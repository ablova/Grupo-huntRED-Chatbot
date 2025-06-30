/**
 * SISTEMA DE ANALYTICS - Grupo huntRED®
 * Tracking y análisis de comportamiento de usuarios
 */

class Analytics {
    constructor() {
        this.events = [];
        this.sessionId = this.generateSessionId();
        this.userId = this.getUserId();
        this.startTime = Date.now();
        this.config = {
            endpoint: '/api/analytics/',
            batchSize: 10,
            flushInterval: 30000, // 30 segundos
            enableTracking: true
        };
        
        this.init();
    }
    
    /**
     * Inicializar analytics
     */
    init() {
        if (!this.config.enableTracking) return;
        
        // Configurar listeners
        this.setupEventListeners();
        
        // Iniciar flush automático
        this.startAutoFlush();
        
        // Track página inicial
        this.trackPageView();
        
        console.log('📊 Analytics inicializado');
    }
    
    /**
     * Generar ID de sesión
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Obtener ID de usuario
     */
    getUserId() {
        return window.userId || 'anonymous';
    }
    
    /**
     * Configurar event listeners
     */
    setupEventListeners() {
        // Click tracking
        document.addEventListener('click', (e) => {
            this.trackClick(e.target);
        });
        
        // Form submissions
        document.addEventListener('submit', (e) => {
            this.trackFormSubmit(e.target);
        });
        
        // Page visibility
        document.addEventListener('visibilitychange', () => {
            this.trackVisibilityChange();
        });
        
        // Scroll tracking
        this.setupScrollTracking();
        
        // Error tracking
        window.addEventListener('error', (e) => {
            this.trackError(e.error);
        });
    }
    
    /**
     * Configurar tracking de scroll
     */
    setupScrollTracking() {
        let scrollTimeout;
        let lastScrollTop = 0;
        
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            
            scrollTimeout = setTimeout(() => {
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                const scrollPercent = Math.round((scrollTop / (document.documentElement.scrollHeight - window.innerHeight)) * 100);
                
                if (scrollPercent > lastScrollTop + 25) {
                    this.trackEvent('scroll', {
                        scroll_percent: scrollPercent,
                        scroll_top: scrollTop
                    });
                    lastScrollTop = scrollPercent;
                }
            }, 150);
        });
    }
    
    /**
     * Track evento
     */
    trackEvent(eventName, properties = {}) {
        if (!this.config.enableTracking) return;
        
        const event = {
            event_name: eventName,
            properties: properties,
            timestamp: Date.now(),
            session_id: this.sessionId,
            user_id: this.userId,
            url: window.location.href,
            user_agent: navigator.userAgent,
            screen_resolution: `${screen.width}x${screen.height}`,
            viewport: `${window.innerWidth}x${window.innerHeight}`
        };
        
        this.events.push(event);
        
        // Flush si alcanza el batch size
        if (this.events.length >= this.config.batchSize) {
            this.flush();
        }
    }
    
    /**
     * Track vista de página
     */
    trackPageView() {
        this.trackEvent('page_view', {
            page_title: document.title,
            page_url: window.location.href,
            referrer: document.referrer
        });
    }
    
    /**
     * Track click
     */
    trackClick(element) {
        const properties = {
            element_tag: element.tagName.toLowerCase(),
            element_class: element.className,
            element_id: element.id,
            element_text: element.textContent?.substring(0, 50),
            element_href: element.href || null
        };
        
        this.trackEvent('click', properties);
    }
    
    /**
     * Track submit de formulario
     */
    trackFormSubmit(form) {
        const properties = {
            form_id: form.id,
            form_class: form.className,
            form_action: form.action,
            form_method: form.method,
            field_count: form.elements.length
        };
        
        this.trackEvent('form_submit', properties);
    }
    
    /**
     * Track cambio de visibilidad
     */
    trackVisibilityChange() {
        this.trackEvent('visibility_change', {
            is_visible: !document.hidden,
            time_on_page: Date.now() - this.startTime
        });
    }
    
    /**
     * Track error
     */
    trackError(error) {
        this.trackEvent('error', {
            error_message: error.message,
            error_stack: error.stack,
            error_type: error.name
        });
    }
    
    /**
     * Track tiempo en página
     */
    trackTimeOnPage() {
        const timeOnPage = Date.now() - this.startTime;
        this.trackEvent('time_on_page', {
            time_on_page: timeOnPage
        });
    }
    
    /**
     * Track conversión
     */
    trackConversion(conversionType, value = null) {
        this.trackEvent('conversion', {
            conversion_type: conversionType,
            conversion_value: value
        });
    }
    
    /**
     * Track funnel step
     */
    trackFunnelStep(step, stepNumber) {
        this.trackEvent('funnel_step', {
            step: step,
            step_number: stepNumber
        });
    }
    
    /**
     * Track performance
     */
    trackPerformance() {
        if ('performance' in window) {
            const perf = performance.getEntriesByType('navigation')[0];
            if (perf) {
                this.trackEvent('performance', {
                    load_time: perf.loadEventEnd - perf.loadEventStart,
                    dom_content_loaded: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
                    first_paint: perf.responseEnd - perf.fetchStart
                });
            }
        }
    }
    
    /**
     * Flush eventos al servidor
     */
    async flush() {
        if (this.events.length === 0) return;
        
        const eventsToSend = [...this.events];
        this.events = [];
        
        try {
            await Utils.API.post(this.config.endpoint, {
                events: eventsToSend
            });
            
            console.log(`📊 Analytics: ${eventsToSend.length} eventos enviados`);
        } catch (error) {
            console.error('Error enviando analytics:', error);
            // Re-encolar eventos fallidos
            this.events.unshift(...eventsToSend);
        }
    }
    
    /**
     * Iniciar auto flush
     */
    startAutoFlush() {
        setInterval(() => {
            this.flush();
        }, this.config.flushInterval);
    }
    
    /**
     * Configurar analytics
     */
    configure(config) {
        this.config = { ...this.config, ...config };
    }
    
    /**
     * Habilitar/deshabilitar tracking
     */
    setTrackingEnabled(enabled) {
        this.config.enableTracking = enabled;
    }
    
    /**
     * Obtener métricas de sesión
     */
    getSessionMetrics() {
        return {
            session_id: this.sessionId,
            user_id: this.userId,
            start_time: this.startTime,
            time_on_page: Date.now() - this.startTime,
            event_count: this.events.length
        };
    }
}

// ===== ANALYTICS ESPECÍFICOS PARA RECLUTAMIENTO =====

class RecruitmentAnalytics extends Analytics {
    constructor() {
        super();
        this.recruitmentEvents = [];
    }
    
    /**
     * Track aplicación a vacante
     */
    trackJobApplication(jobId, jobTitle, companyName) {
        this.trackEvent('job_application', {
            job_id: jobId,
            job_title: jobTitle,
            company_name: companyName,
            application_source: 'website'
        });
        
        this.trackConversion('job_application', 1);
    }
    
    /**
     * Track vista de vacante
     */
    trackJobView(jobId, jobTitle, companyName) {
        this.trackEvent('job_view', {
            job_id: jobId,
            job_title: jobTitle,
            company_name: companyName
        });
    }
    
    /**
     * Track inicio de aplicación
     */
    trackApplicationStart(jobId) {
        this.trackEvent('application_start', {
            job_id: jobId
        });
        
        this.trackFunnelStep('application_start', 1);
    }
    
    /**
     * Track completación de aplicación
     */
    trackApplicationComplete(jobId, timeSpent) {
        this.trackEvent('application_complete', {
            job_id: jobId,
            time_spent: timeSpent
        });
        
        this.trackFunnelStep('application_complete', 2);
    }
    
    /**
     * Track abandono de aplicación
     */
    trackApplicationAbandon(jobId, stepAbandoned) {
        this.trackEvent('application_abandon', {
            job_id: jobId,
            step_abandoned: stepAbandoned
        });
    }
    
    /**
     * Track búsqueda de trabajo
     */
    trackJobSearch(query, filters = {}) {
        this.trackEvent('job_search', {
            query: query,
            filters: filters
        });
    }
    
    /**
     * Track filtro aplicado
     */
    trackFilterApplied(filterType, filterValue) {
        this.trackEvent('filter_applied', {
            filter_type: filterType,
            filter_value: filterValue
        });
    }
    
    /**
     * Track guardado de trabajo
     */
    trackJobSave(jobId) {
        this.trackEvent('job_save', {
            job_id: jobId
        });
    }
    
    /**
     * Track compartir trabajo
     */
    trackJobShare(jobId, shareMethod) {
        this.trackEvent('job_share', {
            job_id: jobId,
            share_method: shareMethod
        });
    }
    
    /**
     * Track evaluación completada
     */
    trackAssessmentComplete(assessmentId, score, timeSpent) {
        this.trackEvent('assessment_complete', {
            assessment_id: assessmentId,
            score: score,
            time_spent: timeSpent
        });
        
        this.trackConversion('assessment_complete', score);
    }
    
    /**
     * Track entrevista programada
     */
    trackInterviewScheduled(jobId, interviewType) {
        this.trackEvent('interview_scheduled', {
            job_id: jobId,
            interview_type: interviewType
        });
        
        this.trackConversion('interview_scheduled', 1);
    }
    
    /**
     * Track aceptación de oferta
     */
    trackOfferAccepted(jobId, offerValue) {
        this.trackEvent('offer_accepted', {
            job_id: jobId,
            offer_value: offerValue
        });
        
        this.trackConversion('offer_accepted', offerValue);
    }
    
    /**
     * Track rechazo de oferta
     */
    trackOfferRejected(jobId, reason) {
        this.trackEvent('offer_rejected', {
            job_id: jobId,
            reason: reason
        });
    }
}

// ===== INICIALIZACIÓN =====

// Crear instancia global
window.Analytics = new RecruitmentAnalytics();

// Track antes de salir de la página
window.addEventListener('beforeunload', () => {
    window.Analytics.trackTimeOnPage();
    window.Analytics.flush();
});

console.log('📊 Recruitment Analytics cargado'); 