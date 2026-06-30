from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException

from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA = PROJECT_ROOT / "data" / "raw" / "patients_raw.csv"
ANON_DATA = PROJECT_ROOT / "data" / "processed" / "patients_anonymized.csv"


def _load_raw_data() -> pd.DataFrame:
    if not RAW_DATA.exists():
        raise HTTPException(
            status_code=404,
            detail="Raw data not found. Run: python scripts/generate_data.py",
        )
    return pd.read_csv(RAW_DATA, dtype=str)


@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(current_user: dict = Depends(get_current_user)):
    df = _load_raw_data()
    return df.head(10).to_dict(orient="records")


@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(current_user: dict = Depends(get_current_user)):
    df = _load_raw_data()
    df_anon = anonymizer.anonymize_dataframe(df)
    ANON_DATA.parent.mkdir(parents=True, exist_ok=True)
    df_anon.to_csv(ANON_DATA, index=False)
    return df_anon.to_dict(orient="records")


@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(current_user: dict = Depends(get_current_user)):
    df = _load_raw_data()
    metrics = (
        df.groupby("benh", dropna=False)
        .size()
        .reset_index(name="patient_count")
        .to_dict(orient="records")
    )
    return {"metrics": metrics}


@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(patient_id: str, current_user: dict = Depends(get_current_user)):
    return {"status": "deleted", "patient_id": patient_id}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
