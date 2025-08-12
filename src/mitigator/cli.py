from mitigator.config import GOOGLE_KEY, YELP_KEY, DB_PATH, CSV_OUT, KEYWORDS, SERVICE_AREAS
from mitigator.collect.google_collect import google_text_search
from mitigator.collect.yelp_collect import yelp_text_search
from mitigator.score import compute_scores
from mitigator.store import db_init, upsert_company, export_csv

def main():
    if not (GOOGLE_KEY or YELP_KEY):
        raise SystemExit("Missing GOOGLE_PLACES_KEY or YELP_FUSION_KEY in .env")

    db_init(DB_PATH)
    all_rows = []
    for loc in SERVICE_AREAS:
        for kw in KEYWORDS:
            if GOOGLE_KEY:
                for r in google_text_search(GOOGLE_KEY, kw, loc):
                    upsert_company(DB_PATH, r); all_rows.append(r)
            if YELP_KEY:
                for r in yelp_text_search(YELP_KEY, kw, loc):
                    upsert_company(DB_PATH, r); all_rows.append(r)

    compute_scores(all_rows)

    import sqlite3
    con = sqlite3.connect(DB_PATH); cur = con.cursor()
    for r in all_rows:
        cur.execute("UPDATE companies SET score=? WHERE source=? AND source_id=?",
                    (r["score"], r["source"], r["source_id"]))
    con.commit(); con.close()

    export_csv(DB_PATH, CSV_OUT)
    print(f"Done. Saved {len(all_rows)} rows.")
    
if __name__ == "__main__":
    main()
