# Nowshera HireOS – Candidate / Recruiter / Admin Hiring Platform

FastAPI backend with a responsive vanilla-JS frontend. It includes candidate, recruiter and admin workflows from the specification, plus a Supabase SQL schema with RLS policies.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. Demo accounts are shown on the sign-in screen. SQLite is used automatically when Supabase variables are not present.

## Supabase

1. Create a Supabase project.
2. Run `supabase/schema.sql` in the SQL editor.
3. Set `SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` in `.env`.
4. The API keeps the service key server-side only. Never expose it in the browser.

## Included

- Candidate signup/sign-in, PDF CV upload (2 MB), job browsing, apply-once validation, applications and withdrawal.
- Recruiter job assignment, applicant review, private notes, AI-summary retry placeholder, ordered stage movement and interview scheduling with overlap checks.
- Admin recruiter management, job lifecycle, assignments and dashboard.
- Automatic job closing rules and final-stage protection.

