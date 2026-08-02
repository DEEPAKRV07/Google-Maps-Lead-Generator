# 🚀 Google-Maps-Lead-Generator v2.0 Enterprise Master Architecture & Roadmap

This document outlines the final, production-ready master architecture, data collection pipeline, normalized SQLite schema, structured logging hierarchy, provider plugin framework, and prioritized feature roadmap for **v2.0 Enterprise Release** of **Google-Maps-Lead-Generator**.

---

## 🏛️ Git Branching & Integration Strategy

`feature/v2-enterprise` functions strictly as the **Integration & Staging Branch**. Individual feature branches branch off `main`, are independently tested, and merge into `feature/v2-enterprise` before final validation into `main`.

```text
main (v1.0.0 Stable Production Tagged & Frozen)
│
├── feature/v2-database      (Priority 1: SQLite Storage Engine & Schema) ◄── ACTIVE BRANCH
├── feature/v2-resume        (Priority 2: Granular Item-Level Resume Engine)
├── feature/v2-multithread   (Priority 3: Worker Queue & Parallel Crawling)
├── feature/v2-dashboard     (Priority 4: Dashboard & SQLite Analytics)
├── feature/v2-antidetect    (Priority 5: Adaptive Delay & Fingerprint Engine)
├── feature/v2-proxy         (Priority 6: Optional Proxy Rotation Pool)
└── feature/v2-ai-analysis   (Priority 7: AI Lead Need & Pitch Analysis for FORCRUX)
        │
        ▼ (Merge Tested Feature Branches)
  feature/v2-enterprise (v2.0 Integration Workspace)
        │
        ▼ (After End-to-End Validation)
      main → v2.0.0
```

---

## ⚡ Master Data Collection & Processing Pipeline

```text
Google Maps (Single Chromium Browser)
      │
      ▼
Playwright Harvester & URL Collector
      │
      ▼
SQLite Queue Engine (database/db.sqlite3)
(States: Pending, Queued, Running, Retry, Completed, Skipped, Failed)
      │
      ├──────────────┐
      ▼              ▼
  Worker 1        Worker 2
      ▼              ▼
  Worker 3        Worker 4  (Parallel Website Extractors, MAX_WORKERS=min(4, cpu_count))
      │
      ▼
Raw Businesses Storage (RawBusinesses Table)
      │
      ▼
Business Validator Engine (Normalizes Phones, Emails, Ratings, Reviews, URLs)
      │
      ▼
SQLite Master Database (Businesses & BusinessHistory Tables - Source of Truth)
      │
      ├───────────────────────────────┬──────────────────────────────┐
      │                               │                              │
      ▼                               ▼                              ▼
Prioritizer Engine            Dashboard Engine              Export Engine
(Scoring & Ranking)        (Excel & HTML Dashboard)    (Profiles: Full, Sales, CRM)
      │                               │                              │
      └───────────────────────────────┴──────────────────────────────┘
                                      │
                                      ▼
                      Outputs Directory (outputs/)
                      ├── outputs/YYYY-MM-DD/ (Historical Snapshot Archive)
                      ├── all_leads.xlsx
                      ├── all_leads_prioritized.xlsx
                      ├── top_25_leads.xlsx
                      ├── top_50_leads.xlsx
                      ├── top_100_leads.xlsx
                      ├── summary.xlsx
                      ├── dashboard.html
                      ├── duplicates.xlsx
                      ├── failed_leads.xlsx
                      ├── leads.txt
                      └── CRM_Exports/ (HubSpot, Zoho, Salesforce)
```

---

## 💾 Storage & Output Policy

| Component | Role & Function |
|---|---|
| **SQLite (`database/db.sqlite3`)** | ⭐ **Master Source of Truth** for all raw/processed leads, queues, resume states, metrics, and audit logs |
| **Emergency Backup (`progress.json`)** | 🛡️ **Disaster Recovery Backup** kept alongside SQLite for fallback restoration |
| **Database Snapshots (`database/backups/`)** | 📸 **Database Rolling Snapshots** (`db_YYYYMMDD.sqlite`) generated periodically |
| **Excel Exports (`outputs/*.xlsx`)** | 📊 **User-Friendly Spreadsheets** generated automatically on demand or at checkpoints |
| **Historical Archive (`outputs/YYYY-MM-DD/`)** | 📁 **Timestamped Archive** preserving historical run snapshots without overwriting |
| **HTML Dashboard (`outputs/dashboard.html`)** | 🌐 **Browser Dashboard** opening in any browser without requiring Microsoft Excel |
| **TXT Export (`outputs/leads.txt`)** | 📝 **Plain Text Export** formatted for quick manual reading |
| **Priority Exports (`top_N_leads.xlsx`)** | 🎯 **Sales-Ready Targets** sorted by score, level, and next action |
| **Categorized Logs (`logs/*/*.log`)** | 🪵 **Audit Trail** separated into `scraper/`, `website/`, `database/`, and `errors/` |

---

## 📁 Directory & Provider Plugin Architecture

