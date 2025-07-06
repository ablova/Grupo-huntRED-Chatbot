-- ============================================================================
-- 🚀 HUNTRED® V2 - COMPLETE DATABASE SCHEMA
-- ============================================================================
-- 
-- Schema unificado que integra todos los módulos del sistema:
-- - Core HR (empleados, nómina, asistencia)
-- - Advanced Features (notificaciones, referencias, feedback)
-- - AI/ML (AURA, GenIA, sentiment analysis)
-- - Business (proposals, payments, referrals, workflows)
-- - Analytics (dashboards, reports, metrics)
--
-- Autor: GHUNTRED V2 Team
-- Fecha: Diciembre 2024
-- Versión: 2.0.0
-- ============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- CORE TABLES - SISTEMA BASE
-- ============================================================================

-- Companies table
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    tax_id VARCHAR(50) UNIQUE,
    industry VARCHAR(100),
    size_category VARCHAR(50),
    
    -- Contact info
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(255),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    
    -- Settings
    timezone VARCHAR(50) DEFAULT 'America/Mexico_City',
    currency VARCHAR(10) DEFAULT 'MXN',
    language VARCHAR(10) DEFAULT 'es',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    is_active BOOLEAN DEFAULT true
);

-- Employees table (enhanced)
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id),
    
    -- Personal info
    employee_number VARCHAR(50) UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    
    -- Employment info
    position VARCHAR(100),
    department VARCHAR(100),
    manager_id UUID REFERENCES employees(id),
    hire_date DATE,
    employment_type VARCHAR(50), -- full_time, part_time, contractor
    employment_status VARCHAR(50) DEFAULT 'active', -- active, inactive, terminated
    
    -- Payroll info
    salary DECIMAL(12,2),
    salary_frequency VARCHAR(20) DEFAULT 'monthly', -- daily, weekly, monthly
    tax_id VARCHAR(50),
    bank_account VARCHAR(50),
    bank_name VARCHAR(100),
    
    -- Location info
    work_location VARCHAR(255),
    office_latitude DECIMAL(10,8),
    office_longitude DECIMAL(11,8),
    allowed_radius INTEGER DEFAULT 100, -- meters
    
    -- Auth info
    password_hash VARCHAR(255),
    role VARCHAR(50) DEFAULT 'employee', -- employee, supervisor, hr_admin, super_admin
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- ============================================================================
-- PAYROLL SYSTEM
-- ============================================================================

-- Payroll records
CREATE TABLE payroll_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    company_id UUID NOT NULL REFERENCES companies(id),
    
    -- Period info
    pay_period_start DATE NOT NULL,
    pay_period_end DATE NOT NULL,
    pay_date DATE NOT NULL,
    
    -- Salary calculations
    base_salary DECIMAL(12,2) NOT NULL,
    regular_hours DECIMAL(8,2) DEFAULT 0,
    overtime_hours DECIMAL(8,2) DEFAULT 0,
    double_overtime_hours DECIMAL(8,2) DEFAULT 0,
    
    -- Additional earnings
    bonuses DECIMAL(12,2) DEFAULT 0,
    commissions DECIMAL(12,2) DEFAULT 0,
    allowances DECIMAL(12,2) DEFAULT 0,
    
    -- Mexican tax calculations
    gross_pay DECIMAL(12,2) NOT NULL,
    isr_tax DECIMAL(12,2) DEFAULT 0, -- ISR
    imss_employee DECIMAL(12,2) DEFAULT 0, -- IMSS empleado
    imss_employer DECIMAL(12,2) DEFAULT 0, -- IMSS patrón
    infonavit DECIMAL(12,2) DEFAULT 0, -- INFONAVIT
    subsidio_empleo DECIMAL(12,2) DEFAULT 0, -- Subsidio para el empleo
    
    -- Other deductions
    other_deductions DECIMAL(12,2) DEFAULT 0,
    
    -- Final amounts
    total_deductions DECIMAL(12,2) NOT NULL,
    net_pay DECIMAL(12,2) NOT NULL,
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft', -- draft, approved, paid
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES employees(id)
);

-- ============================================================================
-- ATTENDANCE SYSTEM
-- ============================================================================

