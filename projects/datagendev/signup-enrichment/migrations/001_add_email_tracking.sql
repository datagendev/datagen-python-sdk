-- Migration: Add Email Tracking to CRM Table
-- Description: Adds columns to track email interactions, status, and follow-up needs
-- Created: 2025-12-01

BEGIN;

-- Email status tracking
-- Values: 'not_contacted', 'contacted', 'replied', 'needs_followup'
ALTER TABLE crm ADD COLUMN IF NOT EXISTS email_status VARCHAR(20) DEFAULT 'not_contacted';

-- Timestamp tracking
ALTER TABLE crm ADD COLUMN IF NOT EXISTS last_email_sent_at TIMESTAMP;
ALTER TABLE crm ADD COLUMN IF NOT EXISTS last_email_received_at TIMESTAMP;
ALTER TABLE crm ADD COLUMN IF NOT EXISTS email_tracking_last_synced_at TIMESTAMP;

-- Email counters
ALTER TABLE crm ADD COLUMN IF NOT EXISTS emails_sent_count INTEGER DEFAULT 0;
ALTER TABLE crm ADD COLUMN IF NOT EXISTS emails_received_count INTEGER DEFAULT 0;

-- Computed flags
-- TRUE if: last_email_sent_at > 3 days ago AND (no reply OR last_received < last_sent)
ALTER TABLE crm ADD COLUMN IF NOT EXISTS needs_followup BOOLEAN DEFAULT FALSE;

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_crm_email_status ON crm(email_status);
CREATE INDEX IF NOT EXISTS idx_crm_needs_followup ON crm(needs_followup) WHERE needs_followup = TRUE;
CREATE INDEX IF NOT EXISTS idx_crm_last_email_sent ON crm(last_email_sent_at) WHERE last_email_sent_at IS NOT NULL;

COMMIT;
