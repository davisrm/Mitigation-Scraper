# src/mitigator/scripts/enrich_emails.py
import os, sqlite3, time
from datetime import date
from mitigator.email_extract import extract_emails
from mitigator.config import DB_PATH

MAX_PAGES = int(os.getenv("EMAIL_MAX_PAGES", "5"))
SLEEP_S   = float(os.getenv("EMAIL_SLEEP_S", "0.25"))
LIMIT     = int(os.getenv("EMAIL_LIMIT", "200"))  # cap per run

def main():
    con = sqlite3.connect(DB_PATH); cur = con.cursor()
    rows = cur.execute("""
      SELECT id, website FROM companies
      WHERE (email IS NULL OR email = '')
        AND website IS NOT NULL AND website <> ''
      LIMIT ?
    """, (LIMIT,)).fetchall()

    updated = 0
    for cid, site in rows:
        emails = extract_emails(site, max_pages=MAX_PAGES, sleep_s=SLEEP_S)
        print(emails)
        if not emails:
            continue
        # pick best (first sorted by confidence)
        e, conf, src = emails[0]
        cur.execute("""
          UPDATE companies
          SET email = ?, email_confidence = ?, email_source = ?, email_last_seen = ?
          WHERE id = ?
        """, (e, conf, src, date.today().isoformat(), cid))
        updated += 1
        # mild pacing between domains
        time.sleep(0.1)
    con.commit(); con.close()
    print(f"Email enrichment updated {updated} companies.")

if __name__ == "__main__":
    main()
