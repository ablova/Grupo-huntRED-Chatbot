/**
 * SocialLink™ - Visualización de red social para CV de candidatos
 * Sistema inteligente para mostrar relaciones entre candidatos de Amigro
 */

class SocialGraph {
    /**
     * Inicializa el grafo social
     * @param {string} containerId - ID del elemento contenedor
     * @param {Object} data - Datos de conexiones sociales
     * @param {Object} options - Opciones de visualización
     */
    constructor(containerId, data, options = {}) {
        this.containerId = containerId;
        this.data = data;
        this.options = Object.assign({
            width: 300,
            height: 200,
            nodeRadius: 25,
            colors: {
                primary: "#0078D7",
                secondary: "#EAEAEA",
                highlight: "#00B294",
                connection: {
                    friend: "#4CAF50",     // Verde
                    family: "#9C27B0",     // Púrpura
                    colleague: "#2196F3",  // Azul
                    classmate: "#FF9800",  // Naranja
                    referral: "#795548"    // Marrón
                }
            },
            labels: {
                show: true,
                fontSize: 10
            },
            animations: true,
            strength: 0.3,
            centerForce: 0.1
        }, options);
        
        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        
        this._init();
    }
    
    /**
     * Inicializa el grafo
     * @private
     */
    _init() {
        if (!this.data || !this.data.nodes || !this.data.links) {
            console.error("SocialGraph: Datos inválidos");
            return;
        }
        
        this.nodes = this.data.nodes;
        this.links = this.data.links;
        
        // Crear SVG
        this.svg = d3.select(`#${this.containerId}`)
            .append("svg")
            .attr("width", this.options.width)
            .attr("height", this.options.height)
            .attr("class", "social-graph");
            
        // Crear defs para los marcadores de flecha (opcional)
        if (this.options.arrows) {
            const defs = this.svg.append("defs");
            defs.append("marker")
                .attr("id", "arrow")
                .attr("viewBox", "0 -5 10 10")
                .attr("refX", 20)
                .attr("refY", 0)
                .attr("markerWidth", 6)
                .attr("markerHeight", 6)
                .attr("orient", "auto")
                .append("path")
                .attr("d", "M0,-5L10,0L0,5")
                .attr("fill", "#999");
        }
        
        // Crear grupos para enlaces y nodos
        const g = this.svg.append("g");
        
        // Crear enlaces
        this.linkElements = g.append("g")
            .selectAll("line")
            .data(this.links)
            .enter()
            .append("line")
            .attr("stroke-width", d => Math.sqrt(d.strength || 1) * 2)
            .attr("stroke", d => this.options.colors.connection[d.type] || "#999")
            .attr("stroke-opacity", 0.6)
            .attr("marker-end", this.options.arrows ? "url(#arrow)" : "");
            
        // Crear grupos de nodos (para combinar círculo y texto)
        this.nodeGroups = g.append("g")
            .selectAll(".node")
            .data(this.nodes)
            .enter()
            .append("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", this._dragStarted.bind(this))
                .on("drag", this._dragged.bind(this))
                .on("end", this._dragEnded.bind(this)));
                
        // Añadir círculos a los nodos
        this.nodeGroups.append("circle")
            .attr("r", d => this.options.nodeRadius * (d.main ? 1.2 : 0.8))
            .attr("fill", d => d.main ? this.options.colors.primary : this.options.colors.secondary)
            .attr("stroke", "#fff")
            .attr("stroke-width", 1.5);
            
        // Añadir iniciales a los nodos
        this.nodeGroups.append("text")
            .attr("text-anchor", "middle")
            .attr("dominant-baseline", "central")
            .attr("fill", "#fff")
            .attr("font-weight", "bold")
            .text(d => this._getInitials(d.name));
            
        // Añadir etiquetas de nombre
        if (this.options.labels.show) {
            this.nodeGroups.append("text")
                .attr("text-anchor", "middle")
                .attr("y", this.options.nodeRadius + 12)
                .attr("font-size", this.options.labels.fontSize)
                .attr("fill", "#333")
                .text(d => d.name);
        }
        
