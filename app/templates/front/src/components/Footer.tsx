import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Calendar, Mail, Phone, ArrowRight, Brain, Star, Zap } from 'lucide-react';

const Footer = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const businessUnits = [
    {
      name: "huntRED® executive",
      contact: "executive@huntred.com",
      phone: "+52 (55) 5914-0089"
    },
    {
      name: "huntRED® Inspiration",
      contact: "inspiration@huntred.com", 
      phone: "+52 (55) 5914-0089"
    },
    {
      name: "huntRED® Experience",
      contact: "experience@huntred.com",
      phone: "+52 (55) 5914-0089"
    },
    {
      name: "huntRED® Solutions",
      contact: "solutions@huntred.com",
      phone: "+52 (55) 5914-0089"
    }
  ];

  const socialLinks = [
    {
      name: "LinkedIn",
      url: "#",
      icon: "LI"
    },
    {
      name: "Twitter", 
      url: "#",
      icon: "TW"
    },
    {
      name: "GitHub",
      url: "#",
      icon: "GH"
    },
    {
      name: "YouTube",
      url: "#",
      icon: "YT"
    }
  ];

  const openGoogleAppointment = () => {
    window.open('https://calendar.google.com/calendar/appointments/your-appointment-link', '_blank', 'width=800,height=600');
    setIsModalOpen(false);
  };

  return (
    <footer className="bg-slate-900 text-slate-100 border-t border-slate-800">
      {/* Enhanced CTA Section */}
      <div className="container mx-auto px-4 lg:px-8 py-16">
        <Card className="glass border-primary/30 max-w-4xl mx-auto bg-slate-800/50 border-2 shadow-2xl relative overflow-hidden">
          {/* Background Effects */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-transparent to-emerald-500/10" />
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/20 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-emerald-500/20 rounded-full blur-2xl" />
          
          <CardContent className="p-8 text-center space-y-6 relative z-10">
            <div className="space-y-4">
              <div className="inline-flex items-center space-x-2 bg-primary/20 rounded-full px-4 py-2 border border-primary/30">
                <Star className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium text-primary">ACCESO EJECUTIVO</span>
              </div>
              
              <h3 className="text-3xl md:text-4xl font-bold text-slate-100">
                Agenda una Demo con nuestro <span className="text-primary font-bold">CEO</span>
              </h3>
              <p className="text-lg text-slate-300 max-w-2xl mx-auto">
                Conecta directamente con nuestra dirección ejecutiva para discutir cómo transformar tu negocio con IA huntRED®
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                <DialogTrigger asChild>
                  <Button 
                    size="lg" 
                    className="huntred-gradient-bg hover:opacity-90 transition-all transform hover:scale-105 shadow-lg hover:shadow-xl border-2 border-red-500/50 font-semibold text-lg px-8 py-4 text-white"
                  >
                    <Calendar className="mr-2 h-6 w-6" />
                    Agendar con CEO
                    <Zap className="ml-2 h-5 w-5" />
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md bg-slate-800 border-slate-700">
                  <DialogHeader>
                    <DialogTitle className="text-slate-100 text-center">
                      <span className="text-primary font-bold">Demo Ejecutiva huntRED®</span>
                    </DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <p className="text-slate-300 text-center">
                      Serás redirigido a nuestro sistema de citas de Google Calendar para seleccionar el mejor horario para tu demo personalizada.
                    </p>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div className="p-3 bg-slate-700/50 rounded-lg">
                        <div className="text-lg font-bold text-primary">60min</div>
                        <div className="text-xs text-slate-400">Demo completa</div>
                      </div>
                      <div className="p-3 bg-slate-700/50 rounded-lg">
                        <div className="text-lg font-bold text-primary">CEO</div>
                        <div className="text-xs text-slate-400">Atención directa</div>
                      </div>
                      <div className="p-3 bg-slate-700/50 rounded-lg">
                        <div className="text-lg font-bold text-primary">1:1</div>
                        <div className="text-xs text-slate-400">Personalizado</div>
                      </div>
                    </div>
                    <Button 
                      onClick={openGoogleAppointment} 
                      className="w-full modern-gradient-bg hover:opacity-90 transition-all font-semibold text-white"
                    >
                      Continuar a Google Calendar
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>

              <Button 
                size="lg" 
                variant="outline" 
                className="border-primary/50 hover:bg-primary/10 text-slate-100 hover:text-primary hover:border-primary transition-all transform hover:scale-105"
              >
                <Mail className="mr-2 h-5 w-5" />
                Contacto Directo
              </Button>
            </div>

            <div className="grid md:grid-cols-3 gap-6 pt-6 border-t border-slate-700">
              <div className="text-center p-4 bg-slate-700/30 rounded-lg">
                <div className="text-xl font-bold text-primary mb-1">C-Level</div>
                <div className="text-sm text-slate-400">Atención ejecutiva personalizada</div>
              </div>
              <div className="text-center p-4 bg-slate-700/30 rounded-lg">
                <div className="text-xl font-bold text-primary mb-1">Demo Live</div>
                <div className="text-sm text-slate-400">Productos reales en funcionamiento</div>
              </div>
              <div className="text-center p-4 bg-slate-700/30 rounded-lg">
                <div className="text-xl font-bold text-primary mb-1">ROI</div>
                <div className="text-sm text-slate-400">Análisis de retorno incluido</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Footer Content */}
      <div className="container mx-auto px-4 lg:px-8 py-12">
        <div className="grid md:grid-cols-4 gap-8">
          {/* Company Info */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 modern-gradient-bg rounded-lg flex items-center justify-center">
                <Brain className="text-white h-4 w-4" />
              </div>
              <span className="text-xl font-bold text-primary">Grupo huntRED®</span>
            </div>
            <p className="text-slate-400 text-sm">
              Transformando empresas con Inteligencia Artificial de vanguardia. 
              Soluciones de reclutamiento y desarrollo profesional ajustadas para tu empresa.
            </p>
            <div className="space-y-2">
              <div className="flex items-center space-x-2 text-sm text-slate-400">
                <Mail className="h-4 w-4 text-primary" />
                <span>hola@huntred.com</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-slate-400">
                <Phone className="h-4 w-4 text-primary" />
                <span>+52 (55) 5914-0089</span>
              </div>
            </div>
          </div>

          {/* Business Units */}
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-200">Unidades de Negocio</h4>
            <div className="space-y-3">
              {businessUnits.map((unit, index) => (
                <div key={index} className="space-y-1 p-2 bg-slate-800/50 rounded-lg hover:bg-slate-700/50 transition-colors">
                  <div className="text-sm font-medium text-slate-300">{unit.name}</div>
                  <div className="text-xs text-slate-500">{unit.contact}</div>
                  <div className="text-xs text-slate-500">{unit.phone}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Links */}
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-200">Enlaces Rápidos</h4>
            <div className="space-y-2">
              {[
                'Tecnologías IA',
                'Casos de Éxito', 
                'Blog Técnico',
                'Recursos',
                'Documentación API',
                'Soporte 24/7'
              ].map(link => (
                <a 
                  key={link} 
                  href="#" 
                  className="block text-sm text-slate-400 hover:text-primary transition-colors hover:translate-x-1 transform"
                >
                  {link}
                </a>
              ))}
            </div>
          </div>

          {/* Social & Legal */}
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-200">Síguenos</h4>
            <div className="flex space-x-3">
              {socialLinks.map(social => (
                <a 
                  key={social.name} 
                  href={social.url} 
                  className="w-10 h-10 bg-slate-800 hover:bg-primary/20 border border-slate-700 hover:border-primary/50 rounded-lg flex items-center justify-center text-slate-400 hover:text-primary transition-all hover:scale-110 transform" 
                  aria-label={social.name}
                >
                  <span className="text-sm font-bold">{social.icon}</span>
                </a>
              ))}
            </div>
            
            <div className="space-y-2 pt-4">
              <h5 className="text-sm font-medium text-slate-200">Legal</h5>
              {['Términos de Servicio', 'Política de Privacidad', 'Cookies'].map(link => (
                <a 
                  key={link} 
                  href="#" 
                  className="block text-xs text-slate-400 hover:text-primary transition-colors"
                >
                  {link}
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-slate-800">
        <div className="container mx-auto px-4 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="text-sm text-slate-400">
              © 2024 <span className="text-primary font-semibold">Grupo huntRED®</span> - GenIA & AURA. Todos los derechos reservados.
            </div>
            <div className="flex items-center space-x-6 text-sm text-slate-400">
              <span>🇲🇽 México • 🇺🇸 Estados Unidos • 🇪🇸 España</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
