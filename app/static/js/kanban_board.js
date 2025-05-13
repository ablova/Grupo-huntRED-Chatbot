/**
 * Kanban Board JavaScript
 * Implementa la funcionalidad para tableros kanban, incluyendo:
 * - Arrastrar y soltar tarjetas entre columnas
 * - Edición rápida de tarjetas
 * - Filtrado de tarjetas
 * - Gestión de notificaciones
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar variables y elementos
    const columns = document.querySelectorAll('.kanban-column-body');
    const filterForm = document.querySelector('#filterDropdown');
    const searchInput = document.querySelector('#searchInput');
    const priorityFilter = document.querySelector('#priorityFilter');
    const assigneeFilter = document.querySelector('#assigneeFilter');
    const applyFiltersBtn = document.querySelector('#applyFilters');
    const markAllReadBtn = document.querySelector('#markAllRead');
    const notificationItems = document.querySelectorAll('.notification-item');
    
    // Inicializar funcionalidad de arrastrar y soltar con SortableJS
    const sortables = [];
    
    // Inicializar cada columna como un contenedor sortable
    columns.forEach(column => {
        const sortable = new Sortable(column, {
            group: 'kanban-cards',
            animation: 150,
            draggable: '.kanban-card',
            handle: '.kanban-card',
            ghostClass: 'kanban-card-ghost',
            chosenClass: 'kanban-card-chosen',
            dragClass: 'kanban-card-drag',
            forceFallback: true,
            fallbackClass: 'kanban-card-fallback',
            
            // Al comenzar a arrastrar
            onStart: function(evt) {
                const item = evt.item;
                item.classList.add('dragging');
            },
            
            // Al terminar de arrastrar
            onEnd: function(evt) {
                const item = evt.item;
                item.classList.remove('dragging');
                
                // Si la tarjeta se movió a una columna diferente
                if (evt.from !== evt.to) {
                    const cardId = item.dataset.id;
                    const targetColumnId = evt.to.dataset.columnId;
                    const position = Array.from(evt.to.children).indexOf(item);
                    
                    // Enviar la solicitud al backend
                    moveCardToColumn(cardId, targetColumnId, position);
                }
            }
        });
        
        sortables.push(sortable);
    });
    
    /**
     * Mueve una tarjeta a otra columna
     * @param {string} cardId - ID de la tarjeta
     * @param {string} targetColumnId - ID de la columna de destino
     * @param {number} position - Posición en la columna
     */
    function moveCardToColumn(cardId, targetColumnId, position) {
        // Mostrar indicador de carga
        const card = document.querySelector(`.kanban-card[data-id="${cardId}"]`);
        card.classList.add('loading');
        
        fetch(KANBAN_API.moveCard, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
            },
            body: JSON.stringify({
                card_id: cardId,
                target_column_id: targetColumnId,
                position: position
            })
        })
        .then(response => response.json())
        .then(data => {
            card.classList.remove('loading');
            
            if (data.error) {
                // Si hay un error, mostrar notificación y restaurar la posición original
                showNotification(data.error, 'error');
                
                // Recargar la página para restaurar el estado original
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                // Si la operación fue exitosa, actualizar la interfaz
                showNotification(data.message, 'success');
                
                // Actualizar la posición en el DOM
                card.dataset.columnId = data.card.column_id;
                card.dataset.position = data.card.position;
            }
        })
        .catch(error => {
            console.error('Error al mover tarjeta:', error);
            card.classList.remove('loading');
            showNotification('Error al mover la tarjeta', 'error');
            
            // Recargar la página para restaurar el estado original
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        });
    }
    
    /**
     * Inicializa los modales de edición rápida de tarjetas
     */
    function initializeQuickEditModal() {
        const quickEditBtns = document.querySelectorAll('.quick-edit-btn');
        const quickEditModal = document.getElementById('quickEditModal');
        const saveQuickEditBtn = document.getElementById('saveQuickEdit');
        const quickEditForm = document.getElementById('quickEditForm');
        
        if (!quickEditModal) return;
        
        // Bootstrap modal instance
        const modal = new bootstrap.Modal(quickEditModal);
        
        // Manejar clic en botones de edición rápida
        quickEditBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const cardId = this.dataset.id;
                const card = document.querySelector(`.kanban-card[data-id="${cardId}"]`);
                
                // Llenar el formulario con los datos actuales de la tarjeta
                document.getElementById('editCardId').value = cardId;
                
                // Obtener y seleccionar valores actuales
                const columnId = card.dataset.columnId;
                document.getElementById('columnSelect').value = columnId;
                
                // Mostrar el modal
                modal.show();
            });
        });
        
        // Manejar guardar cambios
        saveQuickEditBtn.addEventListener('click', function() {
            const cardId = document.getElementById('editCardId').value;
            const assigneeId = document.getElementById('assigneeSelect').value;
            const priority = document.getElementById('prioritySelect').value;
            const dueDate = document.getElementById('dueDateInput').value;
            const targetColumnId = document.getElementById('columnSelect').value;
            
            // Preparar datos para enviar
            const formData = {
                card_id: cardId
            };
            
            // Solo incluir campos que se hayan modificado
            if (assigneeId) formData.assignee_id = assigneeId;
            if (priority) formData.priority = priority;
            if (dueDate) formData.due_date = dueDate;
            
            // Primero actualizar la tarjeta
            updateCard(formData)
                .then(success => {
                    if (success) {
                        // Si también se cambió la columna, mover la tarjeta
                        const card = document.querySelector(`.kanban-card[data-id="${cardId}"]`);
                        const currentColumnId = card.dataset.columnId;
                        
                        if (targetColumnId !== currentColumnId) {
                            // Obtener la posición al final de la columna
                            const targetColumn = document.querySelector(`.kanban-column-body[data-column-id="${targetColumnId}"]`);
                            const position = targetColumn.children.length;
                            
                            // Mover la tarjeta a la nueva columna
                            moveCardToColumn(cardId, targetColumnId, position);
                        }
                        
                        // Cerrar el modal
                        modal.hide();
                    }
                });
        });
    }
    
    /**
     * Actualiza una tarjeta en el servidor
     * @param {Object} formData - Datos del formulario a enviar
     * @returns {Promise<boolean>} - Promesa que resuelve a true si la operación fue exitosa
     */
    function updateCard(formData) {
        return fetch(KANBAN_API.updateCard, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showNotification(data.error, 'error');
                return false;
            } else {
                showNotification(data.message, 'success');
                
                // Si se cambió la prioridad, actualizar el indicador visual
                if (formData.priority) {
                    const card = document.querySelector(`.kanban-card[data-id="${formData.card_id}"]`);
                    card.dataset.priority = formData.priority;
                    
                    const priorityIndicator = card.querySelector('.priority-indicator');
                    priorityIndicator.className = `priority-indicator priority-${formData.priority}`;
                }
                
                return true;
            }
        })
        .catch(error => {
            console.error('Error al actualizar tarjeta:', error);
            showNotification('Error al actualizar la tarjeta', 'error');
            return false;
        });
    }
    
    /**
     * Inicializa la funcionalidad de archivar tarjetas
     */
    function initializeArchiveButtons() {
        const archiveBtns = document.querySelectorAll('.archive-card-btn');
        
        archiveBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const cardId = this.dataset.id;
                
                if (confirm('¿Estás seguro de que deseas archivar esta tarjeta?')) {
                    archiveCard(cardId);
                }
            });
        });
    }
    
    /**
     * Archiva una tarjeta
     * @param {string} cardId - ID de la tarjeta a archivar
     */
    function archiveCard(cardId) {
        fetch(KANBAN_API.archiveCard, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
            },
            body: JSON.stringify({
                card_id: cardId,
                action: 'archive'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showNotification(data.error, 'error');
            } else {
                showNotification(data.message, 'success');
                
                // Eliminar la tarjeta del DOM
                const card = document.querySelector(`.kanban-card[data-id="${cardId}"]`);
                card.remove();
            }
        })
        .catch(error => {
            console.error('Error al archivar tarjeta:', error);
            showNotification('Error al archivar la tarjeta', 'error');
        });
    }
    
    /**
     * Inicializa el filtrado de tarjetas
     */
    function initializeFiltering() {
        if (!applyFiltersBtn) return;
        
        applyFiltersBtn.addEventListener('click', function() {
            const searchTerm = searchInput.value.toLowerCase();
            const priority = priorityFilter.value;
            const assignee = assigneeFilter.value;
            
            // Aplicar filtros a todas las tarjetas
            const cards = document.querySelectorAll('.kanban-card');
            
            cards.forEach(card => {
                let show = true;
                
                // Filtrar por término de búsqueda
                if (searchTerm) {
                    const title = card.querySelector('.kanban-card-title').textContent.toLowerCase();
                    const subtitle = card.querySelector('.kanban-card-subtitle').textContent.toLowerCase();
                    
                    if (!title.includes(searchTerm) && !subtitle.includes(searchTerm)) {
                        show = false;
                    }
                }
                
                // Filtrar por prioridad
                if (priority && card.dataset.priority !== priority) {
                    show = false;
                }
                
                // Filtrar por asignado
                if (assignee) {
                    const cardAssignee = card.dataset.assignee;
                    
                    if (assignee === 'unassigned' && cardAssignee) {
                        show = false;
                    } else if (assignee !== 'unassigned' && assignee !== cardAssignee) {
                        show = false;
                    }
                }
                
                // Mostrar u ocultar la tarjeta
                if (show) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
            
            // Cerrar el dropdown
            const dropdown = bootstrap.Dropdown.getInstance(document.getElementById('filterDropdown'));
            if (dropdown) dropdown.hide();
        });
    }
    
    /**
     * Inicializa la gestión de notificaciones
     */
    function initializeNotifications() {
        if (!markAllReadBtn) return;
        
        // Marcar todas las notificaciones como leídas
        markAllReadBtn.addEventListener('click', function() {
            fetch(KANBAN_API.markNotificationRead, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN,
                },
                body: JSON.stringify({
                    mark_all: true
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Eliminar el indicador de notificaciones
                    const badge = document.querySelector('#notificationsDropdown .badge');
                    if (badge) badge.remove();
                    
                    // Actualizar la lista de notificaciones
                    const container = document.querySelector('#notificationsDropdown + .dropdown-menu > div:last-child');
                    container.innerHTML = `
                        <div class="p-3 text-center text-muted">
                            <i class="fas fa-check-circle mb-2"></i>
                            <p class="mb-0">No tienes notificaciones pendientes</p>
                        </div>
                    `;
                    
                    showNotification('Notificaciones marcadas como leídas', 'success');
                }
            })
            .catch(error => {
                console.error('Error al marcar notificaciones:', error);
            });
        });
        
        // Marcar notificación individual como leída al hacer clic
        notificationItems.forEach(item => {
            item.addEventListener('click', function() {
                const notificationId = this.dataset.id;
                
                fetch(KANBAN_API.markNotificationRead, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': CSRF_TOKEN,
                    },
                    body: JSON.stringify({
                        notification_id: notificationId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Actualizar el estilo de la notificación
                        this.style.opacity = '0.5';
                        
                        // Actualizar el contador
                        const unreadCount = document.querySelectorAll('.notification-item:not([style*="opacity"])').length;
                        const badge = document.querySelector('#notificationsDropdown .badge');
                        
                        if (badge) {
                            if (unreadCount > 0) {
                                badge.textContent = unreadCount;
                            } else {
                                badge.remove();
                            }
                        }
                    }
                })
                .catch(error => {
                    console.error('Error al marcar notificación:', error);
                });
            });
        });
    }
    
    /**
     * Muestra una notificación en pantalla
     * @param {string} message - Mensaje a mostrar
     * @param {string} type - Tipo de notificación (success, error, info)
     */
    function showNotification(message, type = 'info') {
        // Crear el elemento de notificación
        const notification = document.createElement('div');
        notification.className = `toast position-fixed bottom-0 end-0 m-3 ${type === 'error' ? 'bg-danger text-white' : type === 'success' ? 'bg-success text-white' : 'bg-light'}`;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'assertive');
        notification.setAttribute('aria-atomic', 'true');
        
        notification.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">${type === 'error' ? 'Error' : type === 'success' ? 'Éxito' : 'Información'}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // Añadir al DOM
        document.body.appendChild(notification);
        
        // Inicializar como toast de Bootstrap
        const toast = new bootstrap.Toast(notification, {
            autohide: true,
            delay: 5000
        });
        
        // Mostrar y luego eliminar del DOM
        toast.show();
        notification.addEventListener('hidden.bs.toast', function() {
            notification.remove();
        });
    }
    
    // Inicializar todas las funcionalidades
    initializeQuickEditModal();
    initializeArchiveButtons();
    initializeFiltering();
    initializeNotifications();
});
