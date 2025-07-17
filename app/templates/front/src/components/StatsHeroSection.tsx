import React, { useEffect, useRef } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, 
  Clock, 
  Users, 
  DollarSign, 
  Target, 
  Zap,
  Award,
  Globe
} from 'lucide-react';

interface StatItem {
  icon: React.ReactNode;
  value: string;
  label: string;
  description: string;
  color: string;
  delay: number;
}

const StatsHeroSection: React.FC = () => {
  const statsRef = useRef<HTMLDivElement>(null);

  const stats: StatItem[] = [
    {
      icon: <Clock className="w-8 h-8" />,
      value: "25%",
      label: "Reducción en tiempo de contratación",
      description: "Gracias a AURA AI y automatización inteligente",
      color: "bg-gradient-blue-red",
      delay: 0
    },
    {
      icon: <Users className="w-8 h-8" />,
      value: "30%",
      label: "Aumento en contrataciones internas",
      description: "Mejor retención y desarrollo de talento",
      color: "bg-gradient-blue-red",
      delay: 200
    },
    {
      icon: <DollarSign className="w-8 h-8" />,
      value: "50%",
      label: "Más eficiente en gastos de atracción",
      description: "Optimización de presupuestos de reclutamiento",
      color: "bg-gradient-blue-red",
      delay: 400
    },
    {
      icon: <Zap className="w-8 h-8" />,
      value: "11h",
      label: "Horas ahorradas por reclutador/semana",
      description: "Automatización de tareas repetitivas",
      color: "bg-gradient-blue-red",
      delay: 600
    },
    {
      icon: <Target className="w-8 h-8" />,
      value: "95%",
      label: "Precisión en matching de candidatos",
      description: "AURA AI con aprendizaje continuo",
      color: "bg-gradient-blue-red",
      delay: 800
    },
    {
      icon: <Award className="w-8 h-8" />,
      value: "700+",
      label: "Marcas que confían en huntRED®",
      description: "Empresas líderes en Latinoamérica",
      color: "bg-gradient-blue-red",
      delay: 1000
    },
    {
      icon: <TrendingUp className="w-8 h-8" />,
      value: "60%",
      label: "Mejora en calidad de contrataciones",
      description: "Candidatos mejor alineados con la empresa",
      color: "bg-gradient-blue-red",
      delay: 1200
    },
    {
      icon: <Globe className="w-8 h-8" />,
      value: "15",
      label: "Países con presencia huntRED®",
      description: "Cobertura en toda Latinoamérica",
      color: "bg-gradient-blue-red",
      delay: 1400
    }
  ];

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
          }
        });
      },
      { threshold: 0.1 }
    );

    if (statsRef.current) {
      const statCards = statsRef.current.querySelectorAll('.stat-card');
      statCards.forEach((card) => observer.observe(card));
    }

    return () => observer.disconnect();
  }, []);

  return (
    <section className="py-24 bg-gradient-to-br from-blue-900 to-red-500 dark:from-blue-900 dark:to-red-500">
      <div className="container mx-auto px-4">
        {/* Header Section */}
        <div className="text-center mb-16">
          <Badge variant="secondary" className="mb-4 bg-blue-100 text-blue-700 hover:bg-blue-200">
            <TrendingUp className="w-4 h-4 mr-2" />
            Métricas Comprobadas
          </Badge>
          <h2 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            El poder de la
            <span className="bg-gradient-to-r from-blue-600 via-blue-500 to-blue-400 bg-clip-text text-transparent">
              {' '}experiencia de talento
            </span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Más de 700 marcas confían en huntRED® para transformar la eficiencia 
            con automatización e inteligencia artificial. Estos son los resultados reales.
          </p>
        </div>

        {/* Stats Grid */}
        <div 
          ref={statsRef}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {stats.map((stat, index) => (
            <Card 
              key={index}
              className={`stat-card group hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 border-0 bg-white/80 backdrop-blur-sm`}
              style={{ animationDelay: `${stat.delay}ms` }}
            >
              <CardContent className="p-6 text-center">
                <div className={`w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br ${stat.color} flex items-center justify-center text-white group-hover:scale-110 transition-all duration-300`}>
                  {stat.icon}
                </div>
                
                <div className="text-3xl md:text-4xl font-bold text-gray-900 mb-2 group-hover:text-tech-blue transition-colors duration-300">
                  {stat.value}
                </div>
                
                <h3 className="text-lg font-semibold text-gray-800 mb-2 leading-tight">
                  {stat.label}
                </h3>
                
                <p className="text-sm text-gray-600 leading-relaxed">
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-16">
          <div className="bg-gradient-to-r from-blue-600 to-blue-400 rounded-2xl p-8 text-white max-w-4xl mx-auto">
            <h3 className="text-2xl md:text-3xl font-bold mb-4">
              ¿Listo para ver estos resultados en su empresa?
            </h3>
            <p className="text-blue-100 mb-6 text-lg">
              Únase a las 700+ empresas que ya transformaron su reclutamiento con huntRED®
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-white text-tech-blue px-8 py-3 rounded-xl font-semibold hover:bg-gray-100 transition-all duration-300 shadow-lg">
                <TrendingUp className="w-5 h-5 inline mr-2" />
                Ver Demo en Vivo
              </button>
              <button className="border-2 border-white text-white px-8 py-3 rounded-xl font-semibold hover:bg-white hover:text-tech-blue transition-all duration-300">
                <Users className="w-5 h-5 inline mr-2" />
                Solicitar Consulta
              </button>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .stat-card {
          opacity: 0;
          transform: translateY(30px);
          transition: all 0.6s ease;
        }
        
        .stat-card.animate-in {
          opacity: 1;
          transform: translateY(0);
        }
        
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-in {
          animation: fadeInUp 0.6s ease forwards;
        }
      `}</style>
    </section>
  );
};

export default StatsHeroSection; 