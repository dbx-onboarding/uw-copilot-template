"""
uw_copilot.chunker — Hierarchical document chunker.

Produces parent + child chunk pairs from raw document text.
Child chunks are the retrieval unit for Vector Search.
Parent chunks are the context window served to the LLM.

Usage:
    from uw_copilot.chunker import HierarchicalChunker
    chunker = HierarchicalChunker.from_config(cfg)
    chunks = chunker.chunk(text, doc_id="DOC-001", category="Submissions", source_path="s3://...")
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from .config import Config

# Regex patterns that signal a new section boundary.
# Ordered by priority — first match wins.
SECTION_HEADER_PATTERNS = [
    re.compile(r"^#{1,4}\s+\S"),                          # Markdown headers
    re.compile(r"^[A-Z][A-Z\s\-]{4,}$", re.MULTILINE),   # ALL-CAPS headings
    re.compile(r"^\d+\.\d*\s+[A-Z]"),                     # Numbered sections: 3.1 Title
    re.compile(r"^(Section|Article|Part|Chapter)\s+\d+",  # Legal section labels
               re.IGNORECASE),
    re.compile(r"^[A-Z][a-z].{10,}:$"),                   # Title-case lines ending in colon
]


@dataclass
class Chunk:
    chunk_id:    str
    parent_id:   Optional[str]          # None for parent chunks
    chunk_type:  str                    # "parent" or "child"
    text:        str
    doc_id:      str
    category:    str
    source_path: str
    char_start:  int = 0
    char_end:    int = 0
    metadata:    dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "chunk_id":    self.chunk_id,
            "parent_id":   self.parent_id,
            "chunk_type":  self.chunk_type,
            "chunk_text":  self.text,
            "doc_id":      self.doc_id,
            "category":    self.category,
            "source_path": self.source_path,
            "char_start":  self.char_start,
            "char_end":    self.char_end,
        }


class HierarchicalChunker:
    """
    Splits a document into parent chunks (large context windows) and
    child chunks (small retrieval targets).

    Each child chunk carries its parent_id so the LLM can be given
    the full parent context when the child is retrieved.
    """

    def __init__(
        self,
        parent_size: int = 2500,
        child_size: int = 600,
        overlap: int = 100,
    ):
        if child_size >= parent_size:
            raise ValueError("child_size must be smaller than parent_size")
        if overlap >= child_size:
            raise ValueError("overlap must be smaller than child_size")
        self.parent_size = parent_size
        self.child_size  = child_size
        self.overlap     = overlap

    @classmethod
    def from_config(cls, cfg: Config) -> "HierarchicalChunker":
        return cls(
            parent_size=cfg.parent_chunk_size,
            child_size=cfg.child_chunk_size,
            overlap=cfg.chunk_overlap,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def chunk(
        self,
        text: str,
        doc_id: str,
        category: str,
        source_path: str,
    ) -> List[Chunk]:
        """
        Returns a flat list of Chunk objects: [parent, child, child, …, parent, child, …]
        Chunk objects with chunk_type=="parent" are the context windows.
        Chunk objects with chunk_type=="child" are the VS retrieval targets.
        """
        if not text or not text.strip():
            return []

        parents = self._split_parents(text, doc_id, category, source_path)
        all_chunks: List[Chunk] = []
        for parent in parents:
            all_chunks.append(parent)
            children = self._split_children(parent)
            all_chunks.extend(children)
        return all_chunks

    # ── Internal ──────────────────────────────────────────────────────────────

    def _split_parents(
        self, text: str, doc_id: str, category: str, source_path: str
    ) -> List[Chunk]:
        """Split text at section boundaries first, then by size."""
        segments = self._split_at_sections(text)
        parents: List[Chunk] = []
        pos = 0

        for seg in segments:
            # If segment fits in one parent chunk, emit it directly
            if len(seg) <= self.parent_size:
                chunk_id = f"P-{doc_id}-{uuid.uuid4().hex[:8]}"
                end = pos + len(seg)
                parents.append(Chunk(
                    chunk_id=chunk_id, parent_id=None, chunk_type="parent",
                    text=seg.strip(), doc_id=doc_id, category=category,
                    source_path=source_path, char_start=pos, char_end=end,
                ))
                pos = end
            else:
                # Segment is too long — slide through it
                sub_chunks = self._slide(seg, self.parent_size, self.overlap // 2)
                for sub in sub_chunks:
                    chunk_id = f"P-{doc_id}-{uuid.uuid4().hex[:8]}"
                    end = pos + len(sub)
                    parents.append(Chunk(
                        chunk_id=chunk_id, parent_id=None, chunk_type="parent",
                        text=sub.strip(), doc_id=doc_id, category=category,
                        source_path=source_path, char_start=pos, char_end=end,
                    ))
                    pos = end

        return parents

    def _split_children(self, parent: Chunk) -> List[Chunk]:
        """Slice a parent chunk into overlapping child chunks."""
        sub_texts = self._slide(parent.text, self.child_size, self.overlap)
        children: List[Chunk] = []
        offset = parent.char_start

        for sub in sub_texts:
            chunk_id = f"C-{parent.chunk_id}-{uuid.uuid4().hex[:6]}"
            end = offset + len(sub)
            children.append(Chunk(
                chunk_id=chunk_id, parent_id=parent.chunk_id, chunk_type="child",
                text=sub.strip(), doc_id=parent.doc_id, category=parent.category,
                source_path=parent.source_path, char_start=offset, char_end=end,
            ))
            offset = end - self.overlap  # back up by overlap for next window

        return children

    def _split_at_sections(self, text: str) -> List[str]:
        """Split text at detected section header boundaries."""
        lines = text.split("\n")
        segments: List[str] = []
        current: List[str] = []

        for line in lines:
            if current and self._is_section_header(line):
                segments.append("\n".join(current))
                current = [line]
            else:
                current.append(line)

        if current:
            segments.append("\n".join(current))

        return [s for s in segments if s.strip()]

    @staticmethod
    def _is_section_header(line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        return any(p.match(stripped) for p in SECTION_HEADER_PATTERNS)

    @staticmethod
    def _slide(text: str, size: int, overlap: int) -> List[str]:
        """Fixed-size sliding window over text."""
        if len(text) <= size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = start + size
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start = end - overlap
        return chunks
