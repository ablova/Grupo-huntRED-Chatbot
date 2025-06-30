// Gestión de navegación de tabs optimizada para bajo uso de CPU
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanels = document.querySelectorAll('.tab-panel');

    // Función para cambiar de tab
    function switchTab(e) {
        e.preventDefault();
        // Limpiar estado activo de todos los tabs y paneles
        tabButtons.forEach(btn => {
            btn.classList.remove('tab-active', 'text-red-600', 'border-red-600');
            btn.classList.add('border-transparent');
            btn.setAttribute('aria-selected', 'false');
        });
        tabPanels.forEach(panel => panel.classList.add('hidden'));

        // Activar el tab y panel seleccionado
        const targetPanelId = e.currentTarget.getAttribute('aria-controls');
        const targetPanel = document.getElementById(targetPanelId);
        if (targetPanel) {
            e.currentTarget.classList.add('tab-active', 'text-red-600', 'border-red-600');
            e.currentTarget.setAttribute('aria-selected', 'true');
            targetPanel.classList.remove('hidden');
        } else {
            console.error(`Panel no encontrado: ${targetPanelId}`);
        }
    }

    // Añadir eventos a los botones de tabs
    tabButtons.forEach(btn => {
        btn.addEventListener('click', switchTab);
        btn.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                switchTab(e);
            }
        });
    });

    // Link "Editar" en el panel de resumen
    const goToContacts = document.getElementById('go-to-contacts');
    if (goToContacts) {
        goToContacts.addEventListener('click', function(e) {
            e.preventDefault();
            const contactsTab = document.getElementById('tab-contacts');
            if (contactsTab) {
                contactsTab.click();
                window.scrollTo({ top: contactsTab.offsetTop - 100, behavior: 'smooth' });
            }
        });
    }
}); 