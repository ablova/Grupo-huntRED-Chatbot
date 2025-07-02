import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowRight, CreditCard, Shield, Zap, DollarSign, FileText, Target, Calendar, TrendingUp } from 'lucide-react';

const PaymentSystemSection = () => {
  const paymentFeatures = [
    {
      name: "Múltiples Gateways",
      description: "Integración con Stripe, PayPal y bancos locales",
      icon: CreditCard,
      color: "bg-blue-500"
    },
    {
      name: "Seguridad Avanzada",
      description: "Encriptación y cumplimiento PCI DSS",
      icon: Shield,
      color: "bg-emerald-500"
    },
    {
      name: "Procesamiento Rápido",
      description: "Transacciones en tiempo real con webhooks",
      icon: Zap,
      color: "bg-violet-500"
    },
    {
      name: "Hitos Inteligentes",
      description: "Sistema automático de pagos por milestone",
      icon: Target,
      color: "bg-orange-500"
    }
  ];

  const pricingModels = [
    {
      model: "Modelo Porcentaje",
      bu: "huntRED®",
      description: "Cálculo basado en salarios con comisiones optimizadas por IA",
      features: ["Cálculo automático", "Optimización IA", "Addons específicos", "Reportes detallados"],
      icon: DollarSign,
      color: "bg-blue-500"
    },
    {
      model: "Modelo Fijo",
      bu: "huntU / amigro",
      description: "Precios predefinidos con escalas por volumen",
      features: ["Precios fijos", "Escalas de volumen", "Paquetes de servicios", "Promociones"],
      icon: FileText,
      color: "bg-emerald-500"
    },
    {
      model: "Modelo AI",
      bu: "huntRED® Executive",
      description: "Optimización de precios con IA y análisis de mercado",
      features: ["Predicción IA", "Análisis de mercado", "Ajustes dinámicos", "Precios óptimos"],
      icon: TrendingUp,
      color: "bg-primary"
    }
  ];

  const systemComponents = [
    "PaymentProcessor - Procesa pagos multi-gateway",
    "MilestoneTracker - Seguimiento automático de hitos", 
    "WebhookHandler - Notificaciones en tiempo real",
    "FiscalManager - Gestión de responsabilidades fiscales",
    "ProposalGenerator - Propuestas automáticas PDF/HTML",
    "ContractWorkflow - Firma digital y aprobaciones"
  ];

  return (
    <section className="py-20 bg-background">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-16">
          <h2 className="text-3xl md:text-4xl font-bold">
            Sistema de <span className="text-primary">Pagos Inteligente</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Plataforma completa de gestión financiera con múltiples modelos de negocio, hitos automatizados y procesamiento seguro
          </p>
        </div>

        {/* Core Features */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {paymentFeatures.map((feature, index) => (
            <Card key={index} className="glass border-primary/20 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
              <CardHeader className="text-center">
                <div className={`w-12 h-12 ${feature.color} rounded-full flex items-center justify-center text-white mx-auto mb-4`}>
                  <feature.icon className="h-6 w-6" />
                </div>
                <CardTitle className="text-lg">{feature.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground text-center">
                  {feature.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Pricing Models */}
        <div className="space-y-8 mb-16">
          <div className="text-center space-y-4">
            <h3 className="text-2xl font-bold">Modelos de Negocio Especializados</h3>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Cada unidad de negocio opera con un modelo de pricing optimizado para su mercado específico
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {pricingModels.map((model, index) => (
              <Card key={index} className="glass border-primary/20 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 ${model.color} rounded-full flex items-center justify-center text-white`}>
                      <model.icon className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{model.model}</CardTitle>
                      <p className="text-sm text-muted-foreground">{model.bu}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground">{model.description}</p>
                  <div className="space-y-2">
                    {model.features.map((feature, featureIndex) => (
                      <div key={featureIndex} className="flex items-center space-x-2">
                        <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                        <span className="text-xs">{feature}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* System Architecture */}
        <div className="space-y-8">
          <div className="text-center space-y-4">
            <h3 className="text-2xl font-bold">Arquitectura del Sistema</h3>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Componentes especializados que trabajan en conjunto para un ecosistema financiero robusto
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {systemComponents.map((component, index) => (
              <Card key={index} className="glass border-primary/20">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Calendar className="h-5 w-5 text-primary" />
                    <div>
                      <div className="text-sm font-medium">{component.split(' - ')[0]}</div>
                      <div className="text-xs text-muted-foreground">{component.split(' - ')[1]}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="text-center mt-16">
          <Card className="glass border-primary/20 max-w-3xl mx-auto">
            <CardContent className="p-8 space-y-6">
              <h3 className="text-2xl font-bold">Optimiza tus Procesos de Pago</h3>
              <p className="text-muted-foreground">
                Implementa un sistema de pagos robusto y escalable que se adapte a tu modelo de negocio específico.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" className="bg-primary hover:bg-primary/90">
                  Demo del Sistema
                  <CreditCard className="ml-2 h-5 w-5" />
                </Button>
                <Button variant="outline" size="lg">
                  Documentación API
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default PaymentSystemSection;