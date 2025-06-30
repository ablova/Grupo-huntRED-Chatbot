/**
 * UTILIDADES JAVASCRIPT - Grupo huntRED®
 * Funciones centralizadas y reutilizables
 */

// ===== UTILIDADES DE DOM =====

const DOMUtils = {
    /**
     * Crea un elemento con atributos
     */
    createElement(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);
        
        // Aplicar atributos
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'textContent') {
                element.textContent = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else {
                element.setAttribute(key, value);
            }
        });
        
        // Agregar hijos
        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else {
                element.appendChild(child);
            }
        });
        
        return element;
    },
    
    /**
     * Busca elementos con selector
     */
    find(selector, parent = document) {
        return parent.querySelector(selector);
    },
    
    /**
     * Busca múltiples elementos
     */
    findAll(selector, parent = document) {
        return Array.from(parent.querySelectorAll(selector));
    },
    
    /**
     * Verifica si elemento existe
     */
    exists(selector) {
        return !!this.find(selector);
    },
    
    /**
     * Toggle de clases
     */
    toggleClass(element, className) {
        element.classList.toggle(className);
    },
    
    /**
     * Agregar/remover clases
     */
    setClass(element, className, add = true) {
        if (add) {
            element.classList.add(className);
        } else {
            element.classList.remove(className);
        }
    }
};

// ===== UTILIDADES DE EVENTOS =====

const EventUtils = {
    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Throttle function
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    /**
     * Event delegation
     */
    delegate(parent, eventType, selector, handler) {
        parent.addEventListener(eventType, function(event) {
            const target = event.target.closest(selector);
            if (target && parent.contains(target)) {
                handler.call(target, event);
            }
        });
    }
};

// ===== UTILIDADES DE STORAGE =====

const StorageUtils = {
    /**
     * Guardar en localStorage
     */
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('Error guardando en localStorage:', e);
            return false;
        }
    },
    
    /**
     * Obtener de localStorage
     */
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Error obteniendo de localStorage:', e);
            return defaultValue;
        }
    },
    
    /**
     * Remover de localStorage
     */
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Error removiendo de localStorage:', e);
            return false;
        }
    },
    
    /**
     * Limpiar localStorage
     */
    clear() {
        try {
            localStorage.clear();
            return true;
        } catch (e) {
            console.error('Error limpiando localStorage:', e);
            return false;
        }
    }
};

// ===== UTILIDADES DE VALIDACIÓN =====

const ValidationUtils = {
    /**
     * Validar email
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    /**
     * Validar teléfono
     */
    isValidPhone(phone) {
        const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
        return phoneRegex.test(phone.replace(/\s/g, ''));
    },
    
    /**
     * Validar URL
     */
    isValidURL(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },
    
    /**
     * Validar formulario
     */
    validateForm(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        let isValid = true;
        
        inputs.forEach(input => {
            if (input.hasAttribute('required') && !input.value.trim()) {
                this.showError(input, 'Este campo es requerido');
                isValid = false;
            } else if (input.type === 'email' && input.value && !this.isValidEmail(input.value)) {
                this.showError(input, 'Email inválido');
                isValid = false;
            } else {
                this.clearError(input);
            }
        });
        
        return isValid;
    },
    
    /**
     * Mostrar error
     */
    showError(input, message) {
        this.clearError(input);
        input.classList.add('error');
        
        const errorDiv = DOMUtils.createElement('div', {
            className: 'error-message',
            textContent: message
        });
        
        input.parentNode.appendChild(errorDiv);
    },
    
    /**
     * Limpiar error
     */
    clearError(input) {
        input.classList.remove('error');
        const errorDiv = input.parentNode.querySelector('.error-message');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
};

// ===== UTILIDADES DE FORMATO =====

const FormatUtils = {
    /**
     * Formatear fecha
     */
    formatDate(date, format = 'DD/MM/YYYY') {
        const d = new Date(date);
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        
        return format
            .replace('DD', day)
            .replace('MM', month)
            .replace('YYYY', year);
    },
    
    /**
     * Formatear moneda
     */
    formatCurrency(amount, currency = 'USD', locale = 'es-ES') {
        return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency
        }).format(amount);
    },
    
    /**
     * Formatear número
     */
    formatNumber(number, locale = 'es-ES') {
        return new Intl.NumberFormat(locale).format(number);
    },
    
    /**
     * Formatear porcentaje
     */
    formatPercentage(value, decimals = 1) {
        return `${(value * 100).toFixed(decimals)}%`;
    },
    
    /**
     * Formatear tamaño de archivo
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
};

// ===== UTILIDADES DE API =====

const APIUtils = {
    /**
     * Request HTTP
     */
    async request(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    },
    
    /**
     * GET request
     */
    async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        
        return this.request(fullUrl, { method: 'GET' });
    },
    
    /**
     * POST request
     */
    async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    /**
     * PUT request
     */
    async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    /**
     * DELETE request
     */
    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
};

