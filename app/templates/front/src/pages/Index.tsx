// React se importa automáticamente con JSX
import { ThemeProvider } from '@/components/ThemeProvider';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { BrainCircuit, FlaskConical, Calculator } from 'lucide-react';

// New Main Sections
import HeroSection from '@/components/HeroSection';
import TalentEcosystemSection from '@/components/TalentEcosystemSection';
import TalentLifecycleSection from '@/components/TalentLifecycleSection';

// Hero & Stats Sections
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
import PayrollManagementSection from '@/components/PayrollManagementSection';
import PayrollCalculator from '@/components/PayrollCalculator';
import BusinessUnitCalculator from '@/components/BusinessUnitCalculator';
import AICustomizationSection from '@/components/AICustomizationSection';
import ClientsSection from '@/components/ClientsSection';
import TalentJourneyOverview from '@/components/TalentJourneyOverview';
import GenerationalAnalysisSection from '@/components/GenerationalAnalysisSection';
import DragDropDashboard from '@/components/DragDropDashboard';


const Index = () => {
  return (
    <ThemeProvider defaultTheme="system" storageKey="techai-theme">
      <div className="min-h-screen bg-background text-foreground">
        <Header />
        
        <main>
          {/* ===== NEW MAIN SECTIONS ===== */}
          <HeroSection />
          
          {/* New Platform Showcase Section */}
          <section className="py-16 md:py-24 bg-gradient-to-b from-background to-muted/30">
            <div className="container mx-auto px-4">
              <div className="text-center mb-12">
                <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
                  Descubre Nuestras Soluciones Integrales
                </h2>
                <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
                  Plataformas innovadoras diseñadas para transformar tu estrategia de talento y recursos humanos
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                {/* Plataforma Card */}
                <div className="group relative overflow-hidden rounded-2xl border border-border bg-card shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                  <div className="p-6">
                    <div className="w-12 h-12 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center mb-4">
                      <BrainCircuit className="w-6 h-6" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">Plataforma huntRED®</h3>
                    <p className="text-muted-foreground mb-6">
                      Tecnología avanzada de IA para la gestión integral del talento, con módulos especializados en cada etapa del ciclo de vida del empleado.
                    </p>
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-purple-600 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-500" />
                  </div>
                  <div className="px-6 pb-6 pt-2">
                    <a 
                      href="/plataforma" 
                      className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium group-hover:translate-x-1 transition-transform"
                    >
                      Explorar Plataforma
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-1">
                        <path d="M5 12h14"></path>
                        <path d="m12 5 7 7-7 7"></path>
                      </svg>
                    </a>
                  </div>
                </div>

                {/* Laboratorio Card */}
                <div className="group relative overflow-hidden rounded-2xl border border-border bg-card shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                  <div className="p-6">
                    <div className="w-12 h-12 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center mb-4">
                      <FlaskConical className="w-6 h-6" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">Laboratorio de Innovación</h3>
                    <p className="text-muted-foreground mb-6">
                      Explora nuestros proyectos experimentales y las próximas características que revolucionarán la gestión del talento.
                    </p>
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 to-pink-600 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-500" />
                  </div>
                  <div className="px-6 pb-6 pt-2">
                    <a 
                      href="/laboratorio" 
                      className="inline-flex items-center text-purple-600 hover:text-purple-800 font-medium group-hover:translate-x-1 transition-transform"
                    >
                      Ver Proyectos
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-1">
                        <path d="M5 12h14"></path>
                        <path d="m12 5 7 7-7 7"></path>
                      </svg>
                    </a>
                  </div>
                </div>

                {/* Calculadora Card */}
                <div className="group relative overflow-hidden rounded-2xl border border-border bg-card shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                  <div className="p-6">
                    <div className="w-12 h-12 rounded-xl bg-pink-100 text-pink-600 flex items-center justify-center mb-4">
                      <Calculator className="w-6 h-6" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">Calculadora de ROI</h3>
                    <p className="text-muted-foreground mb-6">
                      Descubre cuánto podrías ahorrar optimizando tus procesos de reclutamiento y retención de talento.
                    </p>
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-pink-500 to-rose-600 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-500" />
                  </div>
                  <div className="px-6 pb-6 pt-2">
                    <a 
                      href="/calculadora" 
                      className="inline-flex items-center text-pink-600 hover:text-pink-800 font-medium group-hover:translate-x-1 transition-transform"
                    >
                      Calcular Ahorros
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-1">
                        <path d="M5 12h14"></path>
                        <path d="m12 5 7 7-7 7"></path>
                      </svg>
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <TalentEcosystemSection />
          <TalentLifecycleSection />
          <TalentJourneyOverview />
          <GenerationalAnalysisSection />
          
          {/* ===== HERO & IMPACT SECTIONS ===== */}
          <StatsHeroSection />
          
          {/* ===== VALUE PROPOSITION & COMPETITIVE ===== */}
          <ValuePropositionSection />
          <CompetitiveComparisonSection />
          <CompetitiveAdvantagesSection />
          
          {/* ===== SERVICES & BUSINESS SOLUTIONS ===== */}
          <ServicesSection />
          <BusinessUnitsSection />
          <ProcessSection />

          {/* ===== MODULES & FEATURES ===== */}
          <HuntREDModulesSection />
          <TechnologySection />
          <MLCapabilitiesSection />
          
          {/* ===== CORE TECHNOLOGY & AI ===== */}
          <GenIAAndAURASection />
          <AIFlowsSection />
          <MLFlowsSection />
          <MLPipelineSection />
          <LLMCapabilitiesSection />
          {/* ===== DASHBOARDS & TOOLS ===== */}
          <RecruitmentDashboard />
          <KanbanDashboardSection />
          <DragDropDashboard />
          <AnalyticsDashboardSection />

          <AURAArchitectureSection />
          
          {/* ===== INTEGRATION & PRICING ===== */}
          <HRSystemIntegrationSection />
          <PricingAdvantagesSection />
          <ROIDemonstrationSection />
          <ROICalculatorSection />
          <SolutionCalculator />
          
          {/* ===== ECOSYSTEM & LEARNING ===== */}
          <EcosystemFlow />
          <LearningSection />

          {/* ===== ECOSYSTEM & MARKET ANALYTICS ===== */}
          <MarketAnalysisSection />
          <MatchmakingSection />
          
          {/* ===== SOCIAL PROOF & TESTIMONIALS ===== */}
          <CustomerSuccessStories />
          <TestimonialsSection />
          
          {/* ===== ADVANCED FEATURES ===== */}
          <SimulatorSection />
          <ServiceRoadmapSection />

          <MetaverseSection />
          <QuantumLabSection />
          <PartnershipsSection />
          <PaymentSystemSection />
          
          {/* ===== PAYROLL & BUSINESS UNIT CALCULATOR ===== */}
          <PayrollManagementSection />
          <PayrollCalculator />
          <BusinessUnitCalculator />

          
          {/* ===== AI CUSTOMIZATION & CLIENTS ===== */}
          <AICustomizationSection />
          <ClientsSection />
        </main>
        
        <Footer />
      </div>
    </ThemeProvider>
  );
};

export default Index;
