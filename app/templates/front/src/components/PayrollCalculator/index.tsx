import React from 'react';
import { PayrollCalculatorProvider } from './PayrollCalculatorContext';
import PayrollCalculatorHeader from './PayrollCalculatorHeader';
import CompanyConfigCard from './CompanyConfigCard';
import AddonsCard from './AddonsCard';
import PricingCard from './PricingCard';
import ROICard from './ROICard';

const PayrollCalculator = () => {
  return (
    <section className="py-16 bg-muted/10" data-section="payroll-calculator">
      <div className="container mx-auto px-4 lg:px-8">
        <PayrollCalculatorHeader />
        
        <PayrollCalculatorProvider>
          <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-6">
            <div className="space-y-6">
              <CompanyConfigCard />
              <AddonsCard />
            </div>
            <div className="space-y-6">
              <PricingCard />
              <ROICard />
            </div>
          </div>
        </PayrollCalculatorProvider>
      </div>
    </section>
  );
};

export default PayrollCalculator;