```text
Google-Maps-Lead-Generator/
│
├── lead_generator.py          # Main scraper runner (zero user workflow change)
├── prioritizer.py             # Lead prioritization post-processor
├── validator.py               # Data validator & normalization engine
├── config.py                  # System constants & MAX_WORKERS pool logic
│
├── database/                  # Master Database Directory
│   ├── db.sqlite3             # SQLite master database file
│   ├── schema.sql             # DDL schema definition script
│   ├── migrations/            # Version tracking & schema migration scripts
│   └── backups/               # Database snapshot backups (db_YYYYMMDD.sqlite)
│
├── providers/                 # Plugin Provider Architecture
│   ├── base_provider.py       # Abstract base provider interface
│   ├── google_maps/           # Google Maps modular plugin
│   │   ├── search.py
│   │   ├── extract.py
│   │   ├── selectors.py
│   │   └── utils.py
│   ├── openstreetmap/         # OpenStreetMap modular plugin
│   ├── bing_maps/             # Bing Maps modular plugin
│   ├── justdial/              # JustDial modular plugin
│   ├── indiamart/             # IndiaMart modular plugin
│   └── sulekha/               # Sulekha modular plugin
│
├── logs/                      # Sub-Categorized Logging Hierarchy
│   ├── scraper/               # Google Maps navigation & selector logs
│   ├── website/               # Website contact extraction logs
│   ├── database/              # SQLite queries, transactions, & migrations logs
│   └── errors/                # Critical error tracebacks & exception logs
│
├── cache/                     # Cached raw HTML files
├── screenshots/               # Failure & validation screenshots
├── outputs/                   # Export directory (Excel, TXT, HTML, CRM)
│   └── YYYY-MM-DD/            # Timestamped historical export archives
└── progress.json              # Emergency disaster recovery JSON backup
```

---

## 🗄️ Master SQLite Database Schema (`database/schema.sql`)

### 1. `Version` Table
```sql
CREATE TABLE IF NOT EXISTS version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_version TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_migration TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. `RawBusinesses` Table (Raw Unparsed Extracted Data)
```sql
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
```

### 3. `Businesses` Table (Processed Normalized Master Lead Records)
```sql
CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    source_category TEXT,
    category TEXT,
    search_location TEXT,
    location TEXT,
    address TEXT,
    phone TEXT, -- E.164 / normalized clean phone digits
    website TEXT, -- Clean normalized URL
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
```

### 4. `BusinessHistory` Table (Multi-Run Trend Analysis)
```sql
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
```

### 5. `Queue` Table (Crawl Worker Queue)
```sql
CREATE TABLE IF NOT EXISTS queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    maps_url TEXT UNIQUE,
    category TEXT,
    location TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'queued', 'running', 'retry', 'completed', 'skipped', 'failed'
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6. `Sessions` Table (Session Audit Tracking)
```sql
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
```

### 7. `ResumeState` Table (Granular Item-Level Checkpoint)
```sql
CREATE TABLE IF NOT EXISTS resume_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    location TEXT,
    business_index INTEGER DEFAULT 0,
    maps_url TEXT UNIQUE,
    status TEXT DEFAULT 'pending',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 8. `Contacts` Table
```sql
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER,
    type TEXT, -- 'email', 'phone', 'whatsapp'
    value TEXT,
    status TEXT, -- 'valid', 'invalid', 'third_party'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(business_id) REFERENCES businesses(id)
);
```

### 9. `SocialLinks` Table
```sql
CREATE TABLE IF NOT EXISTS social_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER,
    platform TEXT, -- 'facebook', 'instagram', 'linkedin', 'twitter'
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(business_id) REFERENCES businesses(id)
);
```

### 10. `Logs` Table
```sql
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module TEXT, -- 'scraper', 'website', 'database', 'errors'
    level TEXT, -- 'INFO', 'WARNING', 'ERROR', 'CHECKPOINT'
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎯 Prioritized Feature Implementation Roadmap

1. **`feature/v2-database` (Priority #1 - ACTIVE)**:
   - Establish `database/` directory layout, SQLite schema (`database/schema.sql`), version tracker, and database backup engine.
   - Implement `validator.py` data normalization layer (`RawBusinesses` -> `Businesses`).
   - Connect SQLite as master storage while generating all existing Excel and TXT exports seamlessly.
   - Maintain `progress.json` as an emergency fallback backup.

2. **`feature/v2-resume` (Priority #2)**:
   - Implement item-level granular resume (`Category → Location → Business Index → Crawl State`).

3. **`feature/v2-multithread` (Priority #3)**:
   - Decouple Chromium map harvester from website contact extractors using `ThreadPoolExecutor(max_workers=min(4, cpu_count))`.

4. **`feature/v2-dashboard` (Priority #4)**:
   - Generate both `outputs/Dashboard.xlsx` and lightweight `outputs/dashboard.html` for browser-native analytics.

5. **`feature/v2-antidetect` (Priority #5)**:
   - Adaptive delays, anti-detection fingerprinting, and dynamic pacing.

6. **`feature/v2-proxy` (Priority #6)**:
   - Optional proxy rotation pool (`PROXY_ENABLED = False` default).

7. **`feature/v2-ai-analysis` (Priority #7)**:
   - FORCRUX AI Website Need & Pitch Generator with explainable confidence scores and gap reasons.

---

## 📄 License & Release Plan

- **v1.0.0**: Tagged on `main` branch.
- **v2.0.0**: To be released after `feature/v2-enterprise` completes integration testing.
