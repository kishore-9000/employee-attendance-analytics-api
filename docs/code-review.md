# Code Review: Employee Attendance Starter Application

> **Note**: No starter application was provided with the assignment kit. This document
> records the review of the application implemented for this assignment and documents
> findings that should be addressed before production deployment.

---

## Review Methodology

Each finding is rated by **priority**: Critical / High / Medium / Low.

---

## Finding 1 — No Authentication or Authorisation

| Field | Detail |
|---|---|
| **File** | `app/api/routes/corrections.py`, all routes |
| **Problem** | Any caller can apply corrections or retrieve audit trails. |
| **Why it matters** | Attendance corrections are sensitive HR operations. |
| **Risk** | An external actor could alter attendance records. |
| **Fix** | Implement API key, JWT, or OAuth2 authentication. Enforce role checks (e.g., HR admin only for corrections). |
| **Priority** | **Critical** (for production) |
| **Status** | Not implemented — out of scope for this assignment as no authentication mechanism was specified. Documented as a limitation. |

---

## Finding 2 — No Rate Limiting

| Field | Detail |
|---|---|
| **File** | `app/main.py` |
| **Problem** | Endpoints accept unlimited requests. |
| **Why it matters** | Abuse can cause DoS or excessive DB load. |
| **Fix** | Add a rate limiter (e.g., `slowapi`) at the API gateway or middleware level. |
| **Priority** | **High** |

---

## Finding 3 — Timezone Ambiguity in Punch-In Date

| Field | Detail |
|---|---|
| **File** | `app/services/attendance_service.py`, line `date_str = payload.punch_in.strftime("%Y-%m-%d")` |
| **Problem** | The date is derived from the UTC timestamp. If an employee punches in at 11:30 PM IST (18:00 UTC), the date recorded is the UTC date, not the employee's local date. |
| **Why it matters** | Attendance reports may show the wrong day for late-night shifts. |
| **Fix** | Accept an optional `timezone` field in the request, or require clients to send the local date explicitly. |
| **Priority** | **Medium** |

---

## Finding 4 — Correction Allows No Net Change

| Field | Detail |
|---|---|
| **File** | `app/services/correction_service.py` |
| **Problem** | A user could submit a correction where the provided value equals the existing value (no-op correction). An audit entry is still recorded, adding noise. |
| **Fix** | Compare new values against existing values before inserting an audit entry; reject the request if nothing changed. |
| **Priority** | **Medium** |

---

## Finding 5 — FakeDB Aggregate Returns Empty List

| Field | Detail |
|---|---|
| **File** | `tests/conftest.py`, `FakeCollection.aggregate()` |
| **Problem** | The FakeDB's `aggregate()` always returns `[]`, so analytics endpoints always show zero results in unit tests. |
| **Why it matters** | Incorrect analytics calculations would not be caught by unit tests. |
| **Fix** | Write integration tests against a real MongoDB to validate aggregation pipeline results. Document this limitation clearly. |
| **Priority** | **High** |

---

## Finding 6 — No Input Sanitisation for Injection

| Field | Detail |
|---|---|
| **File** | All routes accepting `employee_id`, `attendance_id` |
| **Problem** | MongoDB is not vulnerable to SQL injection, but malformed ObjectId strings or extremely long strings could cause unexpected behaviour. |
| **Fix** | Validate `employee_id` format (e.g., alphanumeric + hyphen only). Validate `attendance_id` as a 24-hex-char ObjectId before querying. |
| **Priority** | **Low** |

---

## Summary

| Finding | Priority | Status |
|---|---|---|
| No authentication | Critical | Known limitation |
| No rate limiting | High | Known limitation |
| Timezone ambiguity | Medium | Documented assumption |
| No-op corrections not rejected | Medium | Improvement |
| FakeDB aggregate gap | High | Covered by integration test strategy |
| Input sanitisation | Low | Improvement |
