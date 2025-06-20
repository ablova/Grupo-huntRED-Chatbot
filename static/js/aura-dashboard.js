/**
 * AURA Dashboard JavaScript
 * 
 * Maneja la interactividad del dashboard de AURA,
 * incluyendo análisis rápido, verificaciones de salud
 * y comunicación con las APIs.
 */

class AuraDashboard {
    constructor() {
        this.apiBase = '/api/aura/';
        this.init();
    }

    init() {
        console.log('🚀 AURA Dashboard inicializado');
        this.setupEventListeners();
        this.autoRefresh();
    }

    setupEventListeners() {
        // Análisis rápido
        const analyzeBtn = document.querySelector('button[onclick="analyzePerson()"]');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.analyzePerson();
            });
        }

        // Verificación de salud
        const healthBtn = document.querySelector('button[onclick="runHealthCheck()"]');
        if (healthBtn) {
            healthBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.runHealthCheck();
            });
        }

        // Enter key en input
        const personInput = document.getElementById('person_id');
        if (personInput) {
            personInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.analyzePerson();
                }
            });
        }
    }

    async analyzePerson() {
        const personId = document.getElementById('person_id').value;
        const resultDiv = document.getElementById('quick-analysis-result');

        if (!personId) {
            this.showMessage('Por favor ingresa un ID de persona', 'error');
            return;
        }

        // Mostrar loading
        resultDiv.innerHTML = `
            <div class="loading-container">
                <div class="loading"></div>
                <p>Analizando aura de persona ${personId}...</p>
            </div>
        `;
        resultDiv.classList.add('show');

        try {
            const response = await fetch(`${this.apiBase}person/${personId}/`);
            const data = await response.json();

            if (response.ok) {
                this.displayAnalysisResult(data);
            } else {
                this.showMessage(data.error || 'Error analizando persona', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showMessage('Error de conexión', 'error');
        }
    }

    displayAnalysisResult(data) {
        const resultDiv = document.getElementById('quick-analysis-result');
        const auraScore = data.aura_score || 0;
        const scoreColor = this.getScoreColor(auraScore);

        resultDiv.innerHTML = `
            <div class="analysis-success">
                <div class="aura-score" style="background: ${scoreColor}">
                    <i class="fas fa-star"></i>
                    <span>Aura Score:</span>
                    <span class="aura-score-value">${(auraScore * 100).toFixed(1)}%</span>
                </div>
                
                <div class="person-info">
                    <h4>${data.person_data.name || 'Persona'}</h4>
                    <p><strong>Rol:</strong> ${data.person_data.current_role || 'N/A'}</p>
                    <p><strong>Empresa:</strong> ${data.person_data.current_company || 'N/A'}</p>
                    <p><strong>Ubicación:</strong> ${data.person_data.location || 'N/A'}</p>
                </div>

                <div class="network-insights">
                    <h5>Insights de Red</h5>
                    <div class="insight-item">
                        <span>Fuerza de Red:</span>
                        <span>${(data.network_insights.network_strength * 100).toFixed(1)}%</span>
                    </div>
                    <div class="insight-item">
                        <span>Reputación:</span>
                        <span>${(data.network_insights.reputation_score * 100).toFixed(1)}%</span>
                    </div>
                    <div class="insight-item">
                        <span>Conexiones Clave:</span>
                        <span>${data.network_insights.key_connections?.length || 0}</span>
                    </div>
                </div>

                <div class="actions">
                    <a href="/ats/aura/person/${data.person_id}/" class="btn btn-primary">
                        <i class="fas fa-eye"></i> Ver Detalles
                    </a>
                    <a href="/ats/aura/network/${data.person_id}/insights/" class="btn btn-secondary">
                        <i class="fas fa-network-wired"></i> Red Profesional
                    </a>
                </div>
            </div>
        `;
    }

    getScoreColor(score) {
        if (score >= 0.8) return 'linear-gradient(135deg, #10b981, #059669)';
        if (score >= 0.6) return 'linear-gradient(135deg, #f59e0b, #d97706)';
        return 'linear-gradient(135deg, #ef4444, #dc2626)';
    }

    async runHealthCheck() {
        const healthBtn = document.querySelector('button[onclick="runHealthCheck()"]');
        const originalText = healthBtn.innerHTML;

        // Mostrar loading
        healthBtn.innerHTML = '<div class="loading"></div> Verificando...';
        healthBtn.disabled = true;

        try {
            const response = await fetch(`${this.apiBase}health/`);
            const data = await response.json();

            if (response.ok) {
                this.updateHealthStatus(data);
                this.showMessage('Verificación de salud completada', 'success');
            } else {
                this.showMessage('Error en verificación de salud', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showMessage('Error de conexión', 'error');
        } finally {
            // Restaurar botón
            healthBtn.innerHTML = originalText;
            healthBtn.disabled = false;
        }
    }

    updateHealthStatus(healthData) {
        const statusIndicator = document.querySelector('.status-indicator');
        const overallStatus = healthData.overall_status;

        // Actualizar indicador principal
        statusIndicator.className = `status-indicator ${overallStatus}`;
        statusIndicator.innerHTML = `
            <i class="fas fa-circle"></i>
            <span>${overallStatus.charAt(0).toUpperCase() + overallStatus.slice(1)}</span>
        `;

        // Actualizar componentes individuales
        const components = healthData.connectors || {};
        Object.keys(components).forEach(component => {
            const componentElement = document.querySelector(`[data-component="${component}"]`);
            if (componentElement) {
                const status = components[component];
                componentElement.className = `component-item ${status}`;
                const badge = componentElement.querySelector('.status-badge');
                if (badge) {
                    badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                }
            }
        });
    }

    showMessage(message, type = 'info') {
        // Crear elemento de mensaje
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `
            <i class="fas fa-${this.getMessageIcon(type)}"></i>
            <span>${message}</span>
        `;

        // Insertar al inicio del dashboard
        const dashboard = document.querySelector('.aura-dashboard');
        dashboard.insertBefore(messageDiv, dashboard.firstChild);

        // Auto-remover después de 5 segundos
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }

    getMessageIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'error': return 'exclamation-circle';
            case 'warning': return 'exclamation-triangle';
            default: return 'info-circle';
        }
    }

    autoRefresh() {
        // Actualizar métricas cada 5 minutos
        setInterval(() => {
            this.refreshMetrics();
        }, 5 * 60 * 1000);
    }

    async refreshMetrics() {
        try {
            const response = await fetch(`${this.apiBase}metrics/`);
            const data = await response.json();

            if (response.ok) {
                this.updateMetrics(data);
            }
        } catch (error) {
            console.error('Error actualizando métricas:', error);
        }
    }

    updateMetrics(metrics) {
        // Actualizar métricas en tiempo real
        const metricElements = document.querySelectorAll('.metric-value');
        metricElements.forEach(element => {
            const label = element.previousElementSibling?.textContent;
            if (label) {
                switch (label.trim()) {
                    case 'Personas Analizadas:':
                        element.textContent = metrics.total_people_analyzed;
                        break;
                    case 'Conexiones Analizadas:':
                        element.textContent = metrics.total_connections_analyzed;
                        break;
                    case 'Comunidades Detectadas:':
                        element.textContent = metrics.communities_detected;
                        break;
                    case 'Influenciadores Identificados:':
                        element.textContent = metrics.influencers_identified;
                        break;
                    case 'Validaciones Realizadas:':
                        element.textContent = metrics.validations_performed;
                        break;
                }
            }
        });
    }

    // Métodos de utilidad
    formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    }

    formatPercentage(value) {
        return `${(value * 100).toFixed(1)}%`;
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleString();
    }
}

// Funciones globales para compatibilidad con onclick
window.analyzePerson = function() {
    if (window.auraDashboard) {
        window.auraDashboard.analyzePerson();
    }
};

window.runHealthCheck = function() {
    if (window.auraDashboard) {
        window.auraDashboard.runHealthCheck();
    }
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.auraDashboard = new AuraDashboard();
});

// Exportar para uso en otros módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuraDashboard;
} 