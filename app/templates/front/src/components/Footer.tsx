import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Calendar, Mail, Phone, ArrowRight } from 'lucide-react';

const Footer = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const businessUnits = [
    {
      name: "FinTech Solutions",
      contact: "fintech@techai.com",
      phone: "+1 (555) 123-4567"
    },
    {
      name: "Healthcare AI",
      contact: "healthcare@techai.com", 
      phone: "+1 (555) 234-5678"
    },
    {
      name: "Retail Intelligence",
      contact: "retail@techai.com",
      phone: "+1 (555) 345-6789"
    },
    {
      name: "Industrial IoT",
      contact: "industry@techai.com",
      phone: "+1 (555) 456-7890"
    }
  ];

  const socialLinks = [
    { name: "LinkedIn", url: "#", icon: "linkedin" },
    { name: "Twitter", url: "#", icon: "twitter" },
    { name: "GitHub", url: "#", icon: "github" },
    { name: "YouTube", url: "#", icon: "youtube" }
  ];

  const openGoogleAppointment = () => {
    // Aquí iría la URL real de Google Appointments
    window.open('https://calendar.google.com/calendar/appointments/your-appointment-link', '_blank', 'width=800,height=600');
    setIsModalOpen(false);
  };

  return (
    <footer className="bg-card border-t-2 border-primary/20">
      {/* CTA Section in Footer */}
      <div className="container mx-auto px-4 lg:px-8 py-16">
        <Card className="glass border-primary/20 max-w-4xl mx-auto">
          <CardContent className="p-8 text-center space-y-6">
            <div className="space-y-4">
              <h3 className="text-3xl font-bold">
                Agenda una Demo con nuestro <span className="bg-tech-gradient bg-clip-text text-transparent">CEO</span>
              </h3>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Conecta directamente con nuestra dirección ejecutiva para discutir cómo podemos transformar tu negocio con IA
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                <DialogTrigger asChild>
                  <Button size="lg" className="bg-tech-gradient hover:opacity-90 transition-opacity">
                    <Calendar className="mr-2 h-5 w-5" />
                    Agendar con CEO
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>Agendar Demo Ejecutiva</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <p className="text-muted-foreground">
                      Serás redirigido a nuestro sistema de citas de Google Calendar para seleccionar el mejor horario.
                    </p>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-lg font-bold text-primary">60min</div>
                        <div className="text-xs text-muted-foreground">Demo completa</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-primary">CEO</div>
                        <div className="text-xs text-muted-foreground">Atención directa</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-primary">1:1</div>
                        <div className="text-xs text-muted-foreground">Personalizado</div>
                      </div>
                    </div>
                    <Button onClick={openGoogleAppointment} className="w-full bg-tech-gradient">
                      Continuar a Google Calendar
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>

              <Button size="lg" variant="outline" className="border-primary/30 hover:bg-primary/10">
                <Mail className="mr-2 h-5 w-5" />
                Contacto Directo
              </Button>
            </div>

            <div className="grid md:grid-cols-3 gap-6 pt-6 border-t">
              <div className="text-center">
                <div className="text-xl font-bold text-primary">C-Level</div>
                <div className="text-sm text-muted-foreground">Atención ejecutiva</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-primary">Demo Live</div>
                <div className="text-sm text-muted-foreground">Productos reales</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-primary">ROI</div>
                <div className="text-sm text-muted-foreground">Análisis incluido</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Footer Content */}
      <div className="bg-secondary/80 border-t border-primary/20">
        <div className="container mx-auto px-4 lg:px-8 py-12">
          <div className="grid md:grid-cols-4 gap-8">
            {/* Company Info */}
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-tech-gradient rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">AI</span>
                </div>
                <span className="text-xl font-bold bg-tech-gradient bg-clip-text text-transparent">
                  TechAI
                </span>
              </div>
              <p className="text-muted-foreground text-sm">
                Transformando empresas con Inteligencia Artificial de vanguardia. Soluciones personalizadas para el futuro digital.
              </p>
              <div className="space-y-2">
                <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                  <Mail className="h-4 w-4" />
                  <span>contact@techai.com</span>
                </div>
                <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                  <Phone className="h-4 w-4" />
                  <span>+1 (555) 123-4567</span>
                </div>
              </div>
            </div>

            {/* Business Units */}
            <div className="space-y-4">
              <h4 className="font-semibold">Unidades de Negocio</h4>
              <div className="space-y-3">
                {businessUnits.map((unit, index) => (
                  <div key={index} className="space-y-1">
                    <div className="text-sm font-medium">{unit.name}</div>
                    <div className="text-xs text-muted-foreground">{unit.contact}</div>
                    <div className="text-xs text-muted-foreground">{unit.phone}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Links */}
            <div className="space-y-4">
              <h4 className="font-semibold">Enlaces Rápidos</h4>
              <div className="space-y-2">
                {['Tecnologías', 'Casos de Éxito', 'Blog', 'Recursos', 'Documentación', 'Soporte'].map((link) => (
                  <a key={link} href="#" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                    {link}
                  </a>
                ))}
              </div>
            </div>

            {/* Social & Legal */}
            <div className="space-y-4">
              <h4 className="font-semibold">Síguenos</h4>
              <div className="flex space-x-3">
                {socialLinks.map((social) => (
                  <a
                    key={social.name}
                    href={social.url}
                    className="w-10 h-10 bg-muted hover:bg-primary/10 rounded-lg flex items-center justify-center text-muted-foreground hover:text-primary transition-all hover:scale-110"
                    aria-label={social.name}
                  >
                    <span className="text-sm font-bold">{social.icon.slice(0, 2).toUpperCase()}</span>
                  </a>
                ))}
              </div>
              
              <div className="space-y-2 pt-4">
                <h5 className="text-sm font-medium">Legal</h5>
                {['Términos de Servicio', 'Política de Privacidad', 'Cookies'].map((link) => (
                  <a key={link} href="#" className="block text-xs text-muted-foreground hover:text-primary transition-colors">
                    {link}
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="bg-primary/10 border-t border-primary/30">
        <div className="container mx-auto px-4 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="text-sm text-foreground/80">
              © 2024 TechAI. Todos los derechos reservados.
            </div>
            <div className="flex items-center space-x-6 text-sm text-foreground/80">
              <span>🇲🇽 México • 🇺🇸 Estados Unidos • 🇪🇸 España</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
