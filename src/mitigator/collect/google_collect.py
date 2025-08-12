import time, requests
from typing import List, Dict, Any, Optional

DETAILS_FIELDS = "formatted_phone_number,website"

def google_place_details(api_key: str, place_id: str, session: Optional[requests.Session] = None) -> dict:
    """Return {'phone': str|None, 'website': str|None} via Place Details."""
    s = session or requests.Session()
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {"place_id": place_id, "fields": DETAILS_FIELDS, "key": api_key}
    try:
        r = s.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json() or {}
        result = data.get("result", {}) or {}
        return {
            "phone": result.get("formatted_phone_number"),
            "website": result.get("website"),
        }
    except requests.RequestException:
        return {"phone": None, "website": None}

def google_text_search(api_key: str, query: str, location: Optional[str]=None, enrich_details: bool=True) -> List[Dict[str,Any]]:
    """
    Use Text Search for discovery; optionally enrich each result with Place Details
    to populate phone and website.
    """
    q = f"{query} in {location}" if location else query
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": q, "key": api_key}
    out: List[Dict[str, Any]] = []

    s = requests.Session()
    details_cache: dict[str, dict] = {}

    while True:
        r = s.get(url, params=params, timeout=20); r.raise_for_status()
        data = r.json() or {}

        for p in data.get("results", []):
            place_id = p.get("place_id")
            phone, website = None, None

            if enrich_details and place_id:
                if place_id in details_cache:
                    d = details_cache[place_id]
                else:
                    d = google_place_details(api_key, place_id, session=s)
                    details_cache[place_id] = d
                    time.sleep(0.05) 
                phone, website = d.get("phone"), d.get("website")

            out.append({
                "source": "google",
                "source_id": place_id,
                "name": p.get("name"),
                "phone": phone,
                "website": website,
                "address": p.get("formatted_address"),
                "lat": p.get("geometry",{}).get("location",{}).get("lat"),
                "lng": p.get("geometry",{}).get("location",{}).get("lng"),
                "categories": ",".join(p.get("types",[]) or []),
                "rating": p.get("rating"),
                "review_count": p.get("user_ratings_total"),
                "license_number": None,
                "license_status": None,
                "years_in_business": None,
                "permits_24mo": None,
                "score": None,
                "last_seen": time.strftime("%Y-%m-%d"),
            })

        token = data.get("next_page_token")
        if not token:
            break
        # Text Search next_page_token needs a short delay before reuse
        time.sleep(2)
        params = {"pagetoken": token, "key": api_key}

    return out