-- Attendance records
CREATE TABLE attendance_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    company_id UUID NOT NULL REFERENCES companies(id),
    
    -- Timing
    check_in_time TIMESTAMP WITH TIME ZONE,
    check_out_time TIMESTAMP WITH TIME ZONE,
    date DATE NOT NULL,
    
    -- Location tracking
    check_in_latitude DECIMAL(10,8),
    check_in_longitude DECIMAL(11,8),
    check_out_latitude DECIMAL(10,8),
    check_out_longitude DECIMAL(11,8),
    
    -- Calculated fields
    total_hours DECIMAL(8,2),
    regular_hours DECIMAL(8,2),
    overtime_hours DECIMAL(8,2),
    
    -- Status and validation
    status VARCHAR(50) DEFAULT 'present', -- present, absent, late, early_departure
    is_valid_location BOOLEAN DEFAULT true,
    notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- ADVANCED NOTIFICATIONS SYSTEM
-- ============================================================================

-- Notification templates
CREATE TABLE notification_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100), -- recruitment, payroll, attendance, hr
    
    -- Template content
    subject_template TEXT,
    body_template TEXT,
    sms_template TEXT,
    push_template TEXT,
    
    -- Channel configuration
    enabled_channels JSONB DEFAULT '[]', -- ["email", "sms", "whatsapp", "push"]
    
    -- Variables
    available_variables JSONB DEFAULT '{}',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    is_active BOOLEAN DEFAULT true
);

-- Notifications sent
CREATE TABLE notifications_sent (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES notification_templates(id),
    
    -- Recipient info
    recipient_id UUID, -- Can be employee, client, candidate
    recipient_type VARCHAR(50), -- employee, client, candidate
    recipient_email VARCHAR(255),
    recipient_phone VARCHAR(50),
    
    -- Message content
    channel VARCHAR(50) NOT NULL, -- email, sms, whatsapp, push, slack, teams
    subject TEXT,
    content TEXT,
    
    -- Delivery info
    status VARCHAR(50) DEFAULT 'pending', -- pending, sent, delivered, failed, read
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    failed_reason TEXT,
    
    -- Response tracking
    response_data JSONB,
    engagement_score DECIMAL(5,2),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- ADVANCED REFERENCES SYSTEM
-- ============================================================================

-- Reference requests
CREATE TABLE reference_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID NOT NULL, -- Reference to candidate
    
    -- Request info
    reference_type VARCHAR(50) NOT NULL, -- initial, advanced
    stage VARCHAR(50) NOT NULL, -- early_stage, pre_offer
    position_title VARCHAR(255),
    
    -- Reference contact
    reference_name VARCHAR(255) NOT NULL,
    reference_email VARCHAR(255) NOT NULL,
    reference_phone VARCHAR(50),
    reference_position VARCHAR(255),
    reference_company VARCHAR(255),
    relationship VARCHAR(100), -- supervisor, colleague, client, etc.
    
    -- Request details
    questions JSONB, -- Array of questions to ask
    expected_duration INTEGER DEFAULT 15, -- minutes
    
    -- Status and timing
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, expired
    sent_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES employees(id)
);

-- Reference responses
CREATE TABLE reference_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id UUID NOT NULL REFERENCES reference_requests(id),
    
    -- Response data
    responses JSONB NOT NULL, -- Question-answer pairs
    overall_rating DECIMAL(3,2), -- 1.0 to 10.0
    recommendation_strength VARCHAR(50), -- strong, moderate, weak, not_recommended
    
    -- Analysis
    sentiment_score DECIMAL(5,2),
    key_strengths TEXT[],
    areas_concern TEXT[],
    red_flags TEXT[],
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- ADVANCED FEEDBACK SYSTEM
-- ============================================================================

-- Feedback requests
CREATE TABLE feedback_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Request info
    feedback_type VARCHAR(50) NOT NULL, -- client_interview, candidate_process
    related_id UUID NOT NULL, -- interview_id, process_id, etc.
    related_type VARCHAR(50) NOT NULL, -- interview, process, etc.
    
    -- Recipient info
    recipient_id UUID NOT NULL,
    recipient_type VARCHAR(50) NOT NULL, -- client, candidate
    recipient_email VARCHAR(255),
    
    -- Request configuration
    questions JSONB NOT NULL,
    expected_duration INTEGER DEFAULT 5, -- minutes
    
    -- Status and timing
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, expired
    sent_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Reminders
    reminder_count INTEGER DEFAULT 0,
    last_reminder_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES employees(id)
);

