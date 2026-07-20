"""Conservative glossary loading; only explicit rules may change transcript text."""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GlossaryRule:
    wrong_term: str
    correct_term: str
    note: str = ""
    match_mode: str = "prompt_only"
    enabled: bool = True


class Glossary:
    def __init__(self, rules: list[GlossaryRule]):
        self.rules = tuple(rules)

    @classmethod
    def from_csv(cls, path: Path) -> "Glossary":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return cls([
                GlossaryRule(
                    wrong_term=row["wrong_term"].strip(), correct_term=row["correct_term"].strip(),
                    note=row.get("note", "").strip(), match_mode=row.get("match_mode", "prompt_only").strip() or "prompt_only",
                    enabled=row.get("enabled", "true").strip().lower() not in {"0", "false", "no"},
                ) for row in csv.DictReader(handle) if row.get("wrong_term") and row.get("correct_term")
            ])

    @property
    def version_hash(self) -> str:
        source = "\n".join(repr(rule) for rule in self.rules)
        return hashlib.sha256(source.encode()).hexdigest()[:12]

    def prompt(self) -> str:
        terms = [f"{rule.correct_term}（避免誤辨為 {rule.wrong_term}）" for rule in self.rules if rule.enabled]
        return "專有名詞：" + "、".join(terms) if terms else ""

    def apply_deterministic(self, text: str) -> str:
        for rule in self.rules:
            if not rule.enabled:
                continue
            if rule.match_mode == "exact" and text == rule.wrong_term:
                text = rule.correct_term
            elif rule.match_mode == "regex":
                text = re.sub(rule.wrong_term, rule.correct_term, text)
            # contains is intentionally not auto-applied: it needs human review.
        return text
