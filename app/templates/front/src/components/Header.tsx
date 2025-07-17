
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from './ThemeToggle';
import { Menu, Heart, Phone, Settings, BrainCircuit, FlaskConical, Calculator } from 'lucide-react';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 10) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    {
      label: 'Inicio',
      href: '#hero',
      isAnchor: true
    },
    {
      label: 'Plataforma',
      href: '/plataforma',
      icon: <BrainCircuit className="w-4 h-4 mr-1" />,
      isAnchor: false
    },
    {
      label: 'Laboratorio',
      href: '/laboratorio',
      icon: <FlaskConical className="w-4 h-4 mr-1" />,
      isAnchor: false
    },
    {
      label: 'Calculadora',
      href: '/calculadora',
      icon: <Calculator className="w-4 h-4 mr-1" />,
      isAnchor: false
    },
    {
      label: 'Servicios',
      href: '#services',
      isAnchor: true
    },
    {
      label: 'Nosotros',
      href: '#business-units',
      isAnchor: true
    },
    {
      label: 'Tecnología',
      href: '#technology',
      isAnchor: true
    }
  ];

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 border-b transition-all duration-300 ${scrolled ? 'bg-background shadow-md' : 'glass border-border/40 backdrop-blur-xl'}`}>
      <div className="container mx-auto px-4 lg:px-8">
        <nav className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <Link to="/" onClick={closeMenu}>
              <img 
                src="/static/images/g_huntred.png" 
                alt="Grupo huntRED® AI" 
                className="h-12 w-auto object-contain"
              />
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            {navItems.map(item => (
              item.isAnchor ? (
                <a 
                  key={item.label} 
                  href={item.href} 
                  className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors relative group flex items-center"
                >
                  {item.icon}
                  {item.label}
                  <div className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full" />
                </a>
              ) : (
                <Link
                  key={item.label}
                  to={item.href}
                  className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors relative group flex items-center"
                >
                  {item.icon}
                  {item.label}
                  <div className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full" />
                </Link>
              )
            ))}
          </div>

          {/* Desktop Actions */}
          <div className="hidden md:flex items-center space-x-3">
            <a 
              href="https://ai.huntred.com/admin" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-2 text-muted-foreground hover:text-primary transition-colors rounded-full hover:bg-accent"
              title="Panel de administración"
            >
              <Settings className="h-4 w-4" />
            </a>
            <ThemeToggle />
            <Button size="sm" variant="outline" className="border-primary/30 hover:bg-primary/10">
              <Phone className="mr-2 h-4 w-4" />
              Llamar Ahora
            </Button>
            <Button size="sm" className="modern-gradient-bg hover:opacity-90 transition-all hover:scale-105 shadow-lg text-white">
              Conversemos ☕
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center space-x-2">
            <a 
              href="https://ai.huntred.com/admin" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-2 text-muted-foreground hover:text-primary transition-colors rounded-full hover:bg-accent"
              title="Panel de administración"
              onClick={closeMenu}
            >
              <Settings className="h-5 w-5" />
            </a>
            <ThemeToggle />
            <Button 
              variant="ghost" 
              size="icon" 
              className="md:hidden"
              onClick={toggleMenu}
              aria-label={isMenuOpen ? 'Cerrar menú' : 'Abrir menú'}
            >
              <Menu className="h-6 w-6" />
            </Button>
          </div>
        </nav>

        {/* Mobile Menu */}
        <div 
          className={`md:hidden bg-background border-t border-border py-4 px-4 fixed left-0 right-0 top-16 shadow-lg transition-all duration-300 transform ${
            isMenuOpen ? 'translate-y-0' : '-translate-y-full opacity-0 pointer-events-none'
          }`}
        >
          <div className="flex flex-col space-y-3">
            {navItems.map(item => (
              item.isAnchor ? (
                <a 
                  key={item.label} 
                  href={item.href}
                  className="flex items-center py-3 px-4 rounded-lg hover:bg-accent hover:text-accent-foreground transition-colors"
                  onClick={closeMenu}
                >
                  <span className="mr-3">{item.icon}</span>
                  {item.label}
                </a>
              ) : (
                <Link
                  key={item.label}
                  to={item.href}
                  className="flex items-center py-3 px-4 rounded-lg hover:bg-accent hover:text-accent-foreground transition-colors"
                  onClick={closeMenu}
                >
                  <span className="mr-3">{item.icon}</span>
                  {item.label}
                </Link>
              )
            ))}
            <div className="pt-3 border-t border-border mt-2 space-y-2">
              <Button className="w-full" variant="outline">
                <Phone className="mr-2 h-4 w-4" />
                Llamar Ahora
              </Button>
              <Button className="w-full modern-gradient-bg hover:opacity-90 transition-all">
                Conversemos ☕
              </Button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
