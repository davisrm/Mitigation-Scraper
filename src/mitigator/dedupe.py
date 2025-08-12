import re, tldextract
from typing import Dict, Any, List

COMMON_SUFFIXES = r"\b(inc|llc|l\.l\.c|co|corp|corporation|company|ltd|limited|restoration|services?)\b"

def norm_phone(phone: str | None) -> str | None:
    if not phone: return None
    digits = re.sub(r"\D", "", phone)
    return digits or None

def norm_website(url: str | None) -> str | None:
    if not url: return None
    u = url.strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.split("/")[0]
    # root domain only
    ext = tldextract.extract(u)
    if not ext.domain: return None
    root = f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain
    return root

def norm_name(name: str | None) -> str | None:
    if not name: return None
    n = name.lower()
    n = re.sub(COMMON_SUFFIXES, "", n)
    n = re.sub(r"[^a-z0-9]+", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n or None

def extract_city_state(address: str | None) -> tuple[str|None, str|None]:
    if not address: return (None, None)
    m = re.search(r",\s*([^,]+),\s*([A-Z]{2})\b", address)
    if not m: return (None, None)
    return (m.group(1).strip().lower(), m.group(2).strip().upper())

def entity_key(row: Dict[str, Any]) -> str | None:
    p = norm_phone(row.get("phone"))
    if p: return f"ph:{p}"
    w = norm_website(row.get("website"))
    if w: return f"ws:{w}"
    n = norm_name(row.get("name"))
    city, state = extract_city_state(row.get("address"))
    if n and city and state:
        return f"nm:{n}|{city}|{state}"
    if n and state:
        return f"nm:{n}|{state}"
    return None

def merge_rows(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    # keep non-nulls; union categories; choose rating that matches higher review_count
    out = dict(existing)
    def prefer(a, b):
        return b if (a is None or a=="") and (b not in (None,"")) else a

    for f in ["phone","website","address","lat","lng",
              "license_number","license_status","years_in_business","permits_24mo"]:
        out[f] = prefer(existing.get(f), incoming.get(f))

    # categories union
    cats = set(filter(None, (existing.get("categories") or "").split(",")))
    cats |= set(filter(None, (incoming.get("categories") or "").split(",")))
    out["categories"] = ",".join(sorted(c.strip() for c in cats if c.strip()))

    # rating/reviews – keep tuple with higher review_count
    erc = existing.get("review_count") or 0
    irc = incoming.get("review_count") or 0
    if irc > erc:
        out["rating"] = incoming.get("rating")
        out["review_count"] = irc

    # keep best license ‘active’ if either shows active
    if (incoming.get("license_status") or "").lower() == "active":
        out["license_status"] = "active"

    # last_seen – max
    out["last_seen"] = max((existing.get("last_seen") or ""), (incoming.get("last_seen") or ""))

    return out
