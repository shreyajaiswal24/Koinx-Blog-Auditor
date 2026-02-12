"""WordPress REST API client for fetching KoinX blog posts."""

import logging
import time
from typing import List, Dict, Any, Optional

import requests

from config.settings import (
    WP_API_URL,
    TAX_GUIDES_CATEGORY_ID,
    US_TAX_TAG_ID,
    WP_PER_PAGE,
    EXCLUDED_CATEGORY_IDS,
    EXCLUDED_TITLE_KEYWORDS,
)

logger = logging.getLogger(__name__)


class WPApiClient:
    """Fetches blog posts from the KoinX WordPress REST API."""

    FIELDS = "id,title,link,date,modified,content,slug,categories"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "KoinX-Tax-Auditor/1.0",
            "Accept": "application/json",
        })

    def fetch_all_tax_guide_posts(self) -> List[Dict[str, Any]]:
        """Fetch all US tax guide posts using tag 631 (USA Tax Guide)."""
        all_posts = []
        page = 1

        while True:
            params = {
                "tags": US_TAX_TAG_ID,
                "per_page": WP_PER_PAGE,
                "page": page,
                "_fields": self.FIELDS,
            }
            logger.info(f"Fetching page {page} from WP API...")

            try:
                resp = self.session.get(WP_API_URL, params=params, timeout=30)
                resp.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"WP API request failed on page {page}: {e}")
                break

            posts = resp.json()
            if not posts:
                break

            all_posts.extend(posts)
            total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
            logger.info(f"Page {page}/{total_pages} — got {len(posts)} posts")

            if page >= total_pages:
                break

            page += 1
            time.sleep(0.5)  # polite delay

        logger.info(f"Total posts fetched: {len(all_posts)}")
        us_posts = self._filter_us_posts(all_posts)
        logger.info(f"US tax posts after filtering: {len(us_posts)}")
        return us_posts

    def fetch_single_post(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single post by ID."""
        url = f"{WP_API_URL}/{post_id}"
        params = {"_fields": self.FIELDS}
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            post = resp.json()
            if self._is_us_post(post):
                return post
            logger.warning(f"Post {post_id} is not a US tax post, skipping.")
            return None
        except requests.RequestException as e:
            logger.error(f"Failed to fetch post {post_id}: {e}")
            return None

    def _filter_us_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out non-US posts by category IDs and title keywords."""
        return [p for p in posts if self._is_us_post(p)]

    def _is_us_post(self, post: Dict[str, Any]) -> bool:
        """Check if a post is about US tax topics."""
        # Exclude if post belongs to a non-US category
        post_categories = set(post.get("categories", []))
        if post_categories & EXCLUDED_CATEGORY_IDS:
            return False

        # Exclude if title contains non-US keywords
        title = post.get("title", {}).get("rendered", "").lower()
        for keyword in EXCLUDED_TITLE_KEYWORDS:
            if keyword in title:
                return False

        return True
