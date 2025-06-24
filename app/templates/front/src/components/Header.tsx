import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from './ThemeToggle';
import { Menu, Heart, Phone } from 'lucide-react';
const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navItems = [{
    label: 'Inicio',
    href: '#hero'
  }, {
    label: 'Nuestro Proceso',
    href: '#process'
  }, {
    label: 'Tecnología',
    href: '#technology'
  }, {
    label: 'Historias de Éxito',
    href: '#testimonials'
  }, {
    label: 'Industrias',
    href: '#business-units'
  }, {
    label: 'Servicios',
    href: '#services'
  }];
  return <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/40 backdrop-blur-xl">
      <div className="container mx-auto px-4 lg:px-8">
        <nav className="flex items-center justify-between h-16">
          {/* Logo with Heart */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-tech-gradient rounded-xl flex items-center justify-center shadow-lg">
              <Heart className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold bg-tech-gradient bg-clip-text text-transparent">Grupo huntRED®</span>
              <div className="text-xs text-muted-foreground">Ecosistema de Inteligencia Artifical en Recursos Humanos</div>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navItems.map(item => <a key={item.label} href={item.href} className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors relative group">
                {item.label}
                <div className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full" />
              </a>)}
          </div>

          {/* Desktop Actions */}
          <div className="hidden md:flex items-center space-x-4">
            <ThemeToggle />
            <Button size="sm" variant="outline" className="border-primary/30 hover:bg-primary/10">
              <Phone className="mr-2 h-4 w-4" />
              Llamar Ahora
            </Button>
            <Button size="sm" className="bg-tech-gradient hover:opacity-90 transition-all hover:scale-105 shadow-lg">
              Conversemos ☕
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center space-x-2">
            <ThemeToggle />
            <Button variant="ghost" size="sm" onClick={() => setIsMenuOpen(!isMenuOpen)} className="h-8 w-8 p-0">
              <Menu className="h-4 w-4" />
            </Button>
          </div>
        </nav>

        {/* Mobile Navigation */}
        {isMenuOpen && <div className="md:hidden py-4 border-t border-border/40 bg-background/95 backdrop-blur">
            <div className="flex flex-col space-y-3">
              {navItems.map(item => <a key={item.label} href={item.href} className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors py-2 px-2 rounded hover:bg-primary/5" onClick={() => setIsMenuOpen(false)}>
                  {item.label}
                </a>)}
              <div className="flex flex-col gap-3 pt-4 border-t">
                <Button size="sm" variant="outline" className="border-primary/30 hover:bg-primary/10 w-fit">
                  <Phone className="mr-2 h-4 w-4" />
                  Llamar Ahora
                </Button>
                <Button size="sm" className="bg-tech-gradient hover:opacity-90 transition-opacity w-fit">
                  Conversemos ☕
                </Button>
              </div>
            </div>
          </div>}
      </div>
    </header>;
};
export default Header;