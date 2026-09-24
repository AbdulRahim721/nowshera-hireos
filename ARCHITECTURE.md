# HireFlow data and automation map

```text
Browser UI (app/static)
        |
        v
FastAPI API (app/main.py) -- role checks, stage rules, CV validation
        |
        +--> SQLite hireflow.db + app/uploads/ (current local runtime)
        |
        +--> Supabase Project 3 migration/storage policies (cloud target)
        |
        +--> n8n AI Summary webhook
        +--> n8n Email Event webhook
```

Current local persistence:

- Users, jobs, applications, interviews and stage history: `hireflow.db`.
- Uploaded PDFs: `app/uploads/`.
- Supabase SQL/migrations: `supabase/project-3/`.
- n8n URLs: `.env` only; never expose service keys in frontend files.

The browser talks to FastAPI, not directly to n8n. This keeps AI and email credentials out of browser Network requests.
