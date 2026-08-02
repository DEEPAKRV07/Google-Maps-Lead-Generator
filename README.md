# 🚀 Google-Maps-Lead-Generator v2.0.0 Enterprise Lead Platform

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-v1.40%2B-green.svg)](https://playwright.dev/python/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%203-003B57.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release: v2.0.0](https://img.shields.io/badge/Release-v2.0.0-brightgreen.svg)](https://github.com/DEEPAKRV07/Google-Maps-Lead-Generator/releases/tag/v2.0.0)

**Google-Maps-Lead-Generator** is a production-grade, enterprise-scale business lead generation, prioritization, and intelligence platform. Built on Playwright, SQLite Master DB, multithreaded contact crawlers, and AI digital gap analysis engines, it harvests Google Maps businesses and enriches them with contact details, priority scores, dual HTML/Excel dashboards, and multi-CRM export formats.

---

## 🌟 Key Platform Features

- **Single-Command Automated Pipeline**: Running `python lead_generator.py` executes scraping, database persistence, website contact extraction, prioritization, dashboards, CRM exports, and AI analysis automatically in a single command.
- **SQLite Master Source of Truth (`database/db.sqlite3`)**: Zero-RAM relational database storing raw/processed leads, queue states, session audits, and business history trends.
- **Granular Item-Level Resume**: Resumes interruptions at the exact business item index (`Category → Location → Business Index → Item State`).
- **Multithreaded Website Enrichment (`website_crawler.py`)**: `ThreadPoolExecutor(max_workers=4)` worker queue achieves **2.51× faster** website contact crawling without risking Google Maps rate-limits.
- **Standalone HTML & Excel Dashboards (`outputs/dashboard.html`)**: Modern dark-mode web dashboard opening natively in any browser without needing Microsoft Excel.
- **Multi-CRM Exporters (`crm_exporter.py`)**: Automatic formatting for **HubSpot** (`hubspot_import.csv`), **Zoho CRM** (`zoho_import.csv`), and **Salesforce** (`salesforce_import.csv`).
- **FORCRUX AI Website Need & Pitch Analysis (`ai_analyzer.py`)**: Computes explainable confidence scores, digital gap reasons (missing SSL, outdated UI, no social media), and pitch recommendations in `outputs/ai_lead_pitches.xlsx`.
- **Adaptive Delays & Anti-Detection Fingerprinting (`antidetect.py`)**: User-Agent rotation, viewport randomization, smooth human scroll simulation, and latency-based dynamic pacing.
- **Optional Proxy Manager (`proxy_manager.py`)**: Proxy pool rotation with health checks and cooldowns (`PROXY_ENABLED = False` default).

---

## ⚙️ Project Architecture & Pipeline

```text
Google Maps (Single Chromium Harvester)
      │
      ▼
SQLite Master Database (database/db.sqlite3 - Source of Truth)
      │
      ├── Queue Engine (Pending, Queued, Running, Retry, Completed, Failed)
      ├── Item-Level Granular Resume Engine (resume_state Table)
      ├── Processed Master Leads (Businesses & BusinessHistory Tables)
      │
      ├───────────────────────────────┬──────────────────────────────┐
      │                               │                              │
      ▼                               ▼                              ▼
Prioritizer Engine            Dashboard Engine              Export Engine
(Scoring & Ranking)        (Excel & HTML Dashboard)     (Full, CRM, AI Pitches)
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
                      ├── ai_lead_pitches.xlsx
                      ├── duplicates.xlsx
                      ├── failed_leads.xlsx
                      ├── leads.txt
                      └── CRM_Exports/ (HubSpot, Zoho, Salesforce)
```

---

## 📁 Directory Structure

```text
Google-Maps-Lead-Generator/
│
├── lead_generator.py          # Main automated lead generator runner
├── prioritizer.py             # Post-processing prioritization & sales strategy engine
├── validator.py               # Phone/email/URL data validator & normalizer
├── website_crawler.py         # ThreadPoolExecutor multithreaded contact crawler
├── dashboard.py               # Dual HTML & Excel analytics dashboard generator
├── crm_exporter.py            # HubSpot, Zoho, and Salesforce exporter
├── ai_analyzer.py             # FORCRUX AI website need & pitch analyzer
├── antidetect.py              # User-Agent rotation & adaptive pacing engine
├── proxy_manager.py           # Optional proxy pool & health manager
├── logger.py                  # Sub-categorized daily logging framework
├── config.py                  # Central configuration file
├── categories.txt             # Target business categories file
├── locations.txt              # Target geographic locations file
│
├── database/                  # Master Relational Storage
│   ├── db.sqlite3             # SQLite master database file
│   ├── schema.sql             # DDL relational schema script
│   ├── migrations/            # Version tracking & schema migration scripts
│   └── backups/               # Rolling database snapshot backups
│
├── providers/                 # Plugin Provider Architecture
│   ├── base_provider.py       # Abstract base provider contract
│   ├── google_maps/           # Google Maps plugin & selector registry
│   └── provider_manager.py    # Plugin registry manager
│
├── logs/                      # Sub-Categorized Daily Logs
│   ├── scraper/               # Google Maps navigation & selector logs
│   ├── website/               # Website contact extraction logs
│   ├── database/              # SQLite queries, transactions, & migrations logs
│   └── errors/                # Critical error tracebacks & exception logs
│
├── cache/                     # Cached raw HTML files
├── screenshots/               # Failure & error validation screenshots
├── outputs/                   # Generated reports (Excel, TXT, HTML, CRM, AI)
└── progress.json              # Emergency disaster recovery JSON backup
```

---

## 📦 Installation & Setup

### 1. Clone Repository
```bash
git clone https://github.com/DEEPAKRV07/Google-Maps-Lead-Generator.git
cd Google-Maps-Lead-Generator
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 🚀 Running the Platform

To execute the full automated pipeline, run a single command:

```bash
python lead_generator.py
```

This single command automatically:
1. Initializes SQLite Master DB (`database/db.sqlite3`) and applies migrations.
2. Restores item-level granular resume state.
3. Harvests Google Maps search feeds while skipping duplicate URLs.
4. Crawls business websites concurrently using 4 worker threads.
5. Normalizes phone numbers, emails, ratings, and URLs.
6. Flushes master records to SQLite database.
7. Calculates priority scores, levels (`A+`, `A`, `B`, `C`, `D`), and sales strategies (`Call Business`, `Email First`, `Visit Website`, etc.).
8. Generates all Excel workbooks, plain text files, standalone HTML dashboards, multi-CRM CSVs, and AI pitch reports.
9. Creates rolling SQLite database snapshots in `database/backups/`.

---

## 🔧 Configuration (`config.py`)

All system parameters can be customized in `config.py`:

```python
# WORKER POOL & MULTITHREADING
MAX_WORKERS = min(4, os.cpu_count() or 4) # Dynamic thread pool limit
PROXY_ENABLED = False                    # Set to True to enable proxies from proxies.txt

# TIMED SESSION & CHECKPOINT SETTINGS
RUN_MODE = "timed"                       # Options: "timed" or "continuous"
MAX_RUNTIME_MINUTES = 45                 # Timed session runtime limit (minutes)

# DELAY PACING & SCRAPING
HEADLESS = False                         # Set to True for background execution
RANDOM_DELAY_MIN = 1.0                   # Base minimum delay (seconds)
RANDOM_DELAY_MAX = 2.5                   # Base maximum delay (seconds)
```

---

## 📊 Priority Scoring & Sales Strategy Matrix

Leads are scored dynamically based on contactability and digital authority:

| Lead Category | Point Value | Rationale |
|---|---|---|
| **Valid Email** | +25 pts | High-value direct sales channel |
| **Valid Phone** | +20 pts | Direct phone outreach capability |
| **Valid Website** | +15 pts | Indicates established business entity |
| **WhatsApp Link** | +10 pts | Direct mobile messaging channel |
| **Instagram Profile** | +10 pts | Social engagement presence |
| **Facebook Profile** | +10 pts | Social business presence |
| **LinkedIn Profile** | +10 pts | B2B professional network presence |

### Priority Levels
- **`A+` (Score >= 50)**: Premium sales targets (Dark Green `#1E4620`)
- **`A` (Score 35–49)**: High-priority targets (Soft Green `#C3E6CB`)
- **`B` (Score 20–34)**: Medium-priority targets (Soft Yellow `#FFF3CD`)
- **`C` (Score 10–19)**: Low-priority targets (Soft Orange `#FFE8D6`)
- **`D` (Score < 10)**: Minimal contact targets (Soft Red `#F8D7DA`)

---

## 🎯 Generated Output Files

Running `python lead_generator.py` populates the `outputs/` directory:

| File / Directory | Description |
|---|---|
| **`outputs/all_leads.xlsx`** | Master Excel workbook containing all validated business leads |
| **`outputs/all_leads_prioritized.xlsx`** | Prioritized workbook sorted by Priority Score, Level, and Rank |
| **`outputs/top_25_leads.xlsx`** | Export of Top 25 highest-scoring sales leads |
| **`outputs/top_50_leads.xlsx`** | Export of Top 50 highest-scoring sales leads |
| **`outputs/top_100_leads.xlsx`** | Export of Top 100 highest-scoring sales leads |
| **`outputs/summary.xlsx`** | Performance metrics breakdown + `Priority Analytics` sheet |
| **`outputs/dashboard.html`** | Standalone dark-mode web browser analytics dashboard |
| **`outputs/Dashboard.xlsx`** | Excel dashboard workbook |
| **`outputs/ai_lead_pitches.xlsx`** | FORCRUX AI digital gap analysis & pitch report |
| **`outputs/CRM_Exports/`** | Multi-CRM imports (`hubspot_import.csv`, `zoho_import.csv`, `salesforce_import.csv`) |
| **`outputs/duplicates.xlsx`** | Filtered duplicate records |
| **`outputs/failed_leads.xlsx`** | Failed/unparsed extraction records |
| **`outputs/leads.txt`** | Plain-text reference export |

---

## ❓ Frequently Asked Questions (FAQ)

### Q: How do I add new business categories or search locations?
A: Add category names to `categories.txt` (one per line) and location queries to `locations.txt`.

### Q: Can I safely stop the scraper mid-run?
A: Yes! Press `Ctrl + C` or let the timed runtime finish. The scraper creates a safe checkpoint in SQLite (`database/db.sqlite3`) and resumes at the exact next item on rerun.

### Q: Where is the master database stored?
A: SQLite Master Database is stored at `database/db.sqlite3`. Rolling snapshots are saved under `database/backups/`.

### Q: How do I enable proxy rotation?
A: Add HTTP/HTTPS/SOCKS5 proxy URLs to `proxies.txt` and set `PROXY_ENABLED = True` in `config.py`.

---

## 📄 License & Release Notes

- **Version**: **`v2.0.0` Enterprise Release**
- **Repository**: [https://github.com/DEEPAKRV07/Google-Maps-Lead-Generator](https://github.com/DEEPAKRV07/Google-Maps-Lead-Generator)
- **License**: MIT License
