# 🚀 Google-Maps-Lead-Generator v2.0 Enterprise Roadmap

This document outlines the final architectural specifications, normalized SQLite schema, structured logging model, and prioritized feature roadmap for **v2.0 Enterprise Release** of **Google-Maps-Lead-Generator**.

---

## 🏛️ Final Git Branching & Integration Strategy

`feature/v2-enterprise` functions strictly as the **Integration & Staging Branch**. Individual feature branches are built independently, thoroughly tested, and merged into `feature/v2-enterprise` before final validation into `main`.

```text
main (v1.0.0 Stable Production Tagged & Frozen)
│
├── feature/v2-database      (Priority 1: SQLite Storage Engine)  ◄── ACTIVE BRANCH
├── feature/v2-resume        (Priority 2: Granular Item-Level Resume Engine)
├── feature/v2-multithread   (Priority 3: Worker Queue & Multithreaded Crawling)
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

## ⚡ Final Pipeline Architecture

```text
Google Maps
      │
      ▼
Single Browser (Chromium Harvester)
      │
      ▼
URL Collector
      │
      ▼
SQLite Queue Engine
      │
      ├──────────────┐
      ▼              ▼
  Worker 1        Worker 2
      ▼              ▼
  Worker 3        Worker 4  (Parallel Website Contact Extractors)
      │
      ▼
SQLite Master Database (db.sqlite3 - Source of Truth)
      │
      ├── Excel Export (all_leads.xlsx)
      ├── TXT Export (leads.txt)
      ├── CRM Exporters (HubSpot, Zoho, Salesforce)
      ├── Dashboard (Dashboard.xlsx)
      └── Lead Prioritizer Engine
```

---

## 🗄️ Normalized SQLite Database Schema (`db.sqlite3`)

SQLite serves as the **single source of truth** for all lead records, resume states, metrics, and event logs.

### 1. `Businesses` Table
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

### 2. `Contacts` Table
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

### 3. `SocialLinks` Table
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

### 4. `ResumeState` Table
```sql
CREATE TABLE IF NOT EXISTS resume_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    location TEXT,
    business_index INTEGER DEFAULT 0,
    maps_url TEXT UNIQUE,
    status TEXT, -- 'pending', 'crawled', 'failed', 'completed'
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. `Statistics` Table
```sql
CREATE TABLE IF NOT EXISTS statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT UNIQUE,
    metric_value REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6. `Logs` Table
```sql
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT, -- 'INFO', 'WARNING', 'ERROR', 'CHECKPOINT'
    message TEXT,
    category TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📑 Structured Event Logging Framework (`logs/YYYY-MM-DD.log`)

Dedicated daily log files are maintained in `logs/` for production auditing:

```text
[2026-08-02 09:15:00] [INFO] Session initialized. RUN_MODE=timed, MAX_RUNTIME=45m.
[2026-08-02 09:15:02] [INFO] Loaded SQLite Master DB. Total records: 94.
[2026-08-02 09:17:10] [SEARCH] Category: Furniture Store | Location: Chennai, Tamil Nadu.
[2026-08-02 09:35:40] [CHECKPOINT] Item #357 saved to SQLite. 45-minute limit reached.
[2026-08-02 09:35:42] [EXPORT] Generated outputs/all_leads.xlsx from SQLite (94 records).
```

---

## 🎯 Prioritized Feature Implementation Roadmap

### 1. SQLite Master Storage Engine (`feature/v2-database`) ⭐⭐⭐⭐⭐ [ACTIVE]
- Establishes `db.sqlite3` as the single source of truth.
- Implements transactional atomic writes and indexing for zero RAM overhead.
- Excel (`all_leads.xlsx`) and TXT (`leads.txt`) become on-demand export targets.

### 2. Item-Level Granular Resume Engine (`feature/v2-resume`) ⭐⭐⭐⭐☆
- Saves checkpoint state down to individual business items: `Category → Location → Business Index → Crawl State`.
- Interruption at Business #642 resumes at #643.

### 3. Multithreaded Website Enrichment & Worker Queue (`feature/v2-multithread`) ⭐⭐⭐⭐⭐
- Decouples browser map scraping from website contact crawling.
- Single Chromium browser navigates Google Maps; `ThreadPoolExecutor(max_workers=10)` worker queue processes website contact crawling in parallel.

### 4. Dashboard & SQLite Analytics Reports (`feature/v2-dashboard`) ⭐⭐⭐⭐☆
- Generates `outputs/Dashboard.xlsx` with embedded KPI charts, location heatmaps, category breakdown tables, and lead quality metrics derived directly from SQLite.

### 5. Adaptive Delay & Anti-Detection Engine (`feature/v2-antidetect`) ⭐⭐⭐⭐☆
- Dynamic delay engine adjusting pacing based on response latency and captcha challenges.
- Randomizes viewports, user agents, mouse trajectories, scroll velocities, and idle times.

### 6. Optional Proxy Rotation Pool (`feature/v2-proxy`) ⭐⭐☆☆☆
- Supports residential & datacenter proxy pools with auto-rotation, ban detection, exponential backoff, and automatic retry loops (`PROXY_ENABLED = False` by default).

### 7. AI Lead Need & Pitch Analysis for FORCRUX (`feature/v2-ai-analysis`) ⭐⭐⭐☆☆
- Analyzes scraped website content to automatically detect service gaps (e.g. missing SEO, outdated UI, lack of chatbot, slow load speed) and generates tailored outreach pitches for FORCRUX.

---

## 📄 License & Release Plan

- **v1.0.0**: Tagged on `main` branch.
- **v2.0.0**: To be released after `feature/v2-enterprise` completes integration testing.
