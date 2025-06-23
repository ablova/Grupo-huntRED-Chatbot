import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Calendar, Mail, Phone, ArrowRight, Brain } from 'lucide-react';
const Footer = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const businessUnits = [{
    name: "FinTech Solutions",
    contact: "fintech@aura.com",
    phone: "+1 (555) 123-4567"
  }, {
    name: "Healthcare AI",
    contact: "healthcare@aura.com",
    phone: "+1 (555) 234-5678"
  }, {
    name: "Retail Intelligence",
    contact: "retail@aura.com",
    phone: "+1 (555) 345-6789"
  }, {
    name: "Industrial IoT",
    contact: "industry@aura.com",
    phone: "+1 (555) 456-7890"
  }];
  const socialLinks = [{
    name: "LinkedIn",
    url: "#",
    icon: "linkedin"
  }, {
    name: "Twitter",
    url: "#",
    icon: "twitter"
  }, {
    name: "GitHub",
    url: "#",
    icon: "github"
  }, {
    name: "YouTube",
    url: "#",
    icon: "youtube"
  }];
  const openGoogleAppointment = () => {
    // Aquí iría la URL real de Google Appointments
    window.open('https://calendar.google.com/calendar/appointments/your-appointment-link', '_blank', 'width=800,height=600');
    setIsModalOpen(false);
  };
  return <footer className="bg-slate-900 text-slate-100 border-t border-slate-800">
      {/* CTA Section in Footer */}
      <div className="container mx-auto px-4 lg:px-8 py-16">
        <Card className="glass border-primary/20 max-w-4xl mx-auto bg-slate-800/50 border-slate-700">
          <CardContent className="p-8 text-center space-y-6">
            <div className="space-y-4">
              <h3 className="text-3xl font-bold text-slate-100">
                Agenda una Demo con nuestro <span className="bg-tech-gradient bg-clip-text text-transparent">CEO</span>
              </h3>
              <p className="text-lg text-slate-300 max-w-2xl mx-auto">
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
                <DialogContent className="sm:max-w-md bg-slate-800 border-slate-700">
                  <DialogHeader>
                    <DialogTitle className="text-slate-100">Agendar Demo Ejecutiva</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <p className="text-slate-300">
                      Serás redirigido a nuestro sistema de citas de Google Calendar para seleccionar el mejor horario.
                    </p>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-lg font-bold text-primary">60min</div>
                        <div className="text-xs text-slate-400">Demo completa</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-primary">CEO</div>
                        <div className="text-xs text-slate-400">Atención directa</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-primary">1:1</div>
                        <div className="text-xs text-slate-400">Personalizado</div>
                      </div>
                    </div>
                    <Button onClick={openGoogleAppointment} className="w-full bg-tech-gradient">
                      Continuar a Google Calendar
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>

              <Button size="lg" variant="outline" className="border-slate-600 hover:bg-slate-700 text-slate-100 hover:text-slate-100">
                <Mail className="mr-2 h-5 w-5" />
                Contacto Directo
              </Button>
            </div>

            <div className="grid md:grid-cols-3 gap-6 pt-6 border-t border-slate-700">
              <div className="text-center">
                <div className="text-xl font-bold text-primary">C-Level</div>
                <div className="text-sm text-slate-400">Atención ejecutiva</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-primary">Demo Live</div>
                <div className="text-sm text-slate-400">Productos reales</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-primary">ROI</div>
                <div className="text-sm text-slate-400">Análisis incluido</div>
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
              <div className="w-8 h-8 bg-tech-gradient rounded-lg flex items-center justify-center">
                <Brain className="text-white h-4 w-4" />
              </div>
              <span className="text-xl font-bold bg-tech-gradient bg-clip-text text-transparent">Grupo huntRED® </span>
            </div>
            <p className="text-slate-400 text-sm">Transformando empresas con Inteligencia Artificial de vanguardia. Soluciones ajustadas para tu empresa.</p>
            <div className="space-y-2">
              <div className="flex items-center space-x-2 text-sm text-slate-400">
                <Mail className="h-4 w-4" />
                <span>hola@huntred.com</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-slate-400">
                <Phone className="h-4 w-4" />
                <span>+52 (55) 5914-0089</span>
              </div>
            </div>
          </div>

          {/* Business Units */}
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-200">Unidades de Negocio</h4>
            <div className="space-y-3">
              {businessUnits.map((unit, index) => <div key={index} className="space-y-1">
                  <div className="text-sm font-medium text-slate-300">{unit.name}</div>
                  <div className="text-xs text-slate-500">{unit.contact}</div>
                  <div className="text-xs text-slate-500">{unit.phone}</div>
                </div>)}
            </div>
          </div>

          {/* Quick Links */}
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-200">Enlaces Rápidos</h4>
            <div className="space-y-2">
              {['Tecnologías', 'Casos de Éxito', 'Blog', 'Recursos', 'Documentación', 'Soporte'].map(link => <a key={link} href="#" className="block text-sm text-slate-400 hover:text-primary transition-colors">
                  {link}
                </a>)}
            </div>
          </div>

          {/* Social & Legal */}
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-200">Síguenos</h4>
            <div className="flex space-x-3">
              {socialLinks.map(social => <a key={social.name} href={social.url} className="w-10 h-10 bg-slate-800 hover:bg-primary/10 rounded-lg flex items-center justify-center text-slate-400 hover:text-primary transition-all hover:scale-110" aria-label={social.name}>
                  <span className="text-sm font-bold">{social.icon.slice(0, 2).toUpperCase()}</span>
                </a>)}
            </div>
            
            <div className="space-y-2 pt-4">
              <h5 className="text-sm font-medium text-slate-200">Legal</h5>
              {['Términos de Servicio', 'Política de Privacidad', 'Cookies'].map(link => <a key={link} href="#" className="block text-xs text-slate-400 hover:text-primary transition-colors">
                  {link}
                </a>)}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-slate-800">
        <div className="container mx-auto px-4 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="text-sm text-slate-400">
              © 2024 Grupo huntRED® - GenIA & AURA. Todos los derechos reservados.
            </div>
            <div className="flex items-center space-x-6 text-sm text-slate-400">
              <span>🇲🇽 México • 🇺🇸 Estados Unidos • 🇪🇸 España</span>
            </div>
          </div>
        </div>
      </div>
    </footer>;
};
export default Footer;