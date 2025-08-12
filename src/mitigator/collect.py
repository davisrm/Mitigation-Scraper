import time, requests
from typing import List, Dict, Any, Optional

def google_text_search(api_key: str, query: str, location: Optional[str]=None) -> List[Dict[str,Any]]:
    q = f"{query} in {location}" if location else query
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": q, "key": api_key}
    out = []
    while True:
        r = requests.get(url, params=params, timeout=20); r.raise_for_status()
        data = r.json()
        for p in data.get("results", []):
            out.append({
                "source": "google",
                "source_id": p.get("place_id"),
                "name": p.get("name"),
                "phone": None,
                "website": None,
                "address": p.get("formatted_address"),
                "lat": p.get("geometry",{}).get("location",{}).get("lat"),
                "lng": p.get("geometry",{}).get("location",{}).get("lng"),
                "categories": ",".join(p.get("types",[])),
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
        if not token: break
        time.sleep(2)
        params = {"pagetoken": token, "key": api_key}
    return out

def yelp_search(api_key: str, term: str, location: str) -> List[Dict[str,Any]]:
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"term": term, "location": location, "limit": 50}
    r = requests.get(url, params=params, headers=headers, timeout=20); r.raise_for_status()
    out = []
    for b in r.json().get("businesses", []):
        out.append({
            "source": "yelp",
            "source_id": b.get("id"),
            "name": b.get("name"),
            "phone": b.get("phone"),
            "website": b.get("url"),
            "address": ", ".join(filter(None, [
                b.get("location",{}).get("address1"),
                b.get("location",{}).get("city"),
                b.get("location",{}).get("state"),
            ])),
            "lat": b.get("coordinates",{}).get("latitude"),
            "lng": b.get("coordinates",{}).get("longitude"),
            "categories": ",".join([c.get("title") for c in b.get("categories",[])]),
            "rating": b.get("rating"),
            "review_count": b.get("review_count"),
            "license_number": None,
            "license_status": None,
            "years_in_business": None,
            "permits_24mo": None,
            "score": None,
            "last_seen": time.strftime("%Y-%m-%d"),
        })
    return out
