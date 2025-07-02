import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { 
  Carousel, 
  CarouselContent, 
  CarouselItem, 
  CarouselNext, 
  CarouselPrevious 
} from '@/components/ui/carousel';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, Users, Award } from 'lucide-react';

const ClientsSection = () => {
  const clients = [
    { name: "Santander", logo: "/api/placeholder/120/60?text=Santander", sector: "Financiero" },
    { name: "Incode", logo: "/api/placeholder/120/60?text=Incode", sector: "Tecnología" },
    { name: "Termiz", logo: "/api/placeholder/120/60?text=Termiz", sector: "Energía" },
    { name: "Bray", logo: "/api/placeholder/120/60?text=Bray", sector: "Industrial" },
    { name: "Quaker State", logo: "/api/placeholder/120/60?text=QuakerState", sector: "Automotriz" },
    { name: "Interproteccion", logo: "/api/placeholder/120/60?text=Interproteccion", sector: "Seguros" },
    { name: "MetLife", logo: "/api/placeholder/120/60?text=MetLife", sector: "Seguros" },
    { name: "LUMO", logo: "/api/placeholder/120/60?text=LUMO", sector: "Tecnología" }
  ];

  const stats = [
    {
      icon: Users,
      value: "100+",
      label: "Clientes en nuestra historia",
      description: "Empresas que confían en nuestro talento"
    },
    {
      icon: TrendingUp,
      value: "85%",
      label: "Retención de clientes",
      description: "Satisfacción y resultados comprobados"
    },
    {
      icon: Award,
      value: "15+",
      label: "Años de experiencia",
      description: "Consolidando el futuro del talento"
    }
  ];

  return (
    <section className="py-20 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-16">
          <Badge variant="outline" className="mb-4">
            Nuestros Clientes
          </Badge>
          <h2 className="text-3xl md:text-4xl font-bold">
            Empresas que <span className="text-primary">Confían</span> en Nosotros
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Trabajamos con las mejores organizaciones para encontrar y desarrollar el talento que impulsa su crecimiento
          </p>
        </div>

        {/* Carrusel de logos de clientes */}
        <div className="mb-16">
          <Carousel
            opts={{
              align: "start",
              loop: true,
            }}
            className="w-full max-w-6xl mx-auto"
          >
            <CarouselContent className="-ml-4">
              {clients.map((client, index) => (
                <CarouselItem key={index} className="pl-4 basis-1/2 md:basis-1/3 lg:basis-1/4">
                     <Card className="glass border-primary/20 hover:shadow-xl transition-all duration-500 hover:-translate-y-2 group">
                       <CardContent className="flex flex-col items-center justify-center p-6 space-y-3 h-32">
                         <img 
                           src={client.logo} 
                           alt={client.name}
                           className="h-12 w-auto filter grayscale group-hover:grayscale-0 transition-all duration-300 transform group-hover:scale-110"
                         />
                         <div className="text-center space-y-1">
                           <h4 className="text-sm font-semibold opacity-60 group-hover:opacity-100 transition-opacity duration-300">
                             {client.name}
                           </h4>
                           <p className="text-xs text-muted-foreground opacity-0 group-hover:opacity-70 transition-opacity duration-300">
                             {client.sector}
                           </p>
                         </div>
                       </CardContent>
                     </Card>
                </CarouselItem>
              ))}
            </CarouselContent>
            <CarouselPrevious className="hidden md:flex" />
            <CarouselNext className="hidden md:flex" />
          </Carousel>
        </div>

        {/* Estadísticas */}
        <div className="grid md:grid-cols-3 gap-8">
          {stats.map((stat, index) => (
            <Card key={index} className="glass border-primary/20 hover:shadow-lg transition-shadow">
              <CardContent className="p-8 text-center space-y-4">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                  <stat.icon className="h-8 w-8 text-primary" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-3xl font-bold text-primary">{stat.value}</h3>
                  <h4 className="text-lg font-semibold">{stat.label}</h4>
                  <p className="text-sm text-muted-foreground">{stat.description}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Llamada a la acción */}
        <div className="text-center mt-16">
          <Card className="glass border-primary/20 max-w-3xl mx-auto">
            <CardContent className="p-8 space-y-4">
              <h3 className="text-2xl font-semibold">Únete a Nuestros Clientes Exitosos</h3>
              <p className="text-muted-foreground">
                Más de 100 empresas han transformado su proceso de reclutamiento con huntRED®. 
                Descubre por qué somos la opción preferida para encontrar y desarrollar talento excepcional.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default ClientsSection;