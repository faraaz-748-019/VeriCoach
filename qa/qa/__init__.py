"""VeriCoach QA - Quality-Engineering Platform."""

from __future__ import annotations

from pathlib import Path

__version__ = "0.1.0"

# Extend package search path so that qa/framework is directly accessible as qa.framework
_qa_root = Path(__file__).resolve().parent.parent
if str(_qa_root) not in __path__:
    __path__.append(str(_qa_root))
