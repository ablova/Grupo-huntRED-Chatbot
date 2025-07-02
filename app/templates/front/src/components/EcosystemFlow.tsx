// src/components/EcosystemFlow.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowRight } from 'lucide-react';
// Add missing icon imports from lucide-react
import { Calendar, Award, Phone } from 'lucide-react';

// Define interface for ecosystem features to ensure type safety
interface EcosystemFeature {
  title: string;
  description: string;
  features: string[];
  icon: React.ComponentType<{ className?: string }>;
}

// Define interface for mlCycle steps
interface MLCycleStep {
  step: number;
  title: string;
  description: string;
}

// Sample ecosystem features (adjust as per actual data)
const ecosystemFeatures: EcosystemFeature[] = [
  {
    title: 'Event Scheduling',
    description: 'Streamline your event planning with AI-driven scheduling.',
    features: ['Automated reminders', 'Time zone sync', 'Group coordination'],
    icon: Calendar,
  },
  {
    title: 'Achievements',
    description: 'Track and celebrate milestones with our rewards system.',
    features: ['Custom badges', 'Progress tracking', 'Team recognition'],
    icon: Award,
  },
  {
    title: 'Communication Hub',
    description: 'Stay connected with integrated communication tools.',
    features: ['Real-time chat', 'Voice integration', 'Mobile access'],
    icon: Phone,
  },
  // Add other features as needed
];

const EcosystemFlow: React.FC = () => {
  const [mlCycle] = useState<MLCycleStep[]>([
    { step: 1, title: 'Data Collection', description: 'Gather relevant data efficiently.' },
    { step: 2, title: 'Model Training', description: 'Train models with high accuracy.' },
    { step: 3, title: 'Deployment', description: 'Deploy models seamlessly.' },
    { step: 4, title: 'Monitoring', description: 'Monitor performance in real-time.' },
  ]);

  // Memoize computed values to optimize performance
  const renderedLines = useMemo(() => {
    return mlCycle.map((_, index) => {
      if (index < mlCycle.length - 1) {
        const startAngle = -90 + (index * 360) / mlCycle.length;
        const endAngle = -90 + ((index + 1) * 360) / mlCycle.length;
        const startX = 50 + 40 * Math.cos((startAngle * Math.PI) / 180);
        const startY = 50 + 40 * Math.sin((startAngle * Math.PI) / 180);
        const endX = 50 + 40 * Math.cos((endAngle * Math.PI) / 180);
        const endY = 50 + 40 * Math.sin((endAngle * Math.PI) / 180);
        return (
          <line
            key={`line-${index}`}
            x1={`${startX}%`}
            y1={`${startY}%`}
            x2={`${endX}%`}
            y2={`${endY}%`}
            stroke="hsl(var(--muted))"
            strokeWidth="2"
            markerEnd="url(#arrowhead)"
            strokeDasharray="10 5"
          />
        );
      }
      return null;
    });
  }, [mlCycle]);

  return (
    <section className="py-16 bg-background">
      <div className="container mx-auto px-4 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">
            Flujo del <span className="modern-gradient bg-clip-text text-transparent">Ecosistema</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Descubre cómo nuestras soluciones integradas optimizan cada etapa de tu proceso de transformación digital.
          </p>
        </div>

        {/* Flow Diagram */}
        <div className="flex flex-col lg:flex-row gap-12 items-center justify-center">
          <div className="w-full lg:w-1/2">
            <div className="relative">
              {/* SVG Flow */}
              <div className="w-96 h-96 mx-auto">
                <svg viewBox="0 0 100 100" className="w-full h-full">
                  <defs>
                    <marker
                      id="arrowhead"
                      markerWidth="10"
                      markerHeight="7"
                      refX="10"
                      refY="3.5"
                      orient="auto"
                    >
                      <polygon points="0 0, 10 3.5, 0 7" fill="hsl(var(--muted))" />
                    </marker>
                  </defs>
                  {renderedLines}
                </svg>
              </div>

              {/* Step Cards */}
              <div className="flex justify-center">
                <div className="relative w-96 h-96">
                  {mlCycle.map((step, index) => {
                    const angle = -90 + (index * 360) / mlCycle.length;
                    const x = 50 + 40 * Math.cos((angle * Math.PI) / 180);
                    const y = 50 + 40 * Math.sin((angle * Math.PI) / 180);

                    return (
                      <div
                        key={index}
                        className="absolute w-40 transform -translate-x-1/2 -translate-y-1/2"
                        style={{
                          top: `${y}%`,
                          left: `${x}%`,
                        }}
                      >
                        <Card className="glass border-primary/10 hover:border-primary/30 transition-all">
                          <CardHeader className="space-x-2">
                            <CardTitle className="text-sm font-semibold flex items-center space-x-2">
                              <span className="w-5 h-5 rounded-full bg-primary/20 text-primary flex items-center justify-center text-xs">
                                {step.step}
                              </span>
                              <span>{step.title}</span>
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <p className="text-xs text-muted-foreground">{step.description}</p>
                          </CardContent>
                        </Card>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center mt-16">
          <Button size="lg" className="modern-gradient-bg hover:opacity-90 text-white">
            Descubre el Ecosistema
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </div>
    </section>
  );
};

export default EcosystemFlow;
