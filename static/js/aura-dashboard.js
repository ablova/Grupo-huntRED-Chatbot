// AURA Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    initializeEventListeners();
    startAutoRefresh();
});

// Inicializar gráficos
function initializeCharts() {
    // Gráfico de distribución de módulos
    const moduleCtx = document.getElementById('moduleDistributionChart');
    if (moduleCtx) {
        new Chart(moduleCtx, {
            type: 'doughnut',
            data: {
                labels: ['Ethics Engine', 'TruthSense™', 'SocialVerify™', 'Bias Detection', 'Fairness Optimizer', 'Impact Analyzer'],
                datasets: [{
                    data: [25, 20, 18, 15, 12, 10],
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#f5576c',
                        '#4facfe',
                        '#00f2fe'
                    ],
                    borderWidth: 0
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
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    // Gráfico de scores éticos
    const scoresCtx = document.getElementById('ethicalScoresChart');
    if (scoresCtx) {
        new Chart(scoresCtx, {
            type: 'bar',
            data: {
                labels: ['Veracidad', 'Autenticidad', 'Equidad', 'Impacto', 'Integridad', 'Sostenibilidad'],
                datasets: [{
                    label: 'Score Ético',
                    data: [85, 78, 92, 76, 88, 82],
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: '#667eea',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

// Inicializar event listeners
function initializeEventListeners() {
    // Configuración de módulos
    const moduleCards = document.querySelectorAll('.module-card');
    moduleCards.forEach(card => {
        card.addEventListener('click', function() {
            const moduleName = this.querySelector('.module-name').textContent;
            showModuleDetails(moduleName);
        });
    });

    // Botones de acción
    const actionButtons = document.querySelectorAll('.btn');
    actionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
}

// Mostrar detalles del módulo
function showModuleDetails(moduleName) {
    // Implementar modal con detalles del módulo
    console.log('Mostrando detalles de:', moduleName);
    
    // Aquí se podría abrir un modal con información detallada del módulo
    const modal = new bootstrap.Modal(document.getElementById('moduleDetailsModal'));
    modal.show();
}

// Ver análisis específico
function viewAnalysis(analysisId) {
    // Cargar datos del análisis
    fetch(`/aura/api/analysis/${analysisId}/`)
        .then(response => response.json())
        .then(data => {
            displayAnalysisDetails(data);
        })
        .catch(error => {
            console.error('Error cargando análisis:', error);
            showNotification('Error cargando análisis', 'error');
        });
}

// Mostrar detalles del análisis
function displayAnalysisDetails(analysis) {
    const modalBody = document.getElementById('analysisModalBody');
    
    modalBody.innerHTML = `
        <div class="analysis-details">
            <div class="detail-section">
                <h6>Información General</h6>
                <p><strong>ID:</strong> ${analysis.analysis_id}</p>
                <p><strong>Tipo:</strong> ${analysis.analysis_type}</p>
                <p><strong>Fecha:</strong> ${new Date(analysis.timestamp).toLocaleString()}</p>
                <p><strong>Tiempo de ejecución:</strong> ${analysis.execution_time}s</p>
            </div>
            
            <div class="detail-section">
                <h6>Resultados</h6>
                <div class="score-display">
                    <div class="score-item">
                        <span class="score-label">Score Ético:</span>
                        <div class="score-bar">
                            <div class="score-fill" style="width: ${analysis.overall_score}%"></div>
                            <span>${analysis.overall_score}%</span>
                        </div>
                    </div>
                    <div class="score-item">
                        <span class="score-label">Confianza:</span>
                        <div class="score-bar">
                            <div class="score-fill" style="width: ${analysis.confidence}%"></div>
                            <span>${analysis.confidence}%</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h6>Módulos Utilizados</h6>
                <div class="modules-list">
                    ${analysis.modules_used.map(module => `
                        <span class="module-badge">${module}</span>
                    `).join('')}
                </div>
            </div>
            
            <div class="detail-section">
                <h6>Recomendaciones</h6>
                <ul class="recommendations-list">
                    ${analysis.recommendations.map(rec => `
                        <li>${rec}</li>
                    `).join('')}
                </ul>
            </div>
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('analysisModal'));
    modal.show();
}

// Actualizar tier de servicio
function updateServiceTier() {
    const tierSelect = document.getElementById('serviceTierSelect');
    const selectedTier = tierSelect.value;
    
    fetch('/aura/api/update-tier/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            tier: selectedTier
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Tier de servicio actualizado', 'success');
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            showNotification('Error actualizando tier', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    });
}

// Guardar configuración
function saveConfiguration() {
    const config = {
        max_concurrent_analyses: document.getElementById('maxConcurrentAnalyses').value,
        cache_ttl: document.getElementById('cacheTTL').value,
        enable_monitoring: document.getElementById('enableMonitoring').checked
    };
    
    fetch('/aura/api/save-config/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Configuración guardada', 'success');
        } else {
            showNotification('Error guardando configuración', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    });
}

// Restablecer configuración
function resetConfiguration() {
    if (confirm('¿Estás seguro de que quieres restablecer la configuración?')) {
        fetch('/aura/api/reset-config/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Configuración restablecida', 'success');
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                showNotification('Error restableciendo configuración', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error de conexión', 'error');
        });
    }
}

// Actualizar dashboard
function refreshDashboard() {
    const refreshBtn = document.querySelector('.btn-outline-primary');
    refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Actualizando...';
    refreshBtn.disabled = true;
    
    fetch('/aura/api/dashboard-data/')
        .then(response => response.json())
        .then(data => {
            updateDashboardData(data);
            showNotification('Dashboard actualizado', 'success');
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error actualizando dashboard', 'error');
        })
        .finally(() => {
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Actualizar';
            refreshBtn.disabled = false;
        });
}

// Actualizar datos del dashboard
function updateDashboardData(data) {
    // Actualizar métricas principales
    document.querySelector('.metric-value').textContent = data.total_analyses;
    
    // Actualizar scores de módulos
    const moduleCards = document.querySelectorAll('.module-card');
    moduleCards.forEach(card => {
        const moduleName = card.querySelector('.module-name').textContent;
        const scoreElement = card.querySelector('.metric-value');
        
        if (data.module_scores && data.module_scores[moduleName]) {
            scoreElement.textContent = data.module_scores[moduleName] + '%';
        }
    });
    
    // Actualizar tabla de análisis recientes
    updateRecentAnalysesTable(data.recent_analyses);
}

// Actualizar tabla de análisis recientes
function updateRecentAnalysesTable(analyses) {
    const tbody = document.querySelector('.analyses-table tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    analyses.forEach(analysis => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${analysis.analysis_id}</td>
            <td>${analysis.analysis_type}</td>
            <td>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${analysis.overall_score}%"></div>
                    <span>${analysis.overall_score}%</span>
                </div>
            </td>
            <td>${analysis.confidence}%</td>
            <td>${analysis.modules_used.length}</td>
            <td>${analysis.execution_time}s</td>
            <td>
                <span class="status-badge status-completed">Completado</span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="viewAnalysis('${analysis.analysis_id}')">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Auto-refresh del dashboard
function startAutoRefresh() {
    // Actualizar cada 30 segundos
    setInterval(() => {
        fetch('/aura/api/dashboard-data/')
            .then(response => response.json())
            .then(data => {
                updateDashboardData(data);
            })
            .catch(error => {
                console.error('Error en auto-refresh:', error);
            });
    }, 30000);
}

// Mostrar notificaciones
function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Obtener cookie CSRF
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

// Exportar funciones para uso global
window.AURADashboard = {
    viewAnalysis,
    updateServiceTier,
    saveConfiguration,
    resetConfiguration,
    refreshDashboard,
    showNotification
};
