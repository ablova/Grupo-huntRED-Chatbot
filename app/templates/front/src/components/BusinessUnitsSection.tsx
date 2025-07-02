import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowRight, Building, Users, Briefcase, Zap, Target } from 'lucide-react';

const BusinessUnitsSection = () => {
// Pyramid structure for business units
  const pyramidUnits = [
    {
      name: "huntRED® Executive",
      tagline: "Liderazgo C-Level y Dirección Estratégica",
      description: "Búsqueda ejecutiva de más alto nivel para transformar organizaciones con modelo AI optimizado",
      color: "bg-orange-500",
      accent: "text-orange-600",
      bg: "bg-orange-500/10 border-orange-500/30",
      level: 1,
      icon: "👑",
      size: "small",
      width: "w-56"
    },
    {
      name: "huntRED®",
      tagline: "Gerencial y Alta Especialización",
      description: "Reclutamiento especializado para posiciones gerenciales con modelo porcentaje optimizado",
      color: "bg-red-600",
      accent: "text-red-600",
      bg: "bg-red-500/10 border-red-500/30",
      level: 2,
      icon: "🎯",
      size: "medium",
      width: "w-64"
    },
    {
      name: "huntU®",
      tagline: "Talento Joven y Profesionales Junior",
      description: "Conectamos el futuro del talento universitario con modelo fijo especializado",
      color: "bg-emerald-500",
      accent: "text-emerald-600",
      bg: "bg-emerald-500/10 border-emerald-500/30",
      level: 3,
      icon: "🚀",
      size: "medium",
      width: "w-72"
    },
    {
      name: "amigro®",
      tagline: "Reclutamiento Masivo y Operativo",
      description: "Soluciones eficientes para perfiles técnicos migrantes con modelo fijo de volumen",
      color: "bg-primary",
      accent: "text-primary",
      bg: "bg-primary/10 border-primary/30",
      level: 4,
      icon: "⚡",
      size: "large",
      width: "w-80"
    }
  ];

  const specializedUnits = [
    {
      name: "huntRED® Experience",
      tagline: "Talento Senior +50",
      description: "Experiencia laboral avanzada y mentoring",
      icon: "🌟",
      color: "bg-violet-500"
    },
    {
      name: "huntRED® Inspiration",
      tagline: "Inclusión Laboral",
      description: "Diversidad e inclusión empresarial",
      icon: "🤝",
      color: "bg-pink-500"
    },
    {
      name: "huntRED® Solutions",
      tagline: "Consultoría y Outsourcing",
      description: "Soluciones integrales de RH",
      icon: "🔧",
      color: "bg-indigo-500"
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

        {/* Pyramid Structure */}
        <div className="mb-20">
          <div className="flex flex-col lg:flex-row gap-12 items-start justify-center">
            {/* Main Pyramid */}
            <div className="flex-1 max-w-4xl">
              <div className="space-y-6">
                {pyramidUnits.map((unit, index) => (
                  <div key={index} className="flex justify-center">
                    <Card className={`group hover:shadow-xl transition-all duration-300 hover:-translate-y-1 ${unit.bg} border-2 ${unit.width}`}>
                      <CardContent className="p-6">
                        <div className="text-center space-y-4">
                          <div className="flex items-center justify-center gap-4">
                            <div className={`w-14 h-14 ${unit.color} rounded-full flex items-center justify-center text-white text-xl shadow-lg`}>
                              {unit.icon}
                            </div>
                            <div className="text-4xl font-bold text-muted-foreground/20">
                              {unit.level}
                            </div>
                          </div>
                          
                          <div className="space-y-2">
                            <h3 className={`text-xl font-bold ${unit.accent}`}>
                              {unit.name}
                            </h3>
                            <p className="text-base font-medium text-muted-foreground">
                              {unit.tagline}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {unit.description}
                            </p>
                          </div>
                          
                          <Button variant="ghost" size="sm" className="group-hover:bg-primary/10 transition-colors">
                            Conocer Más
                            <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                ))}
              </div>
            </div>

            {/* Specialized Units Support */}
            <div className="lg:w-80 space-y-4">
              <h4 className="text-lg font-semibold text-center mb-6">Unidades Especializadas</h4>
              {specializedUnits.map((unit, index) => (
                <Card key={index} className="glass border-primary/20 hover:shadow-lg transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 ${unit.color} rounded-full flex items-center justify-center text-white text-sm`}>
                        {unit.icon}
                      </div>
                      <div className="flex-1">
                        <h5 className="font-semibold text-sm">{unit.name}</h5>
                        <p className="text-xs text-muted-foreground">{unit.tagline}</p>
                        <p className="text-xs text-muted-foreground mt-1">{unit.description}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
              
              {/* 9 Divisions Support */}
              <div className="mt-8 space-y-4">
                <h4 className="text-lg font-semibold text-center">Soporte Divisional</h4>
                
                {/* Sectorial Divisions */}
                <div className="space-y-2">
                  <h5 className="text-sm font-medium text-muted-foreground">Sectoriales</h5>
                  {sectorialDivisions.map((division, index) => (
                    <div key={index} className="flex items-center gap-2 p-2 rounded-lg glass border border-primary/10">
                      <span className="text-lg">{division.icon}</span>
                      <span className="text-xs font-medium">{division.name}</span>
                    </div>
                  ))}
                </div>
                
                {/* Functional Divisions */}
                <div className="space-y-2">
                  <h5 className="text-sm font-medium text-muted-foreground">Funcionales</h5>
                  {functionalDivisions.map((division, index) => (
                    <div key={index} className="flex items-center gap-2 p-2 rounded-lg glass border border-primary/10">
                      <span className="text-lg">{division.icon}</span>
                      <span className="text-xs font-medium">{division.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
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
