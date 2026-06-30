import hashlib
import secrets

import pandas as pd
from faker import Faker

from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")
Faker.seed(42)


class MedVietAnonymizer:
    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        value = "" if text is None else str(text)
        results = detect_pii(value, self.analyzer)
        if not results:
            return value

        output = value
        for result in sorted(results, key=lambda item: item.start, reverse=True):
            original = output[result.start:result.end]
            if strategy == "replace":
                replacement = self._replacement_for(result.entity_type)
            elif strategy == "mask":
                replacement = self._mask(original)
            elif strategy == "hash":
                replacement = hashlib.sha256(original.encode("utf-8")).hexdigest()
            else:
                raise ValueError(f"Unsupported anonymization strategy: {strategy}")
            output = output[:result.start] + replacement + output[result.end:]
        return output

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df_anon = df.copy()

        if "ho_ten" in df_anon.columns:
            df_anon["ho_ten"] = [f"Patient {i:04d}" for i in range(1, len(df_anon) + 1)]
        if "email" in df_anon.columns:
            df_anon["email"] = [
                f"patient{i:04d}@example.invalid" for i in range(1, len(df_anon) + 1)
            ]
        if "dia_chi" in df_anon.columns:
            df_anon["dia_chi"] = [
                f"Redacted address {i:04d}" for i in range(1, len(df_anon) + 1)
            ]
        if "bac_si_phu_trach" in df_anon.columns:
            df_anon["bac_si_phu_trach"] = [
                f"Doctor {i:04d}" for i in range(1, len(df_anon) + 1)
            ]
        if "ngay_sinh" in df_anon.columns:
            df_anon["ngay_sinh"] = "REDACTED_DATE"
        if "cccd" in df_anon.columns:
            original_cccd = set(df["cccd"].astype(str))
            df_anon["cccd"] = [
                self._indexed_cccd(i, original_cccd) for i in range(1, len(df_anon) + 1)
            ]
        if "so_dien_thoai" in df_anon.columns:
            original_phones = set(df["so_dien_thoai"].astype(str))
            df_anon["so_dien_thoai"] = [
                self._indexed_phone(i, original_phones) for i in range(1, len(df_anon) + 1)
            ]

        return df_anon

    def calculate_detection_rate(self, original_df: pd.DataFrame, pii_columns: list) -> float:
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                if detect_pii(value, self.analyzer):
                    detected += 1

        return detected / total if total > 0 else 0.0

    @staticmethod
    def _fake_cccd() -> str:
        return "".join(str(secrets.randbelow(10)) for _ in range(12))

    @staticmethod
    def _fake_phone() -> str:
        return "0" + secrets.choice(["3", "5", "7", "8", "9"]) + "".join(
            str(secrets.randbelow(10)) for _ in range(8)
        )

    def _fake_cccd_excluding(self, blocked: set[str]) -> str:
        value = self._fake_cccd()
        while value in blocked:
            value = self._fake_cccd()
        return value

    def _fake_phone_excluding(self, blocked: set[str]) -> str:
        value = self._fake_phone()
        while value in blocked:
            value = self._fake_phone()
        return value

    @staticmethod
    def _indexed_cccd(index: int, blocked: set[str]) -> str:
        value = f"999{index:09d}"
        if value in blocked:
            value = f"998{index:09d}"
        return value

    @staticmethod
    def _indexed_phone(index: int, blocked: set[str]) -> str:
        value = f"09{index:08d}"
        if value in blocked:
            value = f"08{index:08d}"
        return value

    def _replacement_for(self, entity_type: str) -> str:
        replacements = {
            "PERSON": fake.name(),
            "EMAIL_ADDRESS": fake.email(),
            "VN_CCCD": self._fake_cccd(),
            "VN_PHONE": self._fake_phone(),
        }
        return replacements.get(entity_type, "[REDACTED]")

    @staticmethod
    def _mask(value: str) -> str:
        if len(value) <= 2:
            return "*" * len(value)
        return value[0] + ("*" * (len(value) - 2)) + value[-1]
