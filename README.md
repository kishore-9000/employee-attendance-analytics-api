# HROne Employee Attendance & Analytics REST API

This is the backend REST API for HROne Employee Attendance & Analytics, built with FastAPI and MongoDB.

## Tech Stack
- **Python 3.11+**
- **FastAPI**
- **MongoDB** (via PyMongo)
- **Pydantic** for data validation

## Local Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd employee-attendance-analytics-api
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Copy `.env.example` to `.env` and configure your settings.
   ```bash
   cp .env.example .env
   ```

5. **Run the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **View API Docs:**
   Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

## Testing
Run the tests using pytest:
```bash
pytest
```
