CREATE TABLE IF NOT EXISTS items (
    serial TEXT PRIMARY KEY,
    product TEXT NOT NULL,
    batch TEXT NOT NULL,
    mfg TEXT NOT NULL,
    nonce TEXT NOT NULL,
    message TEXT NOT NULL,
    signature TEXT NOT NULL,
    qr_path TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial TEXT NOT NULL,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
    device TEXT,
    meta TEXT,
    similarity REAL,
    visual_flag INTEGER DEFAULT 0,
    phash_distance INTEGER,
    orb_ratio REAL,
    FOREIGN KEY (serial) REFERENCES items (serial)
);

CREATE INDEX IF NOT EXISTS idx_scans_serial ON scans(serial);
CREATE INDEX IF NOT EXISTS idx_scans_ts ON scans(ts);