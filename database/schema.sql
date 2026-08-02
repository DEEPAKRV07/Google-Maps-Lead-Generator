-- SQLite Master Database DDL Schema for Google-Maps-Lead-Generator v2.0

-- 1. Schema Versioning Table
CREATE TABLE IF NOT EXISTS version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_version TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_migration TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. System Settings Table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Raw Business Extractions Table
CREATE TABLE IF NOT EXISTS raw_businesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_name TEXT,
    raw_phone TEXT,
    raw_website TEXT,
    raw_rating TEXT,
    raw_reviews TEXT,
    google_maps_link TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Processed Master Businesses Table
CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    source_category TEXT,
    category TEXT,
    search_location TEXT,
    location TEXT,
    address TEXT,
    phone TEXT,
    website TEXT,
    email TEXT,
    whatsapp TEXT,
    facebook TEXT,
    instagram TEXT,
    linkedin TEXT,
    twitter TEXT,
    contact_form TEXT,
    rating REAL,
    reviews INTEGER,
    hours TEXT,
    google_maps_link TEXT UNIQUE,
    website_status TEXT,
    business_type TEXT,
    notes TEXT,
    priority_score INTEGER DEFAULT 0,
    priority_level TEXT DEFAULT 'D',
    rank INTEGER,
    next_action TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Business History Trend Table
CREATE TABLE IF NOT EXISTS business_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER,
    rating REAL,
    reviews INTEGER,
    phone TEXT,
    website TEXT,
    website_status TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(business_id) REFERENCES businesses(id)
);

-- 6. Crawl Queue Table with Rate-Limit & Health States
CREATE TABLE IF NOT EXISTS queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    maps_url TEXT UNIQUE,
    category TEXT,
    location TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'queued', 'running', 'retry', 'cooling_down', 'rate_limited', 'blocked', 'recovered', 'completed', 'skipped', 'failed'
    retry_count INTEGER DEFAULT 0,
    worker_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Session Audit & Worker Health Table
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE,
    category TEXT,
    location TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_seconds INTEGER DEFAULT 0,
    browser_version TEXT,
    worker_count INTEGER DEFAULT 4,
    businesses_found INTEGER DEFAULT 0,
    duplicates INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    avg_speed REAL DEFAULT 0.0
);

-- 8. Granular Item-Level Resume State Table
CREATE TABLE IF NOT EXISTS resume_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    location TEXT,
    business_index INTEGER DEFAULT 0,
    maps_url TEXT UNIQUE,
    status TEXT DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'skipped'
    worker_id TEXT,
    attempt_count INTEGER DEFAULT 1,
    last_error TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Contacts Table
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER,
    type TEXT, -- 'email', 'phone', 'whatsapp'
    value TEXT,
    status TEXT, -- 'valid', 'invalid', 'third_party'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(business_id) REFERENCES businesses(id)
);

-- 10. Social Links Table
CREATE TABLE IF NOT EXISTS social_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER,
    platform TEXT, -- 'facebook', 'instagram', 'linkedin', 'twitter'
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(business_id) REFERENCES businesses(id)
);

-- 11. Application Audit Logs Table
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module TEXT, -- 'scraper', 'website', 'database', 'errors'
    level TEXT, -- 'INFO', 'WARNING', 'ERROR', 'CHECKPOINT'
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for high performance querying
CREATE INDEX IF NOT EXISTS idx_businesses_maps_link ON businesses(google_maps_link);
CREATE INDEX IF NOT EXISTS idx_businesses_phone ON businesses(phone);
CREATE INDEX IF NOT EXISTS idx_businesses_priority ON businesses(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_businesses_cat_loc ON businesses(category, location);
CREATE INDEX IF NOT EXISTS idx_queue_status ON queue(status);
CREATE INDEX IF NOT EXISTS idx_resume_cat_loc ON resume_state(category, location);
CREATE INDEX IF NOT EXISTS idx_resume_status ON resume_state(status);
