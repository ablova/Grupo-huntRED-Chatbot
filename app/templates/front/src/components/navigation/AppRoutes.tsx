import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Layouts
import MainLayout from '../layouts/MainLayout';

// Páginas Principales
import HomePage from '../pages/HomePage';
import RecruitmentPage from '../pages/recruitment/RecruitmentPage';
import AIServicesPage from '../pages/ai/AIServicesPage';
import PayrollPage from '../pages/payroll/PayrollPage';
import AssessmentsPage from '../pages/assessments/AssessmentsPage';

// Sub-páginas de Reclutamiento (servicios más rentables)
import ExecutivePage from '../pages/recruitment/ExecutivePage';
import HuntredPage from '../pages/recruitment/HuntredPage';
import HuntUPage from '../pages/recruitment/HuntUPage';
import AmigroPage from '../pages/recruitment/AmigroPage';

/**
 * Componente principal de rutas de la aplicación
 * Estructura multi-página organizada según líneas de negocio
 */
const AppRoutes: React.FC = () => {
  return (
    <Router>
      <Routes>
        {/* Home */}
        <Route path="/" element={<MainLayout><HomePage /></MainLayout>} />
        
        {/* Reclutamiento (Servicio más rentable) */}
        <Route path="/recruitment" element={<MainLayout><RecruitmentPage /></MainLayout>} />
        <Route path="/recruitment/executive" element={<MainLayout><ExecutivePage /></MainLayout>} />
        <Route path="/recruitment/huntred" element={<MainLayout><HuntredPage /></MainLayout>} />
        <Route path="/recruitment/huntu" element={<MainLayout><HuntUPage /></MainLayout>} />
        <Route path="/recruitment/amigro" element={<MainLayout><AmigroPage /></MainLayout>} />
        
        {/* Servicios de IA - Ecosistema Completo */}
        <Route path="/ai-services" element={<MainLayout><AIServicesPage /></MainLayout>} />
        <Route path="/ai-services/genia" element={<MainLayout><GenIAPage /></MainLayout>} />
        <Route path="/ai-services/aura" element={<MainLayout><AURAPage /></MainLayout>} />
        <Route path="/ai-services/talent-matching" element={<MainLayout><TalentMatchingPage /></MainLayout>} />
        <Route path="/ai-services/skill-mapping" element={<MainLayout><SkillMappingPage /></MainLayout>} />
        <Route path="/ai-services/career-path" element={<MainLayout><CareerPathPage /></MainLayout>} />
        
        {/* Administración de Nómina con IA */}
        <Route path="/payroll" element={<MainLayout><PayrollPage /></MainLayout>} />
        
        {/* Assessments */}
        <Route path="/assessments" element={<MainLayout><AssessmentsPage /></MainLayout>} />
        
        {/* Redirección de rutas no encontradas */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

export default AppRoutes;
