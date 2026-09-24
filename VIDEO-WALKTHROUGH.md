# HireFlow AI explainer video

## Important truth about the current build

When the FastAPI server is running, application data is currently saved in the local SQLite file configured by `DATABASE_PATH` (normally `hireflow.db`). CV files are saved under `app/uploads/`.

The Supabase Project 3 SQL folder is ready, but the current API has not been switched completely from SQLite to Supabase because the Supabase publishable key and a verified database connection were not available. Run the Project 3 migration and finish the Supabase adapter before calling cloud storage live.

If Python is unavailable, `server.mjs` is a demo fallback: its data is in memory and is lost when the process stops. It is for UI testing only.

## 3-minute AI video script

### Scene 1 — The problem (0:00–0:20)

Visual: scattered email, WhatsApp messages and a spreadsheet transform into the HireFlow dashboard.

Voiceover: “HireFlow replaces scattered CVs and spreadsheets with one secure hiring workspace for candidates, recruiters and admins.”

### Scene 2 — Architecture (0:20–0:40)

Visual: Frontend → FastAPI API → SQLite now / Supabase Project 3 when configured → n8n automation.

Voiceover: “The browser shows the interface. FastAPI checks every permission and saves the data. The database layer is currently local SQLite, while the Supabase Project 3 migration is prepared for cloud persistence. n8n is called only by the backend.”

### Scene 3 — Candidate account and CV (0:40–1:00)

Visual: candidate sign-up, name/phone/email fields, PDF upload and 2 MB validation.

Voiceover: “A candidate creates an account and uploads a PDF CV up to 2 MB. The CV used for each application is preserved, even if the candidate later uploads a newer version.”

### Scene 4 — Browse and apply (1:00–1:20)

Visual: open-job cards showing title, department, location, type and deadline; click Apply.

Voiceover: “Candidates see only open jobs. The server blocks duplicate applications, closed jobs and expired deadlines. The apply screen explains that AI may summarise the CV, but people make every decision.”

### Scene 5 — n8n automation (1:20–1:45)

Visual: application saved, two arrows from FastAPI to n8n AI Summary and Email Event workflows.

Voiceover: “After the application is saved, FastAPI sends an AI summary event and an application-received email event to n8n. If n8n is unavailable, the application remains saved and the recruiter sees Summary not available.”

On-screen payload labels: `application_id`, candidate email, job requirements, fixed CV path, `event_type`.

### Scene 6 — Recruiter review (1:45–2:05)

Visual: assigned-applicant card, Open CV, AI summary, Try again and private note controls.

Voiceover: “Recruiters see only jobs assigned to them. They can open the CV, read the AI helper, regenerate a missing summary and add private notes. The AI never ranks, scores or makes a hiring decision.”

### Scene 7 — Stages and interview (2:05–2:25)

Visual: Applied → Shortlisted → Interview → Offer → Hired pipeline; calendar collision warning.

Voiceover: “The API enforces forward-only stages. Rejection is allowed before Hired. Interviews are one hour, must be in the future and cannot overlap another interview for the recruiter.”

### Scene 8 — Admin control room (2:25–2:45)

Visual: create Draft job, open it, assign recruiter, stage counts, close job.

Voiceover: “Admins create draft jobs, open and close them, add or deactivate recruiters, assign ownership and see counts for every stage. Jobs close automatically after the deadline or when openings are filled.”

### Scene 9 — Privacy (2:45–3:00)

Visual: lock icons around candidate CV, notes and AI summary; browser Network tab shows no AI key.

Voiceover: “Candidates see only their own applications. Recruiter notes and AI summaries stay private. The browser never calls the AI service and secret keys stay on the server or in n8n.”

## Demo checklist

1. Start `start.ps1` and open `http://127.0.0.1:8000/`.
2. In both n8n test workflows, click **Execute workflow** first.
3. Apply with a synthetic PDF.
4. Confirm the application is saved and inspect n8n executions.
5. Test duplicate apply, closed job, stage skip, overlap, privacy and mobile view.

## n8n note

The supplied `/webhook-test/` URLs returned HTTP 404 until their workflows are listening. For an always-on site, activate the workflows and use production `/webhook/` URLs in `.env`.
