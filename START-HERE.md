# HireFlow – VS Code start guide

This is the website project. Open this folder in VS Code:

`C:\Users\Fertile\Documents\Codex\2026-09-23\candidate-someone-looking-for-a-job-3`

Then open the integrated terminal and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Or simply run `.\start.ps1`. It automatically uses the FastAPI backend when Python is installed. If Python is unavailable, it starts a Node.js demo server so the website still opens on port 8000.

Browse to `http://127.0.0.1:8000`.

Demo accounts:

- Admin: `admin@hireflow.local` / `password`
- Recruiter: `recruiter@hireflow.local` / `password`
- Candidate: `candidate@hireflow.local` / `password`

The Supabase SQL is in `supabase/schema.sql`. Put real credentials in `.env`; never commit the service-role key.
