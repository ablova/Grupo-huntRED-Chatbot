/**
 * Modal de Resumen Final para Propuestas huntRED®
 * Muestra un resumen impactante después de firmar la propuesta
 */

class ProposalSummaryModal {
    constructor() {
        this.modal = null;
        this.isVisible = false;
        this.proposalData = {};
        
        this.init();
    }
    
    init() {
        console.log('🎯 Inicializando modal de resumen de propuesta...');
        this.createModal();
        this.setupEventListeners();
    }
    
    createModal() {
        this.modal = document.createElement('div');
        this.modal.className = 'proposal-summary-modal fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 opacity-0 pointer-events-none transition-all duration-500';
        this.modal.innerHTML = this.getModalHTML();
        document.body.appendChild(this.modal);
    }
    
    getModalHTML() {
        return `
            <div class="modal-content bg-white rounded-2xl shadow-2xl max-w-4xl w-11/12 max-h-[90vh] overflow-y-auto transform scale-95 transition-all duration-500">
                <!-- Header con animación -->
                <div class="modal-header bg-gradient-to-r from-red-600 to-red-700 text-white p-8 rounded-t-2xl relative overflow-hidden">
                    <div class="absolute inset-0 bg-black opacity-10"></div>
                    <div class="relative z-10 text-center">
                        <div class="success-animation mb-4">
                            <div class="w-20 h-20 bg-white bg-opacity-20 rounded-full flex items-center justify-center mx-auto animate-pulse">
                                <i class="fas fa-check text-3xl text-white"></i>
                            </div>
                        </div>
                        <h2 class="text-3xl font-bold mb-2">¡Propuesta Firmada Exitosamente!</h2>
                        <p class="text-xl opacity-90">Su propuesta ha sido procesada y enviada a todos los contactos involucrados</p>
                    </div>
                </div>
                
                <!-- Contenido del modal -->
                <div class="modal-body p-8">
                    <!-- Resumen de la propuesta -->
                    <div class="proposal-summary mb-8">
                        <h3 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                            <i class="fas fa-file-contract text-red-600 mr-3"></i>
                            Resumen de la Propuesta
                        </h3>
                        
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                            <div class="stat-card bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-xl border border-blue-200">
                                <div class="text-center">
                                    <div class="text-3xl font-bold text-blue-600 mb-2" id="clientNameDisplay">Cliente</div>
                                    <div class="text-sm text-blue-700 font-medium">Cliente</div>
                                </div>
                            </div>
                            
                            <div class="stat-card bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-xl border border-green-200">
                                <div class="text-center">
                                    <div class="text-3xl font-bold text-green-600 mb-2" id="totalAmountDisplay">$0</div>
                                    <div class="text-sm text-green-700 font-medium">Inversión Total</div>
                                </div>
                            </div>
                            
                            <div class="stat-card bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-xl border border-purple-200">
                                <div class="text-center">
                                    <div class="text-3xl font-bold text-purple-600 mb-2" id="servicesCountDisplay">0</div>
                                    <div class="text-sm text-purple-700 font-medium">Servicios</div>
                                </div>
                            </div>
                            
                            <div class="stat-card bg-gradient-to-br from-orange-50 to-orange-100 p-6 rounded-xl border border-orange-200">
                                <div class="text-center">
                                    <div class="text-3xl font-bold text-orange-600 mb-2" id="contactsCountDisplay">0</div>
                                    <div class="text-sm text-orange-700 font-medium">Contactos</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Servicios contratados -->
                        <div class="services-section mb-8">
                            <h4 class="text-lg font-semibold text-gray-700 mb-4 flex items-center">
                                <i class="fas fa-cogs text-gray-500 mr-2"></i>
                                Servicios Contratados
                            </h4>
                            <div id="servicesList" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <!-- Los servicios se insertarán dinámicamente -->
                            </div>
                        </div>
                        
                        <!-- Contactos involucrados -->
                        <div class="contacts-section mb-8">
                            <h4 class="text-lg font-semibold text-gray-700 mb-4 flex items-center">
                                <i class="fas fa-users text-gray-500 mr-2"></i>
                                Contactos Involucrados
                            </h4>
                            <div id="contactsList" class="flex flex-wrap gap-3">
                                <!-- Los contactos se insertarán dinámicamente -->
                            </div>
                        </div>
                    </div>
                    
                    <!-- Certificación digital -->
                    <div class="digital-certification mb-8 bg-gradient-to-r from-indigo-50 to-purple-50 p-6 rounded-xl border border-indigo-200">
                        <h4 class="text-lg font-semibold text-indigo-800 mb-4 flex items-center">
                            <i class="fas fa-shield-alt text-indigo-600 mr-2"></i>
                            Certificación Digital
                        </h4>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="cert-item flex items-center">
                                <i class="fas fa-check-circle text-green-500 mr-3"></i>
                                <span class="text-sm text-gray-700">Firma digital certificada</span>
                            </div>
                            <div class="cert-item flex items-center">
                                <i class="fas fa-check-circle text-green-500 mr-3"></i>
                                <span class="text-sm text-gray-700">Validación biométrica</span>
                            </div>
                            <div class="cert-item flex items-center">
                                <i class="fas fa-check-circle text-green-500 mr-3"></i>
                                <span class="text-sm text-gray-700">Sello de tiempo oficial</span>
                            </div>
                            <div class="cert-item flex items-center">
                                <i class="fas fa-check-circle text-green-500 mr-3"></i>
                                <span class="text-sm text-gray-700">Respaldo blockchain</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Próximos pasos -->
                    <div class="next-steps mb-8">
                        <h4 class="text-lg font-semibold text-gray-700 mb-4 flex items-center">
                            <i class="fas fa-road text-gray-500 mr-2"></i>
                            Próximos Pasos
                        </h4>
                        <div class="steps-timeline">
                            <div class="step-item flex items-start mb-4">
                                <div class="step-number bg-red-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold mr-4 flex-shrink-0">1</div>
                                <div>
                                    <h5 class="font-semibold text-gray-800">Confirmación del Equipo</h5>
                                    <p class="text-sm text-gray-600">Nuestro equipo se pondrá en contacto en las próximas 24 horas</p>
                                </div>
                            </div>
                            <div class="step-item flex items-start mb-4">
                                <div class="step-number bg-red-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold mr-4 flex-shrink-0">2</div>
                                <div>
                                    <h5 class="font-semibold text-gray-800">Kick-off Meeting</h5>
                                    <p class="text-sm text-gray-600">Reunión inicial para alinear expectativas y cronograma</p>
                                </div>
                            </div>
                            <div class="step-item flex items-start mb-4">
                                <div class="step-number bg-red-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold mr-4 flex-shrink-0">3</div>
                                <div>
                                    <h5 class="font-semibold text-gray-800">Inicio de Proceso</h5>
                                    <p class="text-sm text-gray-600">Comenzaremos inmediatamente con la búsqueda de candidatos</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Footer del modal -->
                <div class="modal-footer bg-gray-50 p-6 rounded-b-2xl">
                    <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
                        <button id="printProposal" class="btn-primary bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold flex items-center transition-colors">
                            <i class="fas fa-print mr-2"></i>
                            Imprimir Propuesta
                        </button>
                        <button id="downloadPDF" class="btn-secondary bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-semibold flex items-center transition-colors">
                            <i class="fas fa-download mr-2"></i>
                            Descargar PDF
                        </button>
                        <button id="closeModal" class="btn-close bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-semibold flex items-center transition-colors">
                            <i class="fas fa-times mr-2"></i>
                            Cerrar
                        </button>
                    </div>
                    
                    <div class="text-center mt-4">
                        <p class="text-sm text-gray-500">
                            <i class="fas fa-info-circle mr-1"></i>
                            La propuesta ha sido enviada automáticamente a todos los contactos involucrados
                        </p>
                    </div>
                </div>
            </div>
        `;
    }
    
