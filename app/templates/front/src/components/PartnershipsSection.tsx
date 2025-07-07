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

const PartnershipsSection = () => {
  const partnerships = [
    {
      category: "Tecnología & APIs",
      partners: [
        { name: "BlackTrust", logo: "/assets/logos/blacktrust.png" },
        { name: "Incode", logo: "/assets/logos/incode.png" },
        { name: "Tabiya Technologies", logo: "/assets/logos/tabiya.png" },
        { name: "Aomni", logo: "/assets/logos/aomni.png" },
        { name: "Meta", logo: "/assets/logos/meta.png" }
      ]
    },
    {
      category: "Instituciones Educativas",
      partners: [
        { name: "UVM", logo: "/assets/logos/uvm.png" },
        { name: "UNITEC", logo: "/assets/logos/unitec.png" },
        { name: "Universidad Insurgentes", logo: "/assets/logos/uinsurgentes.png" },
        { name: "Aliat", logo: "/assets/logos/aliat.png" },
        { name: "Funed", logo: "/assets/logos/funed.png" }
      ]
    },
    {
      category: "Fundaciones",
      partners: [
        { name: "Fundación Televisa", logo: "/assets/logos/fundacion-televisa.png" },
        { name: "Fundación Bécalos", logo: "/assets/logos/fundacion-becalos.png" }
      ]
    }
  ];

  return (
    <section className="py-20 bg-background">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-16">
          <Badge variant="outline" className="mb-4">
            Alianzas Estratégicas
          </Badge>
          <h2 className="text-3xl md:text-4xl font-bold">
            Nuestras <span className="text-primary">Conexiones</span> & APIs
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Colaboramos con las mejores tecnologías y instituciones para ofrecer soluciones integrales de reclutamiento y desarrollo de talento
          </p>
        </div>

        <div className="space-y-16">
          {partnerships.map((category, categoryIndex) => (
            <div key={categoryIndex} className="space-y-8">
              <div className="text-center">
                <h3 className="text-2xl font-semibold mb-2">{category.category}</h3>
                <div className="w-24 h-1 bg-primary mx-auto rounded-full" />
              </div>

              <Carousel
                opts={{
                  align: "start",
                  loop: true,
                }}
                className="w-full max-w-6xl mx-auto"
              >
                <CarouselContent className="-ml-4">
                  {category.partners.map((partner, index) => (
                    <CarouselItem key={index} className="pl-4 basis-1/2 md:basis-1/3 lg:basis-1/4">
                       <Card className="glass border-primary/20 hover:shadow-xl transition-all duration-500 hover:-translate-y-2 group">
                         <CardContent className="flex flex-col items-center justify-center p-6 space-y-3 h-28">
                           <img 
                             src={partner.logo} 
                             alt={partner.name}
                             className="h-12 w-auto filter grayscale group-hover:grayscale-0 transition-all duration-300 transform group-hover:scale-110"
                           />
                           <h4 className="text-xs font-medium text-center opacity-60 group-hover:opacity-100 transition-opacity duration-300">
                             {partner.name}
                           </h4>
                         </CardContent>
                       </Card>
                    </CarouselItem>
                  ))}
                </CarouselContent>
                <CarouselPrevious className="hidden md:flex" />
                <CarouselNext className="hidden md:flex" />
              </Carousel>
            </div>
          ))}
        </div>

        <div className="text-center mt-16">
          <Card className="glass border-primary/20 max-w-2xl mx-auto">
            <CardContent className="p-8 space-y-4">
              <h3 className="text-xl font-semibold">Confiabilidad & Compromisos</h3>
              <p className="text-muted-foreground">
                Nuestras alianzas estratégicas nos permiten ofrecer las mejores soluciones tecnológicas y educativas, 
                garantizando la más alta calidad en nuestros servicios de reclutamiento y desarrollo de talento.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default PartnershipsSection;