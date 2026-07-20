from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

VALID_MATCH_MODES = {"prompt_only", "exact", "contains", "regex", "review_only"}


@dataclass(frozen=True, slots=True)
class GlossaryEntry:
    wrong_term: str
    correct_term: str
    note: str = ""
    match_mode: str = "exact"
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.wrong_term.strip():
            raise ValueError("wrong_term must not be empty")
        if self.match_mode not in VALID_MATCH_MODES:
            raise ValueError(f"Unsupported match_mode: {self.match_mode}")
        if self.match_mode not in {"prompt_only", "review_only"} and not self.correct_term.strip():
            raise ValueError("correct_term must not be empty")
        if self.match_mode == "regex":
            re.compile(self.wrong_term)


@dataclass(frozen=True, slots=True)
class GlossaryReplacement:
    wrong_term: str
    correct_term: str
    count: int
    match_mode: str


@dataclass(frozen=True, slots=True)
class GlossaryApplyResult:
    text: str
    replacements: tuple[GlossaryReplacement, ...] = ()
    review_hits: tuple[str, ...] = ()


class Glossary:
    def __init__(self, entries: Sequence[GlossaryEntry] = ()) -> None:
        self.entries = tuple(entry for entry in entries if entry.enabled)

    @classmethod
    def from_csv(cls, path: Path) -> Glossary:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"wrong_term", "correct_term"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ValueError("Glossary CSV requires wrong_term and correct_term columns")

            entries: list[GlossaryEntry] = []
            for row in reader:
                enabled = str(row.get("enabled", "true")).strip().lower() not in {
                    "0",
                    "false",
                    "no",
                    "off",
                }
                entries.append(
                    GlossaryEntry(
                        wrong_term=(row.get("wrong_term") or "").strip(),
                        correct_term=(row.get("correct_term") or "").strip(),
                        note=(row.get("note") or "").strip(),
                        match_mode=(row.get("match_mode") or "exact").strip(),
                        enabled=enabled,
                    )
                )
        return cls(entries)

    @classmethod
    def merge(cls, *glossaries: Glossary) -> Glossary:
        merged: dict[tuple[str, str], GlossaryEntry] = {}
        for glossary in glossaries:
            for entry in glossary.entries:
                merged[(entry.wrong_term, entry.match_mode)] = entry
        return cls(tuple(merged.values()))

    @property
    def version_hash(self) -> str:
        payload = [
            {
                "wrong_term": entry.wrong_term,
                "correct_term": entry.correct_term,
                "note": entry.note,
                "match_mode": entry.match_mode,
                "enabled": entry.enabled,
            }
            for entry in sorted(
                self.entries,
                key=lambda value: (value.wrong_term, value.match_mode, value.correct_term),
            )
        ]
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def prompt_terms(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                entry.correct_term or entry.wrong_term
                for entry in self.entries
                if entry.match_mode in {"prompt_only", "exact", "contains", "regex"}
            )
        )

    def apply(self, text: str, *, max_replacements_per_entry: int = 1000) -> GlossaryApplyResult:
        if max_replacements_per_entry < 1:
            raise ValueError("max_replacements_per_entry must be positive")

        current = text
        replacements: list[GlossaryReplacement] = []
        review_hits: list[str] = []

        for entry in self.entries:
            if entry.match_mode == "prompt_only":
                continue
            if entry.match_mode == "review_only":
                if entry.wrong_term in current:
                    review_hits.append(entry.wrong_term)
                continue

            if entry.match_mode == "regex":
                current, count = re.subn(
                    entry.wrong_term,
                    entry.correct_term,
                    current,
                    count=max_replacements_per_entry,
                )
            elif entry.match_mode == "contains":
                pattern = re.compile(re.escape(entry.wrong_term), re.IGNORECASE)
                current, count = pattern.subn(
                    lambda _match: entry.correct_term,
                    current,
                    count=max_replacements_per_entry,
                )
            else:
                count = min(current.count(entry.wrong_term), max_replacements_per_entry)
                current = current.replace(entry.wrong_term, entry.correct_term, count)

            if count:
                replacements.append(
                    GlossaryReplacement(
                        wrong_term=entry.wrong_term,
                        correct_term=entry.correct_term,
                        count=count,
                        match_mode=entry.match_mode,
                    )
                )

        return GlossaryApplyResult(
            text=current,
            replacements=tuple(replacements),
            review_hits=tuple(dict.fromkeys(review_hits)),
        )