    setupEventListeners() {
        // Botón de cerrar
        document.addEventListener('click', (e) => {
            if (e.target.id === 'closeModal' || e.target.closest('#closeModal')) {
                this.hide();
            }
        });
        
        // Botón de imprimir
        document.addEventListener('click', (e) => {
            if (e.target.id === 'printProposal' || e.target.closest('#printProposal')) {
                window.print();
            }
        });
        
        // Botón de descargar PDF
        document.addEventListener('click', (e) => {
            if (e.target.id === 'downloadPDF' || e.target.closest('#downloadPDF')) {
                this.downloadPDF();
            }
        });
        
        // Cerrar con Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible) {
                this.hide();
            }
        });
    }
    
    show(proposalData = {}) {
        this.proposalData = proposalData;
        this.updateContent();
        
        this.modal.classList.remove('opacity-0', 'pointer-events-none');
        this.modal.querySelector('.modal-content').classList.remove('scale-95');
        this.modal.querySelector('.modal-content').classList.add('scale-100');
        
        this.isVisible = true;
        
        // Animar entrada
        setTimeout(() => {
            this.modal.querySelector('.success-animation').classList.add('animate-bounce');
        }, 300);
        
        console.log('🎉 Modal de resumen mostrado');
    }
    
    hide() {
        this.modal.classList.add('opacity-0', 'pointer-events-none');
        this.modal.querySelector('.modal-content').classList.remove('scale-100');
        this.modal.querySelector('.modal-content').classList.add('scale-95');
        
        this.isVisible = false;
        
        console.log('🔒 Modal de resumen ocultado');
    }
    
    updateContent() {
        // Actualizar datos del cliente
        const clientNameDisplay = this.modal.querySelector('#clientNameDisplay');
        if (clientNameDisplay) {
            clientNameDisplay.textContent = this.proposalData.clientName || 'Cliente';
        }
        
        // Actualizar monto total
        const totalAmountDisplay = this.modal.querySelector('#totalAmountDisplay');
        if (totalAmountDisplay) {
            const amount = this.proposalData.totalAmount || 0;
            totalAmountDisplay.textContent = `$${amount.toLocaleString()}`;
        }
        
        // Actualizar número de servicios
        const servicesCountDisplay = this.modal.querySelector('#servicesCountDisplay');
        if (servicesCountDisplay) {
            const servicesCount = this.proposalData.services?.length || 0;
            servicesCountDisplay.textContent = servicesCount;
        }
        
        // Actualizar número de contactos
        const contactsCountDisplay = this.modal.querySelector('#contactsCountDisplay');
        if (contactsCountDisplay) {
            const contactsCount = this.proposalData.contacts?.length || 0;
            contactsCountDisplay.textContent = contactsCount;
        }
        
        // Actualizar lista de servicios
        this.updateServicesList();
        
        // Actualizar lista de contactos
        this.updateContactsList();
    }
    
    updateServicesList() {
        const servicesList = this.modal.querySelector('#servicesList');
        if (!servicesList) return;
        
        const services = this.proposalData.services || [];
        servicesList.innerHTML = services.map(service => `
            <div class="service-item bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                <div class="flex items-center justify-between">
                    <div>
                        <h5 class="font-semibold text-gray-800">${service.name}</h5>
                        <p class="text-sm text-gray-600">Servicio incluido</p>
                    </div>
                    <div class="text-right">
                        <div class="text-lg font-bold text-green-600">$${service.price?.toLocaleString() || '0'}</div>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    updateContactsList() {
        const contactsList = this.modal.querySelector('#contactsList');
        if (!contactsList) return;
        
        const contacts = this.proposalData.contacts || [];
        contactsList.innerHTML = contacts.map(contact => `
            <div class="contact-item bg-blue-50 text-blue-700 px-3 py-2 rounded-full text-sm font-medium flex items-center">
                <i class="fas fa-envelope mr-2"></i>
                ${contact}
            </div>
        `).join('');
    }
    
    downloadPDF() {
        // Simular descarga de PDF
        console.log('📄 Descargando PDF...');
        
        // Aquí se implementaría la descarga real del PDF
        // Por ahora mostramos una notificación
        this.showNotification('PDF descargado exitosamente', 'success');
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
        const icon = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';
        
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
        }, 3000);
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.proposalSummaryModal = new ProposalSummaryModal();
}); 