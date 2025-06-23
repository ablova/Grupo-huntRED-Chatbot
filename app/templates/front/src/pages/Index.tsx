
import React from 'react';
import { ThemeProvider } from '@/components/ThemeProvider';
import Header from '@/components/Header';
import HeroSection from '@/components/HeroSection';
import ProcessSection from '@/components/ProcessSection';
import TechnologySection from '@/components/TechnologySection';
import TestimonialsSection from '@/components/TestimonialsSection';
import RecruitmentDashboard from '@/components/RecruitmentDashboard';
import AURAArchitectureSection from '@/components/AURAArchitectureSection';
import GenIAAndAURASection from '@/components/GenIAAndAURASection';
import AIFlowsSection from '@/components/AIFlowsSection';
import BusinessUnitsSection from '@/components/BusinessUnitsSection';
import ServicesSection from '@/components/ServicesSection';
import SolutionCalculator from '@/components/SolutionCalculator';
import Footer from '@/components/Footer';

const Index = () => {
  return (
    <ThemeProvider defaultTheme="system" storageKey="techai-theme">
      <div className="min-h-screen bg-background text-foreground">
        <Header />
        <main>
          <HeroSection />
          <ProcessSection />
          <RecruitmentDashboard />
          <AURAArchitectureSection />
          <GenIAAndAURASection />
          <AIFlowsSection />
          <TechnologySection />
          <TestimonialsSection />
          <BusinessUnitsSection />
          <ServicesSection />
          <SolutionCalculator />
        </main>
        <Footer />
      </div>
    </ThemeProvider>
  );
};

export default Index;
