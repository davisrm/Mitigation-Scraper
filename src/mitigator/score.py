import math
from typing import List, Dict, Any

def compute_scores(rows: List[Dict[str,Any]]):
    permits = [r.get("permits_24mo") or 0 for r in rows]
    years   = [r.get("years_in_business") or 0 for r in rows]
    max_p = max(permits) if permits else 1
    max_y = max(years) if years else 1
    for r in rows:
        rating = (r.get("rating") or 0)/5.0
        rc = r.get("review_count") or 0
        rc_term = math.log1p(rc)
        p_term = ((r.get("permits_24mo") or 0)/max_p) if max_p else 0
        y_term = ((r.get("years_in_business") or 0)/max_y) if max_y else 0
        lic_bonus = 1.0 if (r.get("license_status") or "").lower() == "active" else 0.0
        r["score"] = round(
            0.35*rating*rc_term + 0.35*p_term + 0.15*y_term + 0.15*lic_bonus, 4
        )
