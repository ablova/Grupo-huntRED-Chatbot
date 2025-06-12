// Matchmaking Interactive Component
document.addEventListener('DOMContentLoaded', function() {
    // Business Units Data
    const businessUnits = [
        { id: 'huntred-executive', name: 'huntRED® Executive', color: 'from-blue-500 to-indigo-600' },
        { id: 'huntred', name: 'huntRED®', color: 'from-purple-500 to-pink-600' },
        { id: 'huntu', name: 'huntU', color: 'from-green-500 to-emerald-600' },
        { id: 'amigro', name: 'Amigro', color: 'from-amber-500 to-orange-600' }
    ];

    // Industries Data
    const industries = [
        'Servicios Financieros', 'Legal', 'Energía', 'Healthcare', 
        'Finanzas y Contabilidad', 'Ventas y Mercadotecnia', 
        'Manufactura e Industria', 'Tecnologías de la Información', 'Sustentabilidad'
    ];

    // Match Factors
    const matchFactors = [
        {
            id: 'skills',
            name: 'Habilidades Técnicas',
            description: 'Evaluación de habilidades técnicas específicas requeridas para el puesto.',
            weight: 25
        },
        {
            id: 'experience',
            name: 'Experiencia Laboral',
            description: 'Años de experiencia relevante en el campo y puestos similares.',
            weight: 20
        },
        {
            id: 'education',
            name: 'Formación Académica',
            description: 'Nivel educativo y relevancia de la formación con el puesto.',
            weight: 15
        },
        {
            id: 'personality',
            name: 'Perfil de Personalidad',
            description: 'Alineación del perfil de personalidad con la cultura organizacional.',
            weight: 15
        },
        {
            id: 'salary',
            name: 'Expectativas Salariales',
            description: 'Alineación entre expectativas salariales y rango del puesto.',
            weight: 10
        },
        {
            id: 'location',
            name: 'Ubicación y Movilidad',
            description: 'Disponibilidad para movilizarse o trabajar en la ubicación requerida.',
            weight: 5
        },
        {
            id: 'languages',
            name: 'Idiomas',
            description: 'Dominio de idiomas requeridos para el puesto.',
            weight: 5
        },
        {
            id: 'certifications',
            name: 'Certificaciones',
            description: 'Certificaciones profesionales relevantes para el puesto.',
            weight: 3
        },
        {
            id: 'soft-skills',
            name: 'Habilidades Blandas',
            description: 'Competencias interpersonales y de comunicación.',
            weight: 2
        }
    ];

    // Initialize the component
    function initMatchmaking() {
        const container = document.getElementById('matchmaking-container');
        if (!container) return;

        // Render business unit selector
        const buSelect = document.createElement('div');
        buSelect.className = 'mb-8';
        buSelect.innerHTML = `
            <h3 class="text-lg font-semibold mb-3 text-slate-800 dark:text-white">Selecciona tu Unidad de Negocio</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                ${businessUnits.map(bu => `
                    <button 
                        onclick="selectBusinessUnit('${bu.id}')" 
                        class="business-unit-btn p-4 rounded-xl text-center transition-all duration-300 hover:shadow-lg ${bu.id === 'huntred' ? 'bg-gradient-to-r ' + bu.color + ' text-white' : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300'}"
                        data-id="${bu.id}"
                    >
                        <div class="text-2xl mb-2">${getBusinessUnitIcon(bu.id)}</div>
                        <span class="font-medium">${bu.name}</span>
                    </button>
                `).join('')}
            </div>
        `;
        container.appendChild(buSelect);

        // Render industry selector
        const industrySelect = document.createElement('div');
        industrySelect.className = 'mb-8';
        industrySelect.innerHTML = `
            <h3 class="text-lg font-semibold mb-3 text-slate-800 dark:text-white">Selecciona la Industria</h3>
            <select id="industry-select" class="w-full p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                <option value="">-- Selecciona una industria --</option>
                ${industries.map(ind => `<option value="${ind.toLowerCase().replace(/\s+/g, '-')}">${ind}</option>`).join('')}
            </select>
        `;
        container.appendChild(industrySelect);

        // Render match factors
        const factorsSection = document.createElement('div');
        factorsSection.className = 'mt-12';
        factorsSection.innerHTML = `
            <h3 class="text-2xl font-bold mb-6 text-slate-800 dark:text-white">Factores de Match</h3>
            <p class="text-slate-600 dark:text-slate-300 mb-8">
                Nuestro algoritmo analiza múltiples factores para encontrar la mejor coincidencia entre candidatos y oportunidades. 
                Ajusta los pesos según la importancia para tu búsqueda.
            </p>
            <div id="factors-container" class="space-y-6">
                ${matchFactors.map((factor, index) => renderFactor(factor, index)).join('')}
            </div>
        `;
        container.appendChild(factorsSection);

        // Add event listeners
        document.getElementById('industry-select').addEventListener('change', calculateMatch);
        document.querySelectorAll('.factor-slider').forEach(slider => {
            slider.addEventListener('input', calculateMatch);
        });
    }

    // Render a single factor row
    function renderFactor(factor, index) {
        return `
            <div class="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div class="flex-1">
                        <div class="flex items-center mb-1">
                            <span class="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400 text-sm font-medium mr-3">${index + 1}</span>
                            <h4 class="text-lg font-semibold text-slate-800 dark:text-white">${factor.name}</h4>
                        </div>
                        <p class="text-slate-600 dark:text-slate-400 text-sm pl-11">
                            ${factor.description}
                        </p>
                    </div>
                    <div class="w-full md:w-64">
                        <div class="flex justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                            <span>Baja</span>
                            <span>Alta</span>
                        </div>
                        <input 
                            type="range" 
                            min="1" 
                            max="5" 
                            value="${factor.weight / 5}" 
                            class="factor-slider w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer"
                            data-factor="${factor.id}"
                        >
                    </div>
                </div>
            </div>
        `;
    }

    // Calculate match score
    function calculateMatch() {
        const industry = document.getElementById('industry-select').value;
        if (!industry) return;

        // In a real implementation, this would call an API to calculate the match
        // For now, we'll simulate a calculation
        const totalWeight = matchFactors.reduce((sum, factor) => {
            const slider = document.querySelector(`.factor-slider[data-factor="${factor.id}"]`);
            return sum + (parseInt(slider.value) * 5);
        }, 0);

        const maxScore = matchFactors.length * 25; // 5 (max slider) * 5 (weight multiplier)
        const matchPercentage = Math.min(100, Math.round((totalWeight / maxScore) * 100));

        // Update UI with match result
        updateMatchResult(matchPercentage);
    }

    // Update match result UI
    function updateMatchResult(percentage) {
        let resultDiv = document.getElementById('match-result');
        
        if (!resultDiv) {
            resultDiv = document.createElement('div');
            resultDiv.id = 'match-result';
            resultDiv.className = 'mt-12 p-8 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-slate-800/50 dark:to-slate-900/50 rounded-2xl border border-indigo-100 dark:border-slate-700';
            document.getElementById('matchmaking-container').appendChild(resultDiv);
        }

        resultDiv.innerHTML = `
            <div class="text-center">
                <div class="inline-flex items-center justify-center w-32 h-32 rounded-full bg-white dark:bg-slate-800 border-4 border-indigo-100 dark:border-slate-700 mb-6 relative">
                    <div class="absolute inset-0 rounded-full border-4 border-transparent" 
                         style="background: conic-gradient(#4f46e5 0% ${percentage}%, #e0e7ff ${percentage}% 100%);">
                    </div>
                    <div class="w-28 h-28 rounded-full bg-white dark:bg-slate-900 flex items-center justify-center">
                        <span class="text-3xl font-bold text-indigo-600 dark:text-indigo-400">${percentage}%</span>
                    </div>
                </div>
                <h3 class="text-2xl font-bold text-slate-800 dark:text-white mb-2">¡Excelente coincidencia!</h3>
                <p class="text-slate-600 dark:text-slate-300 mb-6 max-w-2xl mx-auto">
                    Basado en tus criterios, hemos encontrado una coincidencia del ${percentage}% con las oportunidades disponibles.
                    Nuestro equipo se pondrá en contacto contigo pronto.
                </p>
                <button class="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors duration-300">
                    Ver Oportunidades Relacionadas
                </button>
            </div>
        `;
    }

    // Helper function to get business unit icon
    function getBusinessUnitIcon(id) {
        const icons = {
            'huntred-executive': '👔',
            'huntred': '💼',
            'huntu': '🎓',
            'amigro': '🌎'
        };
        return icons[id] || '🏢';
    }

    // Global function for business unit selection
    window.selectBusinessUnit = function(buId) {
        // Update UI
        document.querySelectorAll('.business-unit-btn').forEach(btn => {
            const btnBuId = btn.getAttribute('data-id');
            const buData = businessUnits.find(bu => bu.id === btnBuId);
            
            if (btnBuId === buId) {
                btn.className = `p-4 rounded-xl text-center transition-all duration-300 hover:shadow-lg bg-gradient-to-r ${buData.color} text-white`;
            } else {
                btn.className = 'p-4 rounded-xl text-center transition-all duration-300 hover:shadow-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300';
            }
        });

        // In a real implementation, this would filter opportunities by business unit
        calculateMatch();
    };

    // Initialize the component
    initMatchmaking();
});
