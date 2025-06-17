import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Calendar } from 'lucide-react';

const ServicesSection = () => {
  const services = [
    {
      category: "Consultoría",
      title: "Evaluación de IA",
      description: "Análisis completo de la madurez de IA en tu organización y roadmap de implementación.",
      duration: "2-4 semanas",
      deliverables: ["Audit Report", "Implementation Roadmap", "ROI Analysis"],
      price: "Desde $15,000",
      popular: false
    },
    {
      category: "Desarrollo",
      title: "MVP de IA",
      description: "Desarrollo rápido de un producto mínimo viable para validar tu idea con IA real.",
      duration: "6-12 semanas",
      deliverables: ["MVP Functional", "Tech Documentation", "Training Dataset"],
      price: "Desde $50,000",
      popular: true
    },
    {
      category: "Implementación",
      title: "Solución Enterprise",
      description: "Desarrollo completo de soluciones de IA escalables para grandes organizaciones.",
      duration: "3-9 meses",
      deliverables: ["Full Solution", "Integration", "Training & Support"],
      price: "Consultar",
      popular: false
    }
  ];

  const addons = [
    {
      name: "Soporte 24/7",
      description: "Monitoreo continuo y soporte técnico especializado",
      price: "$5,000/mes"
    },
    {
      name: "Training Personalizado",
      description: "Capacitación del equipo interno en las tecnologías implementadas",
      price: "$10,000"
    },
    {
      name: "Data Augmentation",
      description: "Enriquecimiento y limpieza de datasets existentes",
      price: "$15,000"
    },
    {
      name: "API Integration",
      description: "Integración con sistemas existentes vía APIs personalizadas",
      price: "$8,000"
    }
  ];

  return (
    <section id="services" className="py-20 bg-background">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-16">
          <h2 className="text-3xl md:text-4xl font-bold">
            Servicios y <span className="bg-tech-gradient bg-clip-text text-transparent">Evaluaciones</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Desde consultoría estratégica hasta implementaciones completas, te acompañamos en cada etapa de tu transformación con IA
          </p>
        </div>

        {/* Main Services */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {services.map((service, index) => (
            <Card key={index} className={`relative overflow-hidden transition-all duration-300 hover:-translate-y-2 ${
              service.popular ? 'border-primary/50 shadow-xl scale-105' : 'hover:shadow-lg'
            }`}>
              {service.popular && (
                <div className="absolute top-0 left-0 right-0 bg-tech-gradient text-white text-center py-2 text-sm font-medium">
                  Más Popular
                </div>
              )}
              
              <CardHeader className={service.popular ? 'pt-12' : ''}>
                <div className="space-y-2">
                  <Badge variant="secondary" className="w-fit">
                    {service.category}
                  </Badge>
                  <CardTitle className="text-xl">{service.title}</CardTitle>
                  <p className="text-muted-foreground text-sm">{service.description}</p>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Duración:</span>
                    <span className="font-medium">{service.duration}</span>
                  </div>
                  
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Entregables:</span>
                    <ul className="space-y-1">
                      {service.deliverables.map((deliverable, delIndex) => (
                        <li key={delIndex} className="flex items-center space-x-2 text-sm">
                          <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                          <span>{deliverable}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
                
                <div className="border-t pt-4">
                  <div className="text-2xl font-bold bg-tech-gradient bg-clip-text text-transparent mb-4">
                    {service.price}
                  </div>
                  <Button 
                    className={`w-full ${service.popular ? 'bg-tech-gradient hover:opacity-90' : ''}`}
                    variant={service.popular ? 'default' : 'outline'}
                  >
                    Solicitar Cotización
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Add-ons */}
        <div className="space-y-8">
          <h3 className="text-2xl font-bold text-center">Servicios Adicionales</h3>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {addons.map((addon, index) => (
              <Card key={index} className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <CardContent className="p-6 space-y-3">
                  <div className="space-y-2">
                    <h4 className="font-semibold group-hover:text-primary transition-colors">
                      {addon.name}
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      {addon.description}
                    </p>
                  </div>
                  
                  <div className="pt-2 border-t">
                    <div className="text-lg font-bold text-primary">
                      {addon.price}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-16 text-center">
          <Card className="glass border-primary/20 max-w-4xl mx-auto">
            <CardContent className="p-8 space-y-6">
              <h3 className="text-3xl font-bold">¿Listo para transformar tu negocio?</h3>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Agenda una consultoría gratuita con nuestros expertos y descubre cómo la IA puede revolucionar tu empresa
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" className="bg-tech-gradient hover:opacity-90 transition-opacity">
                  <Calendar className="mr-2 h-5 w-5" />
                  Agendar Consultoría Gratuita
                </Button>
                <Button size="lg" variant="outline" className="border-primary/30 hover:bg-primary/10">
                  Ver Casos de Éxito
                </Button>
              </div>
              
              <div className="grid md:grid-cols-3 gap-6 pt-6 border-t">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">30min</div>
                  <div className="text-sm text-muted-foreground">Consultoría inicial</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">100%</div>
                  <div className="text-sm text-muted-foreground">Sin compromiso</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">24h</div>
                  <div className="text-sm text-muted-foreground">Respuesta garantizada</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default ServicesSection;
