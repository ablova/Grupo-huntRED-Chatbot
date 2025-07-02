import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary } from 'react-error-boundary';
import { motion, AnimatePresence } from 'framer-motion';
import ProcessTimeline from './components/ProcessTimeline';
import ClientUnderstanding from './components/ClientUnderstanding';
import RecruitmentDashboard from './components/RecruitmentDashboard';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Error boundary fallback component
function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div role="alert" className="p-4 bg-red-50 border-l-4 border-red-400">
      <p className="font-bold text-red-700">Algo salió mal:</p>
      <pre className="text-red-600 text-sm mt-2">{error.message}</pre>
      <button
        onClick={resetErrorBoundary}
        className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200"
      >
        Reintentar
      </button>
    </div>
  );
}

// Initialize components when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Initialize Process Timeline
  const timelineContainer = document.getElementById('process-timeline-container');
  if (timelineContainer) {
    const root = createRoot(timelineContainer);
    root.render(
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <ProcessTimeline />
          </BrowserRouter>
        </QueryClientProvider>
      </ErrorBoundary>
    );
  }

  // Initialize Client Understanding
  const clientUnderstandingContainer = document.getElementById('client-understanding-container');
  if (clientUnderstandingContainer) {
    const clientData = JSON.parse(clientUnderstandingContainer.dataset.client || '{}');
    const root = createRoot(clientUnderstandingContainer);
    root.render(
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <ClientUnderstanding clientData={clientData} />
          </BrowserRouter>
        </QueryClientProvider>
      </ErrorBoundary>
    );
  }

  // Initialize Recruitment Dashboard
  const recruitmentDashboardContainer = document.getElementById('recruitment-dashboard-container');
  if (recruitmentDashboardContainer) {
    const clientName = recruitmentDashboardContainer.dataset.clientName || 'el cliente';
    const root = createRoot(recruitmentDashboardContainer);
    root.render(
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <RecruitmentDashboard clientName={clientName} />
          </BrowserRouter>
        </QueryClientProvider>
      </ErrorBoundary>
    );
  }
});