        // Tooltip para información adicional
        this.nodeGroups.append("title")
            .text(d => `${d.name}\n${d.role || ""}`);
            
        // Iniciar simulación física
        this.simulation = d3.forceSimulation(this.nodes)
            .force("link", d3.forceLink(this.links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(this.options.width / 2, this.options.height / 2))
            .force("collision", d3.forceCollide().radius(this.options.nodeRadius * 1.5))
            .on("tick", this._ticked.bind(this));
    }
    
    /**
     * Actualiza posiciones en cada tick de la simulación
     * @private
     */
    _ticked() {
        this.linkElements
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
            
        this.nodeGroups
            .attr("transform", d => `translate(${d.x},${d.y})`);
    }
    
    /**
     * Maneja inicio de arrastre
     * @private
     */
    _dragStarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    /**
     * Maneja arrastre en proceso
     * @private
     */
    _dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    /**
     * Maneja fin de arrastre
     * @private
     */
    _dragEnded(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        if (!this.options.fixedPositions) {
            d.fx = null;
            d.fy = null;
        }
    }
    
    /**
     * Obtiene iniciales del nombre
     * @param {string} name - Nombre completo
     * @returns {string} Iniciales
     * @private
     */
    _getInitials(name) {
        return name
            .split(/\s+/)
            .map(n => n[0])
            .join("")
            .toUpperCase()
            .substring(0, 2);
    }
    
    /**
     * Resalta un nodo y sus conexiones
     * @param {string} nodeId - ID del nodo a resaltar
     */
    highlightNode(nodeId) {
        if (!this.nodeGroups) return;
        
        // Reducir opacidad de todos los elementos
        this.nodeGroups.attr("opacity", 0.3);
        this.linkElements.attr("opacity", 0.1);
        
        // Resaltar nodo seleccionado
        const selectedNode = this.nodeGroups.filter(d => d.id === nodeId)
            .attr("opacity", 1);
            
        // Resaltar enlaces conectados
        const connectedLinks = this.linkElements.filter(d => 
            d.source.id === nodeId || d.target.id === nodeId
        ).attr("opacity", 1);
        
        // Resaltar nodos conectados
        const connectedNodeIds = this.links
            .filter(link => link.source.id === nodeId || link.target.id === nodeId)
            .map(link => link.source.id === nodeId ? link.target.id : link.source.id);
            
        this.nodeGroups.filter(d => connectedNodeIds.includes(d.id))
            .attr("opacity", 1);
    }
    
    /**
     * Restaura visualización normal
     */
    resetHighlight() {
        if (!this.nodeGroups) return;
        this.nodeGroups.attr("opacity", 1);
        this.linkElements.attr("opacity", 0.6);
    }
    
    /**
     * Actualiza datos del grafo
     * @param {Object} newData - Nuevos datos para el grafo
     */
    updateData(newData) {
        this.data = newData;
        
        // Limpiar SVG existente
        d3.select(`#${this.containerId}`).select("svg").remove();
        
        // Reinicializar
        this._init();
    }
}

// Función auxiliar para convertir datos de API al formato requerido
function formatSocialConnectionsForGraph(personId, connections) {
    // Formato esperado: { nodes: [...], links: [...] }
    const nodes = [];
    const links = [];
    
    // Añadir nodo principal (el candidato)
    nodes.push({
        id: personId.toString(),
        name: connections.main_person.name,
        role: connections.main_person.role || "",
        main: true
    });
    
    // Añadir conexiones
    connections.connections.forEach(conn => {
        // Añadir nodo si no existe
        if (!nodes.some(n => n.id === conn.person_id.toString())) {
            nodes.push({
                id: conn.person_id.toString(),
                name: conn.name,
                role: conn.role || "",
                main: false
            });
        }
        
        // Añadir enlace
        links.push({
            source: personId.toString(),
            target: conn.person_id.toString(),
            type: conn.relationship_type,
            strength: conn.strength || 1
        });
    });
    
    return { nodes, links };
}
