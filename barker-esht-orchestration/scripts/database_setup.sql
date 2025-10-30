-- Barker v ESHT - Database Setup Script
-- PostgreSQL/Supabase Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Evidence Table
CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exhibit_code TEXT,
    document_type TEXT,
    source_path TEXT,
    normalised_path TEXT,
    sha256 TEXT UNIQUE,
    file_size BIGINT,
    page_count INTEGER,
    tags TEXT[],
    used_in TEXT,
    notes TEXT,
    metadata JSONB,
    date_created TIMESTAMP WITH TIME ZONE,
    date_modified TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Issues Table
CREATE TABLE IF NOT EXISTS issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    priority TEXT,
    status TEXT DEFAULT 'Open',
    evidence_ids UUID[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Timeline Table
CREATE TABLE IF NOT EXISTS timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_date DATE NOT NULL,
    event_time TIME,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    participants TEXT[],
    location TEXT,
    evidence_ids UUID[],
    issue_ids UUID[],
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tasks Table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    workstream TEXT,
    priority TEXT,
    status TEXT DEFAULT 'To Do',
    assigned_to TEXT,
    due_date DATE,
    completed_at TIMESTAMP WITH TIME ZONE,
    evidence_ids UUID[],
    issue_ids UUID[],
    todoist_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_evidence_exhibit_code ON evidence(exhibit_code);
CREATE INDEX IF NOT EXISTS idx_evidence_sha256 ON evidence(sha256);
CREATE INDEX IF NOT EXISTS idx_evidence_created_at ON evidence(created_at);
CREATE INDEX IF NOT EXISTS idx_evidence_metadata ON evidence USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_issues_issue_code ON issues(issue_code);
CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
CREATE INDEX IF NOT EXISTS idx_issues_category ON issues(category);
CREATE INDEX IF NOT EXISTS idx_issues_created_at ON issues(created_at);

CREATE INDEX IF NOT EXISTS idx_timeline_event_date ON timeline(event_date);
CREATE INDEX IF NOT EXISTS idx_timeline_category ON timeline(category);
CREATE INDEX IF NOT EXISTS idx_timeline_created_at ON timeline(created_at);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_workstream ON tasks(workstream);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_evidence_updated_at BEFORE UPDATE ON evidence
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_issues_updated_at BEFORE UPDATE ON issues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_timeline_updated_at BEFORE UPDATE ON timeline
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
-- Enable RLS
ALTER TABLE evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE timeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your authentication setup)
CREATE POLICY "Enable read access for authenticated users" ON evidence
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Enable insert access for authenticated users" ON evidence
    FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Enable update access for authenticated users" ON evidence
    FOR UPDATE TO authenticated USING (true);

-- Similar policies for other tables
CREATE POLICY "Enable read access for authenticated users" ON issues
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Enable insert access for authenticated users" ON issues
    FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Enable update access for authenticated users" ON issues
    FOR UPDATE TO authenticated USING (true);

CREATE POLICY "Enable read access for authenticated users" ON timeline
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Enable insert access for authenticated users" ON timeline
    FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Enable update access for authenticated users" ON timeline
    FOR UPDATE TO authenticated USING (true);

CREATE POLICY "Enable read access for authenticated users" ON tasks
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Enable insert access for authenticated users" ON tasks
    FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Enable update access for authenticated users" ON tasks
    FOR UPDATE TO authenticated USING (true);

-- Views for analytics
CREATE OR REPLACE VIEW evidence_summary AS
SELECT
    COUNT(*) as total_evidence,
    COUNT(CASE WHEN exhibit_code IS NOT NULL THEN 1 END) as with_exhibit_codes,
    ROUND(COUNT(CASE WHEN exhibit_code IS NOT NULL THEN 1 END)::numeric / COUNT(*)::numeric * 100, 2) as pct_with_codes,
    COUNT(DISTINCT document_type) as unique_document_types,
    SUM(file_size) as total_size_bytes,
    SUM(page_count) as total_pages
FROM evidence;

CREATE OR REPLACE VIEW timeline_by_month AS
SELECT
    DATE_TRUNC('month', event_date) as month,
    COUNT(*) as event_count,
    COUNT(DISTINCT category) as unique_categories
FROM timeline
GROUP BY DATE_TRUNC('month', event_date)
ORDER BY month;

CREATE OR REPLACE VIEW tasks_by_workstream AS
SELECT
    workstream,
    status,
    COUNT(*) as task_count
FROM tasks
GROUP BY workstream, status
ORDER BY workstream, status;

-- Sample data for testing (optional)
-- Uncomment to insert sample records
/*
INSERT INTO evidence (exhibit_code, document_type, source_path, sha256)
VALUES ('ESHT-001', 'Medical Record', 'test/document.pdf', 'sample_hash_123');

INSERT INTO issues (issue_code, title, category, priority, status)
VALUES ('ISS-001', 'Sample Issue', 'Clinical Negligence', 'High', 'Open');

INSERT INTO timeline (event_date, title, category, description)
VALUES ('2024-01-15', 'Initial Consultation', 'Medical', 'Patient first visit');

INSERT INTO tasks (title, workstream, priority, status)
VALUES ('Review medical records', 'Evidence Review', 'High', 'To Do');
*/
