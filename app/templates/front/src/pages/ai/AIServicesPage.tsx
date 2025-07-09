import React from 'react';
import { Box, Container, Typography, Grid, Card, CardContent, CardMedia, CardActionArea, Button } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

// Interfaz para los servicios AI
interface AIService {
  id: string;
  title: string;
  description: string;
  imagePath: string;
  route: string;
}

// Lista de servicios AI con sus descripciones
const AI_SERVICES: AIService[] = [
  {
    id: 'genia',
    title: 'GenIA',
    description: 'Inteligencia Artificial Generativa especializada en Talento, capaz de crear perfiles, evaluar candidatos y generar contenido relacionado con procesos de selección y desarrollo.',
    imagePath: '/assets/images/ai/genia.jpg',
    route: '/ai-services/genia'
  },
  {
    id: 'aura',
    title: 'AURA',
    description: 'Automatización de Reconocimiento, Análisis y toma de decisiones Avanzadas para procesos de gestión de talento. Sistema central que coordina todos los módulos de AI.',
    imagePath: '/assets/images/ai/aura.jpg',
    route: '/ai-services/aura'
  },
  {
    id: 'talent-matching',
    title: 'Talent Matching',
    description: 'Algoritmo avanzado que compara perfiles de candidatos con requisitos de posiciones para encontrar el ajuste perfecto basado en habilidades técnicas y blandas.',
    imagePath: '/assets/images/ai/talent-matching.jpg',
    route: '/ai-services/talent-matching'
  },
  {
    id: 'skill-mapping',
    title: 'Skill Mapping',
    description: 'Análisis y visualización de competencias técnicas y blandas para identificar brechas y oportunidades de desarrollo en equipos e individuos.',
    imagePath: '/assets/images/ai/skill-mapping.jpg',
    route: '/ai-services/skill-mapping'
  },
  {
    id: 'career-path',
    title: 'Career Path',
    description: 'Planificación y simulación de trayectorias profesionales basadas en habilidades actuales, potencial y objetivos organizacionales.',
    imagePath: '/assets/images/ai/career-path.jpg',
    route: '/ai-services/career-path'
  }
];

/**
 * Página principal de Servicios AI que muestra el ecosistema completo
 * de soluciones de Inteligencia Artificial para gestión de talento
 */
const AIServicesPage: React.FC = () => {
  return (
    <Box sx={{ py: 8 }}>
      <Container maxWidth="lg">
        <Typography variant="h2" component="h1" gutterBottom align="center" sx={{ mb: 4 }}>
          Ecosistema de Inteligencia Artificial
        </Typography>
        
        <Typography variant="h5" component="p" align="center" color="text.secondary" sx={{ mb: 6, maxWidth: 800, mx: 'auto' }}>
          Soluciones avanzadas de AI que transforman cada etapa del ciclo de vida del talento,
          desde reclutamiento hasta desarrollo profesional y retención.
        </Typography>
        
        <Grid container spacing={4}>
          {AI_SERVICES.map((service) => (
            <Grid item xs={12} sm={6} md={4} key={service.id}>
              <Card sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-8px)',
                  boxShadow: 6
                }
              }}>
                <CardActionArea component={RouterLink} to={service.route} sx={{ flexGrow: 1 }}>
                  <CardMedia
                    component="img"
                    height="180"
                    image={service.imagePath}
                    alt={service.title}
                    onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
                      // Placeholder para imágenes que no cargan
                      e.currentTarget.src = '/assets/images/placeholder-ai.jpg';
                    }}
                  />
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography gutterBottom variant="h5" component="h2">
                      {service.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {service.description}
                    </Typography>
                  </CardContent>
                </CardActionArea>
                <Box sx={{ p: 2, pt: 0 }}>
                  <Button 
                    component={RouterLink} 
                    to={service.route}
                    variant="outlined" 
                    fullWidth
                  >
                    Explorar
                  </Button>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
        
        <Box sx={{ mt: 8, textAlign: 'center' }}>
          <Typography variant="h4" component="h3" gutterBottom>
            Potencia tu estrategia de talento con AI
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 800, mx: 'auto', mb: 4 }}>
            Nuestras soluciones utilizan exclusivamente sistemas internos para el procesamiento de datos,
            garantizando la máxima seguridad y confidencialidad en todo momento.
          </Typography>
          <Button 
            variant="contained" 
            size="large" 
            component={RouterLink} 
            to="/contact"
            sx={{ mt: 2 }}
          >
            Solicitar Demo
          </Button>
        </Box>
      </Container>
    </Box>
  );
};

export default AIServicesPage;
