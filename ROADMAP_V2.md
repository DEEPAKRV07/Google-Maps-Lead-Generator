# 🚀 Google-Maps-Lead-Generator v2.0 Enterprise Roadmap

This document outlines the architectural specifications, Git branching strategy, and prioritized development roadmap for **v2.0 Enterprise Release** of **Google-Maps-Lead-Generator**.

---

## 🏛️ Refined Git Branching & Integration Strategy

To ensure zero risk to stable code and prevent unvalidated features from blocking integration, features are built in isolated feature branches and merged into `feature/v2-enterprise` only after full validation.

```text
main (v1.0.0 Stable Production Tagged)
│
├── feature/v2-database      (Priority 1: SQLite Storage Engine)
├── feature/v2-multithread   (Priority 2: Worker Queue & Multithreaded Crawling)
├── feature/v2-resume        (Priority 3: Granular Item-Level Resume Engine)
├── feature/v2-antidetect    (Priority 4: Adaptive Delay & Fingerprint Engine)
├── feature/v2-dashboard     (Priority 5: Dashboard & Analytics Reports)
├── feature/v2-ai-analysis   (Priority 6: AI Website Pitch & Need Analysis for FORCRUX)
└── feature/v2-proxy         (Priority 7: Optional Proxy Rotation Pool)
        │
        ▼ (Merge Tested Features)
  feature/v2-enterprise (v2.0 Integration Workspace)
        │
        ▼ (After End-to-End Validation)
      main → v2.0.0
```

---

## ⚡ Decoupled Single-Browser + Multi-Worker Queue Architecture

To maximize speed without increasing Google Maps rate-limiting risks, v2.0 decouples map harvesting from website contact crawling:

```text
       ┌────────────────────────┐
       │ Chromium Browser       │
       │ (Google Maps Search)   │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ Place URL Collector    │
       └───────────┬────────────┘
                   │
                   ▼
         ─────── Queue ───────
                   │
       ┌───────────┼───────────┬───────────┐
       ▼           ▼           ▼           ▼
   Worker 1    Worker 2    Worker 3    Worker 4
   (Website)   (Website)   (Website)   (Website)
       │           │           │           │
       └───────────┼───────────┴───────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ SQLite Database Engine │
       │     (db.sqlite3)       │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ Excel / CRM Exporters  │
       └────────────────────────┘
```

---

## 🎯 Prioritized Implementation Order

### 1. SQLite Storage Engine (`feature/v2-database`) ⭐⭐⭐⭐⭐
- Replaces heavy JSON/in-memory data structures with `db.sqlite3`.
- Provides indexed, instant searches, transactional atomic saves, and zero-RAM footprint for millions of leads.
- Excel and CSV files become export targets generated on demand.

### 2. Multithreaded Website Enrichment & Worker Queue (`feature/v2-multithread`) ⭐⭐⭐⭐⭐
- Decouples browser map scraping from website contact crawling.
- Uses `concurrent.futures.ThreadPoolExecutor(max_workers=10)` for 2×–4× faster email & social profile extraction.

### 3. Granular Item-Level Resume Engine (`feature/v2-resume`) ⭐⭐⭐⭐☆
- Saves checkpoint state down to individual business items: `Category → Location → Business Index → Crawl State`.
- Interruption at Business #357 resumes instantly at Business #358.

### 4. Adaptive Delay & Anti-Detection Engine (`feature/v2-antidetect`) ⭐⭐⭐⭐☆
- Dynamic delay engine that adjusts pacing based on response latency and captcha challenges.
- Randomizes viewports, user agents, mouse trajectories, scroll velocities, and idle times.

### 5. Dashboard & Analytics Reports (`feature/v2-dashboard`) ⭐⭐⭐⭐☆
- Generates `Dashboard.xlsx` with embedded KPI charts, location heatmaps, category breakdown tables, and lead quality metrics.

### 6. AI Lead Need & Pitch Analysis for FORCRUX (`feature/v2-ai-analysis`) ⭐⭐⭐☆☆
- Analyzes scraped website content to automatically detect service gaps (e.g. missing SEO, outdated UI, lack of chatbot, slow load speed) and generates tailored outreach pitches for FORCRUX.

### 7. Optional Proxy Rotation Pool (`feature/v2-proxy`) ⭐⭐☆☆☆
- Supports residential & datacenter proxy pools with auto-rotation, ban detection, exponential backoff, and automatic retry loops (disabled by default).

---

## 📄 License & Release Plan

- **v1.0.0**: Tagged on `main` branch.
- **v2.0.0**: To be released after `feature/v2-enterprise` completes integration testing.
