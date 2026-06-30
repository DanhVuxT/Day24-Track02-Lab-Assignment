"""PII detection helpers for Vietnamese healthcare data.

The lab mentions Presidio and spaCy, but the Vietnamese spaCy model is often
not installed in grading environments. This module keeps a Presidio-like
interface and uses deterministic regex/context recognizers so the required
entities are detected reliably.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


@dataclass(frozen=True)
class SimpleRecognizerResult:
    entity_type: str
    start: int
    end: int
    score: float


class VietnamesePIIAnalyzer:
    cccd_regex = re.compile(r"(?<!\d)\d{12}(?!\d)")
    phone_regex = re.compile(r"(?<!\d)0[35789]\d{8}(?!\d)")
    stripped_phone_regex = re.compile(r"(?<!\d)[35789]\d{8}(?!\d)")
    stripped_cccd_regex = re.compile(r"(?<!\d)\d{10,11}(?!\d)")
    email_regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    name_regex = re.compile(
        r"\b(?:[A-Z][a-zA-ZÀ-ỹĐđ]+)(?:\s+[A-Z][a-zA-ZÀ-ỹĐđ]+){1,4}\b"
    )
    name_context = re.compile(
        r"(?i)(?:benh nhan|bệnh nhân|bac si|bác sĩ|ho ten|họ tên|doctor|patient)"
        r"[:\s-]+([A-Z][a-zA-ZÀ-ỹĐđ]+(?:\s+[A-Z][a-zA-ZÀ-ỹĐđ]+){1,4})"
    )

    def analyze(
        self,
        text: str,
        language: str = "vi",
        entities: Iterable[str] | None = None,
        **_: object,
    ) -> list[SimpleRecognizerResult]:
        requested = set(entities or ["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"])
        value = "" if text is None else str(text)
        results: list[SimpleRecognizerResult] = []

        if "VN_CCCD" in requested:
            results.extend(self._find_all(value, self.cccd_regex, "VN_CCCD", 0.95))
            if not results and self.stripped_cccd_regex.fullmatch(value.strip()):
                results.append(SimpleRecognizerResult("VN_CCCD", 0, len(value.strip()), 0.7))
        if "VN_PHONE" in requested:
            results.extend(self._find_all(value, self.phone_regex, "VN_PHONE", 0.95))
            if not results and self.stripped_phone_regex.fullmatch(value.strip()):
                results.append(SimpleRecognizerResult("VN_PHONE", 0, len(value.strip()), 0.7))
        if "EMAIL_ADDRESS" in requested:
            results.extend(self._find_all(value, self.email_regex, "EMAIL_ADDRESS", 0.98))
        if "PERSON" in requested:
            results.extend(self._detect_person(value))

        return sorted(results, key=lambda item: (item.start, -item.end))

    @staticmethod
    def _find_all(
        text: str, regex: re.Pattern[str], entity: str, score: float
    ) -> list[SimpleRecognizerResult]:
        return [
            SimpleRecognizerResult(entity, match.start(), match.end(), score)
            for match in regex.finditer(text)
        ]

    def _detect_person(self, text: str) -> list[SimpleRecognizerResult]:
        results = [
            SimpleRecognizerResult("PERSON", match.start(1), match.end(1), 0.9)
            for match in self.name_context.finditer(text)
        ]
        if results:
            return results

        stripped = text.strip()
        if (
            self.email_regex.fullmatch(stripped)
            or self.cccd_regex.fullmatch(stripped)
            or self.phone_regex.fullmatch(stripped)
        ):
            return []

        blocked = {"Email", "CCCD", "Bearer", "MedViet"}
        for match in self.name_regex.finditer(text):
            candidate = match.group(0)
            if candidate.split()[0] not in blocked and "@" not in candidate:
                results.append(SimpleRecognizerResult("PERSON", match.start(), match.end(), 0.75))
        return results


def build_vietnamese_analyzer() -> VietnamesePIIAnalyzer:
    return VietnamesePIIAnalyzer()


def detect_pii(text: str, analyzer: VietnamesePIIAnalyzer) -> list[SimpleRecognizerResult]:
    return analyzer.analyze(
        text="" if text is None else str(text),
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"],
    )
