# HireFlow Project 3 – Supabase data folder

This folder is the Supabase source of truth for HireFlow. Run the migration in the Supabase SQL Editor, then create the `candidate-cvs` Storage bucket using `storage.sql`.

Setup:
1. Create a Supabase project named `project-3`.
2. Copy `.env.example` to `.env` in the API root.
3. The supplied project URL is already placed in `.env`; add the publishable/anon key. Keep the service-role key server-side only.
4. Run `migrations/202609230001_project_3.sql`.
5. Run `storage.sql`.

RLS is enabled. Candidate data is owner-scoped; recruiter/admin operations should go through FastAPI role checks.
