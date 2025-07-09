import React from 'react';
import { Box, Container, Typography, Grid, Card, CardContent, Divider, Paper, List, ListItem, ListItemIcon, ListItemText, Button } from '@mui/material';
import { AutoAwesome, Speed, Psychology, Security, Analytics } from '@mui/icons-material';

/**
 * Página específica para AURA (Automatización de Reconocimiento, Análisis y toma de decisiones Avanzadas)
 * Detalla el sistema central de AI que coordina todos los módulos del ecosistema
 */
const AURAPage: React.FC = () => {
  return (
    <Box sx={{ py: 8 }}>
      <Container maxWidth="lg">
        <Box sx={{ mb: 6, textAlign: 'center' }}>
          <Typography variant="h2" component="h1" gutterBottom>
            AURA
          </Typography>
          <Typography variant="h5" component="p" color="text.secondary" sx={{ maxWidth: 800, mx: 'auto' }}>
            Automatización de Reconocimiento, Análisis y toma de decisiones Avanzadas
          </Typography>
        </Box>

        <Paper elevation={3} sx={{ p: 4, mb: 6, borderRadius: 2 }}>
          <Typography variant="h4" component="h2" gutterBottom align="center" sx={{ mb: 3 }}>
            El cerebro del ecosistema de AI
          </Typography>
          <Typography variant="body1" paragraph align="center">
            AURA es el sistema central de inteligencia artificial que coordina y potencia todos los módulos 
            de gestión de talento. Actúa como una capa de integración inteligente que procesa, analiza y 
            distribuye información entre los diferentes componentes del ecosistema.
          </Typography>
        </Paper>

        <Grid container spacing={4}>
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%', p: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <AutoAwesome color="primary" fontSize="large" sx={{ mr: 2 }} />
                  <Typography variant="h5" component="h3">
                    Características principales
                  </Typography>
                </Box>
                <Divider sx={{ my: 2 }} />
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <Speed color="primary" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Procesamiento en tiempo real" 
                      secondary="Análisis instantáneo de datos para toma de decisiones ágiles en procesos críticos de talento."
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Psychology color="primary" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Aprendizaje continuo" 
                      secondary="El sistema mejora constantemente basándose en resultados, retroalimentación y nuevos datos."
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Security color="primary" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Seguridad integrada" 
                      secondary="Procesamiento interno sin dependencias externas, garantizando confidencialidad y cumplimiento normativo."
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Analytics color="primary" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Analítica avanzada" 
                      secondary="Generación de insights y recomendaciones basadas en patrones complejos de datos."
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%', p: 3 }}>
              <CardContent>
                <Typography variant="h5" component="h3" gutterBottom>
                  Integración con módulos
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Reclutamiento y Selección
                  </Typography>
                  <Typography variant="body2" paragraph>
                    AURA coordina el análisis de candidatos, filtrado de CVs, programación de entrevistas
                    y evaluación de ajuste cultural, alimentando al sistema de Talent Matching para optimizar
                    las coincidencias.
                  </Typography>
                </Box>
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Desarrollo de Talento
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Integración con Skill Mapping para identificar brechas de competencias y con
                    Career Path para proyectar trayectorias profesionales personalizadas.
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Administración y Nómina
                  </Typography>
                  <Typography variant="body2">
                    Procesamiento inteligente de datos para optimización de costos de talento, 
                    predicción de rotación y gestión eficiente de beneficios.
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Box sx={{ mt: 8 }}>
          <Typography variant="h4" component="h2" gutterBottom align="center">
            Arquitectura del sistema
          </Typography>
          <Typography variant="body1" paragraph align="center" sx={{ mb: 4, maxWidth: 800, mx: 'auto' }}>
            AURA está diseñada como una plataforma modular, escalable y segura, con componentes que 
            se comunican de forma eficiente para proporcionar una experiencia integral.
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} sm={4}>
              <Card sx={{ height: '100%', bgcolor: 'primary.main', color: 'white' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Capa de procesamiento
                  </Typography>
                  <Typography variant="body2">
                    Núcleo de algoritmos de machine learning y procesamiento de lenguaje natural que analiza datos estructurados y no estructurados.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card sx={{ height: '100%', bgcolor: 'secondary.main', color: 'white' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Capa de integración
                  </Typography>
                  <Typography variant="body2">
                    APIs y conectores que permiten el flujo de información entre AURA y los distintos módulos y sistemas organizacionales.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card sx={{ height: '100%', bgcolor: 'info.main', color: 'white' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Capa de presentación
                  </Typography>
                  <Typography variant="body2">
                    Interfaces y visualizaciones que transforman los datos procesados en información accionable para usuarios finales.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>

        <Box sx={{ mt: 8, textAlign: 'center' }}>
          <Button variant="contained" size="large" sx={{ mr: 2 }}>
            Solicitar Demo
          </Button>
          <Button variant="outlined" size="large">
            Documentación Técnica
          </Button>
        </Box>
      </Container>
    </Box>
  );
};

export default AURAPage;
