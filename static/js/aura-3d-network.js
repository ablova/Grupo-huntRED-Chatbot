/**
 * AURA 3D Network Visualization
 * Visualización 3D de redes profesionales usando Three.js
 * 
 * Características:
 * - Visualización 3D interactiva
 * - Animaciones fluidas
 * - Diferentes layouts 3D
 * - Información detallada de nodos
 * - Filtros avanzados
 * - Exportación 3D
 */

import * as THREE from 'https://cdn.skypack.dev/three@0.150.1';
import { OrbitControls } from 'https://cdn.skypack.dev/three@0.150.1/examples/jsm/controls/OrbitControls.js';

class Aura3DNetworkVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.networkData = null;
        this.nodes = [];
        this.edges = [];
        this.nodeMeshes = [];
        this.edgeMeshes = [];
        this.selectedNode = null;
        this.animationId = null;
        this.currentLayout = 'force';
        this.isAnimating = false;
        
        this.init();
    }
    
    init() {
        this.setupScene();
        this.setupCamera();
        this.setupRenderer();
        this.setupControls();
        this.setupLights();
        this.setupEventListeners();
        this.animate();
    }
    
    setupScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a0a);
        
        // Añadir niebla para profundidad
        this.scene.fog = new THREE.Fog(0x0a0a0a, 50, 200);
    }
    
    setupCamera() {
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
        this.camera.position.set(0, 0, 50);
    }
    
    setupRenderer() {
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: true 
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        this.container.appendChild(this.renderer.domElement);
    }
    
    setupControls() {
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.screenSpacePanning = false;
        this.controls.minDistance = 10;
        this.controls.maxDistance = 200;
        this.controls.maxPolarAngle = Math.PI;
    }
    
    setupLights() {
        // Luz ambiental
        const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
        this.scene.add(ambientLight);
        
        // Luz direccional principal
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(50, 50, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);
        
        // Luz puntual para efectos
        const pointLight = new THREE.PointLight(0x6366f1, 0.5, 100);
        pointLight.position.set(-50, 50, -50);
        this.scene.add(pointLight);
    }
    
    setupEventListeners() {
        // Resize handler
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Mouse events
        this.renderer.domElement.addEventListener('click', (event) => this.onMouseClick(event));
        this.renderer.domElement.addEventListener('mousemove', (event) => this.onMouseMove(event));
        
        // Touch events para móviles
        this.renderer.domElement.addEventListener('touchstart', (event) => this.onTouchStart(event));
    }
    
    loadNetworkData(data) {
        this.networkData = data;
        this.clearNetwork();
        this.createNodes();
        this.createEdges();
        this.applyLayout(this.currentLayout);
        this.updateNodeInfo();
    }
    
    createNodes() {
        this.nodes = [];
        this.nodeMeshes = [];
        
        this.networkData.nodes.forEach((nodeData, index) => {
            // Crear geometría del nodo
            const geometry = new THREE.SphereGeometry(this.getNodeSize(nodeData), 32, 32);
            
            // Crear material con color basado en tipo
            const material = new THREE.MeshPhongMaterial({
                color: this.getNodeColor(nodeData.type),
                emissive: this.getNodeEmissive(nodeData.type),
                shininess: 100,
                transparent: true,
                opacity: 0.9
            });
            
            // Crear mesh
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.set(
                (Math.random() - 0.5) * 100,
                (Math.random() - 0.5) * 100,
                (Math.random() - 0.5) * 100
            );
            
            // Añadir datos del nodo
            mesh.userData = {
                id: nodeData.id,
                type: nodeData.type,
                name: nodeData.name,
                data: nodeData
            };
            
            // Añadir sombra
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            
            this.scene.add(mesh);
            this.nodes.push(nodeData);
            this.nodeMeshes.push(mesh);
        });
    }
    
    createEdges() {
        this.edges = [];
        this.edgeMeshes = [];
        
        this.networkData.edges.forEach((edgeData) => {
            const fromNode = this.nodeMeshes.find(mesh => mesh.userData.id === edgeData.from);
            const toNode = this.nodeMeshes.find(mesh => mesh.userData.id === edgeData.to);
            
            if (fromNode && toNode) {
                // Crear geometría de la conexión
                const geometry = new THREE.CylinderGeometry(0.1, 0.1, 1, 8);
                const material = new THREE.MeshPhongMaterial({
                    color: 0x6366f1,
                    transparent: true,
                    opacity: 0.6
                });
                
                const edgeMesh = new THREE.Mesh(geometry, material);
                
                // Posicionar y orientar la conexión
                this.updateEdgePosition(edgeMesh, fromNode, toNode);
                
                // Añadir datos de la conexión
                edgeMesh.userData = {
                    from: edgeData.from,
                    to: edgeData.to,
                    strength: edgeData.strength || 1,
                    data: edgeData
                };
                
                this.scene.add(edgeMesh);
                this.edges.push(edgeData);
                this.edgeMeshes.push(edgeMesh);
            }
        });
    }
    
    updateEdgePosition(edgeMesh, fromNode, toNode) {
        const fromPos = fromNode.position;
        const toPos = toNode.position;
        
        // Calcular posición central
        const center = new THREE.Vector3().addVectors(fromPos, toPos).multiplyScalar(0.5);
        edgeMesh.position.copy(center);
        
        // Calcular orientación
        const direction = new THREE.Vector3().subVectors(toPos, fromPos);
        const distance = direction.length();
        
        // Escalar la conexión
        edgeMesh.scale.set(1, distance, 1);
        
        // Orientar hacia la dirección correcta
        edgeMesh.lookAt(toPos);
        edgeMesh.rotateX(Math.PI / 2);
    }
    
    getNodeSize(nodeData) {
        // Tamaño basado en influencia o importancia
        const baseSize = 1;
        const influenceFactor = nodeData.influence_score || 0.5;
        return baseSize + influenceFactor * 2;
    }
    
    getNodeColor(nodeType) {
        const colors = {
            'influencer': 0xef4444,    // Rojo
            'connector': 0xf59e0b,     // Naranja
            'regular': 0x6366f1,       // Azul
            'community': 0x10b981,     // Verde
            'default': 0x6b7280        // Gris
        };
        return colors[nodeType] || colors.default;
    }
    
    getNodeEmissive(nodeType) {
        const emissive = {
            'influencer': 0x330000,
            'connector': 0x331a00,
            'regular': 0x1a1a33,
            'community': 0x00331a,
            'default': 0x1a1a1a
        };
        return emissive[nodeType] || emissive.default;
    }
    
    applyLayout(layoutType) {
        this.currentLayout = layoutType;
        this.isAnimating = true;
        
        switch (layoutType) {
            case 'force':
                this.applyForceLayout();
                break;
            case 'spherical':
                this.applySphericalLayout();
                break;
            case 'cylindrical':
                this.applyCylindricalLayout();
                break;
            case 'hierarchical':
                this.applyHierarchicalLayout();
                break;
            case 'community':
                this.applyCommunityLayout();
                break;
            default:
                this.applyForceLayout();
        }
    }
    
    applyForceLayout() {
        // Simulación de fuerzas 3D
        const positions = this.nodeMeshes.map(mesh => mesh.position);
        const velocities = positions.map(() => new THREE.Vector3());
        
        const animate = () => {
            // Aplicar fuerzas de repulsión
            for (let i = 0; i < positions.length; i++) {
                for (let j = i + 1; j < positions.length; j++) {
                    const force = new THREE.Vector3().subVectors(positions[i], positions[j]);
                    const distance = force.length();
                    
                    if (distance > 0) {
                        const repulsion = 1000 / (distance * distance);
                        force.normalize().multiplyScalar(repulsion);
                        
                        velocities[i].add(force);
                        velocities[j].sub(force);
                    }
                }
            }
            
            // Aplicar fuerzas de atracción (conexiones)
            this.edgeMeshes.forEach(edgeMesh => {
                const fromIndex = this.nodeMeshes.findIndex(mesh => mesh.userData.id === edgeMesh.userData.from);
                const toIndex = this.nodeMeshes.findIndex(mesh => mesh.userData.id === edgeMesh.userData.to);
                
                if (fromIndex !== -1 && toIndex !== -1) {
                    const force = new THREE.Vector3().subVectors(positions[toIndex], positions[fromIndex]);
                    const distance = force.length();
                    const attraction = (distance - 10) * 0.1;
                    
                    force.normalize().multiplyScalar(attraction);
                    velocities[fromIndex].add(force);
                    velocities[toIndex].sub(force);
                }
            });
            
            // Actualizar posiciones
            for (let i = 0; i < positions.length; i++) {
                velocities[i].multiplyScalar(0.95); // Fricción
                positions[i].add(velocities[i]);
                
                // Mantener dentro de límites
                const maxDistance = 50;
                if (positions[i].length() > maxDistance) {
                    positions[i].normalize().multiplyScalar(maxDistance);
                }
            }
            
            // Actualizar conexiones
            this.updateEdgePositions();
            
            if (this.isAnimating) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }
    
    applySphericalLayout() {
        const radius = 30;
        const positions = this.nodeMeshes.map((mesh, index) => {
            const phi = Math.acos(-1 + (2 * index) / this.nodeMeshes.length);
            const theta = Math.sqrt(this.nodeMeshes.length * Math.PI) * phi;
            
            return new THREE.Vector3(
                radius * Math.cos(theta) * Math.sin(phi),
                radius * Math.sin(theta) * Math.sin(phi),
                radius * Math.cos(phi)
            );
        });
        
        this.animateToPositions(positions);
    }
    
    applyCylindricalLayout() {
        const radius = 25;
        const height = 40;
        const positions = this.nodeMeshes.map((mesh, index) => {
            const angle = (index / this.nodeMeshes.length) * Math.PI * 2;
            const z = (index / this.nodeMeshes.length - 0.5) * height;
            
            return new THREE.Vector3(
                radius * Math.cos(angle),
                radius * Math.sin(angle),
                z
            );
        });
        
        this.animateToPositions(positions);
    }
    
    applyHierarchicalLayout() {
        // Agrupar por tipo y crear jerarquía
        const groups = {};
        this.nodeMeshes.forEach(mesh => {
            const type = mesh.userData.type;
            if (!groups[type]) groups[type] = [];
            groups[type].push(mesh);
        });
        
        const positions = [];
        let yOffset = 0;
        
        Object.entries(groups).forEach(([type, meshes]) => {
            const groupRadius = 15;
            meshes.forEach((mesh, index) => {
                const angle = (index / meshes.length) * Math.PI * 2;
                positions.push(new THREE.Vector3(
                    groupRadius * Math.cos(angle),
                    yOffset,
                    groupRadius * Math.sin(angle)
                ));
            });
            yOffset += 20;
        });
        
        this.animateToPositions(positions);
    }
    
    applyCommunityLayout() {
        // Layout basado en comunidades detectadas
        const positions = this.nodeMeshes.map((mesh, index) => {
            const community = mesh.userData.data.community || 0;
            const communityAngle = (community / 5) * Math.PI * 2;
            const nodeAngle = (index / this.nodeMeshes.length) * Math.PI * 2;
            const radius = 20 + community * 5;
            
            return new THREE.Vector3(
                radius * Math.cos(communityAngle + nodeAngle * 0.1),
                community * 10,
                radius * Math.sin(communityAngle + nodeAngle * 0.1)
            );
        });
        
        this.animateToPositions(positions);
    }
    
    animateToPositions(targetPositions) {
        const duration = 2000; // 2 segundos
        const startTime = Date.now();
        const startPositions = this.nodeMeshes.map(mesh => mesh.position.clone());
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Función de easing
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            
            this.nodeMeshes.forEach((mesh, index) => {
                const startPos = startPositions[index];
                const targetPos = targetPositions[index];
                
                mesh.position.lerpVectors(startPos, targetPos, easeOutQuart);
            });
            
            this.updateEdgePositions();
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                this.isAnimating = false;
            }
        };
        
        animate();
    }
    
    updateEdgePositions() {
        this.edgeMeshes.forEach(edgeMesh => {
            const fromNode = this.nodeMeshes.find(mesh => mesh.userData.id === edgeMesh.userData.from);
            const toNode = this.nodeMeshes.find(mesh => mesh.userData.id === edgeMesh.userData.to);
            
            if (fromNode && toNode) {
                this.updateEdgePosition(edgeMesh, fromNode, toNode);
            }
        });
    }
    
    onMouseClick(event) {
        const mouse = new THREE.Vector2();
        mouse.x = (event.clientX / this.renderer.domElement.clientWidth) * 2 - 1;
        mouse.y = -(event.clientY / this.renderer.domElement.clientHeight) * 2 + 1;
        
        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, this.camera);
        
        const intersects = raycaster.intersectObjects(this.nodeMeshes);
        
        if (intersects.length > 0) {
            const clickedNode = intersects[0].object;
            this.selectNode(clickedNode);
        } else {
            this.deselectNode();
        }
    }
    
    onMouseMove(event) {
        const mouse = new THREE.Vector2();
        mouse.x = (event.clientX / this.renderer.domElement.clientWidth) * 2 - 1;
        mouse.y = -(event.clientY / this.renderer.domElement.clientHeight) * 2 + 1;
        
        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, this.camera);
        
        const intersects = raycaster.intersectObjects(this.nodeMeshes);
        
        // Cambiar cursor
        this.renderer.domElement.style.cursor = intersects.length > 0 ? 'pointer' : 'default';
        
        // Efecto hover
        this.nodeMeshes.forEach(mesh => {
            const isHovered = intersects.some(intersect => intersect.object === mesh);
            mesh.material.emissive.setHex(isHovered ? 0x333333 : this.getNodeEmissive(mesh.userData.type));
        });
    }
    
    onTouchStart(event) {
        // Manejar eventos táctiles para móviles
        if (event.touches.length === 1) {
            const touch = event.touches[0];
            const mouseEvent = new MouseEvent('click', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            this.onMouseClick(mouseEvent);
        }
    }
    
    selectNode(nodeMesh) {
        this.deselectNode();
        
        this.selectedNode = nodeMesh;
        
        // Efecto visual de selección
        nodeMesh.material.emissive.setHex(0x666666);
        nodeMesh.scale.setScalar(1.5);
        
        // Mostrar información del nodo
        this.showNodeInfo(nodeMesh.userData);
        
        // Resaltar conexiones
        this.highlightConnections(nodeMesh.userData.id);
    }
    
    deselectNode() {
        if (this.selectedNode) {
            this.selectedNode.material.emissive.setHex(this.getNodeEmissive(this.selectedNode.userData.type));
            this.selectedNode.scale.setScalar(1);
            this.selectedNode = null;
            
            // Ocultar información
            this.hideNodeInfo();
            
            // Quitar resaltado de conexiones
            this.unhighlightConnections();
        }
    }
    
    highlightConnections(nodeId) {
        this.edgeMeshes.forEach(edgeMesh => {
            if (edgeMesh.userData.from === nodeId || edgeMesh.userData.to === nodeId) {
                edgeMesh.material.color.setHex(0xff6b6b);
                edgeMesh.material.opacity = 1;
            }
        });
    }
    
    unhighlightConnections() {
        this.edgeMeshes.forEach(edgeMesh => {
            edgeMesh.material.color.setHex(0x6366f1);
            edgeMesh.material.opacity = 0.6;
        });
    }
    
    showNodeInfo(nodeData) {
        // Crear o actualizar panel de información
        let infoPanel = document.getElementById('node-info-panel');
        if (!infoPanel) {
            infoPanel = document.createElement('div');
            infoPanel.id = 'node-info-panel';
            infoPanel.className = 'node-info-panel';
            this.container.appendChild(infoPanel);
        }
        
        infoPanel.innerHTML = `
            <div class="node-info-header">
                <h3>${nodeData.name}</h3>
                <span class="node-type ${nodeData.type}">${nodeData.type}</span>
            </div>
            <div class="node-info-content">
                <p><strong>Influencia:</strong> ${(nodeData.data.influence_score * 100).toFixed(1)}%</p>
                <p><strong>Conexiones:</strong> ${nodeData.data.connection_count || 0}</p>
                <p><strong>Comunidad:</strong> ${nodeData.data.community || 'N/A'}</p>
                <p><strong>Reputación:</strong> ${(nodeData.data.reputation_score * 100).toFixed(1)}%</p>
            </div>
            <div class="node-info-actions">
                <button onclick="aura3D.showNodeDetails(${nodeData.id})">Ver Detalles</button>
                <button onclick="aura3D.analyzeNode(${nodeData.id})">Analizar</button>
            </div>
        `;
        
        infoPanel.style.display = 'block';
    }
    
    hideNodeInfo() {
        const infoPanel = document.getElementById('node-info-panel');
        if (infoPanel) {
            infoPanel.style.display = 'none';
        }
    }
    
    updateNodeInfo() {
        // Actualizar estadísticas generales
        const stats = {
            totalNodes: this.nodes.length,
            totalEdges: this.edges.length,
            influencers: this.nodes.filter(n => n.type === 'influencer').length,
            communities: new Set(this.nodes.map(n => n.community).filter(c => c)).size
        };
        
        // Actualizar panel de estadísticas si existe
        const statsPanel = document.getElementById('network-stats-panel');
        if (statsPanel) {
            statsPanel.innerHTML = `
                <div class="stat-item">
                    <span class="stat-value">${stats.totalNodes}</span>
                    <span class="stat-label">Nodos</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.totalEdges}</span>
                    <span class="stat-label">Conexiones</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.influencers}</span>
                    <span class="stat-label">Influenciadores</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.communities}</span>
                    <span class="stat-label">Comunidades</span>
                </div>
            `;
        }
    }
    
    filterNodes(filterType, value) {
        this.nodeMeshes.forEach(mesh => {
            let visible = true;
            
            switch (filterType) {
                case 'type':
                    visible = mesh.userData.type === value;
                    break;
                case 'influence':
                    visible = mesh.userData.data.influence_score >= value;
                    break;
                case 'community':
                    visible = mesh.userData.data.community === value;
                    break;
            }
            
            mesh.visible = visible;
        });
        
        // Ocultar conexiones de nodos filtrados
        this.edgeMeshes.forEach(edgeMesh => {
            const fromNode = this.nodeMeshes.find(mesh => mesh.userData.id === edgeMesh.userData.from);
            const toNode = this.nodeMeshes.find(mesh => mesh.userData.id === edgeMesh.userData.to);
            
            edgeMesh.visible = fromNode.visible && toNode.visible;
        });
    }
    
    exportNetwork(format = 'png') {
        switch (format) {
            case 'png':
                this.renderer.render(this.scene, this.camera);
                const dataURL = this.renderer.domElement.toDataURL('image/png');
                this.downloadFile(dataURL, 'aura-network-3d.png');
                break;
            case 'json':
                const networkData = {
                    nodes: this.nodes,
                    edges: this.edges,
                    metadata: {
                        exportDate: new Date().toISOString(),
                        layout: this.currentLayout,
                        totalNodes: this.nodes.length,
                        totalEdges: this.edges.length
                    }
                };
                const jsonData = JSON.stringify(networkData, null, 2);
                this.downloadFile('data:text/json;charset=utf-8,' + encodeURIComponent(jsonData), 'aura-network-3d.json');
                break;
        }
    }
    
    downloadFile(dataURL, filename) {
        const link = document.createElement('a');
        link.href = dataURL;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(width, height);
    }
    
    clearNetwork() {
        // Limpiar nodos
        this.nodeMeshes.forEach(mesh => {
            this.scene.remove(mesh);
            mesh.geometry.dispose();
            mesh.material.dispose();
        });
        
        // Limpiar conexiones
        this.edgeMeshes.forEach(mesh => {
            this.scene.remove(mesh);
            mesh.geometry.dispose();
            mesh.material.dispose();
        });
        
        this.nodeMeshes = [];
        this.edgeMeshes = [];
        this.nodes = [];
        this.edges = [];
    }
    
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        // Actualizar controles
        this.controls.update();
        
        // Animación de rotación suave
        if (!this.isAnimating) {
            this.scene.rotation.y += 0.001;
        }
        
        // Renderizar escena
        this.renderer.render(this.scene, this.camera);
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        this.clearNetwork();
        
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        if (this.container && this.renderer) {
            this.container.removeChild(this.renderer.domElement);
        }
    }
    
    // Métodos públicos para integración
    showNodeDetails(nodeId) {
        console.log(`Mostrando detalles del nodo ${nodeId}`);
        // Implementar navegación a página de detalles
    }
    
    analyzeNode(nodeId) {
        console.log(`Analizando nodo ${nodeId}`);
        // Implementar análisis detallado
    }
}

