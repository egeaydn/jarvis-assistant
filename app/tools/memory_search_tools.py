"""
Phase 10 — Konuşma / Agent Geçmişinde Arama.

search_agent_history: Kalıcı agent adımı geçmişini (data/agent_history.jsonl)
tarih ve anahtar kelimeye göre filtreler.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_HISTORY_FILE = _DATA_DIR / "agent_history.jsonl"


def search_agent_history(query: str = "", days_back: int = 7) -> List[Dict[str, str]]:
    """
    Kalıcı agent adımı geçmişinde (Thought/Action/Observation) tarih ve
    anahtar kelimeye göre arama yapar. query boş verilirse sadece tarihe göre filtreler.
    """
    if days_back < 0:
        raise ValueError("days_back negatif olamaz.")
    if not _HISTORY_FILE.exists():
        return []

    needle = (query or "").strip().lower()
    cutoff = datetime.now() - timedelta(days=days_back)

    results: List[Dict[str, str]] = []
    for line in _HISTORY_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            ts = datetime.fromisoformat(record["timestamp"])
        except (KeyError, ValueError):
            continue
        if ts < cutoff:
            continue

        haystack = " ".join([
            record.get("thought", ""),
            record.get("action", ""),
            json.dumps(record.get("action_input", {}), ensure_ascii=False),
            record.get("observation", ""),
        ]).lower()
        if needle and needle not in haystack:
            continue

        results.append(record)

    return list(reversed(results))
