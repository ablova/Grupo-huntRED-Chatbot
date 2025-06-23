
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Quote, Star, Heart } from 'lucide-react';

const TestimonialsSection = () => {
  const testimonials = [
    {
      name: "María González",
      role: "CEO, EcoVerde",
      company: "Startup Sostenible",
      content: "No solo desarrollaron nuestra plataforma, entendieron nuestra misión. Cada reunión se sentía como hablar con amigos que realmente querían ver nuestro proyecto crecer.",
      image: "https://images.unsplash.com/photo-1494790108755-2616b332e234?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&q=80",
      impact: "300% incremento en usuarios",
      emotion: "💚"
    },
    {
      name: "Carlos Mendoza",
      role: "Director de Innovación",
      company: "TechMed Solutions",
      content: "Transformaron años de frustración con sistemas obsoletos en una experiencia que nuestros médicos aman usar. El cambio fue inmediato y profundo.",
      image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&q=80",
      impact: "89% reducción en tiempo de consultas",
      emotion: "🚀"
    },
    {
      name: "Ana Rodríguez",
      role: "Fundadora",
      company: "MiPyme Digital",
      content: "Llegué con miedo a la tecnología y me enseñaron que puede ser hermosa y simple. Ahora mi negocio familiar compite con las grandes empresas.",
      image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&q=80",
      impact: "500% crecimiento en ventas",
      emotion: "✨"
    }
  ];

  return (
    <section className="py-20 bg-gradient-to-br from-background to-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-6 mb-16">
          <div className="inline-flex items-center gap-2 bg-primary/10 rounded-full px-4 py-2 text-sm font-medium text-primary">
            <Heart className="w-4 h-4" />
            Historias reales de personas reales
          </div>
          
          <h2 className="text-3xl md:text-4xl font-bold">
            Más que clientes, son <span className="bg-tech-gradient bg-clip-text text-transparent">familia</span>
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Cada proyecto nos enseña algo nuevo. Cada cliente se convierte en parte de nuestra historia.
            Estas son algunas de las transformaciones que hemos vivido juntos.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {testimonials.map((testimonial, index) => (
            <Card key={index} className="group hover:shadow-xl transition-all duration-500 hover:-translate-y-2 border-0 shadow-lg bg-card/50 backdrop-blur">
              <CardContent className="p-8 space-y-6">
                {/* Quote Icon */}
                <div className="flex justify-between items-start">
                  <Quote className="w-8 h-8 text-primary/30" />
                  <div className="text-2xl">{testimonial.emotion}</div>
                </div>
                
                {/* Content */}
                <blockquote className="text-muted-foreground leading-relaxed italic">
                  "{testimonial.content}"
                </blockquote>
                
                {/* Impact Metric */}
                <div className="p-4 bg-primary/5 rounded-lg border-l-4 border-primary">
                  <div className="font-semibold text-primary">Resultado:</div>
                  <div className="text-sm text-muted-foreground">{testimonial.impact}</div>
                </div>
                
                {/* Author */}
                <div className="flex items-center space-x-4 pt-4 border-t">
                  <img
                    src={testimonial.image}
                    alt={testimonial.name}
                    className="w-12 h-12 rounded-full object-cover ring-2 ring-primary/20"
                  />
                  <div>
                    <div className="font-semibold">{testimonial.name}</div>
                    <div className="text-sm text-muted-foreground">{testimonial.role}</div>
                    <div className="text-xs text-primary">{testimonial.company}</div>
                  </div>
                </div>
                
                {/* Rating */}
                <div className="flex items-center space-x-1">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Trust Section */}
        <div className="text-center">
          <Card className="glass border-primary/20 max-w-2xl mx-auto">
            <CardContent className="p-8 space-y-4">
              <h3 className="text-2xl font-bold">¿Lista para escribir tu historia de éxito?</h3>
              <p className="text-muted-foreground">
                Cada gran proyecto comienza con una conversación honesta. 
                Cuéntanos tus desafíos y descubramos juntos las soluciones.
              </p>
              <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
                <span>• Sin compromisos</span>
                <span>• Consulta gratuita</span>
                <span>• Respuesta en 24h</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default TestimonialsSection;
