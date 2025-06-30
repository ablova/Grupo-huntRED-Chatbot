/**
 * Sistema de Tabs Robusto para Propuestas huntRED
 * Maneja la navegación entre secciones con accesibilidad completa
 */

class ProposalTabs {
    constructor() {
        this.tabs = document.querySelectorAll('.tab-button');
        this.panels = document.querySelectorAll('.tab-panel');
        this.currentTab = null;
        this.init();
    }

    init() {
        // Configurar event listeners
        this.tabs.forEach(tab => {
            tab.addEventListener('click', (e) => this.switchTab(e));
            tab.addEventListener('keydown', (e) => this.handleKeydown(e));
        });

        // Configurar navegación por teclado
        document.addEventListener('keydown', (e) => this.handleGlobalKeydown(e));

        // Inicializar estado
        this.initializeState();

        // Configurar enlaces internos
        this.setupInternalLinks();

        console.log('Sistema de tabs inicializado correctamente');
    }

    initializeState() {
        // Asegurar que solo el primer tab esté activo
        this.tabs.forEach((tab, index) => {
            if (index === 0) {
                tab.classList.add('tab-active', 'text-red-600', 'border-red-600', 'bg-red-50');
                tab.setAttribute('aria-selected', 'true');
            } else {
                tab.classList.remove('tab-active', 'text-red-600', 'border-red-600', 'bg-red-50');
                tab.classList.add('text-gray-500', 'border-transparent');
                tab.setAttribute('aria-selected', 'false');
            }
        });

        // Asegurar que solo el primer panel esté visible
        this.panels.forEach((panel, index) => {
            if (index === 0) {
                panel.classList.add('active');
                panel.classList.remove('hidden');
            } else {
                panel.classList.remove('active');
                panel.classList.add('hidden');
            }
        });

        this.currentTab = this.tabs[0];
    }

    switchTab(event) {
        event.preventDefault();
        const targetTab = event.currentTarget;
        const targetId = targetTab.id.replace('tab-', 'panel-');
        const targetPanel = document.getElementById(targetId);

        if (!targetPanel) {
            console.error('Panel no encontrado:', targetId);
            return;
        }

        // Actualizar tabs
        this.tabs.forEach(tab => {
            tab.classList.remove('tab-active', 'text-red-600', 'border-red-600', 'bg-red-50');
            tab.classList.add('text-gray-500', 'border-transparent');
            tab.setAttribute('aria-selected', 'false');
        });

        targetTab.classList.remove('text-gray-500', 'border-transparent');
        targetTab.classList.add('tab-active', 'text-red-600', 'border-red-600', 'bg-red-50');
        targetTab.setAttribute('aria-selected', 'true');

        // Actualizar panels
        this.panels.forEach(panel => {
            panel.classList.remove('active');
            panel.classList.add('hidden');
        });

        targetPanel.classList.remove('hidden');
        targetPanel.classList.add('active');

        // Actualizar estado actual
        this.currentTab = targetTab;

        // Scroll suave al panel
        this.scrollToPanel(targetPanel);

        // Disparar evento personalizado
        this.dispatchTabChangeEvent(targetTab, targetPanel);
    }

    scrollToPanel(panel) {
        const offset = 100; // Offset para el header
        const panelTop = panel.offsetTop - offset;
        
        window.scrollTo({
            top: panelTop,
            behavior: 'smooth'
        });
    }

    handleKeydown(event) {
        const key = event.key;
        
        switch (key) {
            case 'Enter':
            case ' ':
                event.preventDefault();
                this.switchTab(event);
                break;
            case 'ArrowRight':
            case 'ArrowDown':
                event.preventDefault();
                this.navigateTabs(1);
                break;
            case 'ArrowLeft':
            case 'ArrowUp':
                event.preventDefault();
                this.navigateTabs(-1);
                break;
            case 'Home':
                event.preventDefault();
                this.goToFirstTab();
                break;
            case 'End':
                event.preventDefault();
                this.goToLastTab();
                break;
        }
    }

    handleGlobalKeydown(event) {
        // Atajos de teclado globales
        if (event.altKey) {
            const key = event.key;
            let tabIndex = -1;

            switch (key) {
                case '1':
                    tabIndex = 0;
                    break;
                case '2':
                    tabIndex = 1;
                    break;
                case '3':
                    tabIndex = 2;
                    break;
                case '4':
                    tabIndex = 3;
                    break;
                case '5':
                    tabIndex = 4;
                    break;
            }

            if (tabIndex >= 0 && tabIndex < this.tabs.length) {
                event.preventDefault();
                this.tabs[tabIndex].click();
            }
        }
    }

    navigateTabs(direction) {
        const currentIndex = Array.from(this.tabs).indexOf(this.currentTab);
        const newIndex = (currentIndex + direction + this.tabs.length) % this.tabs.length;
        this.tabs[newIndex].click();
    }

    goToFirstTab() {
        this.tabs[0].click();
    }

    goToLastTab() {
        this.tabs[this.tabs.length - 1].click();
    }

    setupInternalLinks() {
        // Configurar enlaces internos como "go-to-contacts"
        const internalLinks = document.querySelectorAll('[id^="go-to-"]');
        internalLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetTabName = link.id.replace('go-to-', '');
                const targetTab = document.getElementById(`tab-${targetTabName}`);
                if (targetTab) {
                    targetTab.click();
                }
            });
        });
    }

    dispatchTabChangeEvent(tab, panel) {
        const event = new CustomEvent('tabChanged', {
            detail: {
                tab: tab,
                panel: panel,
                tabId: tab.id,
                panelId: panel.id
            }
        });
        document.dispatchEvent(event);
    }

    // Métodos públicos para control externo
    goToTab(tabName) {
        const tab = document.getElementById(`tab-${tabName}`);
        if (tab) {
            tab.click();
        }
    }

    getCurrentTab() {
        return this.currentTab;
    }

    getCurrentPanel() {
        const currentTabId = this.currentTab.id;
        const panelId = currentTabId.replace('tab-', 'panel-');
        return document.getElementById(panelId);
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    // Verificar que los elementos existen
    const tabsExist = document.querySelectorAll('.tab-button').length > 0;
    const panelsExist = document.querySelectorAll('.tab-panel').length > 0;

    if (tabsExist && panelsExist) {
        window.proposalTabs = new ProposalTabs();
        console.log('Sistema de tabs de propuesta inicializado');
    } else {
        console.warn('Elementos de tabs no encontrados en la página');
    }
});

// Exportar para uso global
if (typeof window !== 'undefined') {
    window.ProposalTabs = ProposalTabs;
} 