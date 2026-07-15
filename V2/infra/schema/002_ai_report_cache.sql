ALTER TABLE reconstruction_reports
    ADD COLUMN IF NOT EXISTS ai_report JSONB,
    ADD COLUMN IF NOT EXISTS ai_report_cache_key TEXT,
    ADD COLUMN IF NOT EXISTS ai_report_generated_at TIMESTAMPTZ;
