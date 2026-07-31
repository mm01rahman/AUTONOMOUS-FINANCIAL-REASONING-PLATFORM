"""KERNEL.md bootloader parser (WP-IMP-0003, FIT-006).

Parses ``00-governance/KERNEL.md`` and asserts the constitutional word budget
``W <= 400`` (FIT-006), raising :class:`InvariantError` on breach.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from afrp.core.exceptions import ContractReferenceError, InvariantError

KERNEL_MAX_WORDS = 400
_WORD_PATTERN = re.compile(r"\S+")
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*\S)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class KernelDocument:
    """Parsed, validated KERNEL bootloader document."""

    path: Path
    title: str
    word_count: int
    sections: tuple[str, ...]
    text: str


def count_words(text: str) -> int:
    """Count whitespace-delimited tokens (deterministic FIT-006 metric)."""
    return len(_WORD_PATTERN.findall(text))


def load_kernel(path: Path, max_words: int = KERNEL_MAX_WORDS) -> KernelDocument:
    """Load the KERNEL document at ``path`` and enforce FIT-006.

    Raises:
        ContractReferenceError: the kernel file does not exist.
        InvariantError: word count exceeds ``max_words`` or no title heading.
    """
    if not path.is_file():
        raise ContractReferenceError(str(path))
    text = path.read_text(encoding="utf-8")

    words = count_words(text)
    if words > max_words:
        raise InvariantError(
            "FIT-006",
            f"KERNEL word count {words} exceeds budget {max_words}",
        )

    headings = _HEADING_PATTERN.findall(text)
    if not headings:
        raise InvariantError("FIT-006", "KERNEL has no markdown title heading")
    title = headings[0][1]
    sections = tuple(h[1] for h in headings[1:])
    return KernelDocument(
        path=path,
        title=title,
        word_count=words,
        sections=sections,
        text=text,
    )
