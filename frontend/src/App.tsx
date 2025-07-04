import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { useAuth } from './hooks/useAuth';

// Layout Components
import Layout from './components/Layout/Layout';
import AuthLayout from './components/Layout/AuthLayout';

// Page Components
import LoginPage from './pages/auth/LoginPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import CandidatesPage from './pages/candidates/CandidatesPage';
import CandidateDetailPage from './pages/candidates/CandidateDetailPage';
import JobsPage from './pages/jobs/JobsPage';
import JobDetailPage from './pages/jobs/JobDetailPage';
import CompaniesPage from './pages/companies/CompaniesPage';
import WorkflowsPage from './pages/workflows/WorkflowsPage';
import AssessmentsPage from './pages/assessments/AssessmentsPage';
import AssessmentDetailPage from './pages/assessments/AssessmentDetailPage';
import ReportsPage from './pages/reports/ReportsPage';
import SettingsPage from './pages/settings/SettingsPage';
import MLAnalyticsPage from './pages/ml/MLAnalyticsPage';
import AuraPage from './pages/aura/AuraPage';
import NotificationsPage from './pages/notifications/NotificationsPage';
import ProfilePage from './pages/profile/ProfilePage';
import NotFoundPage from './pages/NotFoundPage';

// Loading Component
import LoadingSpinner from './components/common/LoadingSpinner';

// Styles
import './App.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
};

// Public Route Component (redirect if authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return <AuthLayout>{children}</AuthLayout>;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <Router>
            <div className="App min-h-screen bg-gray-50 dark:bg-gray-900">
              <Routes>
                {/* Public Routes */}
                <Route 
                  path="/login" 
                  element={
                    <PublicRoute>
                      <LoginPage />
                    </PublicRoute>
                  } 
                />

                {/* Protected Routes */}
                <Route 
                  path="/dashboard" 
                  element={
                    <ProtectedRoute>
                      <DashboardPage />
                    </ProtectedRoute>
                  } 
                />

                {/* Candidates */}
                <Route 
                  path="/candidates" 
                  element={
                    <ProtectedRoute>
                      <CandidatesPage />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/candidates/:id" 
                  element={
                    <ProtectedRoute>
                      <CandidateDetailPage />
                    </ProtectedRoute>
                  } 
                />

                {/* Jobs */}
                <Route 
                  path="/jobs" 
                  element={
                    <ProtectedRoute>
                      <JobsPage />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/jobs/:id" 
                  element={
                    <ProtectedRoute>
                      <JobDetailPage />
                    </ProtectedRoute>
                  } 
                />

                {/* Companies */}
                <Route 
                  path="/companies" 
                  element={
                    <ProtectedRoute>
                      <CompaniesPage />
                    </ProtectedRoute>
                  } 
                />

                {/* Workflows */}
                <Route 
                  path="/workflows" 
                  element={
                    <ProtectedRoute>
                      <WorkflowsPage />
                    </ProtectedRoute>
                  } 
                />

                {/* Assessments */}
                <Route 
                  path="/assessments" 
                  element={
                    <ProtectedRoute>
                      <AssessmentsPage />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/assessments/:id" 
                  element={
                    <ProtectedRoute>
                      <AssessmentDetailPage />
                    </ProtectedRoute>
                  } 
                />

                {/* ML & AI */}
                <Route 
                  path="/ml-analytics" 
                  element={
                    <ProtectedRoute>
                      <MLAnalyticsPage />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/aura" 
                  element={
                    <ProtectedRoute>
                      <AuraPage />
                    </ProtectedRoute>
                  } 
                />

                {/* Reports */}
                <Route 
                  path="/reports" 
                  element={
                    <ProtectedRoute>
                      <ReportsPage />
                    </ProtectedRoute>
                  } 
                />

                {/* Notifications */}
                <Route 
                  path="/notifications" 
                  element={
                    <ProtectedRoute>
                      <NotificationsPage />
                    </ProtectedRoute>
                  } 
                />

                {/* Settings */}
                <Route 
                  path="/settings" 
                  element={
                    <ProtectedRoute>
                      <SettingsPage />
                    </ProtectedRoute>
                  } 
                />

                {/* Profile */}
                <Route 
                  path="/profile" 
                  element={
                    <ProtectedRoute>
                      <ProfilePage />
                    </ProtectedRoute>
                  } 
                />

                {/* Redirects */}
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                
                {/* 404 */}
                <Route 
                  path="*" 
                  element={
                    <ProtectedRoute>
                      <NotFoundPage />
                    </ProtectedRoute>
                  } 
                />
              </Routes>

              {/* Global Components */}
              <Toaster
                position="top-right"
                toastOptions={{
                  duration: 4000,
                  style: {
                    background: '#363636',
                    color: '#fff',
                  },
                  success: {
                    duration: 3000,
                    iconTheme: {
                      primary: '#4ade80',
                      secondary: '#fff',
                    },
                  },
                  error: {
                    duration: 5000,
                    iconTheme: {
                      primary: '#ef4444',
                      secondary: '#fff',
                    },
                  },
                }}
              />
            </div>
          </Router>
        </AuthProvider>
      </ThemeProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;