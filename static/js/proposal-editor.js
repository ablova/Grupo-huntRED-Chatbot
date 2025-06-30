// Sistema de edición inline ultra mejorado - Grupo huntRED®
document.addEventListener('DOMContentLoaded', function() {
    // Configuración global
    const CONFIG = {
        csrfToken: document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '',
        clientId: document.querySelector('[data-client-id]')?.dataset.clientId || '',
        companyId: document.querySelector('[data-company-id]')?.dataset.companyId || '',
        endpoints: {
            clientInfo: '/proposals/client/update-info/',
            companyContacts: '/proposals/company/update-contacts/',
            addInvitee: '/proposals/company/add-invitee/',
            removeInvitee: '/proposals/company/remove-invitee/'
        }
    };

    // Estado global de la aplicación
    let editingState = {
        currentField: null,
        pendingChanges: new Map(),
        isSaving: false
    };

    // ===== SISTEMA DE EDICIÓN INLINE =====
    
    // Activar edición de sección completa
    window.toggleSectionEdit = function(sectionId) {
        const section = document.getElementById(sectionId + '-fields');
        if (!section) return;
        
        const fields = section.querySelectorAll('.editable-field, .editable-select');
        fields.forEach(field => {
            const display = field.querySelector('.field-display');
            const input = field.querySelector('.field-input');
            
            if (display && input) {
                display.classList.add('hidden');
                input.classList.remove('hidden');
                input.focus();
                input.select();
            }
        });
    };

    // Guardar campo individual
    window.saveField = async function(input, fieldName) {
        const originalValue = input.dataset.original;
        const newValue = input.value.trim();
        
        // Si no hay cambios, solo volver a modo vista
        if (newValue === originalValue) {
            toggleFieldView(input, false);
            return;
        }

        // Validación básica
        if (!validateField(fieldName, newValue)) {
            showToast('Valor inválido para ' + fieldName, 'error');
            input.focus();
            return;
        }

        try {
            // Mostrar estado de carga
            const fieldContainer = input.closest('.editable-field, .editable-select');
            fieldContainer.classList.add('loading');
            
            // Preparar datos
            const formData = new FormData();
            formData.append('field', fieldName);
            formData.append('value', newValue);
            formData.append('csrfmiddlewaretoken', CONFIG.csrfToken);

            // Enviar al servidor
            const response = await fetch(CONFIG.endpoints.clientInfo + CONFIG.clientId + '/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                // Actualizar vista
                const display = fieldContainer.querySelector('.field-display');
                if (display) {
                    display.textContent = newValue;
                }
                
                // Actualizar valor original
                input.dataset.original = newValue;
                
                // Feedback visual
                fieldContainer.classList.add('save-success');
                setTimeout(() => fieldContainer.classList.remove('save-success'), 600);
                
                showToast('Campo actualizado correctamente', 'success');
                
                // Volver a modo vista
                toggleFieldView(input, false);
            } else {
                throw new Error(result.message || 'Error al guardar');
            }
        } catch (error) {
            console.error('Error saving field:', error);
            showToast('Error al guardar: ' + error.message, 'error');
            
            // Restaurar valor original
            input.value = originalValue;
        } finally {
            fieldContainer.classList.remove('loading');
        }
    };

    // Manejar tecla Enter
    window.handleEnter = function(event, input) {
        if (event.key === 'Enter') {
            event.preventDefault();
            input.blur(); // Esto dispara saveField
        }
    };

    // Alternar entre modo vista y edición
    function toggleFieldView(input, toEdit = true) {
        const fieldContainer = input.closest('.editable-field, .editable-select');
        const display = fieldContainer.querySelector('.field-display');
        
        if (toEdit) {
            display.classList.add('hidden');
            input.classList.remove('hidden');
            input.focus();
            input.select();
        } else {
            display.classList.remove('hidden');
            input.classList.add('hidden');
        }
    }

    // Validación de campos
    function validateField(fieldName, value) {
        const validators = {
            email: (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val),
            phone: (val) => /^[\d\s\-\+\(\)]+$/.test(val),
            tax_id: (val) => /^[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}$/.test(val),
            required: (val) => val.length > 0
        };

        const fieldValidations = {
            email: ['email', 'required'],
            tax_email: ['email', 'required'],
            phone: ['phone', 'required'],
            tax_id: ['tax_id', 'required'],
            name: ['required'],
            industry: ['required'],
            address: ['required'],
            city: ['required'],
            primary_contact_name: ['required'],
            primary_contact_position: ['required'],
            tax_name: ['required'],
            tax_address: ['required'],
            tax_regime: ['required'],
            tax_cfdi: ['required']
        };

        const validations = fieldValidations[fieldName] || ['required'];
        
        return validations.every(validation => {
            if (validation === 'required') {
                return validators.required(value);
            }
            return validators[validation](value);
        });
    }

    // ===== SISTEMA DE CHIPS PARA INVITADOS =====
    
    // Mostrar modal para añadir invitado
    window.showAddInviteeModal = function() {
        const modal = document.getElementById('addInviteeModal');
        modal.classList.remove('hidden');
        document.getElementById('inviteeName').focus();
    };

    // Ocultar modal
    window.hideAddInviteeModal = function() {
        const modal = document.getElementById('addInviteeModal');
        modal.classList.add('hidden');
        document.getElementById('addInviteeForm').reset();
    };

    // Añadir invitado
    window.addInvitee = async function(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        formData.append('csrfmiddlewaretoken', CONFIG.csrfToken);

        try {
            const response = await fetch(CONFIG.endpoints.addInvitee + CONFIG.companyId + '/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                // Añadir chip al contenedor
                addChipToContainer(result.person);
                
                // Cerrar modal
                hideAddInviteeModal();
                
                showToast('Invitado añadido correctamente', 'success');
            } else {
                throw new Error(result.message || 'Error al añadir invitado');
            }
        } catch (error) {
            console.error('Error adding invitee:', error);
            showToast('Error al añadir invitado: ' + error.message, 'error');
        }
    };

    // Eliminar invitado
    window.removeInvitee = async function(personId) {
        if (!confirm('¿Está seguro de que desea eliminar este invitado?')) {
            return;
        }

        try {
            const formData = new FormData();
            formData.append('person_id', personId);
            formData.append('csrfmiddlewaretoken', CONFIG.csrfToken);

            const response = await fetch(CONFIG.endpoints.removeInvitee + CONFIG.companyId + '/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                // Eliminar chip del DOM
                const chip = document.querySelector(`[data-person-id="${personId}"]`);
                if (chip) {
                    chip.remove();
                }
                
                showToast('Invitado eliminado correctamente', 'success');
            } else {
                throw new Error(result.message || 'Error al eliminar invitado');
            }
        } catch (error) {
            console.error('Error removing invitee:', error);
            showToast('Error al eliminar invitado: ' + error.message, 'error');
        }
    };

    // Añadir chip al contenedor
    function addChipToContainer(person) {
        const container = document.getElementById('invitees-chips');
        const chip = document.createElement('span');
        chip.className = 'chip';
        chip.dataset.personId = person.id;
        chip.innerHTML = `
            ${person.nombre} (${person.company_email})
            <button type="button" class="chip-remove" onclick="removeInvitee('${person.id}')" aria-label="Eliminar">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Insertar antes del botón "Añadir"
        const addBtn = container.querySelector('.add-chip-btn');
        container.insertBefore(chip, addBtn);
    }

    // ===== SISTEMA DE NOTIFICACIONES =====
    
    // Mostrar toast notification
    function showToast(message, type = 'info') {
        // Remover toasts existentes
        const existingToasts = document.querySelectorAll('.toast');
        existingToasts.forEach(toast => toast.remove());

        // Crear nuevo toast
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${getToastIcon(type)} mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animar entrada
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto-remover después de 4 segundos
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // Obtener icono para toast
    function getToastIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    // ===== EVENTOS DE EDICIÓN INLINE =====
    
    // Activar edición al hacer clic en campos
    document.addEventListener('click', function(event) {
        const editableField = event.target.closest('.editable-field, .editable-select');
        if (!editableField) return;
        
        // Solo permitir edición para usuarios autorizados
        if (!document.querySelector('.edit-section-btn')) return;
        
        const display = editableField.querySelector('.field-display');
        const input = editableField.querySelector('.field-input');
        
        if (display && input && !editingState.isSaving) {
            toggleFieldView(input, true);
        }
    });

    // Cerrar modal al hacer clic fuera
    document.addEventListener('click', function(event) {
        const modal = document.getElementById('addInviteeModal');
        if (event.target === modal) {
            hideAddInviteeModal();
        }
    });

    // Cerrar modal con Escape
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            hideAddInviteeModal();
        }
    });

    // ===== INICIALIZACIÓN =====
    
    // Configurar formulario de invitados
    const addInviteeForm = document.getElementById('addInviteeForm');
    if (addInviteeForm) {
        addInviteeForm.addEventListener('submit', addInvitee);
    }

    // Mostrar mensaje de bienvenida para usuarios autorizados
    if (document.querySelector('.edit-section-btn')) {
        setTimeout(() => {
            showToast('Haga clic en cualquier campo para editarlo', 'info');
        }, 1000);
    }

    console.log('✅ Sistema de edición inline ultra mejorado cargado');
}); 