-- Feedback responses
CREATE TABLE feedback_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id UUID NOT NULL REFERENCES feedback_requests(id),
    
    -- Response data
    responses JSONB NOT NULL,
    overall_satisfaction DECIMAL(3,2), -- 1.0 to 10.0
    
    -- Sentiment analysis
    sentiment_score DECIMAL(5,2), -- -1.0 to 1.0
    sentiment_label VARCHAR(50), -- positive, neutral, negative
    key_topics TEXT[],
    improvement_suggestions TEXT[],
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- AI/ML SYSTEM TABLES
-- ============================================================================

-- AURA conversation sessions
CREATE TABLE aura_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES employees(id),
    
    -- Session info
    session_type VARCHAR(50) DEFAULT 'general', -- general, recruitment, analysis
    personality VARCHAR(50) DEFAULT 'professional', -- professional, friendly, analytical
    
    -- Context
    context_data JSONB DEFAULT '{}',
    memory_snapshot JSONB DEFAULT '{}',
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, ended
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AURA messages
CREATE TABLE aura_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES aura_sessions(id),
    
    -- Message info
    role VARCHAR(50) NOT NULL, -- user, assistant
    content TEXT NOT NULL,
    
    -- Processing info
    intent VARCHAR(100),
    confidence DECIMAL(5,2),
    entities JSONB DEFAULT '{}',
    
    -- Response metadata
    processing_time DECIMAL(8,3), -- seconds
    model_used VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- GenIA matchmaking results
CREATE TABLE genia_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Job and candidate info
    job_id VARCHAR(255) NOT NULL,
    candidate_id UUID NOT NULL,
    
    -- Scoring (9 categories)
    technical_skills_score DECIMAL(5,2),
    soft_skills_score DECIMAL(5,2),
    experience_fit_score DECIMAL(5,2),
    cultural_alignment_score DECIMAL(5,2),
    growth_potential_score DECIMAL(5,2),
    performance_indicators_score DECIMAL(5,2),
    stability_factors_score DECIMAL(5,2),
    diversity_equity_score DECIMAL(5,2),
    market_competitiveness_score DECIMAL(5,2),
    
    -- Overall scoring
    overall_score DECIMAL(5,2) NOT NULL,
    confidence_level DECIMAL(5,2),
    tier_classification VARCHAR(20), -- tier_1, tier_2, tier_3
    
    -- Analysis details
    strengths TEXT[],
    concerns TEXT[],
    recommendations TEXT[],
    
    -- Bias detection
    bias_flags TEXT[],
    bias_confidence DECIMAL(5,2),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- BUSINESS MODULES
-- ============================================================================

-- Proposals
CREATE TABLE proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    
    -- Proposal info
    title VARCHAR(255) NOT NULL,
    description TEXT,
    proposal_type VARCHAR(50), -- hr_services, payroll_outsourcing, consulting
    
    -- Pricing
    base_price DECIMAL(12,2),
    currency VARCHAR(10) DEFAULT 'MXN',
    pricing_model VARCHAR(50), -- fixed, hourly, subscription
    
    -- Services included
    services JSONB DEFAULT '[]',
    deliverables JSONB DEFAULT '[]',
    timeline_days INTEGER,
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft', -- draft, sent, approved, rejected, expired
    valid_until DATE,
    
    -- Approval workflow
    approval_status VARCHAR(50) DEFAULT 'pending',
    approved_by UUID REFERENCES employees(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES employees(id)
);

-- Payments
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proposal_id UUID REFERENCES proposals(id),
    client_id UUID NOT NULL,
    
    -- Payment info
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'MXN',
    payment_method VARCHAR(50), -- credit_card, bank_transfer, paypal, oxxo
    
    -- Transaction details
    transaction_id VARCHAR(255),
    gateway_response JSONB,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed, refunded
    
    -- Timing
    due_date DATE,
    paid_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Referrals
CREATE TABLE referrals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Referrer info
    referrer_id UUID NOT NULL, -- Can be employee, client, or external
    referrer_type VARCHAR(50) NOT NULL, -- employee, client, partner
    
    -- Referred entity
    referred_id UUID NOT NULL,
    referred_type VARCHAR(50) NOT NULL, -- candidate, client
    
    -- Program info
    program_type VARCHAR(50), -- customer, employee, partner
    reward_type VARCHAR(50), -- percentage, fixed_amount, bonus
    reward_amount DECIMAL(12,2),
    
    -- Status and tracking
    status VARCHAR(50) DEFAULT 'pending', -- pending, qualified, completed, paid
    qualified_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    
    -- Performance tracking
    conversion_value DECIMAL(12,2),
    commission_earned DECIMAL(12,2),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- WORKFLOW SYSTEM
