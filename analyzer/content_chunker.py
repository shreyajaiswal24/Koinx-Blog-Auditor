"""Section-based content chunking for LLM analysis."""

import logging
from typing import List, Dict

from config.settings import MAX_CHUNK_CHARS

logger = logging.getLogger(__name__)


class ContentChunker:
    """Splits parsed blog post content into LLM-friendly chunks."""

    def chunk_post(self, parsed_post: Dict) -> List[Dict[str, str]]:
        """Split a parsed post into chunks based on heading sections.

        Each chunk contains one or more sections, staying under MAX_CHUNK_CHARS.

        Returns:
            List of {"heading": str, "text": str} chunks
        """
        sections = parsed_post.get("sections", [])
        if not sections:
            return []

        chunks = []
        current_heading_parts = []
        current_text_parts = []
        current_length = 0

        for section in sections:
            section_text = section.get("text", "")
            section_heading = section.get("heading", "")
            section_length = len(section_text)

            # If a single section exceeds max, split it
            if section_length > MAX_CHUNK_CHARS:
                # Flush current buffer first
                if current_text_parts:
                    chunks.append({
                        "heading": " / ".join(current_heading_parts),
                        "text": "\n\n".join(current_text_parts),
                    })
                    current_heading_parts = []
                    current_text_parts = []
                    current_length = 0

                # Split the large section into sub-chunks
                sub_chunks = self._split_large_text(section_heading, section_text)
                chunks.extend(sub_chunks)
                continue

            # If adding this section would exceed max, flush
            if current_length + section_length > MAX_CHUNK_CHARS and current_text_parts:
                chunks.append({
                    "heading": " / ".join(current_heading_parts),
                    "text": "\n\n".join(current_text_parts),
                })
                current_heading_parts = []
                current_text_parts = []
                current_length = 0

            current_heading_parts.append(section_heading)
            current_text_parts.append(section_text)
            current_length += section_length

        # Flush remaining
        if current_text_parts:
            chunks.append({
                "heading": " / ".join(current_heading_parts),
                "text": "\n\n".join(current_text_parts),
            })

        logger.debug(
            f"Post '{parsed_post.get('title', 'unknown')}' → {len(chunks)} chunks"
        )
        return chunks

    def _split_large_text(
        self, heading: str, text: str
    ) -> List[Dict[str, str]]:
        """Split a large text block into smaller chunks by paragraphs."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_parts = []
        current_length = 0

        for para in paragraphs:
            if current_length + len(para) > MAX_CHUNK_CHARS and current_parts:
                chunks.append({
                    "heading": heading,
                    "text": "\n\n".join(current_parts),
                })
                current_parts = []
                current_length = 0

            current_parts.append(para)
            current_length += len(para)

        if current_parts:
            chunks.append({
                "heading": heading,
                "text": "\n\n".join(current_parts),
            })

        return chunks
