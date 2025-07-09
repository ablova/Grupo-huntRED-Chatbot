import React, { useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  Toolbar,
  IconButton,
  Typography,
  Menu,
  Container,
  Button,
  MenuItem,
  Drawer,
  List,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Collapse,
  useMediaQuery,
  useTheme
} from '@mui/material';
import {
  Menu as MenuIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Work as WorkIcon,
  Psychology as PsychologyIcon,
  Assessment as AssessmentIcon,
  AccountBalance as PayrollIcon,
  Home as HomeIcon
} from '@mui/icons-material';

// Definición de páginas principales y subpáginas
interface PageItem {
  title: string;
  path: string;
  icon?: React.ReactNode;
  subPages?: PageItem[];
  highlight?: boolean; // Para destacar servicios más rentables
}

const pages: PageItem[] = [
  { 
    title: 'Inicio', 
    path: '/',
    icon: <HomeIcon />
  },
  { 
    title: 'Reclutamiento', 
    path: '/recruitment',
    icon: <WorkIcon />,
    highlight: true, // Servicio más rentable
    subPages: [
      { title: 'huntRED® Executive', path: '/recruitment/executive', highlight: true },
      { title: 'huntRED®', path: '/recruitment/huntred', highlight: true },
      { title: 'huntU', path: '/recruitment/huntu' },
      { title: 'amigro', path: '/recruitment/amigro' },
    ]
  },
  { 
    title: 'Servicios AI', 
    path: '/ai-services',
    icon: <PsychologyIcon />,
    subPages: [
      { 
        title: 'GenIA', 
        path: '/ai-services/genia',
        description: 'Inteligencia Artificial Generativa especializada en Talento, capaz de crear perfiles, evaluar candidatos y generar contenido relacionado con procesos de selección y desarrollo.' 
      },
      { 
        title: 'AURA', 
        path: '/ai-services/aura',
        description: 'Automatización de Reconocimiento, Análisis y toma de decisiones Avanzadas para procesos de gestión de talento. Sistema central que coordina todos los módulos de AI.' 
      },
      { 
        title: 'Talent Matching', 
        path: '/ai-services/talent-matching',
        description: 'Algoritmo avanzado que compara perfiles de candidatos con requisitos de posiciones para encontrar el ajuste perfecto basado en habilidades técnicas y blandas.' 
      },
      { 
        title: 'Skill Mapping', 
        path: '/ai-services/skill-mapping',
        description: 'Análisis y visualización de competencias técnicas y blandas para identificar brechas y oportunidades de desarrollo en equipos e individuos.' 
      },
      { 
        title: 'Career Path', 
        path: '/ai-services/career-path',
        description: 'Planificación y simulación de trayectorias profesionales basadas en habilidades actuales, potencial y objetivos organizacionales.' 
      }
    ]
  },
  { 
    title: 'Assessments', 
    path: '/assessments',
    icon: <AssessmentIcon />,
    subPages: [
      { title: 'Talent Assessment', path: '/assessments/talent' },
      { title: 'Evaluación Psicométrica', path: '/assessments/psychometric' },
      { title: 'Evaluación Técnica', path: '/assessments/technical' },
      { title: 'Perfil de Liderazgo', path: '/assessments/leadership' },
      { title: 'NOM-35', path: '/assessments/nom35' },
      { title: 'Evaluación de Ventas', path: '/assessments/sales' },
    ]
  },
  { 
    title: 'Nómina AI', 
    path: '/payroll',
    icon: <PayrollIcon />
  },
];

