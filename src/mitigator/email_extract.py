# src/mitigator/email_extract.py
import re, time
from typing import cast
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
CANDIDATE_PATHS = ["/", "/contact", "/about", "/team", "/privacy", "/impressum"]

def get_root(url: str) -> str:
    u = urlparse(url if url.startswith("http") else f"https://{url}")
    scheme = u.scheme or "https"
    netloc = u.netloc or u.path
    return f"{scheme}://{netloc}"

def fetch(url: str, session: requests.Session, timeout=15) -> str:
    r = session.get(url, timeout=timeout, headers={"User-Agent": "mitigator/1.0"})
    r.raise_for_status()
    return r.text

def emails_from_html(html: str) -> set[str]:
    return {e.strip() for e in EMAIL_RE.findall(html or "")}

def extract_emails(website: str, max_pages: int = 5, sleep_s: float = 0.25):
    if not website:
        return []
    base = get_root(website)
    session = requests.Session()
    seen, results = set(), []
    queue = [urljoin(base, p) for p in CANDIDATE_PATHS]
    while queue and len(seen) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            html = fetch(url, session)
        except requests.RequestException:
            continue
        emails = emails_from_html(html)
        if emails:
            is_contact = any(x in url for x in ("/contact", "/about", "/team"))
            conf = 0.9 if is_contact else 0.7
            for e in emails:
                results.append((e, conf, "website"))
        # harvest mailto on the root page
        if url.rstrip("/") == base.rstrip("/"):
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.select("a[href^='mailto:']"):
                href = a.get("href")
                if not href:
                    continue
                addr = href[7:]
                if EMAIL_RE.fullmatch(cast(str, addr)):
                    results.append((addr, 0.95, "website"))
        time.sleep(sleep_s)
    # dedupe by lowercase, keep highest confidence
    out, seen_lower = [], {}
    for e, c, s in sorted(results, key=lambda x: -x[1]):
        el = e.lower()
        if el not in seen_lower:
            seen_lower[el] = True
            out.append((e, c, s))
    return out
