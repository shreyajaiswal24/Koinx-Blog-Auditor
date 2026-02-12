"""Multi-factor confidence rescoring for audit findings."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any

from config.settings import CONFIDENCE_WEIGHTS

logger = logging.getLogger(__name__)

# Issue type severity weights (higher = more likely a real issue)
ISSUE_TYPE_SCORES = {
    "outdated_info": 0.9,
    "incorrect_fact": 0.95,
    "missing_update": 0.8,
    "misleading_language": 0.6,
    "incomplete_info": 0.5,
}


class ConfidenceScorer:
    """Rescores LLM-generated confidence using multiple factors."""

    def rescore(self, issue: Dict[str, Any], post_date: str, post_modified: str) -> float:
        """Calculate a weighted confidence score from multiple factors.

        Args:
            issue: Dict with keys from LLM output (confidence, issue_type, source)
            post_date: ISO date string of post publication
            post_modified: ISO date string of last modification

        Returns:
            Final confidence score between 0.0 and 1.0
        """
        weights = CONFIDENCE_WEIGHTS

        # Factor 1: LLM raw confidence (40%)
        llm_raw = float(issue.get("confidence", 0.5))

        # Factor 2: Post age (20%) — older posts more likely to have issues
        post_age_score = self._score_post_age(post_modified or post_date)

        # Factor 3: Source specificity (20%) — specific citations = higher confidence
        source_score = self._score_source_specificity(issue.get("source", ""))

        # Factor 4: Issue type severity (10%)
        issue_type = issue.get("issue_type", "incomplete_info")
        type_score = ISSUE_TYPE_SCORES.get(issue_type, 0.5)

        # Factor 5: Cross-reference indicator (10%) — does the issue cite a real regulation?
        xref_score = self._score_cross_reference(issue)

        final = (
            weights["llm_raw"] * llm_raw
            + weights["post_age"] * post_age_score
            + weights["source_specificity"] * source_score
            + weights["issue_type"] * type_score
            + weights["cross_reference"] * xref_score
        )

        return round(min(max(final, 0.0), 1.0), 3)

    def _score_post_age(self, date_str: str) -> float:
        """Score based on how old the post is. Older = higher score."""
        try:
            post_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            days_old = (now - post_date).days

            if days_old > 730:  # > 2 years
                return 0.95
            elif days_old > 365:  # > 1 year
                return 0.8
            elif days_old > 180:  # > 6 months
                return 0.6
            elif days_old > 90:  # > 3 months
                return 0.4
            else:
                return 0.2
        except (ValueError, TypeError):
            return 0.5  # neutral if date unparseable

    def _score_source_specificity(self, source: str) -> float:
        """Score based on how specific the cited source is."""
        if not source:
            return 0.2

        source_lower = source.lower()

        # Very specific citations
        specific_markers = [
            "notice 2014-21", "rev. rul.", "td 10000", "irc §",
            "publication", "form 1099", "form 8949", "schedule d",
            "final regulation", "§1091", "§1012", "§1222",
        ]
        if any(marker in source_lower for marker in specific_markers):
            return 0.95

        # Moderately specific
        if "irs" in source_lower or "regulation" in source_lower:
            return 0.7

        return 0.4

    def _score_cross_reference(self, issue: Dict[str, Any]) -> float:
        """Score based on whether the issue references verifiable regulations."""
        source = issue.get("source", "").lower()
        description = issue.get("description", "").lower()
        combined = source + " " + description

        verifiable_refs = [
            "notice 2014-21", "rev. rul. 2019-24", "rev. rul. 2023-14",
            "td 10000", "infrastructure investment", "form 1099-da",
            "irc §", "publication 544", "fincen",
        ]

        matches = sum(1 for ref in verifiable_refs if ref in combined)
        if matches >= 2:
            return 0.95
        elif matches == 1:
            return 0.75
        return 0.3