// Componente de navegación principal
const AppNavBar: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const location = useLocation();
  
  // Estados para el menú móvil
  const [anchorElNav, setAnchorElNav] = useState<null | HTMLElement>(null);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  
  // Estados para submenús desplegables
  const [openSubMenus, setOpenSubMenus] = useState<Record<string, boolean>>({});

  // Manejo de menú móvil
  const handleOpenNavMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElNav(event.currentTarget);
  };

  const handleCloseNavMenu = () => {
    setAnchorElNav(null);
  };
  
  // Manejo de drawer móvil
  const toggleMobileDrawer = () => {
    setMobileDrawerOpen(!mobileDrawerOpen);
  };
  
  // Manejo de submenús
  const handleToggleSubMenu = (title: string) => {
    setOpenSubMenus(prev => ({
      ...prev,
      [title]: !prev[title]
    }));
  };
  
  // Verifica si una ruta está activa (para destacarla en el menú)
  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <AppBar position="static" color="default" elevation={1}>
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          {/* Logo para pantallas grandes */}
          <Typography
            variant="h6"
            noWrap
            component={RouterLink}
            to="/"
            sx={{
              mr: 2,
              display: { xs: 'none', md: 'flex' },
              fontWeight: 700,
              color: 'inherit',
              textDecoration: 'none',
            }}
          >
            Grupo huntRED®
          </Typography>

          {/* Menú móvil */}
          <Box sx={{ flexGrow: 1, display: { xs: 'flex', md: 'none' } }}>
            <IconButton
              size="large"
              aria-label="menu"
              aria-controls="menu-appbar"
              aria-haspopup="true"
              onClick={toggleMobileDrawer}
              color="inherit"
            >
              <MenuIcon />
            </IconButton>
            
            <Drawer
              anchor="left"
              open={mobileDrawerOpen}
              onClose={toggleMobileDrawer}
            >
              <Box
                sx={{ width: 280 }}
                role="presentation"
              >
                <List>
                  {pages.map((page) => (
                    <React.Fragment key={page.title}>
                      {page.subPages ? (
                        <>
                          <ListItemButton 
                            onClick={() => handleToggleSubMenu(page.title)}
                            sx={{
                              bgcolor: isActive(page.path) ? 'rgba(0, 0, 0, 0.08)' : 'transparent',
                              color: page.highlight ? theme.palette.primary.main : 'inherit',
                              fontWeight: page.highlight ? 700 : 400,
                            }}
                          >
                            {page.icon && <ListItemIcon sx={{ 
                              color: page.highlight ? theme.palette.primary.main : 'inherit' 
                            }}>
                              {page.icon}
                            </ListItemIcon>}
                            <ListItemText primary={page.title} />
                            {openSubMenus[page.title] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          </ListItemButton>
                          <Collapse in={openSubMenus[page.title]} timeout="auto" unmountOnExit>
                            <List component="div" disablePadding>
                              {page.subPages.map((subPage) => (
                                <ListItemButton
                                  key={subPage.title}
                                  component={RouterLink}
                                  to={subPage.path}
                                  onClick={toggleMobileDrawer}
                                  sx={{ 
                                    pl: 4,
                                    bgcolor: isActive(subPage.path) ? 'rgba(0, 0, 0, 0.08)' : 'transparent',
                                    color: subPage.highlight ? theme.palette.primary.main : 'inherit',
                                    fontWeight: subPage.highlight ? 700 : 400,
                                  }}
                                >
                                  <ListItemText primary={subPage.title} />
                                </ListItemButton>
                              ))}
                            </List>
                          </Collapse>
                        </>
                      ) : (
                        <ListItemButton
                          component={RouterLink}
                          to={page.path}
                          onClick={toggleMobileDrawer}
                          sx={{ 
                            bgcolor: isActive(page.path) ? 'rgba(0, 0, 0, 0.08)' : 'transparent',
                            color: page.highlight ? theme.palette.primary.main : 'inherit',
                            fontWeight: page.highlight ? 700 : 400,
                          }}
                        >
                          {page.icon && <ListItemIcon sx={{ 
                            color: page.highlight ? theme.palette.primary.main : 'inherit' 
                          }}>
                            {page.icon}
                          </ListItemIcon>}
                          <ListItemText primary={page.title} />
                        </ListItemButton>
                      )}
                    </React.Fragment>
                  ))}
                </List>
              </Box>
            </Drawer>
          </Box>
          
          {/* Logo para móviles */}
          <Typography
            variant="h6"
            noWrap
            component={RouterLink}
            to="/"
            sx={{
              mr: 2,
              display: { xs: 'flex', md: 'none' },
              flexGrow: 1,
              fontWeight: 700,
              color: 'inherit',
              textDecoration: 'none',
            }}
          >
            Grupo huntRED®
          </Typography>
          
          {/* Menú de escritorio */}
          <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' } }}>
            {pages.map((page) => (
              <Box key={page.title} sx={{ position: 'relative' }}>
                <Button
                  component={RouterLink}
                  to={page.path}
                  sx={{
                    my: 2, 
                    color: isActive(page.path) || page.highlight ? theme.palette.primary.main : 'inherit',
                    fontWeight: page.highlight ? 700 : 400,
                    display: 'flex',
                    '&:hover': {
                      color: theme.palette.primary.main,
                      bgcolor: 'transparent'
                    }
                  }}
                  endIcon={page.subPages && <ExpandMoreIcon />}
                  onMouseEnter={page.subPages ? () => handleToggleSubMenu(page.title) : undefined}
                  onClick={page.subPages ? () => handleToggleSubMenu(page.title) : undefined}
                >
                  {page.title}
                </Button>
                
                {/* Submenú desplegable para escritorio */}
                {page.subPages && (
                  <Menu
                    id={`menu-${page.title}`}
                    anchorEl={document.getElementById(`btn-${page.title}`)}
                    open={Boolean(openSubMenus[page.title])}
                    onClose={() => handleToggleSubMenu(page.title)}
                    MenuListProps={{
                      onMouseLeave: () => handleToggleSubMenu(page.title),
                      'aria-labelledby': `btn-${page.title}`,
                    }}
                    PaperProps={{
                      elevation: 3,
                    }}
                  >
                    {page.subPages.map((subPage) => (
                      <MenuItem
                        key={subPage.title}
                        component={RouterLink}
                        to={subPage.path}
                        onClick={() => handleToggleSubMenu(page.title)}
                        sx={{ 
                          color: subPage.highlight ? theme.palette.primary.main : 'inherit',
                          fontWeight: subPage.highlight ? 700 : 400,
                          minWidth: 200
                        }}
                      >
                        {subPage.title}
                      </MenuItem>
                    ))}
                  </Menu>
                )}
              </Box>
            ))}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default AppNavBar;
