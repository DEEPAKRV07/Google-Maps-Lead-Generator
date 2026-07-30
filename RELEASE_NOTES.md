# 🚀 Release v1.0.0 — Google Maps Lead Generator

We are proud to announce the **v1.0.0 official release** of **Google-Maps-Lead-Generator**!

---

## 🌟 What's New in v1.0.0

### 1. 🛡️ Timed Sessions & Resumable Checkpoints
- **45-Minute Session Limit (`RUN_MODE = "timed"`)**: Auto-stops after 45 minutes to prevent browser DOM slowdowns or Google Maps rate-limits.
- **`progress.json` State File**: Remembers every completed search batch and processed Maps URL. Resume anytime with zero lost data or duplicates.

### 2. ⚡ Atomic File Writes & Backup Rotation
- **Atomic Renaming (`.tmp.xlsx` → `os.replace`)**: All Excel outputs (`all_leads.xlsx`, `failed_leads.xlsx`, `duplicates.xlsx`, `summary.xlsx`) are written atomically to prevent file corruption if interrupted.
- **Timestamped Rolling Backups (`backups/`)**: Automatically saves rolling backups before every checkpoint, maintaining the 10 latest sets.

### 3. 🔍 Smart Contact Extraction & Strict Validation
- **Subpage Email Crawler**: Automatically inspects `/contact`, `/contact-us`, `/about`, and `/privacy` subpages.
- **Strict Email Filter**: Rejects non-business placeholders (`example.com`), error tracking pixels (`@sentry.io`, `@wixpress.com`), and malformed strings.
- **Social Profile Disambiguation**: Moves Instagram/Facebook links out of official website columns into dedicated social columns.

### 4. 📊 Rich Data Analytics & Prioritization
- **Lead Priority Matrix**: Rates leads as `High` (Phone + Website + Email), `Medium`, or `Low`.
- **Entity Classification**: Categorizes leads into `Chain Store`, `Corporate`, `Franchise`, `Local Shop`, or `Unknown`.
- **Live Console Monitor**: Shows real-time speed (`biz/min`) and estimated batch finish time (`ETA`).

---

## 📥 Installation

```bash
git clone https://github.com/DEEPAKRV07/Google-Maps-Lead-Generator.git
cd Google-Maps-Lead-Generator
pip install -r requirements.txt
playwright install chromium
python lead_generator.py
```
