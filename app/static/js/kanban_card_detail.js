/**
 * Kanban Card Detail JavaScript
 * Implementa la funcionalidad para la vista detallada de tarjetas:
 * - Edición de información de la tarjeta
 * - Movimiento entre columnas
 * - Gestión de comentarios
 * - Subida de archivos adjuntos
 * - Archivado/Desarchivado de tarjetas
 */

document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos DOM
    const moveCardForm = document.getElementById('moveCardForm');
    const saveMoveBtnID = document.getElementById('saveMove');
    const editCardForm = document.getElementById('editCardForm');
    const saveEditBtn = document.getElementById('saveEdit');
    const commentForm = document.getElementById('commentForm');
    const attachmentForm = document.getElementById('attachmentForm');
    const archiveCardBtn = document.getElementById('archiveCardBtn');
    const unarchiveCardBtn = document.getElementById('unarchiveCardBtn');
    
    // Inicializar el movimiento de tarjetas entre columnas
    if (moveCardForm && saveMoveBtnID) {
        saveMoveBtnID.addEventListener('click', function() {
            const targetColumnId = document.getElementById('moveColumnSelect').value;
            
            // Enviar solicitud para mover la tarjeta
            fetch(KANBAN_API.moveCard, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN,
                },
                body: JSON.stringify({
                    card_id: CARD_ID,
                    target_column_id: targetColumnId,
                    position: null // Colocar al final
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    showNotification(data.message, 'success');
                    
                    // Cerrar el modal y refrescar la página
                    const modal = bootstrap.Modal.getInstance(document.getElementById('moveCardModal'));
                    modal.hide();
                    
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            })
            .catch(error => {
                console.error('Error al mover tarjeta:', error);
                showNotification('Error al mover la tarjeta', 'error');
            });
        });
    }
    
    // Inicializar la edición de tarjetas
    if (editCardForm && saveEditBtn) {
        saveEditBtn.addEventListener('click', function() {
            const formData = {
                card_id: CARD_ID,
                assignee_id: document.getElementById('assigneeSelect').value,
                priority: document.getElementById('prioritySelect').value,
                due_date: document.getElementById('dueDateInput').value,
            };
            
            // Enviar solicitud para actualizar la tarjeta
            fetch(KANBAN_API.updateCard, {
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
                } else {
                    showNotification(data.message, 'success');
                    
                    // Cerrar el modal y refrescar la página
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editCardModal'));
                    modal.hide();
                    
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            })
            .catch(error => {
                console.error('Error al editar tarjeta:', error);
                showNotification('Error al editar la tarjeta', 'error');
            });
        });
    }
    
    // Inicializar el formulario de comentarios
    if (commentForm) {
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const commentText = document.getElementById('commentInput').value.trim();
            
            if (!commentText) {
                showNotification('Por favor, introduce un comentario', 'error');
                return;
            }
            
            // Enviar solicitud para añadir comentario
            fetch(KANBAN_API.addComment, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN,
                },
                body: JSON.stringify({
                    card_id: CARD_ID,
                    comment: commentText
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    // Limpiar el campo de comentario
                    document.getElementById('commentInput').value = '';
                    
                    // Añadir el nuevo comentario al DOM
                    addCommentToDOM(data.comment);
                    
                    showNotification(data.message, 'success');
                }
            })
            .catch(error => {
                console.error('Error al añadir comentario:', error);
                showNotification('Error al añadir el comentario', 'error');
            });
        });
    }
    
    // Inicializar el formulario de subida de archivos
    if (attachmentForm) {
        attachmentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('fileInput');
            
            if (!fileInput.files || fileInput.files.length === 0) {
                showNotification('Por favor, selecciona un archivo', 'error');
                return;
            }
            
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('card_id', CARD_ID);
            formData.append('file', file);
            
            // Mostrar indicador de carga
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Subiendo...';
            submitBtn.disabled = true;
            
            // Enviar solicitud para subir archivo
            fetch(KANBAN_API.uploadAttachment, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': CSRF_TOKEN,
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Restaurar botón
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
                
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    // Limpiar el campo de archivo
                    fileInput.value = '';
                    
                    // Añadir el nuevo archivo al DOM
                    addAttachmentToDOM(data.attachment);
                    
                    showNotification(data.message, 'success');
                }
            })
            .catch(error => {
                // Restaurar botón
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
                
                console.error('Error al subir archivo:', error);
                showNotification('Error al subir el archivo', 'error');
            });
        });
    }
    
    // Inicializar el botón de archivar
    if (archiveCardBtn) {
        archiveCardBtn.addEventListener('click', function() {
            if (confirm('¿Estás seguro de que quieres archivar esta tarjeta?')) {
                archiveOrUnarchiveCard('archive');
            }
        });
    }
    
    // Inicializar el botón de desarchivar
    if (unarchiveCardBtn) {
        unarchiveCardBtn.addEventListener('click', function() {
            if (confirm('¿Estás seguro de que quieres restaurar esta tarjeta?')) {
                archiveOrUnarchiveCard('unarchive');
            }
        });
    }
    
    /**
     * Archiva o desarchiva una tarjeta
     * @param {string} action - 'archive' o 'unarchive'
     */
    function archiveOrUnarchiveCard(action) {
        fetch(KANBAN_API.archiveCard, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
            },
            body: JSON.stringify({
                card_id: CARD_ID,
                action: action
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showNotification(data.error, 'error');
            } else {
                showNotification(data.message, 'success');
                
                // Redireccionar a la vista del tablero
                setTimeout(() => {
                    window.location.href = document.referrer || '/kanban/';
                }, 1000);
            }
        })
        .catch(error => {
            console.error(`Error al ${action === 'archive' ? 'archivar' : 'desarchivar'} tarjeta:`, error);
            showNotification(`Error al ${action === 'archive' ? 'archivar' : 'desarchivar'} la tarjeta`, 'error');
        });
    }
    
    /**
     * Añade un comentario al DOM
     * @param {Object} comment - Datos del comentario
     */
    function addCommentToDOM(comment) {
        const container = document.getElementById('commentsContainer');
        
        // Eliminar mensaje de "No hay comentarios" si existe
        const emptyMessage = container.querySelector('.text-center.text-muted');
        if (emptyMessage) {
            emptyMessage.remove();
        }
        
        // Crear elemento de comentario
        const commentElement = document.createElement('div');
        commentElement.className = 'comment-item mb-3';
        
        const initials = comment.user.split(' ').map(name => name[0]).join('');
        
        commentElement.innerHTML = `
            <div class="d-flex">
                <div class="avatar me-2">
                    <span>${initials}</span>
                </div>
                <div class="comment-content">
                    <div class="comment-header d-flex justify-content-between align-items-center">
                        <strong>${comment.user}</strong>
                        <small class="text-muted">${formatDateTime(comment.created_at)}</small>
                    </div>
                    <div class="comment-body">
                        ${comment.text.replace(/\n/g, '<br>')}
                    </div>
                </div>
            </div>
        `;
        
        // Añadir al principio del contenedor
        container.insertBefore(commentElement, container.firstChild);
    }
    
    /**
     * Añade un archivo adjunto al DOM
     * @param {Object} attachment - Datos del archivo
     */
    function addAttachmentToDOM(attachment) {
        const container = document.getElementById('attachmentsContainer');
        
        // Eliminar mensaje de "No hay archivos" si existe
        const emptyMessage = container.querySelector('.text-center.text-muted');
        if (emptyMessage) {
            emptyMessage.remove();
        }
        
        // Determinar icono basado en tipo de archivo
        let iconClass = 'fa-file';
        const fileExtension = attachment.filename.split('.').pop().toLowerCase();
        
        if (['jpg', 'jpeg', 'png', 'gif', 'svg'].includes(fileExtension)) {
            iconClass = 'fa-file-image';
        } else if (['pdf'].includes(fileExtension)) {
            iconClass = 'fa-file-pdf';
        } else if (['doc', 'docx'].includes(fileExtension)) {
            iconClass = 'fa-file-word';
        } else if (['xls', 'xlsx'].includes(fileExtension)) {
            iconClass = 'fa-file-excel';
        } else if (['zip', 'rar'].includes(fileExtension)) {
            iconClass = 'fa-file-archive';
        }
        
        // Crear elemento de archivo
        const attachmentElement = document.createElement('div');
        attachmentElement.className = 'attachment-item d-flex align-items-center mb-2 p-2 border rounded';
        
        attachmentElement.innerHTML = `
            <i class="fas ${iconClass} fa-2x me-3"></i>
            <div class="flex-grow-1">
                <div class="attachment-name">${attachment.filename}</div>
                <div class="small text-muted">
                    ${formatFileSize(attachment.size)} • 
                    Subido por ${attachment.uploaded_by}
                </div>
            </div>
            <a href="${attachment.url}" class="btn btn-sm btn-outline-primary" target="_blank">
                <i class="fas fa-download"></i>
            </a>
        `;
        
        // Añadir al principio del contenedor
        container.insertBefore(attachmentElement, container.firstChild);
    }
    
    /**
     * Formatea un tamaño de archivo en una representación legible
     * @param {number} bytes - Tamaño en bytes
     * @returns {string} - Tamaño formateado
     */
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        let i = Math.floor(Math.log(bytes) / Math.log(1024));
        return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + ['B', 'KB', 'MB', 'GB', 'TB'][i];
    }
    
    /**
     * Formatea una fecha y hora en formato legible
     * @param {string} dateString - Fecha en formato ISO
     * @returns {string} - Fecha formateada
     */
    function formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('es-ES', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
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
});
