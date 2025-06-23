
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Heart, Coffee, Lightbulb, Rocket, Users, CheckCircle } from 'lucide-react';

const ProcessSection = () => {
  const steps = [
    {
      icon: Coffee,
      title: "Conversemos como humanos",
      description: "Todo comienza con café (virtual o presencial). Queremos conocerte, entender tu mundo y los desafíos que enfrentas día a día.",
      details: [
        "Escuchamos tu historia completa",
        "Identificamos tus verdaderas necesidades", 
        "Sin jerga técnica, solo conversación honesta"
      ],
      duration: "1-2 semanas",
      color: "bg-orange-500/10 border-orange-500/20 text-orange-600"
    },
    {
      icon: Lightbulb,
      title: "Diseñamos juntos la solución",
      description: "Tu experiencia + nuestra tecnología = magia. Creamos prototipos que puedas tocar, sentir y mejorar con nosotros.",
      details: [
        "Bocetos que puedes entender",
        "Prototipos interactivos",
        "Tus ideas son protagonistas"
      ],
      duration: "2-3 semanas",
      color: "bg-yellow-500/10 border-yellow-500/20 text-yellow-600"
    },
    {
      icon: Heart,
      title: "Construimos con cariño",
      description: "Cada línea de código la escribimos pensando en las personas que la usarán. Calidad, elegancia y funcionalidad van de la mano.",
      details: [
        "Desarrollo iterativo y transparente",
        "Pruebas constantes contigo",
        "Atención a cada detalle"
      ],
      duration: "4-12 semanas",
      color: "bg-red-500/10 border-red-500/20 text-red-600"
    },
    {
      icon: Rocket,
      title: "Lanzamos y celebramos",
      description: "El lanzamiento es solo el comienzo. Te acompañamos en cada paso del crecimiento de tu proyecto.",
      details: [
        "Lanzamiento sin estrés",
        "Monitoreo en tiempo real",
        "Ajustes inmediatos si es necesario"
      ],
      duration: "1 semana",
      color: "bg-blue-500/10 border-blue-500/20 text-blue-600"
    },
    {
      icon: Users,
      title: "Crecemos contigo",
      description: "Tu éxito es nuestro éxito. Estamos aquí para todas las etapas de crecimiento de tu proyecto.",
      details: [
        "Soporte técnico humano",
        "Nuevas funcionalidades según crezcas",
        "Relación a largo plazo"
      ],
      duration: "Para siempre",
      color: "bg-green-500/10 border-green-500/20 text-green-600"
    }
  ];

  return (
    <section className="py-16 bg-background">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-12">
          <div className="inline-flex items-center gap-2 bg-primary/10 rounded-full px-4 py-2 text-sm font-medium text-primary">
            <Heart className="w-4 h-4" />
            Nuestro proceso centrado en las personas
          </div>
          
          <h2 className="text-3xl md:text-4xl font-bold">
            Cómo transformamos <span className="bg-tech-gradient bg-clip-text text-transparent">ideas en realidad</span>
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">No seguimos metodologías rígidas. Nos adaptamos a tu ritmo, tu estilo y tus necesidades. Porque cada cliente es único, como las personas detrás.</p>
        </div>

        {/* Process Timeline - Reduced spacing */}
        <div className="relative">
          {/* Connection Line */}
          <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary/30 via-primary/60 to-primary/30 transform -translate-x-1/2 hidden lg:block" />
          
          <div className="space-y-8">
            {steps.map((step, index) => (
              <div key={index} className={`flex items-center gap-8 ${index % 2 === 1 ? 'lg:flex-row-reverse' : ''}`}>
                {/* Content Card */}
                <div className="flex-1">
                  <Card className={`${step.color} border-2 hover:shadow-xl transition-all duration-300 hover:-translate-y-1`}>
                    <CardContent className="p-6 space-y-4">
                      <div className="flex items-start gap-4">
                        <div className={`w-12 h-12 rounded-full ${step.color} flex items-center justify-center`}>
                          <step.icon className="w-6 h-6" />
                        </div>
                        <div className="space-y-2 flex-1">
                          <h3 className="text-xl font-bold">{step.title}</h3>
                          <p className="text-muted-foreground">{step.description}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium text-primary">{step.duration}</div>
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        {step.details.map((detail, detailIndex) => (
                          <div key={detailIndex} className="flex items-center gap-3">
                            <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                            <span className="text-sm text-muted-foreground">{detail}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Step Number */}
                <div className="hidden lg:flex w-16 h-16 rounded-full bg-tech-gradient items-center justify-center text-white font-bold text-xl shadow-lg">
                  {index + 1}
                </div>

                {/* Spacer for alternating layout */}
                <div className="flex-1 hidden lg:block" />
              </div>
            ))}
          </div>
        </div>

        {/* Call to Action - Reduced spacing */}
        <div className="mt-12 text-center">
          <Card className="glass border-primary/20 max-w-4xl mx-auto">
            <CardContent className="p-6 space-y-4">
              <h3 className="text-3xl font-bold">¿Te gustaría comenzar este viaje juntos?</h3>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                No importa si tu idea está en pañales o si ya tienes todo planeado. 
                Estamos aquí para escucharte y acompañarte en cada paso.
              </p>
              
              <div className="grid md:grid-cols-3 gap-6 mt-6">
                <div className="text-center space-y-2">
                  <div className="text-2xl">📞</div>
                  <div className="font-semibold">Llamada inicial</div>
                  <div className="text-sm text-muted-foreground">30 min • Completamente gratis</div>
                </div>
                <div className="text-center space-y-2">
                  <div className="text-2xl">💡</div>
                  <div className="font-semibold">Propuesta personalizada</div>
                  <div className="text-sm text-muted-foreground">Diseñada específicamente para ti</div>
                </div>
                <div className="text-center space-y-2">
                  <div className="text-2xl">🤝</div>
                  <div className="font-semibold">Sin compromiso</div>
                  <div className="text-sm text-muted-foreground">Decides después de conocernos</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default ProcessSection;
