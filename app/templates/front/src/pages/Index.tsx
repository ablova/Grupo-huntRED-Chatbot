import React from 'react';
import { ThemeProvider } from '@/components/ThemeProvider';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

// Hero & Stats Sections
import HeroSection from '@/components/HeroSection';
import StatsHeroSection from '@/components/StatsHeroSection';

// Value Proposition & Competitive
import ValuePropositionSection from '@/components/ValuePropositionSection';
import CompetitiveComparisonSection from '@/components/CompetitiveComparisonSection';
import CompetitiveAdvantagesSection from '@/components/CompetitiveAdvantagesSection';

// Core Technology & AI
import AURAArchitectureSection from '@/components/AURAArchitectureSection';
import GenIAAndAURASection from '@/components/GenIAAndAURASection';
import AIFlowsSection from '@/components/AIFlowsSection';
import MLFlowsSection from '@/components/MLFlowsSection';
import MLPipelineSection from '@/components/MLPipelineSection';
import LLMCapabilitiesSection from '@/components/LLMCapabilitiesSection';

// Modules & Features
import HuntREDModulesSection from '@/components/HuntREDModulesSection';
import TechnologySection from '@/components/TechnologySection';
import MLCapabilitiesSection from '@/components/MLCapabilitiesSection';

// Business Solutions
import BusinessUnitsSection from '@/components/BusinessUnitsSection';
import ServicesSection from '@/components/ServicesSection';
import ProcessSection from '@/components/ProcessSection';

// Integration & Pricing
import HRSystemIntegrationSection from '@/components/HRSystemIntegrationSection';
import PricingAdvantagesSection from '@/components/PricingAdvantagesSection';
import ROIDemonstrationSection from '@/components/ROIDemonstrationSection';
import ROICalculatorSection from '@/components/ROICalculatorSection';
import SolutionCalculator from '@/components/SolutionCalculator';

// Dashboards & Tools
import RecruitmentDashboard from '@/components/RecruitmentDashboard';
import KanbanDashboardSection from '@/components/KanbanDashboardSection';
import AnalyticsDashboardSection from '@/components/AnalyticsDashboardSection';

// Ecosystem & Learning
import EcosystemFlow from '@/components/EcosystemFlow';
import LearningSection from '@/components/LearningSection';

// Social Proof & Testimonials
import CustomerSuccessStories from '@/components/CustomerSuccessStories';
import TestimonialsSection from '@/components/TestimonialsSection';

// Advanced Features
import SimulatorSection from '@/components/SimulatorSection';
import ServiceRoadmapSection from '@/components/ServiceRoadmapSection';
import MarketAnalysisSection from '@/components/MarketAnalysisSection';
import MatchmakingSection from '@/components/MatchmakingSection';
import MetaverseSection from '@/components/MetaverseSection';
import QuantumLabSection from '@/components/QuantumLabSection';
import PartnershipsSection from '@/components/PartnershipsSection';
import PaymentSystemSection from '@/components/PaymentSystemSection';
import ClientsSection from '@/components/ClientsSection';

const Index = () => {
  return (
    <ThemeProvider defaultTheme="system" storageKey="techai-theme">
      <div className="min-h-screen bg-background text-foreground">
        <Header />
        
        <main>
          {/* ===== HERO & IMPACT SECTIONS ===== */}
          <HeroSection />
          <StatsHeroSection />
          
          {/* ===== VALUE PROPOSITION & COMPETITIVE ===== */}
          <ValuePropositionSection />
          <CompetitiveComparisonSection />
          <CompetitiveAdvantagesSection />
          
          {/* ===== CORE TECHNOLOGY & AI ===== */}
          <AURAArchitectureSection />
          <GenIAAndAURASection />
          <AIFlowsSection />
          <MLFlowsSection />
          <MLPipelineSection />
          <LLMCapabilitiesSection />
          
          {/* ===== MODULES & FEATURES ===== */}
          <HuntREDModulesSection />
          <TechnologySection />
          <MLCapabilitiesSection />
          
          {/* ===== BUSINESS SOLUTIONS ===== */}
          <BusinessUnitsSection />
          <ServicesSection />
          <ProcessSection />
          
          {/* ===== INTEGRATION & PRICING ===== */}
          <HRSystemIntegrationSection />
          <PricingAdvantagesSection />
          <ROIDemonstrationSection />
          <ROICalculatorSection />
          <SolutionCalculator />
          
          {/* ===== DASHBOARDS & TOOLS ===== */}
          <RecruitmentDashboard />
          <KanbanDashboardSection />
          <AnalyticsDashboardSection />
          
          {/* ===== ECOSYSTEM & LEARNING ===== */}
          <EcosystemFlow />
          <LearningSection />
          
          {/* ===== SOCIAL PROOF & TESTIMONIALS ===== */}
          <CustomerSuccessStories />
          <TestimonialsSection />
          
          {/* ===== ADVANCED FEATURES ===== */}
          <SimulatorSection />
          <ServiceRoadmapSection />
          <MarketAnalysisSection />
          <MatchmakingSection />
          <MetaverseSection />
          <QuantumLabSection />
          <PartnershipsSection />
          <PaymentSystemSection />
          <ClientsSection />
        </main>
        
        <Footer />
      </div>
    </ThemeProvider>
  );
};

export default Index;
