/**
 * Sistema UI/UX Moderno para Grupo huntRED®
 * 
 * Funcionalidades:
 * - Drag & Drop avanzado
 * - Kanban Boards interactivos
 * - Micro-interacciones
 * - Temas dinámicos
 * - Animaciones fluidas
 * - Gestión de estado
 */

class ModernUISystem {
    constructor() {
        this.draggedElement = null;
        this.dropZones = new Set();
        this.kanbanBoards = new Map();
        this.theme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        this.setupTheme();
        this.setupDragAndDrop();
        this.setupKanbanBoards();
        this.setupMicroInteractions();
        this.setupAnimations();
        this.setupEventListeners();
    }

    // ===== GESTIÓN DE TEMAS =====
    setupTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        this.updateThemeColors();
    }

    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.theme);
        document.documentElement.setAttribute('data-theme', this.theme);
        this.updateThemeColors();
        this.animateThemeTransition();
    }

    updateThemeColors() {
        const root = document.documentElement;
        if (this.theme === 'dark') {
            root.style.setProperty('--bg-primary', '#0a0a0a');
            root.style.setProperty('--text-primary', '#ffffff');
        } else {
            root.style.setProperty('--bg-primary', '#ffffff');
            root.style.setProperty('--text-primary', '#1a1a1a');
        }
    }

    animateThemeTransition() {
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }

    // ===== DRAG & DROP AVANZADO =====
    setupDragAndDrop() {
        document.addEventListener('dragstart', this.handleDragStart.bind(this));
        document.addEventListener('dragend', this.handleDragEnd.bind(this));
        document.addEventListener('dragover', this.handleDragOver.bind(this));
        document.addEventListener('drop', this.handleDrop.bind(this));
        document.addEventListener('dragenter', this.handleDragEnter.bind(this));
        document.addEventListener('dragleave', this.handleDragLeave.bind(this));
    }

    handleDragStart(e) {
        if (e.target.classList.contains('draggable') || e.target.closest('.draggable')) {
            this.draggedElement = e.target.classList.contains('draggable') ? e.target : e.target.closest('.draggable');
            this.draggedElement.classList.add('dragging');
            
            // Crear ghost element
            const ghost = this.draggedElement.cloneNode(true);
            ghost.style.opacity = '0.5';
            ghost.style.position = 'absolute';
            ghost.style.pointerEvents = 'none';
            ghost.style.zIndex = '9999';
            document.body.appendChild(ghost);
            
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', this.draggedElement.outerHTML);
            e.dataTransfer.setDragImage(ghost, 0, 0);
            
            // Animar inicio del drag
            this.animateDragStart(this.draggedElement);
        }
    }

    handleDragEnd(e) {
        if (this.draggedElement) {
            this.draggedElement.classList.remove('dragging');
            this.draggedElement = null;
            
            // Limpiar ghost element
            const ghost = document.querySelector('.drag-ghost');
            if (ghost) ghost.remove();
            
            // Limpiar drop zones
            this.dropZones.forEach(zone => {
                zone.classList.remove('drag-over');
            });
            this.dropZones.clear();
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    handleDrop(e) {
        e.preventDefault();
        
        if (this.draggedElement && e.target.closest('.drop-zone')) {
            const dropZone = e.target.closest('.drop-zone');
            const newParent = dropZone.querySelector('.drop-target') || dropZone;
            
            // Animar el drop
            this.animateDrop(this.draggedElement, newParent);
            
            // Mover el elemento
            newParent.appendChild(this.draggedElement);
            
            // Actualizar estado
            this.updateKanbanState();
            
            // Disparar evento personalizado
            this.dispatchCustomEvent('itemDropped', {
                element: this.draggedElement,
                from: this.draggedElement.parentElement,
                to: newParent
            });
        }
    }

    handleDragEnter(e) {
        if (e.target.closest('.drop-zone')) {
            const dropZone = e.target.closest('.drop-zone');
            dropZone.classList.add('drag-over');
            this.dropZones.add(dropZone);
        }
    }

    handleDragLeave(e) {
        if (e.target.closest('.drop-zone')) {
            const dropZone = e.target.closest('.drop-zone');
            if (!dropZone.contains(e.relatedTarget)) {
                dropZone.classList.remove('drag-over');
                this.dropZones.delete(dropZone);
            }
        }
    }

    // ===== KANBAN BOARDS =====
    setupKanbanBoards() {
        const kanbanBoards = document.querySelectorAll('.kanban-board');
        
        kanbanBoards.forEach(board => {
            const boardId = board.dataset.boardId || this.generateId();
            board.dataset.boardId = boardId;
            
            this.kanbanBoards.set(boardId, {
                element: board,
                columns: new Map(),
                items: new Map()
            });
            
            this.initializeKanbanBoard(boardId);
        });
    }

    initializeKanbanBoard(boardId) {
        const board = this.kanbanBoards.get(boardId);
        const columns = board.element.querySelectorAll('.kanban-column');
        
        columns.forEach(column => {
            const columnId = column.dataset.columnId || this.generateId();
            column.dataset.columnId = columnId;
            
            board.columns.set(columnId, {
                element: column,
                items: []
            });
            
            // Hacer items draggables
            const items = column.querySelectorAll('.kanban-item');
            items.forEach(item => {
                item.draggable = true;
                item.classList.add('draggable');
                
                const itemId = item.dataset.itemId || this.generateId();
                item.dataset.itemId = itemId;
                
                board.items.set(itemId, {
                    element: item,
                    columnId: columnId
                });
                
                board.columns.get(columnId).items.push(itemId);
            });
            
            // Actualizar contador
            this.updateColumnCount(columnId);
        });
    }

    updateColumnCount(columnId) {
        const column = document.querySelector(`[data-column-id="${columnId}"]`);
        if (column) {
            const count = column.querySelectorAll('.kanban-item').length;
            const countElement = column.querySelector('.kanban-column-count');
            if (countElement) {
                countElement.textContent = count;
            }
        }
    }

    updateKanbanState() {
        this.kanbanBoards.forEach((board, boardId) => {
            board.columns.forEach((column, columnId) => {
                column.items = [];
                const items = column.element.querySelectorAll('.kanban-item');
                items.forEach(item => {
                    const itemId = item.dataset.itemId;
                    if (itemId) {
                        column.items.push(itemId);
                        board.items.get(itemId).columnId = columnId;
                    }
                });
                this.updateColumnCount(columnId);
            });
        });
    }

    // ===== MICRO-INTERACCIONES =====
    setupMicroInteractions() {
        // Hover effects para cards
        this.setupCardHoverEffects();
        
        // Click effects para botones
        this.setupButtonClickEffects();
        
        // Focus effects para inputs
        this.setupInputFocusEffects();
        
        // Scroll effects
        this.setupScrollEffects();
    }

    setupCardHoverEffects() {
        const cards = document.querySelectorAll('.card-modern');
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                this.animateCardHover(card, true);
            });
            
            card.addEventListener('mouseleave', () => {
                this.animateCardHover(card, false);
            });
        });
    }

    setupButtonClickEffects() {
        const buttons = document.querySelectorAll('.btn-modern');
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.animateButtonClick(button, e);
            });
        });
    }

    setupInputFocusEffects() {
        const inputs = document.querySelectorAll('.input-modern');
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                this.animateInputFocus(input, true);
            });
            
            input.addEventListener('blur', () => {
                this.animateInputFocus(input, false);
            });
        });
    }

    setupScrollEffects() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in-up');
                }
            });
        }, observerOptions);

        const elements = document.querySelectorAll('.card-modern, .kanban-column, .btn-modern');
        elements.forEach(el => observer.observe(el));
    }

    // ===== ANIMACIONES =====
    setupAnimations() {
        // Animaciones de entrada
        this.setupEntranceAnimations();
        
        // Animaciones de hover
        this.setupHoverAnimations();
        
        // Animaciones de transición
        this.setupTransitionAnimations();
    }

    setupEntranceAnimations() {
        const elements = document.querySelectorAll('[data-animate]');
        elements.forEach(element => {
            const animation = element.dataset.animate;
            element.classList.add(`animate-${animation}`);
        });
    }

    setupHoverAnimations() {
        const hoverElements = document.querySelectorAll('[data-hover]');
        hoverElements.forEach(element => {
            const hoverEffect = element.dataset.hover;
            element.addEventListener('mouseenter', () => {
                this.applyHoverEffect(element, hoverEffect);
            });
            
            element.addEventListener('mouseleave', () => {
                this.removeHoverEffect(element, hoverEffect);
            });
        });
    }

    setupTransitionAnimations() {
        // Transiciones suaves para cambios de estado
        document.addEventListener('DOMContentLoaded', () => {
            document.body.classList.add('loaded');
        });
    }

    // ===== MÉTODOS DE ANIMACIÓN =====
    animateDragStart(element) {
        element.style.transform = 'rotate(5deg) scale(1.02)';
        element.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.3)';
        element.style.zIndex = '9999';
    }

    animateDrop(element, newParent) {
        element.style.transform = 'scale(1.05)';
        element.style.boxShadow = '0 10px 20px rgba(59, 130, 246, 0.3)';
        
        setTimeout(() => {
            element.style.transform = '';
            element.style.boxShadow = '';
            element.style.zIndex = '';
        }, 300);
    }

    animateCardHover(card, isHovering) {
        if (isHovering) {
            card.style.transform = 'translateY(-8px) scale(1.02)';
            card.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.15)';
        } else {
            card.style.transform = 'translateY(0) scale(1)';
            card.style.boxShadow = '';
        }
    }

    animateButtonClick(button, event) {
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        `;
        
        button.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    animateInputFocus(input, isFocused) {
        if (isFocused) {
            input.style.transform = 'scale(1.02)';
            input.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
        } else {
            input.style.transform = 'scale(1)';
            input.style.boxShadow = '';
        }
    }

    applyHoverEffect(element, effect) {
        switch (effect) {
            case 'glow':
                element.style.boxShadow = '0 0 20px rgba(59, 130, 246, 0.5)';
                break;
            case 'scale':
                element.style.transform = 'scale(1.05)';
                break;
            case 'lift':
                element.style.transform = 'translateY(-5px)';
                break;
        }
    }

    removeHoverEffect(element, effect) {
        element.style.transform = '';
        element.style.boxShadow = '';
    }

    // ===== EVENT LISTENERS =====
    setupEventListeners() {
        // Theme toggle
        const themeToggle = document.querySelector('[data-theme-toggle]');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Modal controls
        this.setupModalControls();
        
        // Sidebar controls
        this.setupSidebarControls();
        
        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
    }

    setupModalControls() {
        const modalTriggers = document.querySelectorAll('[data-modal]');
        const modalCloses = document.querySelectorAll('[data-modal-close]');
        
        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', () => {
                const modalId = trigger.dataset.modal;
                this.openModal(modalId);
            });
        });
        
        modalCloses.forEach(close => {
            close.addEventListener('click', () => {
                this.closeModal();
            });
        });
    }

    setupSidebarControls() {
        const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
        const sidebar = document.querySelector('.sidebar-modern');
        
        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('show');
            });
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K para búsqueda
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.openSearch();
            }
            
            // Escape para cerrar modales
            if (e.key === 'Escape') {
                this.closeModal();
            }
            
            // Ctrl/Cmd + T para toggle theme
            if ((e.ctrlKey || e.metaKey) && e.key === 't') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }

    // ===== UTILIDADES =====
    generateId() {
        return Math.random().toString(36).substr(2, 9);
    }

    dispatchCustomEvent(eventName, detail) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }

    openModal(modalId) {
        const modal = document.querySelector(`[data-modal-id="${modalId}"]`);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal() {
        const modals = document.querySelectorAll('.modal-modern.show');
        modals.forEach(modal => {
            modal.classList.remove('show');
        });
        document.body.style.overflow = '';
    }

    openSearch() {
        // Implementar búsqueda global
        console.log('Opening search...');
    }

    // ===== API PÚBLICA =====
    static getInstance() {
        if (!ModernUISystem.instance) {
            ModernUISystem.instance = new ModernUISystem();
        }
        return ModernUISystem.instance;
    }

    // Métodos públicos para uso externo
    addKanbanItem(boardId, columnId, itemData) {
        const board = this.kanbanBoards.get(boardId);
        if (board) {
            const column = board.columns.get(columnId);
            if (column) {
                const item = this.createKanbanItem(itemData);
                column.element.querySelector('.kanban-items').appendChild(item);
                this.updateColumnCount(columnId);
            }
        }
    }

    createKanbanItem(data) {
        const item = document.createElement('div');
        item.className = 'kanban-item draggable';
        item.draggable = true;
        item.dataset.itemId = this.generateId();
        
        item.innerHTML = `
            <div class="item-header">
                <h4>${data.title}</h4>
                <span class="item-priority ${data.priority}">${data.priority}</span>
            </div>
            <p>${data.description}</p>
            <div class="item-footer">
                <span class="item-assignee">${data.assignee}</span>
                <span class="item-date">${data.dueDate}</span>
            </div>
        `;
        
        return item;
    }
}

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', () => {
    const ui = ModernUISystem.getInstance();
    
    // Exponer globalmente para uso en otros scripts
    window.ModernUI = ui;
});

// ===== CSS ANIMATIONS =====
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .loaded {
        opacity: 1;
        transition: opacity 0.3s ease;
    }
    
    body:not(.loaded) {
        opacity: 0;
    }
`;
document.head.appendChild(style); 