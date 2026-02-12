import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "storage" / "auditor.db"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Mistral AI
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL = "mistral-small-latest"  # free tier friendly, fast responses
MISTRAL_TEMPERATURE = 0.1
MISTRAL_MAX_TOKENS = 4096
MISTRAL_RPM_LIMIT = 30  # requests per minute

# WordPress API
WP_BASE_URL = "https://new-blog.koinx.com"
WP_API_URL = f"{WP_BASE_URL}/wp-json/wp/v2/posts"
TAX_GUIDES_CATEGORY_ID = 119
US_TAX_TAG_ID = 631  # "USA Tax Guide" tag — returns ~26 US-specific posts
WP_PER_PAGE = 100

# Category IDs to exclude (non-US countries) — safety net for category-based queries
EXCLUDED_CATEGORY_IDS = {464, 468, 674, 462}  # India, Australia, Germany, UK

# Non-US title keywords to exclude — safety net
EXCLUDED_TITLE_KEYWORDS = [
    "india", "australia", "uk", "united kingdom", "germany",
    "canada", "japan", "south korea", "singapore", "brazil",
    "spain", "netherlands", "belgium", "ireland", "france",
    "italy", "portugal", "south africa", "nigeria", "mexico",
    "sweden", "switzerland", "austria", "poland", "denmark",
]

# IRS source URLs
IRS_SOURCES = {
    "digital_assets": "https://www.irs.gov/businesses/small-businesses-self-employed/digital-assets",
    "digital_assets_filing": "https://www.irs.gov/filing/digital-assets",
    "newsroom": "https://www.irs.gov/newsroom",
    "pub_544": "https://www.irs.gov/publications/p544",
    "notice_2014_21": "https://www.irs.gov/irb/2014-16_IRB#NOT-2014-21",
}

# Tax reference cache TTL (seconds)
TAX_REFERENCE_TTL = 86400  # 24 hours

# Content chunking
MAX_CHUNK_CHARS = 8000

# Audit limits (set to None to audit all posts)
MAX_POSTS = 4  # limit for demo/free tier — analyzes first N posts

# Confidence scoring weights
CONFIDENCE_WEIGHTS = {
    "llm_raw": 0.40,
    "post_age": 0.20,
    "source_specificity": 0.20,
    "issue_type": 0.10,
    "cross_reference": 0.10,
}

# Scheduler
SCHEDULE_HOUR = 2
SCHEDULE_MINUTE = 0
