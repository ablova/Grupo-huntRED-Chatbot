import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowRight, Building, Users, Briefcase, Zap, Target } from 'lucide-react';

const BusinessUnitsSection = () => {
  const huntredBrands = [
    {
      name: "huntRED® Executive",
      tagline: "Liderazgo C-Level y Dirección Estratégica",
      description: "Búsqueda ejecutiva de más alto nivel para transformar organizaciones",
      color: "bg-purple-600",
      accent: "text-purple-600",
      bg: "bg-purple-500/15 border-purple-500/30",
      level: 1,
      icon: "👑"
    },
    {
      name: "huntRED®",
      tagline: "Gerencial y Alta Especialización",
      description: "Reclutamiento especializado para posiciones gerenciales estratégicas",
      color: "bg-red-600",
      accent: "text-red-600",
      bg: "bg-red-500/15 border-red-500/30",
      level: 2,
      icon: "🎯"
    },
    {
      name: "huntU®",
      tagline: "Talento Joven y Profesionales Junior",
      description: "Conectamos el futuro del talento con oportunidades de crecimiento",
      color: "bg-orange-500",
      accent: "text-orange-600",
      bg: "bg-orange-500/15 border-orange-500/30",
      level: 3,
      icon: "🚀"
    },
    {
      name: "amigro®",
      tagline: "Reclutamiento Masivo y Operativo",
      description: "Soluciones eficientes para posiciones operativas y reclutamiento de volumen",
      color: "bg-green-500",
      accent: "text-green-600",
      bg: "bg-green-500/15 border-green-500/30",
      level: 4,
      icon: "⚡"
    }
  ];

  const sectorialDivisions = [
    {
      name: "Legal",
      description: "Abogados, consultores jurídicos y especialistas en compliance",
      icon: "⚖️",
      specialties: ["Derecho Corporativo", "Compliance", "Propiedad Intelectual", "Litigation"]
    },
    {
      name: "Servicios Financieros",
      description: "Banca, seguros, fintech y gestión de activos",
      icon: "💰",
      specialties: ["Banking", "Insurance", "FinTech", "Asset Management"]
    },
    {
      name: "Energía",
      description: "Renovables, petróleo, gas y eficiencia energética",
      icon: "⚡",
      specialties: ["Renewables", "Oil & Gas", "Energy Efficiency", "Smart Grid"]
    },
    {
      name: "Healthcare",
      description: "Salud, farmacéutica, biotecnología y dispositivos médicos",
      icon: "🏥",
      specialties: ["Pharmaceutical", "Biotech", "Medical Devices", "Digital Health"]
    }
  ];

  const functionalDivisions = [
    {
      name: "Ventas y Mercadotecnia",
      description: "Comercial, marketing digital y growth marketing",
      icon: "📈",
      specialties: ["Sales", "Digital Marketing", "Growth", "CRM"]
    },
    {
      name: "Finanzas y Contabilidad",
      description: "CFO, controllers, auditores y analistas financieros",
      icon: "📊",
      specialties: ["Finance", "Accounting", "Audit", "FP&A"]
    },
    {
      name: "Manufactura e Industria",
      description: "Operaciones, supply chain y lean manufacturing",
      icon: "🏭",
      specialties: ["Operations", "Supply Chain", "Lean", "Quality"]
    },
    {
      name: "Tecnologías de la Información",
      description: "Desarrollo, infraestructura, ciberseguridad y datos",
      icon: "💻",
      specialties: ["Software Development", "Infrastructure", "Cybersecurity", "Data"]
    },
    {
      name: "Sustentabilidad",
      description: "ESG, economía circular y responsabilidad social",
      icon: "🌱",
      specialties: ["ESG", "Circular Economy", "CSR", "Carbon Management"]
    }
  ];

  return (
    <section id="business-units" className="py-20 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        {/* Call to Action moved before Business Units */}
        <div className="mb-16 text-center">
          <Card className="glass border-primary/20 max-w-4xl mx-auto">
            <CardContent className="p-8 space-y-6">
              <h3 className="text-3xl font-bold">¿Necesitas talento especializado?</h3>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Nuestras 4 unidades de negocio y 9 divisiones de expertise nos permiten encontrar exactamente 
                el perfil que tu empresa necesita.
              </p>
              
              <div className="grid md:grid-cols-3 gap-6 mt-8">
                <div className="text-center space-y-2">
                  <div className="text-2xl">🎯</div>
                  <div className="font-semibold">Especialización</div>
                  <div className="text-sm text-muted-foreground">Expertise profunda en cada sector</div>
                </div>
                <div className="text-center space-y-2">
                  <div className="text-2xl">⚡</div>
                  <div className="font-semibold">Rapidez</div>
                  <div className="text-sm text-muted-foreground">Procesos optimizados con IA</div>
                </div>
                <div className="text-center space-y-2">
                  <div className="text-2xl">🤝</div>
                  <div className="font-semibold">Confianza</div>
                  <div className="text-sm text-muted-foreground">Metodología probada y resultados</div>
                </div>
              </div>
              
              <Button size="lg" className="bg-tech-gradient hover:opacity-90 transition-opacity">
                Solicitar Consultoría Especializada
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="text-center space-y-4 mb-16">
          <h2 className="text-3xl md:text-4xl font-bold">
            Nuestras <span className="bg-tech-gradient bg-clip-text text-transparent">Unidades de Negocio</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Estructura jerárquica organizacional con cuatro niveles especializados
          </p>
        </div>

        {/* Hierarchical Business Units */}
        <div className="space-y-8 mb-16">
          {huntredBrands.map((brand, index) => (
            <Card key={index} className={`group hover:shadow-xl transition-all duration-300 hover:-translate-y-1 ${brand.bg} border-2 max-w-4xl mx-auto`}>
              <CardContent className="p-8">
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-4">
                    <div className={`w-16 h-16 ${brand.color} rounded-full flex items-center justify-center text-white text-2xl`}>
                      {brand.icon}
                    </div>
                    <div className="text-6xl font-bold text-muted-foreground/20">
                      {brand.level}
                    </div>
                  </div>
                  
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className={`text-2xl font-bold ${brand.accent}`}>
                        {brand.name}
                      </h3>
                      <div className="text-sm text-muted-foreground">
                        Nivel {brand.level}
                      </div>
                    </div>
                    <p className="text-lg font-medium text-muted-foreground">
                      {brand.tagline}
                    </p>
                    <p className="text-muted-foreground">
                      {brand.description}
                    </p>
                    
                    <Button variant="ghost" size="sm" className="group-hover:bg-primary/10 transition-colors">
                      Conocer Más
                      <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Metodología de Especialización */}
        <div className="space-y-12">
          <div className="text-center space-y-4">
            <h3 className="text-2xl font-bold">Metodología de Especialización</h3>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              9 divisiones de expertise que soportan todas nuestras marcas con conocimiento profundo del mercado
            </p>
          </div>

          {/* Divisiones Sectoriales */}
          <div className="space-y-6">
            <h4 className="text-xl font-semibold text-center">Divisiones Sectoriales</h4>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {sectorialDivisions.map((division, index) => (
                <Card key={index} className="glass border-primary/20 hover:shadow-lg transition-shadow">
                  <CardContent className="p-4 space-y-3">
                    <div className="text-center">
                      <div className="text-3xl mb-2">{division.icon}</div>
                      <h5 className="font-semibold">{division.name}</h5>
                      <p className="text-xs text-muted-foreground">{division.description}</p>
                    </div>
                    <div className="space-y-1">
                      {division.specialties.map((specialty, specIndex) => (
                        <div key={specIndex} className="flex items-center space-x-2">
                          <div className="w-1 h-1 bg-primary rounded-full" />
                          <span className="text-xs">{specialty}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Divisiones Funcionales */}
          <div className="space-y-6">
            <h4 className="text-xl font-semibold text-center">Divisiones Funcionales</h4>
            <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-4">
              {functionalDivisions.map((division, index) => (
                <Card key={index} className="glass border-primary/20 hover:shadow-lg transition-shadow">
                  <CardContent className="p-4 space-y-3">
                    <div className="text-center">
                      <div className="text-3xl mb-2">{division.icon}</div>
                      <h5 className="font-semibold text-sm">{division.name}</h5>
                      <p className="text-xs text-muted-foreground">{division.description}</p>
                    </div>
                    <div className="space-y-1">
                      {division.specialties.map((specialty, specIndex) => (
                        <div key={specIndex} className="flex items-center space-x-2">
                          <div className="w-1 h-1 bg-primary rounded-full" />
                          <span className="text-xs">{specialty}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default BusinessUnitsSection;
