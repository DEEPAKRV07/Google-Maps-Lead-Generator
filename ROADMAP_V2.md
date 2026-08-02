# 🚀 Google-Maps-Lead-Generator v2.0 Enterprise Roadmap

This document outlines the architectural specifications and development roadmap for **v2.0 Enterprise Release** of **Google-Maps-Lead-Generator**.

---

## 🏗️ Versioning & Branch Strategy

- **`main` Branch**: Frozen at **`v1.0.0` (Stable Production)**. All existing functionality, scrapers, checkpoints, atomic writers, and prioritization logic remain untouched.
- **`feature/v2-enterprise` Branch**: Isolated development workspace for all v2.0 enterprise upgrades.
- **Release Target**: **`v2.0.0` Enterprise** (to be merged into `main` after complete validation).

---

## 🏛️ v2.0 Architecture Upgrades

```text
                                 ┌─────────────────────────────────┐
                                 │       Unified CLI Engine        │
                                 │     (main.py cli interface)     │
                                 └────────────────┬────────────────┘
                                                  │
                ┌─────────────────────────────────┼─────────────────────────────────┐
                │                                 │                                 │
                ▼                                 ▼                                 ▼
   ┌──────────────────────────┐     ┌──────────────────────────┐      ┌──────────────────────────┐
   │    Multi-Provider Core   │     │ SQLite Database & Engine │      │ Anti-Detection & Proxies │
   │ (Google, OSM, Bing, etc) │     │ (Zero-RAM / Million-Row) │      │ (Rotation Pool & Delays) │
   └────────────┬─────────────┘     └─────────────┬────────────┘      └─────────────┬────────────┘
                │                                 │                                 │
                └─────────────────────────────────┼─────────────────────────────────┘
                                                  │
                                                  ▼
                                   ┌──────────────────────────────┐
                                   │ Multi-Threaded Contact Crawl │
                                   │   (ThreadPoolExecutor x10)   │
                                   └──────────────┬───────────────┘
                                                  │
                                                  ▼
                                   ┌──────────────────────────────┐
                                   │ AI Need Analysis & Scoring   │
                                   │ (FORCRUX Pitch Engine & CRM) │
                                   └──────────────────────────────┘
```

---

## ⚡ Key Upgrade Specifications

### 1. SQLite Enterprise Storage Engine (`db.sqlite3`)
- Replaces heavy JSON/in-memory array storage for handling millions of leads seamlessly.
- Provides indexed, instant searches, transactional atomic checkpoints, and zero-RAM footprint.
- Excel and CSV files become export targets generated on demand.

### 2. Plug-and-Play Multi-Provider Framework
- Extensible scraper plugins for:
  - Google Maps
  - OpenStreetMap (Overpass API)
  - Bing Maps
  - JustDial / Sulekha / IndiaMart
  - Facebook Business Pages
  - Direct Website Crawlers
  - YellowPages

### 3. Granular Business-Level Resume Engine
- Saves resume state down to individual business indices: `Category → Location → Business Index → Crawl State`.
- Interruptions at Business #357 resume instantly at Business #358.

### 4. Multi-Threaded Website Contact Extraction
- Decouples browser map scraping from website contact crawling.
- Uses `concurrent.futures.ThreadPoolExecutor(max_workers=10)` for 2×–4× faster email & social profile extraction.

### 5. Advanced Proxy & Rotation Manager
- Supports residential & datacenter proxy pools with auto-rotation, ban detection, exponential backoff, and automatic retry loops.

### 6. Adaptive Delay & Fingerprint Engine
- Dynamic delay engine that adjusts pacing based on response latency and captcha challenges.
- Randomizes viewports, user agents, mouse trajectories, scroll velocities, and idle times.

### 7. Smart Fuzzy Deduplication
- Multi-dimensional fuzzy matching combining Levenshtein name similarity, normalized address hashing, and phone/domain unification.

### 8. Multi-Dimensional Contact Quality & Trust Scores
- Replaces basic score with granular metrics: `Website Quality`, `Email Trust`, `Phone Trust`, `Social Trust`, `Reputation Score`, and `Sales Opportunity Score`.

### 9. AI Website Pitch & Need Analysis Engine
- Analyzes scraped website content to automatically detect service gaps (e.g. missing SEO, outdated UI, lack of chatbot, slow load speed) and generates tailored outreach pitches for FORCRUX.

### 10. Enterprise CLI Suite (`main.py`)
- Modular command-line interface:
  ```bash
  python main.py scrape --category "Furniture Store" --location "Chennai"
  python main.py prioritize
  python main.py export --format excel,csv,hubspot,zoho
  python main.py dashboard
  python main.py verify
  ```

### 11. Multi-CRM Ready Exporters
- Direct formatting and schema export for **HubSpot**, **Zoho CRM**, **Salesforce**, CSV, and SQLite DB dumps.

---

## 🛠️ Feature Branch Strategy

- `feature/v2-enterprise` (Master v2 branch)
  - `feature/v2-database` (SQLite implementation)
  - `feature/v2-multithread` (Async contact crawler)
  - `feature/v2-cli` (Command line suite)
  - `feature/v2-ai-analysis` (AI pitch generator)

All features will be thoroughly tested in isolation before merging into `feature/v2-enterprise` and tagging `v2.0.0`.
