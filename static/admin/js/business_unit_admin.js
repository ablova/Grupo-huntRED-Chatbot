(function($) {
    'use strict';
    
    // Función para formatear JSON
    function formatJSON(json) {
        try {
            return JSON.stringify(json, null, 2);
        } catch (e) {
            return json;
        }
    }
    
    // Función para validar JSON
    function validateJSON(json) {
        try {
            JSON.parse(json);
            return true;
        } catch (e) {
            return false;
        }
    }
    
    // Función para inicializar los editores JSON
    function initJSONEditors() {
        $('.json-field').each(function() {
            const $field = $(this);
            const $textarea = $field.find('textarea');
            const $preview = $('<div class="json-preview"></div>');
            
            // Agregar botón de formato
            const $formatButton = $('<button type="button" class="button format-json">Formatear JSON</button>');
            $field.append($formatButton);
            
            // Agregar vista previa
            $field.append($preview);
            
            // Formatear JSON inicial
            $preview.text(formatJSON($textarea.val()));
            
            // Manejar clic en botón de formato
            $formatButton.on('click', function() {
                const json = $textarea.val();
                if (validateJSON(json)) {
                    const formatted = formatJSON(JSON.parse(json));
                    $textarea.val(formatted);
                    $preview.text(formatted);
                } else {
                    alert('JSON inválido');
                }
            });
            
            // Actualizar vista previa al cambiar el texto
            $textarea.on('input', function() {
                $preview.text(formatJSON($(this).val()));
            });
        });
    }
    
    // Función para manejar la configuración de integraciones
    function initIntegrationConfig() {
        $('.integration-field').each(function() {
            const $field = $(this);
            const $enabled = $field.find('input[type="checkbox"]');
            const $config = $field.find('.integration-config');
            
            // Mostrar/ocultar configuración según estado
            function toggleConfig() {
                if ($enabled.is(':checked')) {
                    $config.show();
                    $field.addClass('enabled').removeClass('disabled');
                } else {
                    $config.hide();
                    $field.addClass('disabled').removeClass('enabled');
                }
            }
            
            // Inicializar estado
            toggleConfig();
            
            // Manejar cambios
            $enabled.on('change', toggleConfig);
        });
    }
    
    // Función para manejar la configuración de precios
    function initPricingConfig() {
        $('.pricing-tier').each(function() {
            const $tier = $(this);
            const $price = $tier.find('.price');
            const $features = $tier.find('.features');
            
            // Agregar botón para agregar características
            const $addFeature = $('<button type="button" class="button add-feature">Agregar Característica</button>');
            $tier.append($addFeature);
            
            // Manejar clic en botón
            $addFeature.on('click', function() {
                const $feature = $('<div class="feature"><input type="text" placeholder="Nueva característica"><button type="button" class="button remove-feature">×</button></div>');
                $features.append($feature);
                
                // Manejar eliminación
                $feature.find('.remove-feature').on('click', function() {
                    $feature.remove();
                });
            });
        });
    }
    
    // Función para manejar la configuración de ATS
    function initATSConfig() {
        $('.ats-config-section').each(function() {
            const $section = $(this);
            const $stages = $section.find('.workflow-stages');
            
            // Agregar botón para agregar etapa
            const $addStage = $('<button type="button" class="button add-stage">Agregar Etapa</button>');
            $section.append($addStage);
            
            // Manejar clic en botón
            $addStage.on('click', function() {
                const $stage = $('<div class="stage"><input type="text" placeholder="Nueva etapa"><button type="button" class="button remove-stage">×</button></div>');
                $stages.append($stage);
                
                // Manejar eliminación
                $stage.find('.remove-stage').on('click', function() {
                    $stage.remove();
                });
            });
        });
    }
    
    // Función para manejar la configuración de analytics
    function initAnalyticsConfig() {
        $('.analytics-metric').each(function() {
            const $metric = $(this);
            const $enabled = $metric.find('input[type="checkbox"]');
            
            // Manejar cambios en métricas
            $enabled.on('change', function() {
                if ($(this).is(':checked')) {
                    $metric.addClass('enabled').removeClass('disabled');
                } else {
                    $metric.addClass('disabled').removeClass('enabled');
                }
            });
        });
    }
    
    // Función para manejar la configuración de learning
    function initLearningConfig() {
        $('.learning-section').each(function() {
            const $section = $(this);
            const $enabled = $section.find('input[type="checkbox"]');
            const $config = $section.find('.learning-config');
            
            // Mostrar/ocultar configuración según estado
            function toggleConfig() {
                if ($enabled.is(':checked')) {
                    $config.show();
                    $section.addClass('enabled').removeClass('disabled');
                } else {
                    $config.hide();
                    $section.addClass('disabled').removeClass('enabled');
                }
            }
            
            // Inicializar estado
            toggleConfig();
            
            // Manejar cambios
            $enabled.on('change', toggleConfig);
        });
    }
    
    // Función para manejar la validación en tiempo real
    function initValidation() {
        $('.validation-field').each(function() {
            const $field = $(this);
            const $input = $field.find('input, textarea, select');
            const $icon = $field.find('.validation-icon');
            
            // Función de validación
            function validate() {
                const value = $input.val();
                let isValid = true;
                
                // Validar campos requeridos
                if ($field.hasClass('required') && !value) {
                    isValid = false;
                }
                
                // Validar JSON
                if ($field.hasClass('json-field') && !validateJSON(value)) {
                    isValid = false;
                }
                
                // Actualizar estado
                if (isValid) {
                    $field.addClass('valid').removeClass('invalid');
                    $icon.text('✓');
                } else {
                    $field.addClass('invalid').removeClass('valid');
                    $icon.text('×');
                }
            }
            
            // Validar al cambiar
            $input.on('input', validate);
            
            // Validar inicialmente
            validate();
        });
    }
    
    // Función para manejar la configuración avanzada
    function initAdvancedConfig() {
        $('.advanced-config-toggle').each(function() {
            const $toggle = $(this);
            const $config = $toggle.next('.advanced-config');
            
            // Ocultar configuración inicialmente
            $config.hide();
            
            // Manejar clic
            $toggle.on('click', function() {
                $config.slideToggle();
                $toggle.text($config.is(':visible') ? 'Ocultar Configuración Avanzada' : 'Mostrar Configuración Avanzada');
            });
        });
    }
    
    // Inicializar todo cuando el documento esté listo
    $(document).ready(function() {
        initJSONEditors();
        initIntegrationConfig();
        initPricingConfig();
        initATSConfig();
        initAnalyticsConfig();
        initLearningConfig();
        initValidation();
        initAdvancedConfig();
    });
    
})(django.jQuery); 