// Estilos CSS para los paneles
const styles = `
<style>
.node-info-panel {
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    min-width: 300px;
    z-index: 1000;
    display: none;
}

.node-info-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.node-info-header h3 {
    margin: 0;
    color: #1f2937;
    font-size: 1.2rem;
}

.node-type {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
}

.node-type.influencer { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
.node-type.connector { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
.node-type.regular { background: rgba(99, 102, 241, 0.1); color: #6366f1; }
.node-type.community { background: rgba(16, 185, 129, 0.1); color: #10b981; }

.node-info-content p {
    margin: 8px 0;
    color: #6b7280;
    font-size: 0.9rem;
}

.node-info-actions {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}

.node-info-actions button {
    flex: 1;
    padding: 8px 16px;
    border: none;
    border-radius: 8px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
}

.node-info-actions button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(99, 102, 241, 0.3);
}

.network-stats-panel {
    position: absolute;
    bottom: 20px;
    left: 20px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    z-index: 1000;
}

.stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 10px 0;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: 800;
    color: #6366f1;
}

.stat-label {
    font-size: 0.8rem;
    color: #6b7280;
    text-transform: uppercase;
    font-weight: 600;
}
</style>
`;

// Añadir estilos al documento
document.head.insertAdjacentHTML('beforeend', styles);

// Exportar para uso global
window.Aura3DNetworkVisualizer = Aura3DNetworkVisualizer; 