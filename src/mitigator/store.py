import sqlite3, csv
from pathlib import Path
from typing import Dict, Any
from mitigator.dedupe import entity_key, merge_rows

def db_init(db_path: str):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS companies (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source TEXT, source_id TEXT,
      name TEXT, phone TEXT, website TEXT, address TEXT,
      lat REAL, lng REAL, categories TEXT,
      rating REAL, review_count INTEGER,
      license_number TEXT, license_status TEXT, years_in_business INTEGER,
      permits_24mo INTEGER,
      score REAL, last_seen TEXT,
      entity_key TEXT
    );
    """)
    # Add entity_key if it was missing (older DBs)
    cols = {c[1] for c in cur.execute("PRAGMA table_info(companies)").fetchall()}
    if "entity_key" not in cols:
        cur.execute("ALTER TABLE companies ADD COLUMN entity_key TEXT;")
    # Unique index for dedupe
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_entity_key ON companies(entity_key)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_source ON companies(source, source_id)")
    con.commit(); con.close()

def upsert_company(db_path: str, row: Dict[str, Any]):
    ek = entity_key(row)
    if not ek:
        # fallback: insert as-is; no key -> cannot upsert
        _insert(db_path, row | {"entity_key": None})
        return

    con = sqlite3.connect(db_path); cur = con.cursor()
    cur.execute("SELECT rowid, * FROM companies WHERE entity_key = ?", (ek,))
    hit = cur.fetchone()
    if not hit:
        _insert(db_path, row | {"entity_key": ek}, con, cur)
        con.commit(); con.close(); return

    # Build dict from existing row (column order from PRAGMA)
    cols = [c[1] for c in cur.execute("PRAGMA table_info(companies)").fetchall()]
    existing = dict(zip(cols, hit[1:]))  # skip rowid
    merged = merge_rows(existing, row | {"entity_key": ek})

    # Update merged fields
    sets = ", ".join([f"{k}=?" for k in merged.keys()])
    vals = list(merged.values()) + [existing["id"]]
    cur.execute(f"UPDATE companies SET {sets} WHERE id = ?", vals)
    con.commit(); con.close()

def _insert(db_path: str, row: Dict[str, Any], con=None, cur=None):
    owned = False
    if con is None:
        con = sqlite3.connect(db_path); cur = con.cursor(); owned = True
    cols = ",".join(row.keys())
    qmarks = ",".join(["?"] * len(row))
    cur.execute(f"INSERT OR IGNORE INTO companies ({cols}) VALUES ({qmarks})", list(row.values())) # type: ignore
    if owned:
        con.commit(); con.close()

def export_csv(db_path: str, csv_out: str):
    con = sqlite3.connect(db_path); cur = con.cursor()
    cols = [c[1] for c in cur.execute("PRAGMA table_info(companies);").fetchall()]
    rows = cur.execute("SELECT * FROM companies").fetchall()
    Path(csv_out).parent.mkdir(parents=True, exist_ok=True)
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols); w.writerows(rows)
    con.close()
