-- Run this in Supabase SQL Editor. Keep service-role credentials server-side.
create extension if not exists pgcrypto;
create type public.user_role as enum ('candidate','recruiter','admin');
create type public.job_status as enum ('draft','open','closed');
create type public.application_stage as enum ('Applied','Shortlisted','Interview','Offer','Hired','Rejected','Withdrawn');
create table public.profiles(id uuid primary key references auth.users(id) on delete cascade,name text not null,phone text,email text not null,role public.user_role not null default 'candidate',active boolean not null default true,cv_path text,created_at timestamptz not null default now());
create table public.jobs(id uuid primary key default gen_random_uuid(),title text not null,department text not null,location text not null,job_type text not null check(job_type in ('Full-time','Part-time','Internship')),description text not null,requirements text not null,deadline date not null,openings int not null check(openings>0),status public.job_status not null default 'draft',created_at timestamptz not null default now());
create table public.job_recruiters(job_id uuid references public.jobs(id) on delete cascade,recruiter_id uuid references public.profiles(id) on delete cascade,primary key(job_id,recruiter_id));
create table public.applications(id uuid primary key default gen_random_uuid(),job_id uuid references public.jobs(id) on delete cascade,candidate_id uuid references public.profiles(id) on delete cascade,cv_path text not null,stage public.application_stage not null default 'Applied',ai_summary jsonb,note text,created_at timestamptz not null default now(),updated_at timestamptz not null default now());
create table public.interviews(id uuid primary key default gen_random_uuid(),application_id uuid unique references public.applications(id) on delete cascade,starts_at timestamptz not null,location text,meeting_link text,created_at timestamptz not null default now());
create table public.stage_events(id uuid primary key default gen_random_uuid(),application_id uuid references public.applications(id) on delete cascade,from_stage public.application_stage,to_stage public.application_stage,actor_id uuid references public.profiles(id),created_at timestamptz not null default now());
create unique index one_active_application_per_job on public.applications(job_id,candidate_id) where stage <> 'Withdrawn';
alter table public.profiles enable row level security; alter table public.jobs enable row level security; alter table public.job_recruiters enable row level security; alter table public.applications enable row level security; alter table public.interviews enable row level security; alter table public.stage_events enable row level security;
create policy "open jobs public" on public.jobs for select using(status='open' and deadline>=current_date);
create policy "candidate own profile" on public.profiles for select using(id=auth.uid());
create policy "candidate own applications" on public.applications for select using(candidate_id=auth.uid());
create policy "candidate create own application" on public.applications for insert with check(candidate_id=auth.uid());
create policy "candidate withdraw own application" on public.applications for update using(candidate_id=auth.uid()) with check(candidate_id=auth.uid());
create policy "candidate own interviews" on public.interviews for select using(application_id in(select id from public.applications where candidate_id=auth.uid()));
-- Recruiter/admin writes should go through FastAPI using the server-side service key and explicit role checks.
grant usage on schema public to anon, authenticated;
grant select on public.jobs to anon, authenticated;
grant select,insert,update on public.profiles,public.applications,public.interviews to authenticated;
