# MedViet Governance - Lab 24

## PII Columns
The raw dataset contains these PII columns: `ho_ten`, `cccd`, `ngay_sinh`, `so_dien_thoai`, `email`, `dia_chi`, and `bac_si_phu_trach`.

## Setup
```bash
pip install -r requirements.txt
python scripts/generate_data.py
python -m pytest tests/ -v --tb=short
uvicorn src.api.main:app --reload
```

If Presidio or the Vietnamese spaCy model is unavailable, the project still runs through the local regex/context fallback in `src/pii/detector.py`.

## RBAC Smoke Tests
```bash
curl -H "Authorization: Bearer token-alice" http://localhost:8000/api/patients/raw
curl -H "Authorization: Bearer token-bob" http://localhost:8000/api/patients/raw
curl -H "Authorization: Bearer token-bob" http://localhost:8000/api/patients/anonymized
curl -H "Authorization: Bearer token-carol" http://localhost:8000/api/metrics/aggregated
curl -X DELETE -H "Authorization: Bearer token-bob" http://localhost:8000/api/patients/demo
```

Expected: Alice can read raw data; Bob gets 403 for raw data and delete, but can read anonymized training data; Carol can read aggregated metrics only.

## Encryption Round Trip
```bash
python -c "from src.encryption.vault import SimpleVault; v=SimpleVault(); s='Nguyen Van A - CCCD: 012345678901'; p=v.encrypt_data(s); assert v.decrypt_data(p)==s; print('Encryption test passed')"
```

`.vault_key` is generated locally and excluded from git.

## Security Scans
```bash
mkdir -p reports
bandit -r src/ -f json -o reports/bandit_report.json
trufflehog git file://. --only-verified > reports/trufflehog_report.txt
```

If `trufflehog` is not installed, install it from its official release package and rerun the command. Do not commit real credentials.

## Submission Zip
```bash
zip -r lab24_submission_<ten_sv>.zip src/ tests/ policies/ data/processed/ compliance_checklist.md reports/ requirements.txt README.md .github/hooks/pre-commit
```

Do not include `data/raw/`, `.vault_key`, or real credentials in the final submission.
