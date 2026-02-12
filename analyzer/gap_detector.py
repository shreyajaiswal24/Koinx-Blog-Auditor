"""Main orchestrator: crawl blog posts → analyze with Mistral → score findings."""

import logging
from typing import List, Dict, Any, Optional, Callable

from crawler.wp_api_client import WPApiClient
from crawler.content_parser import ContentParser
from tax_sources.tax_reference_store import TaxReferenceStore
from analyzer.mistral_client import MistralClient
from analyzer.content_chunker import ContentChunker
from analyzer.confidence_scorer import ConfidenceScorer
from analyzer.prompts import SYSTEM_PROMPT, GAP_DETECTION_PROMPT

logger = logging.getLogger(__name__)


class GapDetector:
    """Orchestrates the full audit pipeline."""

    def __init__(self, db):
        """Initialize with a Database instance.

        Args:
            db: storage.database.Database instance
        """
        self.wp_client = WPApiClient()
        self.parser = ContentParser()
        self.chunker = ContentChunker()
        self.mistral = MistralClient()
        self.scorer = ConfidenceScorer()
        self.tax_store = TaxReferenceStore(db)

    def run_full_audit(
        self,
        single_post_id: Optional[int] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> List[Dict[str, Any]]:
        """Run the complete audit pipeline.

        Args:
            single_post_id: If set, audit only this post ID.
            progress_callback: Optional callback for progress events.

        Returns:
            List of finding dicts with all metadata.
        """
        def _notify(event: Dict[str, Any]):
            if progress_callback:
                try:
                    progress_callback(event)
                except Exception:
                    pass

        # Step 1: Fetch posts
        if single_post_id:
            logger.info(f"Fetching single post: {single_post_id}")
            post = self.wp_client.fetch_single_post(single_post_id)
            raw_posts = [post] if post else []
        else:
            logger.info("Fetching all US tax guide posts...")
            raw_posts = self.wp_client.fetch_all_tax_guide_posts()

        if not raw_posts:
            logger.warning("No posts to audit.")
            _notify({"event": "audit_complete", "total_findings": 0})
            return []

        # Apply MAX_POSTS limit if configured
        from config.settings import MAX_POSTS
        if MAX_POSTS and not single_post_id:
            raw_posts = raw_posts[:MAX_POSTS]
            logger.info(f"Limited to {MAX_POSTS} posts (MAX_POSTS setting)")

        logger.info(f"Auditing {len(raw_posts)} posts...")
        _notify({"event": "audit_started", "total_posts": len(raw_posts)})

        # Step 2: Build tax reference corpus
        tax_corpus = self.tax_store.get_reference_corpus()
        logger.info(f"Tax reference corpus: {len(tax_corpus)} chars")

        # Step 3: Process each post
        all_findings = []
        for i, raw_post in enumerate(raw_posts, 1):
            post_title = raw_post.get("title", {}).get("rendered", "Unknown")
            logger.info(f"[{i}/{len(raw_posts)}] Analyzing: {post_title}")

            try:
                findings = self._analyze_post(raw_post, tax_corpus)
                all_findings.extend(findings)
                logger.info(f"  Found {len(findings)} issues")
                _notify({
                    "event": "post_analyzed",
                    "current": i,
                    "total": len(raw_posts),
                    "post_title": post_title,
                    "findings_in_post": len(findings),
                })
            except Exception as e:
                logger.error(f"  Error analyzing post: {e}")
                _notify({
                    "event": "post_analyzed",
                    "current": i,
                    "total": len(raw_posts),
                    "post_title": post_title,
                    "findings_in_post": 0,
                    "error": str(e),
                })

        # Step 4: Deduplicate
        all_findings = self._deduplicate(all_findings)

        logger.info(f"Total findings: {len(all_findings)}")
        logger.info(f"API usage: {self.mistral.get_usage_stats()}")

        _notify({"event": "audit_complete", "total_findings": len(all_findings)})

        return all_findings

    def _analyze_post(
        self, raw_post: Dict[str, Any], tax_corpus: str
    ) -> List[Dict[str, Any]]:
        """Analyze a single blog post for tax law gaps."""
        parsed = self.parser.parse_post(raw_post)
        chunks = self.chunker.chunk_post(parsed)

        findings = []
        for chunk in chunks:
            user_prompt = GAP_DETECTION_PROMPT.format(
                post_title=parsed["title"],
                post_url=parsed["link"],
                post_date=parsed["date"],
                post_modified=parsed["modified"],
                section_heading=chunk["heading"],
                section_text=chunk["text"],
                tax_reference=tax_corpus,
            )

            result = self.mistral.analyze(SYSTEM_PROMPT, user_prompt)
            if not result:
                continue

            issues = result.get("issues", [])
            for issue in issues:
                # Rescore confidence
                final_confidence = self.scorer.rescore(
                    issue, parsed["date"], parsed["modified"]
                )

                findings.append({
                    "blog_url": parsed["link"],
                    "blog_title": parsed["title"],
                    "blog_date": parsed["date"],
                    "blog_modified": parsed["modified"],
                    "section_heading": chunk["heading"],
                    "exact_quote": issue.get("exact_quote", ""),
                    "issue_type": issue.get("issue_type", ""),
                    "description": issue.get("description", ""),
                    "suggested_update": issue.get("suggested_update", ""),
                    "source": issue.get("source", ""),
                    "llm_confidence": issue.get("confidence", 0),
                    "confidence": final_confidence,
                    "priority": issue.get("priority", "low"),
                })

        return findings

    def _deduplicate(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate findings based on blog_url + exact_quote."""
        seen = set()
        unique = []
        for f in findings:
            key = (f["blog_url"], f["exact_quote"])
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique
