/* 
 * Message Log Admin JS
 * Script para mejorar la funcionalidad de la página de administración de MessageLog
 * Específicamente para Meta Conversations 2025
 */

(function($) {
    'use strict';
    
    // Ejecutar cuando el DOM esté listo
    $(document).ready(function() {
        // Añadir botón de reportes a la lista de herramientas si existe la URL
        if (typeof reportUrl !== 'undefined' && $('#changelist-form').length > 0) {
            const $tools = $('.object-tools');
            if ($tools.length && !$tools.find('.reportlink').length) {
                $tools.prepend(
                    '<li><a href="' + reportUrl + '" class="reportlink">' +
                    'Ver Dashboard Meta Conversations</a></li>'
                );
            }
        }
        
        // Destacar canales de Meta Conversations
        $('#result_list tbody tr').each(function() {
            const $row = $(this);
            const $channelCell = $row.find('td.field-channel');
            const channelValue = $channelCell.text().trim().toLowerCase();
            
            if (['whatsapp', 'messenger', 'instagram'].includes(channelValue)) {
                $channelCell.attr('data-value', channelValue);
                $row.addClass('meta-channel-row');
            }
        });
        
        // Mejorar la visualización de los costos Meta
        $('.field-meta_cost').each(function() {
            const $cell = $(this);
            const costValue = parseFloat($cell.text().trim());
            
            if (!isNaN(costValue) && costValue > 0) {
                $cell.addClass('has-cost');
            }
        });
        
        // Añadir filtros avanzados desplegables
        const $filterButton = $('<button type="button" class="toggle-filters">Mostrar filtros avanzados</button>');
        const $advancedFilters = $('<div class="advanced-filters" style="display:none;"></div>');
        
        $advancedFilters.html(`
            <h3>Filtros avanzados para Meta Conversations 2025</h3>
            <div class="form-row">
                <div class="form-group">
                    <label for="filter-pricing-model">Modelo de precio:</label>
                    <select id="filter-pricing-model" name="meta_pricing_model">
                        <option value="">Todos</option>
                        <option value="standard">Estándar</option>
                        <option value="premium">Premium</option>
                        <option value="business">Business</option>
                        <option value="enterprise">Enterprise</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="filter-pricing-type">Tipo de precio:</label>
                    <select id="filter-pricing-type" name="meta_pricing_type">
                        <option value="">Todos</option>
                        <option value="message">Por mensaje</option>
                        <option value="session">Por sesión</option>
                        <option value="api_call">Por API call</option>
                        <option value="template">Por plantilla</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="filter-date-start">Fecha inicio:</label>
                    <input type="date" id="filter-date-start" name="sent_at__gte">
                </div>
                <div class="form-group">
                    <label for="filter-date-end">Fecha fin:</label>
                    <input type="date" id="filter-date-end" name="sent_at__lte">
                </div>
            </div>
        `);
        
        // Insertar filtros avanzados en el DOM
        if ($('#changelist-filter').length) {
            $filterButton.insertBefore('#changelist-filter');
            $advancedFilters.insertAfter($filterButton);
            
            $filterButton.on('click', function() {
                $advancedFilters.slideToggle();
                const buttonText = $advancedFilters.is(':visible') ? 
                    'Ocultar filtros avanzados' : 'Mostrar filtros avanzados';
                $filterButton.text(buttonText);
            });
        }
        
        // Añadir exportación rápida a CSV
        if ($('.object-tools').length && $('.actions').length) {
            $('.object-tools').append(
                '<li><a href="#" class="export" id="export-csv">Exportar visualización actual</a></li>'
            );
            
            $('#export-csv').on('click', function(e) {
                e.preventDefault();
                
                // Obtener todos los parámetros actuales de la URL
                const currentUrl = window.location.href;
                const exportUrl = currentUrl + (currentUrl.includes('?') ? '&' : '?') + 'export=csv';
                
                window.location.href = exportUrl;
            });
        }
        
        // Añadir tooltips informativos
        $('.help').attr('title', 'Meta Conversations 2025: Esta información ayuda a rastrear y reportar el uso y costos de mensajería a través de WhatsApp, Messenger e Instagram.');
    });
    
})(django.jQuery);