// ===== UTILIDADES DE ANIMACIÓN =====

const AnimationUtils = {
    /**
     * Fade in
     */
    fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.min(progress / duration, 1);
            
            element.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    },
    
    /**
     * Fade out
     */
    fadeOut(element, duration = 300) {
        let start = null;
        const initialOpacity = parseFloat(getComputedStyle(element).opacity);
        
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.max(initialOpacity - (progress / duration), 0);
            
            element.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
            }
        };
        
        requestAnimationFrame(animate);
    },
    
    /**
     * Slide down
     */
    slideDown(element, duration = 300) {
        element.style.height = '0px';
        element.style.overflow = 'hidden';
        element.style.display = 'block';
        
        const targetHeight = element.scrollHeight;
        let start = null;
        
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const height = Math.min((progress / duration) * targetHeight, targetHeight);
            
            element.style.height = height + 'px';
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                element.style.height = 'auto';
                element.style.overflow = 'visible';
            }
        };
        
        requestAnimationFrame(animate);
    },
    
    /**
     * Slide up
     */
    slideUp(element, duration = 300) {
        const targetHeight = element.scrollHeight;
        element.style.height = targetHeight + 'px';
        element.style.overflow = 'hidden';
        
        let start = null;
        
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const height = Math.max(targetHeight - (progress / duration) * targetHeight, 0);
            
            element.style.height = height + 'px';
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
                element.style.height = 'auto';
                element.style.overflow = 'visible';
            }
        };
        
        requestAnimationFrame(animate);
    }
};

// ===== UTILIDADES DE NOTIFICACIONES =====

const NotificationUtils = {
    /**
     * Mostrar notificación
     */
    show(message, type = 'info', duration = 5000) {
        const notification = DOMUtils.createElement('div', {
            className: `notification notification-${type}`,
            innerHTML: `
                <div class="notification-content">
                    <span class="notification-message">${message}</span>
                    <button class="notification-close">&times;</button>
                </div>
            `
        });
        
        // Agregar al DOM
        const container = this.getContainer();
        container.appendChild(notification);
        
        // Animar entrada
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Auto cerrar
        if (duration > 0) {
            setTimeout(() => {
                this.hide(notification);
            }, duration);
        }
        
        // Evento de cerrar
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            this.hide(notification);
        });
        
        return notification;
    },
    
    /**
     * Ocultar notificación
     */
    hide(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    },
    
    /**
     * Obtener contenedor de notificaciones
     */
    getContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = DOMUtils.createElement('div', {
                id: 'notification-container',
                className: 'notification-container'
            });
            document.body.appendChild(container);
        }
        return container;
    },
    
    /**
     * Métodos de conveniencia
     */
    success(message, duration) {
        return this.show(message, 'success', duration);
    },
    
    error(message, duration) {
        return this.show(message, 'error', duration);
    },
    
    warning(message, duration) {
        return this.show(message, 'warning', duration);
    },
    
    info(message, duration) {
        return this.show(message, 'info', duration);
    }
};

// ===== EXPORTAR UTILIDADES =====

window.Utils = {
    DOM: DOMUtils,
    Event: EventUtils,
    Storage: StorageUtils,
    Validation: ValidationUtils,
    Format: FormatUtils,
    API: APIUtils,
    Animation: AnimationUtils,
    Notification: NotificationUtils
};

// ===== INICIALIZACIÓN =====

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Utils cargadas correctamente');
}); 