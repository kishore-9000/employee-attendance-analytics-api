# Requirements

> This document lists requirements derived from the HROne assignment prompt.
> No original assignment kit was available; requirements are inferred from the
> assignment description. Mark any items that conflict with the actual kit.

## Functional Requirements

### FR-01 Punch-In
An employee can record a punch-in event with their employee ID and a UTC timestamp.

### FR-02 Duplicate Punch-In Prevention
Only one punch-in is allowed per employee per calendar day. Duplicate attempts return HTTP 409.

### FR-03 Punch-Out
A punch-out can be recorded against an existing attendance record. The punch-out must be chronologically after the punch-in.

### FR-04 Duplicate Punch-Out Prevention
If punch-out is already recorded, a second punch-out attempt returns HTTP 409.

### FR-05 Attendance Retrieval by ID
A single attendance record can be retrieved by its unique identifier.

### FR-06 Employee Attendance History
All attendance records for a given employee can be retrieved with pagination.

### FR-07 Manual Correction — Punch-In
An authorised user can correct the punch-in timestamp on an existing attendance record.

### FR-08 Manual Correction — Punch-Out
An authorised user can correct the punch-out timestamp on an existing attendance record.

### FR-09 Correction Audit Trail
Every manual correction is recorded with: old values, new values, who made the change, when, and why.

### FR-10 Audit Trail Is Append-Only
Corrections are never deleted or overwritten.

### FR-11 Daily Analytics
The system provides per-day attendance counts (present, absent, incomplete) for a date range.

### FR-12 Employee Analytics
The system provides per-employee attendance summaries including total work minutes.

### FR-13 Overall Summary Analytics
The system provides overall attendance counts and total work minutes, optionally filtered by date range.

### FR-14 Work Duration Calculation
Work duration in minutes is computed from punch_in and punch_out and stored on the attendance record.

### FR-15 Status Tracking
Each attendance record has a status: `present`, `absent`, or `incomplete`.

## Non-Functional Requirements

### NFR-01 API Documentation
The API exposes Swagger UI at `/docs` and ReDoc at `/redoc`.

### NFR-02 Configuration via Environment Variables
All sensitive and environment-specific configuration is provided via `.env` (excluded from version control).

### NFR-03 No Secrets in Code
No credentials, passwords, or connection strings are hardcoded.

### NFR-04 Automated Test Suite
All major endpoints and business rules are covered by automated tests runnable with `pytest`.

### NFR-05 Local MongoDB Support
The application supports a local MongoDB instance and MongoDB Atlas via configuration.

### NFR-06 Sample Data
A seed script loads demonstration data safely (idempotent).
