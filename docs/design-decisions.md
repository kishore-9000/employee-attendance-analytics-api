# Design Decisions

## 1. Layered Architecture

**Problem**: Mixing route handlers, business logic, and database calls makes the codebase hard to test and maintain.

**Approach**: Three distinct layers — Routes → Services → Repositories.

**Why**: Routes handle HTTP only. Services enforce business rules. Repositories handle MongoDB queries. Each layer can be tested independently.

**Trade-offs**: More files for a small project, but much easier to maintain and extend.

---

## 2. Synchronous PyMongo (not async)

**Problem**: FastAPI supports both sync and async handlers. Motor is the async MongoDB driver.

**Approach**: PyMongo (synchronous) with standard `def` route handlers.

**Why**: PyMongo is more mature, better documented, and simpler for this assignment scope. FastAPI runs sync handlers in a thread pool automatically, so there is no performance cliff for low concurrency. Mixing sync DB access with async route handlers would require explicit `run_in_executor` calls and adds complexity without benefit at this scale.

**Limitation**: Under very high concurrency, Motor (async) would be preferable.

---

## 3. Single MongoClient per Process

**Problem**: Creating a `MongoClient` per request is expensive and exhausts connection pools.

**Approach**: One `MongoClient` created at startup via FastAPI's `lifespan` context, stored as a module-level global, and closed at shutdown.

**Why**: This is the PyMongo-recommended pattern. The client is thread-safe and manages an internal connection pool.

---

## 4. Correction History — Append-Only `$push`

**Problem**: If corrections overwrite existing data, the audit trail is lost.

**Approach**: `$push` is used to append each correction entry atomically. The corrections array is never replaced or cleared.

**Why**: Preserves full audit history. Each entry captures `old_values`, `new_values`, `corrected_by`, `corrected_at`, and `reason`.

**Trade-off**: Documents grow over time with many corrections. For very high correction volumes, a separate `corrections` collection would be more appropriate, but a separate collection adds JOIN complexity not justified at this scale.

---

## 5. Status and Duration Derived in Service, Not Database

**Problem**: Where should `status` and `work_duration_minutes` be computed?

**Approach**: Computed in `attendance_service.py` and `correction_service.py` whenever punch_in or punch_out changes, then stored in MongoDB.

**Why**: Storing derived fields avoids recomputing them on every read — a read-optimised pattern appropriate for an HR analytics API where reads dominate. The alternative (compute on read via aggregation) is less performant and adds pipeline complexity to every query.

---

## 6. Date String Key for Uniqueness (`YYYY-MM-DD`)

**Problem**: How to enforce one attendance record per employee per day?

**Approach**: Store `date` as a string (`YYYY-MM-DD`) derived from `punch_in` (UTC). Use `(employee_id, date)` lookup to detect duplicates.

**Why**: Simple and legible. MongoDB does not have a native date-only type; using a string makes aggregation grouping by date straightforward.

**Limitation**: If punch_in spans midnight in a local timezone, the UTC date may differ from the employee's local date. A future improvement would accept an explicit timezone or store local date separately.

---

## 7. Analytics via MongoDB Aggregation Pipelines

**Problem**: Computing attendance stats in Python requires loading all records into memory.

**Approach**: All analytics use `$group`, `$match`, `$project` pipelines executed entirely in MongoDB.

**Why**: Efficient, scalable, and correct. MongoDB performs the computation close to the data. Three pipelines cover all required analytics: daily summary, per-employee summary, and overall summary.

---

## 8. FakeDB for Unit Tests

**Problem**: Running `pytest` against a real MongoDB makes tests slow and non-portable.

**Approach**: A dict-based `FakeDB` / `FakeCollection` is monkeypatched in for unit tests. Integration tests (marked `@pytest.mark.integration`) require a real MongoDB.

**Why**: Unit tests run anywhere without infrastructure. Aggregation pipelines, which cannot be replicated in a fake, are covered by integration tests only.

**Limitation**: The FakeDB does not replicate every MongoDB behaviour (e.g., complex aggregation stages). Any test that relies on aggregation results should be run as an integration test.

---

## 9. Error Handling — No Stack Traces in Responses

**Problem**: Exposing internal errors in HTTP responses is a security risk and a poor user experience.

**Approach**: Global exception handlers in `main.py` catch `PyMongoError` and generic `Exception`, log the full details, and return a sanitised JSON error with an appropriate HTTP status code.

**Why**: Users receive actionable messages; operators get full details in logs.

---

## 10. Index Strategy

Three indexes on the `attendance` collection:

| Index | Purpose |
|---|---|
| `(employee_id, punch_in DESC)` | Employee attendance history queries |
| `(date ASC)` | Date-range analytics and daily lookup |
| `(status ASC)` | Status-based filtering |

A unique index on `(employee_id, date)` was considered but not added because the business rule is enforced in the service layer, and a unique index would prevent manual corrections from changing the date (edge case). The service-layer check is sufficient at this scale.
