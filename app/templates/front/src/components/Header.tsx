
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from './ThemeToggle';
import { Menu } from 'lucide-react';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navItems = [
    { label: 'Inicio', href: '#hero' },
    { label: 'Unidades de Negocio', href: '#business-units' },
    { label: 'Módulos ML', href: '#ml-modules' },
    { label: 'NLP Multilingual', href: '#nlp' },
    { label: 'Dashboard', href: '#kanban-dashboard' },
    { label: 'Analytics', href: '#analytics' },
    { label: 'Simuladores', href: '#simulators' },
    { label: 'Roadmap', href: '#roadmap' },
    { label: 'ROI', href: '#roi' },
    { label: 'Servicios', href: '#services' },
    { label: 'Contacto', href: '#contact' },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/40">
      <div className="container mx-auto px-4 lg:px-8">
        <nav className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-tech-gradient rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xs">HR</span>
            </div>
            <span className="text-xl font-bold bg-tech-gradient bg-clip-text text-transparent">
              huntRED® AI
            </span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navItems.map((item) => (
              <a
                key={item.label}
                href={item.href}
                className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
              >
                {item.label}
              </a>
            ))}
          </div>

          {/* Desktop Actions */}
          <div className="hidden md:flex items-center space-x-4">
            <ThemeToggle />
            <Button 
              size="sm" 
              className="bg-tech-gradient hover:opacity-90 transition-opacity"
            >
              Agendar Demo
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center space-x-2">
            <ThemeToggle />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="h-8 w-8 p-0"
            >
              <Menu className="h-4 w-4" />
            </Button>
          </div>
        </nav>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t border-border/40">
            <div className="flex flex-col space-y-3">
              {navItems.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors py-2"
                  onClick={() => setIsMenuOpen(false)}
                >
                  {item.label}
                </a>
              ))}
              <Button 
                size="sm" 
                className="bg-tech-gradient hover:opacity-90 transition-opacity w-fit mt-4"
              >
                Agendar Demo
              </Button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
