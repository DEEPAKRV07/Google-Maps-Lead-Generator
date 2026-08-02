# 🚀 Google-Maps-Lead-Generator v2.0 Enterprise Roadmap

This document outlines the master architectural specifications, database directory layout, schema migration model, structured logging hierarchy, provider plugin framework, and prioritized feature roadmap for **v2.0 Enterprise Release** of **Google-Maps-Lead-Generator**.

---

## 🏛️ Git Branching & Integration Strategy

`feature/v2-enterprise` functions strictly as the **Integration & Staging Branch**. Individual feature branches branch off `main`, are independently tested, and merge into `feature/v2-enterprise` before final validation into `main`.

```text
main (v1.0.0 Stable Production Tagged & Frozen)
│
├── feature/v2-database      (Priority 1: SQLite Storage Engine & Database Layout) ◄── ACTIVE BRANCH
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

## ⚡ Master Data Pipeline Architecture

SQLite (`database/db.sqlite3`) operates as the **master source of truth**. All user-facing Excel, TXT, CRM, and HTML reports are generated automatically as high-speed snapshots from SQLite.

```text
Google Maps (Single Chromium Browser)
      │
      ▼
Playwright Scraper / URL Collector
      │
      ▼
SQLite Queue Engine (database/db.sqlite3)
      │
      ├──────────────┐
      ▼              ▼
  Worker 1        Worker 2
      ▼              ▼
  Worker 3        Worker 4  (Parallel Website Contact Extractors, MAX_WORKERS=4)
      │
      ▼
SQLite Master Database (database/db.sqlite3 - Master Source of Truth)
      │
      ├───────────────────────────────┬──────────────────────────────┐
      │                               │                              │
      ▼                               ▼                              ▼
Prioritizer Engine            Dashboard Engine              Export Engine
(Scoring & Ranking)        (Excel & HTML Dashboard)     (On-Demand / Checkpoints)
      │                               │                              │
      └───────────────────────────────┴──────────────────────────────┘
                                      │
                                      ▼
                      Outputs Directory (outputs/)
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

## 💾 Storage & Recovery Policy

| Component | Role & Function |
|---|---|
| **SQLite (`database/db.sqlite3`)** | ⭐ **Master Data Source of Truth** for all records, queue items, resume state, and metrics |
| **Emergency Backup (`progress.json`)** | 🛡️ **Disaster Recovery Backup** kept alongside SQLite for fallback restoration |
| **Excel Exports (`outputs/*.xlsx`)** | 📊 **User-Friendly Spreadsheets** generated automatically on demand or at checkpoints |
| **HTML Dashboard (`outputs/dashboard.html`)** | 🌐 **Browser Dashboard** opening in any browser without requiring Microsoft Excel |
| **TXT Export (`outputs/leads.txt`)** | 📝 **Plain Text Export** formatted for quick manual reading |
| **Priority Exports (`top_N_leads.xlsx`)** | 🎯 **Sales-Ready Targets** sorted by score, level, and next action |
| **Categorized Logs (`logs/*/*.log`)** | 🪵 **Audit Trail** separated into scraper, website, database, and error logs |

---

## 📁 Modular Directory Layout

```text
Google-Maps-Lead-Generator/
│
├── lead_generator.py          # Main scraper runner
├── prioritizer.py             # Lead prioritization post-processor
├── config.py                  # System constants & pool parameters
│
├── database/                  # Master Database Directory
│   ├── db.sqlite3             # SQLite master database file
│   ├── schema.sql             # DDL schema definition script
│   ├── migrations/            # Schema version evolution scripts (v2.0 -> v2.1 -> v2.2)
│   └── backups/               # Database snapshot backups
│
├── providers/                 # Plugin Provider Architecture
│   ├── base_provider.py       # Abstract base provider interface
│   ├── google_maps.py         # Google Maps plugin
│   ├── openstreetmap.py       # OpenStreetMap plugin
│   ├── bing_maps.py           # Bing Maps plugin
│   ├── justdial.py            # JustDial plugin
│   ├── indiamart.py           # IndiaMart plugin
│   └── sulekha.py             # Sulekha plugin
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
└── progress.json              # Emergency disaster recovery JSON backup
```

---

## 🗄️ Master SQLite Database Schema (`database/schema.sql`)

### 1. `Version` Table (Migration Tracker)
```sql
CREATE TABLE IF NOT EXISTS version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_version TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_migration TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. `Businesses` Table (Master Lead Records)
```sql
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
```

### 3. `Queue` Table (Crawl Worker Queue)
```sql
CREATE TABLE IF NOT EXISTS queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    maps_url TEXT UNIQUE,
    category TEXT,
    location TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. `Sessions` Table (Structured Session Statistics)
```sql
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE,
    category TEXT,
    location TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    businesses_found INTEGER DEFAULT 0,
    duplicates INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,
    avg_speed REAL DEFAULT 0.0
);
```

### 5. `ResumeState` Table (Granular Item-Level Checkpoint)
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

### 6. `Contacts` Table
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

### 7. `SocialLinks` Table
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

### 8. `Logs` Table
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

## 🎯 Prioritized Feature Implementation Sequence

1. **`feature/v2-database` (Priority #1 - ACTIVE)**:
   - Establish `database/` directory layout, SQLite schema (`database/schema.sql`), and version tracking.
   - Connect SQLite as master storage while generating all existing Excel and TXT exports seamlessly.
   - Maintain `progress.json` as an emergency fallback backup.

2. **`feature/v2-resume` (Priority #2)**:
   - Implement item-level granular resume (`Category → Location → Business Index → Crawl State`).
   - Interruption at Business #642 resumes at #643.

3. **`feature/v2-multithread` (Priority #3)**:
   - Decouple Chromium map harvester from website contact extractors using `ThreadPoolExecutor(max_workers=4)`.

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