-- ============================================================================

-- Workflow definitions
CREATE TABLE workflow_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    
    -- Workflow info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100), -- onboarding, recruitment, expense_approval
    version INTEGER DEFAULT 1,
    
    -- Configuration
    steps JSONB NOT NULL, -- Array of workflow steps
    variables JSONB DEFAULT '{}',
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft', -- draft, active, deprecated
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES employees(id)
);

-- Workflow executions
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    definition_id UUID NOT NULL REFERENCES workflow_definitions(id),
    
    -- Execution info
    entity_id UUID, -- ID of the entity being processed (employee, candidate, etc.)
    entity_type VARCHAR(50),
    
    -- Progress tracking
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER,
    
    -- Data
    execution_data JSONB DEFAULT '{}',
    variables JSONB DEFAULT '{}',
    
    -- Status and timing
    status VARCHAR(50) DEFAULT 'running', -- running, completed, failed, paused
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- BUSINESS UNITS SYSTEM
-- ============================================================================

-- Business units
CREATE TABLE business_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id),
    parent_id UUID REFERENCES business_units(id),
    
    -- Unit info
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    type VARCHAR(50), -- division, department, team, project
    
    -- Hierarchy
    level INTEGER DEFAULT 0,
    path TEXT, -- Materialized path for quick hierarchy queries
    
    -- Management
    manager_id UUID REFERENCES employees(id),
    
    -- Budget and KPIs
    annual_budget DECIMAL(15,2),
    budget_currency VARCHAR(10) DEFAULT 'MXN',
    kpis JSONB DEFAULT '{}',
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, restructuring
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES employees(id)
);

-- Employee assignments to business units
CREATE TABLE employee_business_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    business_unit_id UUID NOT NULL REFERENCES business_units(id),
    
    -- Assignment info
    role VARCHAR(255),
    allocation_percentage DECIMAL(5,2) DEFAULT 100.00, -- % of time allocated
    
    -- Timing
    start_date DATE NOT NULL,
    end_date DATE,
    
    -- Status
    is_primary BOOLEAN DEFAULT false,
    status VARCHAR(50) DEFAULT 'active',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(employee_id, business_unit_id, start_date)
);

-- ============================================================================
-- ANALYTICS AND REPORTING
-- ============================================================================

-- System metrics
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Metric info
    metric_name VARCHAR(255) NOT NULL,
    metric_category VARCHAR(100), -- performance, usage, business
    
    -- Values
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(50),
    
    -- Dimensions
    dimensions JSONB DEFAULT '{}', -- Additional categorization
    
    -- Timing
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Core indexes
CREATE INDEX idx_employees_company_id ON employees(company_id);
CREATE INDEX idx_employees_manager_id ON employees(manager_id);
CREATE INDEX idx_employees_email ON employees(email);
CREATE INDEX idx_employees_employee_number ON employees(employee_number);

-- Payroll indexes
CREATE INDEX idx_payroll_records_employee_id ON payroll_records(employee_id);
CREATE INDEX idx_payroll_records_period ON payroll_records(pay_period_start, pay_period_end);
CREATE INDEX idx_payroll_records_status ON payroll_records(status);

-- Attendance indexes
CREATE INDEX idx_attendance_records_employee_id ON attendance_records(employee_id);
CREATE INDEX idx_attendance_records_date ON attendance_records(date);
CREATE INDEX idx_attendance_records_status ON attendance_records(status);

-- Notifications indexes
CREATE INDEX idx_notifications_sent_recipient ON notifications_sent(recipient_id, recipient_type);
CREATE INDEX idx_notifications_sent_status ON notifications_sent(status);
CREATE INDEX idx_notifications_sent_channel ON notifications_sent(channel);

-- AI/ML indexes
CREATE INDEX idx_aura_sessions_user_id ON aura_sessions(user_id);
CREATE INDEX idx_aura_messages_session_id ON aura_messages(session_id);
CREATE INDEX idx_genia_matches_job_id ON genia_matches(job_id);
CREATE INDEX idx_genia_matches_candidate_id ON genia_matches(candidate_id);
CREATE INDEX idx_genia_matches_score ON genia_matches(overall_score DESC);

-- Business indexes
CREATE INDEX idx_proposals_client_id ON proposals(client_id);
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_payments_proposal_id ON payments(proposal_id);
CREATE INDEX idx_payments_status ON payments(status);

