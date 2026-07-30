# Changelog

All notable changes to the **Google Maps Lead Generator** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-30

### Added
- **Single-File Playwright Scraper**: Core Google Maps scraper in `lead_generator.py` with zero paid API dependencies.
- **Configurable Inputs**: External file loaders for `categories.txt` (67 categories) and `locations.txt` (18 target regions).
- **Timed Session & Safe Checkpointing**: Auto-stop after 45 minutes with `RUN_MODE = "timed"` and zero data loss.
- **Atomic File Writes**: All Excel and JSON file writes perform atomic `.tmp.xlsx` / `.tmp` renaming (`os.replace`) to prevent corruption.
- **Auto Backup Rotation**: Timestamped backups saved into `backups/` maintaining the 10 latest rolling sets.
- **Strict Email Validation Filter**: Automatic rejection of placeholders (`example.com`), tracking pixels (`sentry.io`, `wixpress.com`), and malformed strings.
- **Subpage Email Crawling**: Crawls `/contact`, `/contact-us`, `/about`, `/privacy` when no email is found on the homepage.
- **Website & Social Profile Separation**: Distinguishes official websites from Instagram/Facebook profiles.
- **Lead Priority & Audit Columns**: `Priority` (`High`, `Medium`, `Low`), `Business Type`, `Source Category`, `Search Location`, `Last Verified`.
- **Multi-File Exports**: `outputs/all_leads.xlsx`, `outputs/failed_leads.xlsx`, `outputs/duplicates.xlsx`, `outputs/summary.xlsx`, `outputs/leads.txt`.
- **Live Speed & ETA Monitor**: Console output showing businesses/minute speed and estimated time remaining.
