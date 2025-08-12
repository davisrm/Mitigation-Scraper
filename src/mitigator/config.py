import os
from dotenv import load_dotenv
load_dotenv()

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_KEY", "")
YELP_KEY   = os.getenv("YELP_FUSION_KEY", "")
DB_PATH    = os.getenv("DB_PATH", "src/data/mitigation.db")
CSV_OUT    = os.getenv("CSV_OUT", "src/data/companies.csv")

KEYWORDS = [
    "water damage restoration",
    "fire damage restoration",
    "mold remediation",
    "smoke damage cleanup",
    "asbestos abatement",
]

SERVICE_AREAS = [
    "Seattle, WA", "Tacoma, WA", "Bellevue, WA", "Everett, WA", "Renton, WA"
]
