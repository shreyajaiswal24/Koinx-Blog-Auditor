"""Parse WordPress post HTML content into structured sections."""

import re
import logging
from typing import Dict, List, Any

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentParser:
    """Parses Elementor/WordPress HTML into structured text sections."""

    def parse_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a WP API post object into structured content.

        Returns:
            {
                "id": int,
                "title": str,
                "link": str,
                "date": str,
                "modified": str,
                "slug": str,
                "full_text": str,
                "sections": [{"heading": str, "text": str}, ...],
            }
        """
        html = post.get("content", {}).get("rendered", "")
        title = post.get("title", {}).get("rendered", "")

        soup = BeautifulSoup(html, "lxml")

        # Remove scripts, styles, nav elements
        for tag in soup.find_all(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()

        full_text = self._clean_text(soup.get_text(separator="\n"))
        sections = self._extract_sections(soup)

        return {
            "id": post.get("id"),
            "title": self._clean_text(BeautifulSoup(title, "lxml").get_text()),
            "link": post.get("link", ""),
            "date": post.get("date", ""),
            "modified": post.get("modified", ""),
            "slug": post.get("slug", ""),
            "full_text": full_text,
            "sections": sections,
        }

    def _extract_sections(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract content organized by h2/h3 headings."""
        sections = []
        current_heading = "Introduction"
        current_texts = []

        for element in soup.find_all(True):
            if element.name in ("h2", "h3"):
                # Save previous section
                if current_texts:
                    text = self._clean_text("\n".join(current_texts))
                    if text:
                        sections.append({
                            "heading": current_heading,
                            "text": text,
                        })
                current_heading = self._clean_text(element.get_text())
                current_texts = []
            elif element.name in ("p", "li", "td", "th", "span", "div"):
                # Only grab direct text, not nested elements' text repeatedly
                if not element.find(["p", "li", "td", "h2", "h3"]):
                    text = element.get_text(separator=" ").strip()
                    if text and len(text) > 5:
                        current_texts.append(text)

        # Save last section
        if current_texts:
            text = self._clean_text("\n".join(current_texts))
            if text:
                sections.append({
                    "heading": current_heading,
                    "text": text,
                })

        # Fallback: if no sections found, put everything in one section
        if not sections:
            full = self._clean_text(soup.get_text(separator="\n"))
            if full:
                sections.append({"heading": "Full Content", "text": full})

        return sections

    def _clean_text(self, text: str) -> str:
        """Remove excess whitespace and normalize text."""
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()
