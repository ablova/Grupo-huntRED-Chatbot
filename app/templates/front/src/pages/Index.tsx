
import React from 'react';
import { ThemeProvider } from '@/components/ThemeProvider';
import Header from '@/components/Header';
import HeroSection from '@/components/HeroSection';
import TechnologySection from '@/components/TechnologySection';
import LLMCapabilitiesSection from '@/components/LLMCapabilitiesSection';
import MLPipelineSection from '@/components/MLPipelineSection';
import MatchmakingSection from '@/components/MatchmakingSection';
import LearningSection from '@/components/LearningSection';
import MarketAnalysisSection from '@/components/MarketAnalysisSection';
import MLFlowsSection from '@/components/MLFlowsSection';
import BusinessUnitsSection from '@/components/BusinessUnitsSection';
import QuantumLabSection from '@/components/QuantumLabSection';
import MetaverseSection from '@/components/MetaverseSection';
import ServicesSection from '@/components/ServicesSection';
import KanbanDashboardSection from '@/components/KanbanDashboardSection';
import AnalyticsDashboardSection from '@/components/AnalyticsDashboardSection';
import SimulatorSection from '@/components/SimulatorSection';
import ServiceRoadmapSection from '@/components/ServiceRoadmapSection';
import ROICalculatorSection from '@/components/ROICalculatorSection';
import Footer from '@/components/Footer';

const Index = () => {
  return (
    <ThemeProvider defaultTheme="system" storageKey="huntred-ai-theme">
      <div className="min-h-screen bg-background text-foreground">
        <Header />
        <main>
          <HeroSection />
          <TechnologySection />
          <LLMCapabilitiesSection />
          <MLPipelineSection />
          <MatchmakingSection />
          <LearningSection />
          <MarketAnalysisSection />
          <MLFlowsSection />
          <BusinessUnitsSection />
          <QuantumLabSection />
          <MetaverseSection />
          <ServicesSection />
          <KanbanDashboardSection />
          <AnalyticsDashboardSection />
          <SimulatorSection />
          <ServiceRoadmapSection />
          <ROICalculatorSection />
        </main>
        <Footer />
      </div>
    </ThemeProvider>
  );
};

export default Index;
