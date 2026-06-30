# ND13/2023 Compliance Checklist - MedViet AI Platform

## A. Data Localization
- [x] Patient data is stored on Vietnam-hosted infrastructure. Technical solution: production buckets/databases must use VN region tags and OPA blocks restricted exports when `destination_country != "VN"`.
- [x] Backups remain inside Vietnam. Technical solution: backup jobs target VN-only storage accounts and emit audit logs for restore/export events.
- [x] External transfer logging is required. Technical solution: API gateway and data export workers log user, role, resource, destination country, timestamp, and decision.

## B. Explicit Consent
- [x] Consent is collected before AI training. Technical solution: add `consent_status`, `consent_scope`, and `consent_timestamp` to the patient source system before datasets are released.
- [x] Right to erasure is supported. Technical solution: admin-only delete endpoint accepts `patient_id`, records the erasure request, and downstream jobs exclude revoked IDs.
- [x] Consent records include timestamps. Technical solution: consent events are append-only and linked to `patient_id`.

## C. Breach Notification 72h
- [x] Incident response plan exists. Technical solution: security runbook assigns severity, owner, containment steps, and regulator notification workflow.
- [x] Automated breach detection is planned. Technical solution: alert on abnormal API 403/401 spikes, unusual export volume, and secret-scan findings.
- [x] 72-hour notification workflow is defined. Technical solution: incident ticket must include detection time, DPO approval, affected data classes, and notification deadline.

## D. DPO Appointment
- [x] Data Protection Officer placeholder assigned.
- [x] DPO contact: dpo-placeholder@medviet.example.

## E. Technical Controls
| ND13 Requirement | Technical Control | Status | Owner |
|---|---|---|---|
| Data minimization | PII detection and anonymization pipeline for names, CCCD, phones, emails, addresses, and doctors | Done | AI Team |
| Access control | Casbin RBAC in FastAPI plus OPA policy for data export decisions | Done | Platform Team |
| Encryption at rest | AES-256-GCM envelope encryption with local KEK file excluded by `.gitignore` | Done | Infra Team |
| Encryption in transit | Serve FastAPI behind TLS 1.3 reverse proxy in production | Planned | Infra Team |
| Audit logging | Log auth subject, role, endpoint, resource, action, decision, and request id to SIEM | Planned | Platform Team |
| Breach detection | Prometheus/SIEM anomaly rules for failed auth, high-volume exports, and unexpected geographies | Planned | Security Team |
| Security scan | Bandit JSON report and TruffleHog report under `reports/` | Done | Security Team |
| Data localization | OPA denies restricted exports outside VN | Done | Compliance Team |
| Consent management | Consent fields and revocation workflow mapped to training-data release | Planned | Product Team |
| Right to erasure | Admin delete endpoint and downstream exclusion list | Done | Platform Team |