-- Workflow indexes
CREATE INDEX idx_workflow_executions_definition_id ON workflow_executions(definition_id);
CREATE INDEX idx_workflow_executions_entity ON workflow_executions(entity_id, entity_type);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);

-- Business units indexes
CREATE INDEX idx_business_units_company_id ON business_units(company_id);
CREATE INDEX idx_business_units_parent_id ON business_units(parent_id);
CREATE INDEX idx_employee_business_units_employee_id ON employee_business_units(employee_id);
CREATE INDEX idx_employee_business_units_unit_id ON employee_business_units(business_unit_id);

-- Metrics indexes
CREATE INDEX idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_category ON system_metrics(metric_category);
CREATE INDEX idx_system_metrics_recorded_at ON system_metrics(recorded_at);

-- Full-text search indexes
CREATE INDEX idx_employees_search ON employees USING gin(to_tsvector('spanish', first_name || ' ' || last_name || ' ' || email));
CREATE INDEX idx_business_units_search ON business_units USING gin(to_tsvector('spanish', name));

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all relevant tables
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_employees_updated_at BEFORE UPDATE ON employees FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payroll_records_updated_at BEFORE UPDATE ON payroll_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_attendance_records_updated_at BEFORE UPDATE ON attendance_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notification_templates_updated_at BEFORE UPDATE ON notification_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notifications_sent_updated_at BEFORE UPDATE ON notifications_sent FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_aura_sessions_updated_at BEFORE UPDATE ON aura_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_genia_matches_updated_at BEFORE UPDATE ON genia_matches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_proposals_updated_at BEFORE UPDATE ON proposals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_referrals_updated_at BEFORE UPDATE ON referrals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflow_definitions_updated_at BEFORE UPDATE ON workflow_definitions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflow_executions_updated_at BEFORE UPDATE ON workflow_executions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_business_units_updated_at BEFORE UPDATE ON business_units FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_employee_business_units_updated_at BEFORE UPDATE ON employee_business_units FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Employee full info view
CREATE VIEW employee_full_info AS
SELECT 
    e.*,
    c.name as company_name,
    m.first_name as manager_first_name,
    m.last_name as manager_last_name,
    bu.name as primary_business_unit
FROM employees e
LEFT JOIN companies c ON e.company_id = c.id
LEFT JOIN employees m ON e.manager_id = m.id
LEFT JOIN employee_business_units ebu ON e.id = ebu.employee_id AND ebu.is_primary = true
LEFT JOIN business_units bu ON ebu.business_unit_id = bu.id;

-- Latest payroll view
CREATE VIEW latest_payroll AS
SELECT DISTINCT ON (employee_id) *
FROM payroll_records
ORDER BY employee_id, pay_period_end DESC;

-- Current attendance view
CREATE VIEW current_attendance AS
SELECT 
    employee_id,
    date,
    check_in_time,
    check_out_time,
    total_hours,
    status
FROM attendance_records
WHERE date = CURRENT_DATE;

-- Active workflows view
CREATE VIEW active_workflows AS
SELECT 
    we.*,
    wd.name as workflow_name,
    wd.category as workflow_category
FROM workflow_executions we
JOIN workflow_definitions wd ON we.definition_id = wd.id
WHERE we.status IN ('running', 'paused');

-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================

-- Insert sample company
INSERT INTO companies (name, legal_name, tax_id, industry, email, phone, timezone, currency, language)
VALUES (
    'HuntRED® México',
    'HuntRED México S.A. de C.V.',
    'HRM123456789',
    'Human Resources Technology',
    'info@huntred.mx',
    '+52-55-1234-5678',
    'America/Mexico_City',
    'MXN',
    'es'
);

-- ============================================================================
-- COMPLETION SUMMARY
-- ============================================================================

-- Database schema complete with:
-- ✅ 20+ core tables for all modules
-- ✅ Comprehensive indexes for performance
-- ✅ Automatic timestamp triggers
-- ✅ Useful views for common queries
-- ✅ Sample data structure
-- ✅ Full integration between all modules
-- ✅ Mexican payroll compliance fields
-- ✅ Advanced AI/ML tracking
-- ✅ Complete workflow system
-- ✅ Business units hierarchy
-- ✅ Analytics and metrics foundation

COMMENT ON DATABASE postgres IS 'HuntRED® v2 - Sistema completo de reclutamiento y RH con IA avanzada';