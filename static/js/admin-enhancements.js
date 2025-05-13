// Mejoras en la UX del admin de Django

// Mejoras en los filtros
document.addEventListener('DOMContentLoaded', function() {
    // Expandir filtros por defecto
    const filterToggle = document.querySelector('.changelist-filter-toggle');
    if (filterToggle) {
        filterToggle.click();
    }

    // Mejorar la interacción con los filtros
    const filterLinks = document.querySelectorAll('.changelist-filter a');
    filterLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const filterSection = this.closest('.changelist-filter');
            if (filterSection) {
                const filterItems = filterSection.querySelectorAll('li');
                filterItems.forEach(item => {
                    item.classList.remove('active');
                });
                this.closest('li').classList.add('active');
            }
        });
    });
});

// Mejoras en las acciones en bulk
function setupBulkActions() {
    const bulkActions = document.querySelector('.bulk-actions');
    if (bulkActions) {
        const selectAll = document.querySelector('input[type=checkbox].action-select');
        const checkboxes = document.querySelectorAll('input[type=checkbox].action-select');
        
        selectAll.addEventListener('change', function() {
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }
}

// Mejoras en la tabla de resultados
function enhanceResultsTable() {
    const table = document.querySelector('.results');
    if (table) {
        // Añadir tooltips a los estados
        const statusTags = document.querySelectorAll('.status-tag');
        statusTags.forEach(tag => {
            const tooltip = document.createElement('span');
            tooltip.className = 'tooltip';
            tooltip.textContent = tag.textContent;
            tag.appendChild(tooltip);
        });

        // Mejorar el scroll horizontal
        table.closest('.table-responsive').style.overflowX = 'auto';
    }
}

// Mejoras en los formularios
function enhanceForms() {
    const forms = document.querySelectorAll('.form-row');
    forms.forEach(form => {
        // Mejorar el feedback de validación
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                this.classList.remove('focused');
            });
        });
    });
}

// Inicializar todas las mejoras
document.addEventListener('DOMContentLoaded', function() {
    setupBulkActions();
    enhanceResultsTable();
    enhanceForms();
});

// Manejar cambios en el tamaño de la ventana
window.addEventListener('resize', function() {
    enhanceResultsTable();
});
