
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowRight, Settings, Zap, Brain, Shield, Cpu, Database, Activity, Sparkles, CheckCircle } from 'lucide-react';

const BusinessUnitsSection = () => {
  const [selectedUnit, setSelectedUnit] = useState(0);
  const [activeConfig, setActiveConfig] = useState('features');

  const businessUnits = [
    {
      title: "FinTech & Banking",
      description: "Soluciones de IA para servicios financieros, detección de fraudes y análisis de riesgo crediticio.",
      features: ["Análisis de Riesgo", "Detección de Fraudes", "Robo-Advisory", "KYC Automatizado"],
      image: "https://images.unsplash.com/photo-1605810230434-7631ac76ec81?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
      color: "bg-blue-500/10 border-blue-500/20",
      accentColor: "text-blue-600",
      gradient: "from-blue-400 to-cyan-600",
      configurations: {
        compliance: ["SOX", "PCI-DSS", "GDPR", "Basel III"],
        integrations: ["Core Banking", "Payment Gateways", "CRM Systems", "Regulatory APIs"],
        models: ["Credit Scoring", "Fraud Detection", "Market Analysis", "Risk Assessment"],
        security: ["End-to-End Encryption", "Multi-Factor Auth", "Audit Trails", "Data Masking"]
      }
    },
    {
      title: "Healthcare & Medical",
      description: "Tecnologías de diagnóstico asistido por IA y análisis de imágenes médicas avanzadas.",
      features: ["Diagnóstico por IA", "Análisis de Imágenes", "Predicción de Enfermedades", "Telemedicina"],
      image: "https://images.unsplash.com/photo-1649972904349-6e44c42644a7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
      color: "bg-green-500/10 border-green-500/20",
      accentColor: "text-green-600",
      gradient: "from-green-400 to-emerald-600",
      configurations: {
        compliance: ["HIPAA", "FDA", "CE Marking", "ISO 13485"],
        integrations: ["EMR/EHR", "PACS Systems", "Lab Equipment", "Wearable Devices"],
        models: ["Image Analysis", "Drug Discovery", "Patient Monitoring", "Clinical Decision Support"],
        security: ["PHI Protection", "Secure Messaging", "Access Controls", "Anonymization"]
      }
    },
    {
      title: "Retail & E-commerce",
      description: "Personalización de experiencias de compra y optimización de inventarios mediante IA.",
      features: ["Recomendaciones Personalizadas", "Optimización de Precios", "Análisis de Sentimientos", "Chatbots de Ventas"],
      image: "https://images.unsplash.com/photo-1487058792275-0ad4aaf24ca7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
      color: "bg-purple-500/10 border-purple-500/20",
      accentColor: "text-purple-600",
      gradient: "from-purple-400 to-pink-600",
      configurations: {
        compliance: ["PCI DSS", "CCPA", "GDPR", "Local Tax Laws"],
        integrations: ["E-commerce Platforms", "CRM", "ERP Systems", "Social Media APIs"],
        models: ["Recommendation Engine", "Price Optimization", "Demand Forecasting", "Customer Segmentation"],
        security: ["Payment Security", "Customer Data Protection", "Fraud Prevention", "API Security"]
      }
    },
    {
      title: "Manufacturing & IoT",
      description: "Automatización inteligente y mantenimiento predictivo para la industria 4.0.",
      features: ["Mantenimiento Predictivo", "Control de Calidad", "Optimización de Procesos", "IoT Analytics"],
      image: "https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
      color: "bg-orange-500/10 border-orange-500/20",
      accentColor: "text-orange-600",
      gradient: "from-orange-400 to-red-600",
      configurations: {
        compliance: ["ISO 9001", "ISO 27001", "OSHA", "Environmental Standards"],
        integrations: ["MES Systems", "SCADA", "IoT Sensors", "Supply Chain APIs"],
        models: ["Predictive Maintenance", "Quality Control", "Energy Optimization", "Production Planning"],
        security: ["OT Security", "Edge Computing", "Secure Communication", "Asset Protection"]
      }
    },
    {
      title: "Legal & Compliance",
      description: "Análisis automatizado de documentos legales y cumplimiento normativo inteligente.",
      features: ["Document Review", "Contract Analysis", "Compliance Monitoring", "Legal Research"],
      image: "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
      color: "bg-red-500/10 border-red-500/20",
      accentColor: "text-red-600",
      gradient: "from-red-400 to-rose-600",
      configurations: {
        compliance: ["Legal Standards", "Data Protection", "Industry Regulations", "Cross-Border Laws"],
        integrations: ["Legal Databases", "Document Management", "Case Management", "Court Systems"],
        models: ["Document Classification", "Contract Analysis", "Legal Research", "Risk Assessment"],
        security: ["Attorney-Client Privilege", "Document Security", "Access Controls", "Audit Trails"]
      }
    },
    {
      title: "Education & Training",
      description: "Plataformas de aprendizaje adaptativo y evaluación automatizada con IA.",
      features: ["Aprendizaje Personalizado", "Evaluación Automática", "Tutores Virtuales", "Analytics Educativo"],
      image: "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
      color: "bg-cyan-500/10 border-cyan-500/20",
      accentColor: "text-cyan-600",
      gradient: "from-cyan-400 to-blue-600",
      configurations: {
        compliance: ["FERPA", "COPPA", "Accessibility Standards", "Academic Standards"],
        integrations: ["LMS Platforms", "Student Information Systems", "Assessment Tools", "Content Libraries"],
        models: ["Learning Analytics", "Adaptive Learning", "Performance Prediction", "Content Recommendation"],
        security: ["Student Privacy", "Secure Assessment", "Data Protection", "Access Management"]
      }
    }
  ];

  const configTabs = [
    { id: 'features', label: 'Características', icon: Sparkles },
    { id: 'compliance', label: 'Cumplimiento', icon: Shield },
    { id: 'integrations', label: 'Integraciones', icon: Cpu },
    { id: 'models', label: 'Modelos IA', icon: Brain },
    { id: 'security', label: 'Seguridad', icon: Database }
  ];

  return (
    <section id="business-units" className="py-20 bg-muted/30 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 quantum-grid opacity-10" />
      <div className="absolute top-20 left-10 w-64 h-64 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-full blur-3xl animate-float" />
      <div className="absolute bottom-20 right-10 w-48 h-48 bg-gradient-to-r from-cyan-500/10 to-pink-500/10 rounded-full blur-2xl animate-float-delay" />
      
      <div className="container mx-auto px-4 lg:px-8 relative z-10">
        <div className="text-center space-y-4 mb-16">
          <div className="inline-flex items-center space-x-2 glass rounded-full px-6 py-2 border border-primary/20">
            <Settings className="h-5 w-5 text-primary" />
            <span className="text-sm font-medium">CONFIGURACIONES AVANZADAS</span>
          </div>
          
          <h2 className="text-3xl md:text-4xl font-bold">
            Unidades de <span className="text-gradient">Negocio</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Soluciones altamente configurables con ajustes específicos para cada industria
          </p>
        </div>

        {/* Enhanced Business Units Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {businessUnits.map((unit, index) => (
            <Card 
              key={index} 
              className={`group cursor-pointer transition-all duration-500 hover:scale-105 ${unit.color} border-2 ${
                selectedUnit === index ? 'border-primary/50 shadow-2xl' : 'hover:border-primary/30'
              }`}
              onClick={() => setSelectedUnit(index)}
            >
              <CardHeader className="p-0">
                <div className="relative h-48 overflow-hidden rounded-t-lg">
                  <img
                    src={unit.image}
                    alt={unit.title}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                  />
                  <div className={`absolute inset-0 bg-gradient-to-br ${unit.gradient} opacity-20`} />
                  <div className="absolute top-4 left-4 glass rounded-lg px-3 py-1">
                    <span className="text-sm font-medium">Especializado</span>
                  </div>
                  <div className="absolute top-4 right-4">
                    <Settings className={`h-5 w-5 ${unit.accentColor} animate-pulse`} />
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="p-6 space-y-4">
                <CardTitle className={`text-xl ${unit.accentColor}`}>
                  {unit.title}
                </CardTitle>
                
                <p className="text-muted-foreground text-sm">
                  {unit.description}
                </p>
                
                <div className="flex flex-wrap gap-2">
                  {unit.features.slice(0, 2).map((feature, featureIndex) => (
                    <Badge key={featureIndex} variant="secondary" className="text-xs">
                      {feature}
                    </Badge>
                  ))}
                  <Badge variant="outline" className="text-xs">
                    +{unit.features.length - 2} más
                  </Badge>
                </div>
                
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className={`w-full group-hover:bg-gradient-to-r group-hover:${unit.gradient} group-hover:text-white transition-all`}
                >
                  Configurar
                  <Settings className="ml-2 h-4 w-4 transition-transform group-hover:rotate-180" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Advanced Configuration Panel */}
        <Card className="glass border-primary/20 mb-16">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <div className={`w-4 h-4 bg-gradient-to-r ${businessUnits[selectedUnit].gradient} rounded-full animate-pulse`} />
              <span>Configuración Avanzada: {businessUnits[selectedUnit].title}</span>
            </CardTitle>
          </CardHeader>
          
          <CardContent>
            <Tabs value={activeConfig} onValueChange={setActiveConfig} className="w-full">
              <TabsList className="grid w-full grid-cols-5 mb-6">
                {configTabs.map((tab) => (
                  <TabsTrigger key={tab.id} value={tab.id} className="flex items-center space-x-2">
                    <tab.icon className="h-4 w-4" />
                    <span className="hidden md:inline">{tab.label}</span>
                  </TabsTrigger>
                ))}
              </TabsList>
              
              {configTabs.map((tab) => (
                <TabsContent key={tab.id} value={tab.id} className="space-y-4">
                  <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {(tab.id === 'features' ? businessUnits[selectedUnit].features : 
                      businessUnits[selectedUnit].configurations[tab.id as keyof typeof businessUnits[0]['configurations']])
                      ?.map((item, itemIndex) => (
                      <div 
                        key={itemIndex}
                        className="glass rounded-lg p-4 hover:bg-primary/5 transition-all duration-300 border border-primary/10 hover:border-primary/30 group"
                      >
                        <div className="flex items-center space-x-3">
                          <CheckCircle className={`h-5 w-5 ${businessUnits[selectedUnit].accentColor} group-hover:animate-pulse`} />
                          <span className="text-sm font-medium">{item}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>

        {/* Custom Consultation Section */}
        <div className="text-center">
          <Card className="glass border-primary/20 max-w-4xl mx-auto neural-connection">
            <CardContent className="p-8 space-y-6">
              <div className="flex items-center justify-center space-x-2 mb-4">
                <Zap className="h-8 w-8 text-primary animate-pulse" />
                <h3 className="text-2xl font-bold">Configuración Personalizada</h3>
              </div>
              
              <p className="text-muted-foreground text-lg">
                ¿Necesitas ajustes específicos para tu industria? Nuestro equipo de especialistas 
                puede configurar soluciones completamente personalizadas.
              </p>
              
              <div className="grid md:grid-cols-3 gap-4 my-6">
                <div className="text-center">
                  <Activity className="h-12 w-12 mx-auto text-primary mb-2 animate-bounce" />
                  <h4 className="font-semibold">Análisis Profundo</h4>
                  <p className="text-sm text-muted-foreground">Evaluamos tus necesidades específicas</p>
                </div>
                <div className="text-center">
                  <Cpu className="h-12 w-12 mx-auto text-primary mb-2 animate-pulse" />
                  <h4 className="font-semibold">Configuración Custom</h4>
                  <p className="text-sm text-muted-foreground">Adaptamos cada parámetro a tu negocio</p>
                </div>
                <div className="text-center">
                  <Shield className="h-12 w-12 mx-auto text-primary mb-2 animate-spin-slow" />
                  <h4 className="font-semibold">Implementación Segura</h4>
                  <p className="text-sm text-muted-foreground">Despliegue con máxima seguridad</p>
                </div>
              </div>
              
              <Button size="lg" className="btn-gradient">
                Solicitar Configuración Personalizada
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default BusinessUnitsSection;
