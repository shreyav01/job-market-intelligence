-- Run this once on your Supabase database to create all tables

CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    job_url TEXT UNIQUE,
    date_posted DATE,
    date_scraped TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_skills (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_insights (
    id SERIAL PRIMARY KEY,
    insight_text TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_jobs_date ON jobs(date_scraped);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
CREATE INDEX IF NOT EXISTS idx_skills_name ON job_skills(skill_name);
