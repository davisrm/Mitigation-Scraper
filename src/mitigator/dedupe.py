import re, tldextract
import time
from typing import Dict, Any

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

def root_domain(url: str | None) -> str | None:
    if not url: return None
    u = url.strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.split("/")[0]
    ext = tldextract.extract(u)
    if not ext.domain: return None
    return f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain

def choose_email(existing: dict, incoming: dict) -> tuple[str|None, float|None, str|None]:
    e_email, e_conf = existing.get("email"), existing.get("email_confidence") or 0.0
    i_email, i_conf = incoming.get("email"), incoming.get("email_confidence") or 0.0
    if not i_email:
        return e_email, e_conf or None, existing.get("email_source")
    if not e_email:
        return i_email, i_conf or None, incoming.get("email_source")

    e_site = root_domain(existing.get("website"))
    i_site = root_domain(incoming.get("website") or existing.get("website"))
    def dom_match(email, site):
        return 1 if (site and email and email.lower().endswith("@"+site)) else 0
    e_score = (e_conf, dom_match(e_email, e_site))
    i_score = (i_conf, dom_match(i_email, i_site))
    return (i_email, i_conf, incoming.get("email_source")) if i_score > e_score else (e_email, e_conf, existing.get("email_source"))

def merge_rows(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(existing)
    def prefer(a, b):
        return b if (a is None or a=="") and (b not in (None,"")) else a

    for f in ["phone","website","address","lat","lng",
              "license_number","license_status","years_in_business","permits_24mo"]:
        out[f] = prefer(existing.get(f), incoming.get(f))

    cats = set(filter(None, (existing.get("categories") or "").split(",")))
    cats |= set(filter(None, (incoming.get("categories") or "").split(",")))
    out["categories"] = ",".join(sorted(c.strip() for c in cats if c.strip()))

    erc = existing.get("review_count") or 0
    irc = incoming.get("review_count") or 0
    if irc > erc:
        out["rating"] = incoming.get("rating")
        out["review_count"] = irc

    if (incoming.get("license_status") or "").lower() == "active":
        out["license_status"] = "active"

    out["last_seen"] = max((existing.get("last_seen") or ""), (incoming.get("last_seen") or ""))

    email, conf, src = choose_email(existing, incoming)
    out["email"] = email
    out["email_confidence"] = conf
    out["email_source"] = src
    if incoming.get("email"):
        out["email_last_seen"] = max((existing.get("email_last_seen") or ""), time.strftime("%Y-%m-%d"))

    return out
