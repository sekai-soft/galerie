-- Migration: Add history_limit column to users table
-- Date: 2025-11-10
-- Description: Adds history_limit column to users table with default value of 500

ALTER TABLE users
ADD COLUMN IF NOT EXISTS history_limit INTEGER DEFAULT 500 NOT NULL;
