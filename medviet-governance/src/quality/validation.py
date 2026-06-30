import re
from pathlib import Path

import pandas as pd


VALID_DISEASES = {
    "Tieu duong",
    "Huyet ap cao",
    "Tim mach",
    "Khoe manh",
    "Tiểu đường",
    "Huyết áp cao",
    "Tim mạch",
    "Khỏe mạnh",
    "Tiá»ƒu Ä‘Æ°á»ng",
    "Huyáº¿t Ã¡p cao",
    "Tim máº¡ch",
    "Khá»e máº¡nh",
}
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def build_patient_expectation_suite() -> dict:
    return {
        "suite_name": "patient_data_suite",
        "expectations": [
            "patient_id not null",
            "patient_id unique",
            "cccd length 12",
            "ket_qua_xet_nghiem between 0 and 50",
            "benh in valid disease list",
            "email matches regex",
        ],
    }


def validate_anonymized_data(filepath: str) -> dict:
    path = Path(filepath)
    df = pd.read_csv(path, dtype=str)
    failed_checks: list[str] = []

    required_columns = [
        "patient_id",
        "cccd",
        "so_dien_thoai",
        "email",
        "benh",
        "ket_qua_xet_nghiem",
    ]

    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        failed_checks.append(f"Missing required columns: {missing_columns}")

    if "patient_id" in df.columns:
        if df["patient_id"].isna().any():
            failed_checks.append("patient_id contains null values")
        if not df["patient_id"].is_unique:
            failed_checks.append("patient_id contains duplicate values")

    if "cccd" in df.columns:
        cccd_values = df["cccd"].astype(str)
        if not cccd_values.str.fullmatch(r"\d{12}").all():
            failed_checks.append("cccd must contain exactly 12 digits after replacement")

    if "so_dien_thoai" in df.columns:
        phones = df["so_dien_thoai"].astype(str)
        if not phones.str.fullmatch(r"0[35789]\d{8}").all():
            failed_checks.append("so_dien_thoai must match Vietnamese phone pattern")

    if "ket_qua_xet_nghiem" in df.columns:
        values = pd.to_numeric(df["ket_qua_xet_nghiem"], errors="coerce")
        if values.isna().any() or not values.between(0, 50).all():
            failed_checks.append("ket_qua_xet_nghiem must be numeric and between 0 and 50")

    if "benh" in df.columns and not df["benh"].isin(VALID_DISEASES).all():
        failed_checks.append("benh contains values outside the approved disease list")

    if "email" in df.columns:
        email_ok = df["email"].astype(str).map(lambda value: bool(EMAIL_REGEX.match(value)))
        if not email_ok.all():
            failed_checks.append("email contains invalid email values")

    raw_path = Path("data/raw/patients_raw.csv")
    if raw_path.exists():
        original_rows = len(pd.read_csv(raw_path, dtype=str))
        if len(df) != original_rows:
            failed_checks.append(
                f"Row count changed: anonymized={len(df)}, original={original_rows}"
            )

    return {
        "success": not failed_checks,
        "failed_checks": failed_checks,
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns),
            "null_counts": df.isna().sum().to_dict(),
        },
    }
