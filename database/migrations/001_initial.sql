-- Migration 001: Initial v2.0 Enterprise Database Setup
INSERT OR IGNORE INTO version (schema_version) VALUES ('2.0.0');

INSERT OR REPLACE INTO settings (key, value) VALUES ('MAX_WORKERS', '4');
INSERT OR REPLACE INTO settings (key, value) VALUES ('RUN_MODE', 'timed');
INSERT OR REPLACE INTO settings (key, value) VALUES ('CHECKPOINT_MINUTES', '45');
INSERT OR REPLACE INTO settings (key, value) VALUES ('EXPORT_PROFILE', 'Full');
