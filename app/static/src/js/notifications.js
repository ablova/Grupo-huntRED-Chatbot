// Notifications System
document.addEventListener('DOMContentLoaded', function() {
    // Notification types and their styles
    const NOTIFICATION_TYPES = {
        info: {
            icon: 'ℹ️',
            bg: 'bg-blue-50 dark:bg-blue-900/30',
            text: 'text-blue-800 dark:text-blue-200',
            border: 'border-blue-200 dark:border-blue-800'
        },
        success: {
            icon: '✅',
            bg: 'bg-green-50 dark:bg-green-900/30',
            text: 'text-green-800 dark:text-green-200',
            border: 'border-green-200 dark:border-green-800'
        },
        warning: {
            icon: '⚠️',
            bg: 'bg-yellow-50 dark:bg-yellow-900/30',
            text: 'text-yellow-800 dark:text-yellow-200',
            border: 'border-yellow-200 dark:border-yellow-800'
        },
        error: {
            icon: '❌',
            bg: 'bg-red-50 dark:bg-red-900/30',
            text: 'text-red-800 dark:text-red-200',
            border: 'border-red-200 dark:border-red-800'
        },
        chat: {
            icon: '💬',
            bg: 'bg-indigo-50 dark:bg-indigo-900/30',
            text: 'text-indigo-800 dark:text-indigo-200',
            border: 'border-indigo-200 dark:border-indigo-800'
        },
        system: {
            icon: '⚙️',
            bg: 'bg-slate-50 dark:bg-slate-800/30',
            text: 'text-slate-800 dark:text-slate-200',
            border: 'border-slate-200 dark:border-slate-700'
        }
    };

    // Notification queue
    let notificationQueue = [];
    let isShowingNotification = false;

    // Initialize notifications container
    function initNotifications() {
        // Create notifications container if it doesn't exist
        if (!document.getElementById('notifications-container')) {
            const container = document.createElement('div');
            container.id = 'notifications-container';
            container.className = 'fixed top-4 right-4 z-50 space-y-3 w-full max-w-sm';
            document.body.appendChild(container);
        }
    }

    // Show a notification
    function showNotification(notification) {
        const container = document.getElementById('notifications-container');
        if (!container) return;

        const { type = 'info', title, message, duration = 5000, action } = notification;
        const notificationType = NOTIFICATION_TYPES[type] || NOTIFICATION_TYPES.info;

        // Create notification element
        const notificationEl = document.createElement('div');
        notificationEl.className = `notification-item transform transition-all duration-300 ease-out translate-x-96 opacity-0 ${notificationType.bg} ${notificationType.border} border rounded-xl p-4 shadow-lg`;
        notificationEl.role = 'alert';

        // Add notification content
        notificationEl.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0 pt-0.5 text-xl mr-3">${notificationType.icon}</div>
                <div class="flex-1">
                    <h4 class="font-semibold ${notificationType.text} mb-1">${title}</h4>
                    <p class="text-sm text-slate-600 dark:text-slate-300">${message}</p>
                    ${action ? `
                        <div class="mt-2">
                            <button class="text-xs font-medium ${notificationType.text} hover:underline focus:outline-none">
                                ${action.label}
                            </button>
                        </div>
                    ` : ''}
                </div>
                <button class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 ml-2" aria-label="Cerrar">
                    <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        `;

        // Add close button handler
        const closeBtn = notificationEl.querySelector('button[aria-label="Cerrar"]');
        closeBtn.addEventListener('click', () => {
            hideNotification(notificationEl);
        });

        // Add action button handler if exists
        if (action) {
            const actionBtn = notificationEl.querySelector('button:not([aria-label="Cerrar"])');
            actionBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (typeof action.callback === 'function') {
                    action.callback();
                }
                hideNotification(notificationEl);
            });
        }

        // Add to container
        container.appendChild(notificationEl);

        // Trigger animation
        setTimeout(() => {
            notificationEl.classList.remove('translate-x-96', 'opacity-0');
            notificationEl.classList.add('translate-x-0', 'opacity-100');
        }, 10);

        // Auto-remove after duration if not persistent
        if (duration > 0) {
            setTimeout(() => {
                hideNotification(notificationEl);
            }, duration);
        }

        // Add to queue if needed
        if (isShowingNotification) {
            notificationQueue.push(notification);
            return;
        }

        isShowingNotification = true;

        // Return function to manually remove notification
        return () => hideNotification(notificationEl);
    }


    // Hide a notification
    function hideNotification(notificationEl) {
        if (!notificationEl) return;

        // Trigger exit animation
        notificationEl.classList.add('translate-x-96', 'opacity-0');

        // Remove from DOM after animation
        setTimeout(() => {
            if (notificationEl.parentNode) {
                notificationEl.parentNode.removeChild(notificationEl);
            }
            
            // Show next notification in queue
            isShowingNotification = false;
            if (notificationQueue.length > 0) {
                const nextNotification = notificationQueue.shift();
                showNotification(nextNotification);
            }
        }, 300);
    }

    // Public API
    window.Notifications = {
        // Show a notification
        show: showNotification,
        
        // Show a success notification
        success: (title, message, options = {}) => {
            return showNotification({
                type: 'success',
                title,
                message,
                ...options
            });
        },
        
        // Show an error notification
        error: (title, message, options = {}) => {
            return showNotification({
                type: 'error',
                title,
                message,
                ...options
            });
        },
        
        // Show a warning notification
        warning: (title, message, options = {}) => {
            return showNotification({
                type: 'warning',
                title,
                message,
                ...options
            });
        },
        
        // Show an info notification
        info: (title, message, options = {}) => {
            return showNotification({
                type: 'info',
                title,
                message,
                ...options
            });
        },
        
        // Show a chat notification
        chat: (title, message, options = {}) => {
            return showNotification({
                type: 'chat',
                title,
                message,
                ...options
            });
        },
        
        // Show a system notification
        system: (title, message, options = {}) => {
            return showNotification({
                type: 'system',
                title,
                message,
                ...options
            });
        },
        
        // Clear all notifications
        clearAll: () => {
            const container = document.getElementById('notifications-container');
            if (container) {
                container.innerHTML = '';
            }
            notificationQueue = [];
            isShowingNotification = false;
        }
    };

    // Initialize on load
    initNotifications();

    // Example usage (for testing):
    // window.Notifications.success('Éxito', '¡Operación completada con éxito!');
    // window.Notifications.error('Error', 'Ha ocurrido un error inesperado.');
    // window.Notifications.warning('Advertencia', 'Esto es una advertencia importante.');
    // window.Notifications.info('Información', 'Esta es una notificación informativa.');
    // window.Notifications.chat('Nuevo mensaje', 'Tienes un nuevo mensaje de Juan Pérez', {
    //     action: {
    //         label: 'Ver mensaje',
    //         callback: () => console.log('Ver mensaje clickeado')
    //     }
    // });
});

// WebSocket connection for real-time updates
function initWebSocket() {
    // Check if WebSocket is supported
    if (!('WebSocket' in window)) {
        console.warn('WebSockets not supported in this browser');
        return;
    }

    // Create WebSocket connection
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = protocol + window.location.host + '/ws/notifications/';
    
    const socket = new WebSocket(wsUrl);

    // Connection opened
    socket.addEventListener('open', function(event) {
        console.log('WebSocket connection established');
        // Notify.success('Conectado', 'Notificaciones en tiempo real activadas');
    });

    // Listen for messages
    socket.addEventListener('message', function(event) {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    });

    // Connection closed
    socket.addEventListener('close', function(event) {
        console.log('WebSocket connection closed:', event);
        // Try to reconnect after 5 seconds
        setTimeout(initWebSocket, 5000);
    });

    // Connection error
    socket.addEventListener('error', function(error) {
        console.error('WebSocket error:', error);
    });
}

// Handle incoming WebSocket messages
function handleWebSocketMessage(data) {
    if (!data || !data.type) return;

    const { type, payload } = data;
    
    switch (type) {
        case 'NEW_MESSAGE':
            window.Notifications.chat(
                `Nuevo mensaje de ${payload.sender || 'un contacto'}`,
                payload.message || 'Tienes un nuevo mensaje',
                {
                    duration: 10000,
                    action: {
                        label: 'Abrir chat',
                        callback: () => {
                            // Open chat interface
                            const chatToggle = document.querySelector('#chatbot-toggle');
                            if (chatToggle) chatToggle.click();
                        }
                    }
                }
            );
            break;
            
        case 'STATUS_UPDATE':
            window.Notifications.info(
                'Actualización de estado',
                payload.message || 'El estado de tu solicitud ha cambiado',
                { duration: 8000 }
            );
            break;
            
        case 'SYSTEM_ALERT':
            window.Notifications.system(
                payload.title || 'Notificación del sistema',
                payload.message || 'Hay una actualización disponible',
                { duration: 0 } // Persistent until dismissed
            );
            break;
            
        case 'ERROR':
            window.Notifications.error(
                payload.title || 'Error',
                payload.message || 'Ha ocurrido un error en el sistema',
                { duration: 10000 }
            );
            break;
            
        default:
            console.log('Unhandled WebSocket message type:', type, payload);
    }
}

// Initialize WebSocket connection when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWebSocket);
} else {
    initWebSocket();
}
