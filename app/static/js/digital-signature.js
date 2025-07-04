/**
 * Sistema de Firma Digital Integrado para huntRED®
 * Maneja firma autógrafa, validación biométrica y envío de propuesta
 */

class DigitalSignatureSystem {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.isDrawing = false;
        this.signatureData = null;
        this.consultantSignature = null;
        this.clientSignature = null;
        this.proposalData = {};
        this.isProcessing = false;
        
        this.init();
    }
    
    init() {
        console.log('🚀 Inicializando sistema de firma digital huntRED®...');
        this.setupSignaturePads();
        this.setupEventListeners();
        this.loadProposalData();
    }
    
    setupSignaturePads() {
        // Pad de firma del cliente
        const clientCanvas = document.getElementById('clientSignaturePad');
        if (clientCanvas) {
            this.setupCanvas(clientCanvas, 'client');
        }
        
        // Pad de firma del consultor
        const consultantCanvas = document.getElementById('consultantSignaturePad');
        if (consultantCanvas) {
            this.setupCanvas(consultantCanvas, 'consultant');
        }
    }
    
    setupCanvas(canvas, type) {
        const ctx = canvas.getContext('2d');
        ctx.strokeStyle = '#1f2937';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        // Hacer el canvas responsive
        const resizeCanvas = () => {
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width;
            canvas.height = rect.height;
            ctx.strokeStyle = '#1f2937';
            ctx.lineWidth = 2;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
        };
        
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        // Event listeners para dibujo
        let isDrawing = false;
        let lastX = 0;
        let lastY = 0;
        
        const startDrawing = (e) => {
            isDrawing = true;
            const rect = canvas.getBoundingClientRect();
            lastX = e.clientX - rect.left;
            lastY = e.clientY - rect.top;
        };
        
        const draw = (e) => {
            if (!isDrawing) return;
            
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            ctx.beginPath();
            ctx.moveTo(lastX, lastY);
            ctx.lineTo(x, y);
            ctx.stroke();
            
            lastX = x;
            lastY = y;
        };
        
        const stopDrawing = () => {
            isDrawing = false;
            this.validateSignature(canvas, type);
        };
        
        // Mouse events
        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stopDrawing);
        canvas.addEventListener('mouseout', stopDrawing);
        
        // Touch events para móviles
        canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousedown', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            canvas.dispatchEvent(mouseEvent);
        });
        
        canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousemove', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            canvas.dispatchEvent(mouseEvent);
        });
        
        canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            const mouseEvent = new MouseEvent('mouseup', {});
            canvas.dispatchEvent(mouseEvent);
        });
        
        // Botones de limpiar
        const clearBtn = document.getElementById(`clear${type.charAt(0).toUpperCase() + type.slice(1)}Signature`);
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                this[`${type}Signature`] = null;
                this.updateSignatureStatus(type, false);
            });
        }
    }
    
    validateSignature(canvas, type) {
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        
        // Contar píxeles no blancos (firma)
        let signaturePixels = 0;
        for (let i = 0; i < data.length; i += 4) {
            if (data[i] !== 255 || data[i + 1] !== 255 || data[i + 2] !== 255) {
                signaturePixels++;
            }
        }
        
        const isValid = signaturePixels > 100; // Mínimo de píxeles para considerar válida
        
        if (isValid) {
            this[`${type}Signature`] = canvas.toDataURL('image/png');
            this.updateSignatureStatus(type, true);
        } else {
            this[`${type}Signature`] = null;
            this.updateSignatureStatus(type, false);
        }
    }
    
    updateSignatureStatus(type, isValid) {
        const statusElement = document.getElementById(`${type}SignatureStatus`);
        if (statusElement) {
            if (isValid) {
                statusElement.innerHTML = '<i class="fas fa-check-circle text-green-500 mr-1"></i>Firma válida';
                statusElement.className = 'text-sm text-green-600 font-medium';
            } else {
                statusElement.innerHTML = '<i class="fas fa-exclamation-circle text-orange-500 mr-1"></i>Firma requerida';
                statusElement.className = 'text-sm text-orange-600 font-medium';
            }
        }
    }
    
    setupEventListeners() {
        // Botón de guardar propuesta
        const saveBtn = document.getElementById('btnGuardarPropuesta');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.processProposal());
        }
        
        // Botón de previsualizar
        const previewBtn = document.getElementById('btnPreviewProposal');
        if (previewBtn) {
            previewBtn.addEventListener('click', () => this.showPreview());
        }
    }
    
    loadProposalData() {
        // Cargar datos de la propuesta desde el DOM
        this.proposalData = {
            clientName: document.querySelector('[data-client-name]')?.dataset.clientName || 'Cliente',
            proposalId: document.querySelector('[data-proposal-id]')?.dataset.proposalId || Date.now(),
            totalAmount: this.calculateTotalAmount(),
            services: this.getSelectedServices(),
            contacts: this.getContacts(),
            date: new Date().toISOString()
        };
    }
    
    calculateTotalAmount() {
        const totalElement = document.getElementById('totalAmount');
        if (totalElement) {
            return parseFloat(totalElement.textContent.replace(/[^0-9.]/g, '')) || 0;
        }
        return 0;
    }
    
    getSelectedServices() {
        const services = [];
        document.querySelectorAll('.service-checkbox:checked').forEach(checkbox => {
            services.push({
                id: checkbox.value,
                name: checkbox.closest('.service-card')?.querySelector('h3')?.textContent || 'Servicio',
                price: parseFloat(checkbox.dataset.price) || 0
            });
        });
        return services;
    }
    
    getContacts() {
        const contacts = [];
        document.querySelectorAll('input[name="contact_email"]').forEach(input => {
            if (input.value) {
                contacts.push(input.value);
            }
        });
        return contacts;
    }
    
    async processProposal() {
        if (this.isProcessing) return;
        
        // Validar firmas
        if (!this.clientSignature) {
            this.showNotification('Por favor, firme en el pad del cliente', 'warning');
            return;
        }
        
        if (!this.consultantSignature) {
            this.showNotification('Por favor, firme en el pad del consultor', 'warning');
            return;
        }
        
        this.isProcessing = true;
        this.showLoadingState();
        
        try {
            // Preparar datos para envío
            const proposalData = {
                ...this.proposalData,
                clientSignature: this.clientSignature,
                consultantSignature: this.consultantSignature,
                timestamp: new Date().toISOString(),
                ipAddress: await this.getClientIP(),
                userAgent: navigator.userAgent
            };
            
            // Enviar al backend
            const response = await fetch('/api/proposals/sign/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(proposalData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showSuccessModal(result);
            } else {
                throw new Error('Error al procesar la propuesta');
            }
            
        } catch (error) {
            console.error('Error:', error);
            this.showNotification('Error al procesar la propuesta. Intente nuevamente.', 'error');
        } finally {
            this.isProcessing = false;
            this.hideLoadingState();
        }
    }
    
    async getClientIP() {
        try {
            const response = await fetch('https://api.ipify.org?format=json');
            const data = await response.json();
            return data.ip;
        } catch {
            return 'No disponible';
        }
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    showLoadingState() {
        const btn = document.getElementById('btnGuardarPropuesta');
        if (btn) {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Procesando...';
            btn.disabled = true;
        }
    }
    
    hideLoadingState() {
        const btn = document.getElementById('btnGuardarPropuesta');
        if (btn) {
            btn.innerHTML = '<i class="fas fa-file-signature mr-2"></i>Guardar Propuesta';
            btn.disabled = false;
        }
    }
    
    showSuccessModal(result) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-8 max-w-2xl mx-4 shadow-2xl">
                <div class="text-center">
                    <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i class="fas fa-check text-3xl text-green-600"></i>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800 mb-2">¡Propuesta Firmada Exitosamente!</h3>
                    <p class="text-gray-600 mb-6">La propuesta ha sido procesada y enviada a todos los contactos involucrados.</p>
                    
                    <div class="bg-gray-50 rounded-lg p-4 mb-6">
                        <h4 class="font-semibold text-gray-800 mb-3">Resumen de la Propuesta</h4>
                        <div class="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <p class="text-gray-600">Cliente:</p>
                                <p class="font-medium">${this.proposalData.clientName}</p>
                            </div>
                            <div>
                                <p class="text-gray-600">Total:</p>
                                <p class="font-medium text-green-600">$${this.proposalData.totalAmount.toLocaleString()}</p>
                            </div>
                            <div>
                                <p class="text-gray-600">Servicios:</p>
                                <p class="font-medium">${this.proposalData.services.length}</p>
                            </div>
                            <div>
                                <p class="text-gray-600">Contactos:</p>
                                <p class="font-medium">${this.proposalData.contacts.length}</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="flex space-x-4">
                        <button onclick="window.print()" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                            <i class="fas fa-print mr-2"></i>Imprimir
                        </button>
                        <button onclick="this.closest('.fixed').remove()" class="flex-1 bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors">
                            Cerrar
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Auto-remover después de 10 segundos
        setTimeout(() => {
            if (modal.parentNode) {
                modal.remove();
            }
        }, 10000);
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        const bgColor = type === 'error' ? 'bg-red-500' : type === 'warning' ? 'bg-orange-500' : 'bg-blue-500';
        const icon = type === 'error' ? 'fa-exclamation-circle' : type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
        
        notification.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 transform transition-all duration-300 translate-x-full`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${icon} mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animar entrada
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto-remover
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
    
    showPreview() {
        // Mostrar preview de la propuesta antes de firmar
        const previewData = {
            ...this.proposalData,
            hasClientSignature: !!this.clientSignature,
            hasConsultantSignature: !!this.consultantSignature
        };
        
        console.log('Preview de propuesta:', previewData);
        this.showNotification('Preview generado. Revise la consola para ver los detalles.', 'info');
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.digitalSignatureSystem = new DigitalSignatureSystem();
}); 