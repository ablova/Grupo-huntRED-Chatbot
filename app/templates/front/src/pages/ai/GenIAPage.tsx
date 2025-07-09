import React from 'react';
import { Box, Container, Typography, Grid, Card, CardContent, List, ListItem, ListItemIcon, ListItemText, Button } from '@mui/material';
import { CheckCircle as CheckCircleIcon, Create as CreateIcon, Psychology as PsychologyIcon, AutoAwesome as AutoAwesomeIcon } from '@mui/icons-material';

/**
 * Página específica para GenIA (Inteligencia Artificial Generativa)
 * Detalla las capacidades y aplicaciones de GenIA en el ecosistema de talento
 */
const GenIAPage: React.FC = () => {
  return (
    <Box sx={{ py: 8 }}>
      <Container maxWidth="lg">
        <Box sx={{ mb: 6, textAlign: 'center' }}>
          <Typography variant="h2" component="h1" gutterBottom>
            GenIA
          </Typography>
          <Typography variant="h5" component="p" color="text.secondary" sx={{ maxWidth: 800, mx: 'auto' }}>
            Inteligencia Artificial Generativa especializada en Talento
          </Typography>
        </Box>

        <Grid container spacing={6}>
          <Grid item xs={12} md={6}>
            <Box sx={{ pr: { md: 4 } }}>
              <Typography variant="h4" component="h2" gutterBottom>
                Transformando la gestión del talento
              </Typography>
              <Typography variant="body1" paragraph>
                GenIA representa nuestra avanzada tecnología de Inteligencia Artificial Generativa diseñada específicamente para optimizar 
                procesos relacionados con talento humano. Utilizando modelos de lenguaje de última generación entrenados con datos 
                especializados del sector.
              </Typography>
              <Typography variant="body1" paragraph>
                A diferencia de soluciones genéricas, GenIA comprende el contexto organizacional, las dinámicas del mercado laboral 
                y los matices culturales que influyen en la contratación y desarrollo del talento.
              </Typography>
              <Typography variant="body1" paragraph>
                Todos los datos son procesados por nuestros sistemas internos de forma segura, sin dependencias de proveedores externos,
                garantizando la máxima confidencialidad y control sobre la información.
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent>
                <Typography variant="h5" component="h3" gutterBottom color="primary">
                  Capacidades principales
                </Typography>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <CreateIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Creación de perfiles" 
                      secondary="Genera descripciones de puesto detalladas y personalizadas basadas en requisitos específicos y cultura organizacional."
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <PsychologyIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Evaluación de candidatos" 
                      secondary="Analiza respuestas y comportamientos para identificar fortalezas, áreas de mejora y compatibilidad con el equipo."
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <AutoAwesomeIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Generación de contenido" 
                      secondary="Crea comunicaciones personalizadas, retroalimentaciones constructivas y planes de desarrollo individual."
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <CheckCircleIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Reconocimiento de patrones" 
                      secondary="Identifica tendencias y predice necesidades futuras de talento basándose en datos históricos y proyecciones."
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Box sx={{ my: 8 }}>
          <Typography variant="h4" component="h2" gutterBottom align="center">
            Aplicaciones prácticas
          </Typography>
          <Grid container spacing={4} sx={{ mt: 2 }}>
            <Grid item xs={12} sm={6} lg={3}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent>
                  <Typography variant="h6" component="h3" gutterBottom>
                    Reclutamiento
                  </Typography>
                  <Typography variant="body2">
                    Optimización de descripciones de puesto, análisis de CVs, preguntas personalizadas para entrevistas y evaluación de respuestas.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} lg={3}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent>
                  <Typography variant="h6" component="h3" gutterBottom>
                    Onboarding
                  </Typography>
                  <Typography variant="body2">
                    Generación de planes personalizados, materiales de capacitación adaptados y seguimiento del proceso de integración.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} lg={3}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent>
                  <Typography variant="h6" component="h3" gutterBottom>
                    Desarrollo
                  </Typography>
                  <Typography variant="body2">
                    Creación de planes de carrera, identificación de oportunidades de crecimiento y recomendaciones de aprendizaje.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} lg={3}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent>
                  <Typography variant="h6" component="h3" gutterBottom>
                    Retención
                  </Typography>
                  <Typography variant="body2">
                    Detección temprana de señales de rotación, análisis de satisfacción y generación de estrategias de reconocimiento.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>

        <Box sx={{ textAlign: 'center', mt: 6 }}>
          <Button variant="contained" size="large" href="/contact">
            Solicitar una demostración
          </Button>
        </Box>
      </Container>
    </Box>
  );
};

export default GenIAPage;
