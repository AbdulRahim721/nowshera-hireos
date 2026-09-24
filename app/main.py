import os, sqlite3, uuid, hashlib, secrets, json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from fastapi import FastAPI, HTTPException, UploadFile, File, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parent
DB_PATH = os.getenv('DATABASE_PATH', 'hireflow.db')
UPLOADS = ROOT / 'uploads'; UPLOADS.mkdir(exist_ok=True)
app = FastAPI(title='Nowshera HireOS API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
N8N_AI_WEBHOOK=os.getenv('N8N_AI_WEBHOOK','https://ai-skool-n8n-57b1748669d9.herokuapp.com/webhook-test/ats-ai-summary')
N8N_EMAIL_WEBHOOK=os.getenv('N8N_EMAIL_WEBHOOK','https://ai-skool-n8n-57b1748669d9.herokuapp.com/webhook-test/ats-email-event')

def post_n8n(url,payload):
    try:
        req=Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-HireFlow-Event':'ats'})
        with urlopen(req,timeout=12) as response:
            raw=response.read().decode(errors='replace')
            try: body=json.loads(raw)
            except Exception: body={'raw':raw}
            return {'status':response.status,'body':body}
    except Exception as exc:
        print(f'n8n webhook failed: {exc}')
        return None

def recruiter_can_access(con, user, application_id):
    if user['role']=='admin': return True
    return con.execute('''SELECT 1 FROM applications a JOIN assignments x ON x.job_id=a.job_id
                          WHERE a.id=? AND x.recruiter_id=?''',(application_id,user['id'])).fetchone() is not None

def save_ai_result(application_id, result):
    if not result or result.get('status',0) < 200 or result.get('status',0) >= 300: return False
    body=result.get('body') or {}
    summary=body.get('summary') or body.get('ai_summary') or body.get('data',{}).get('summary') if isinstance(body,dict) else None
    if not summary: return False
    con=db(); con.execute('UPDATE applications SET ai_summary=?,updated_at=? WHERE id=?',(json.dumps(summary) if isinstance(summary,(dict,list)) else str(summary),now(),application_id)); con.commit(); con.close(); return True

def send_ai_summary(application_id,payload):
    save_ai_result(application_id,post_n8n(N8N_AI_WEBHOOK,payload))

def db():
    con = sqlite3.connect(DB_PATH); con.row_factory = sqlite3.Row; return con

def init_db():
    con = db(); con.executescript('''
    CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, name TEXT NOT NULL, phone TEXT, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'candidate', active INTEGER NOT NULL DEFAULT 1, cv_path TEXT, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, title TEXT NOT NULL, department TEXT, location TEXT, job_type TEXT, description TEXT, requirements TEXT, deadline TEXT, openings INTEGER DEFAULT 1, status TEXT DEFAULT 'draft', created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS assignments(job_id TEXT, recruiter_id TEXT, PRIMARY KEY(job_id,recruiter_id));
    CREATE TABLE IF NOT EXISTS applications(id TEXT PRIMARY KEY, job_id TEXT, candidate_id TEXT, cv_path TEXT, stage TEXT DEFAULT 'Applied', ai_summary TEXT, note TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(job_id,candidate_id));
    CREATE TABLE IF NOT EXISTS interviews(id TEXT PRIMARY KEY, application_id TEXT, starts_at TEXT, location TEXT, meeting_link TEXT, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS stage_events(id TEXT PRIMARY KEY, application_id TEXT, from_stage TEXT, to_stage TEXT, actor_id TEXT, created_at TEXT NOT NULL);
    ''')
    for idx in con.execute('PRAGMA index_list(applications)').fetchall():
        if idx[2]:
            cols=[r[2] for r in con.execute(f'PRAGMA index_info("{idx[1]}")').fetchall()]
            if set(cols)=={'job_id','candidate_id'}:
                con.executescript('''CREATE TABLE applications_migrated(id TEXT PRIMARY KEY,job_id TEXT,candidate_id TEXT,cv_path TEXT,stage TEXT DEFAULT 'Applied',ai_summary TEXT,note TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL); INSERT INTO applications_migrated SELECT id,job_id,candidate_id,cv_path,stage,ai_summary,note,created_at,updated_at FROM applications; DROP TABLE applications; ALTER TABLE applications_migrated RENAME TO applications;''')
                break
    if con.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        now = datetime.utcnow().isoformat()
        demo=[('admin-1','Ayesha Admin','03000000000','admin@hireflow.local','admin'),('recruiter-1','Hamza Recruiter','03000000001','recruiter@hireflow.local','recruiter'),('candidate-1','Sara Candidate','03000000002','candidate@hireflow.local','candidate')]
        for uid,n,p,e,r in demo: con.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?)',(uid,n,p,e,hashpw('password'),r,1,None,now))
    configured=[
        ('configured-admin',os.getenv('ADMIN_EMAIL','').strip().lower(),os.getenv('ADMIN_PASSWORD',''),'admin'),
        ('configured-recruiter',os.getenv('RECRUITER_EMAIL','').strip().lower(),os.getenv('RECRUITER_PASSWORD',''),'recruiter')
    ]
    for uid,email,password,role in configured:
        if email and password:
            con.execute('''INSERT INTO users(id,name,phone,email,password,role,active,cv_path,created_at) VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(email) DO UPDATE SET password=excluded.password,role=excluded.role,active=1''',(uid,role.title(),'',email,hashpw(password),role,1,None,now()))
    if con.execute('SELECT COUNT(*) FROM jobs').fetchone()[0] == 0:
        job_seed=[
            ('demo-job-1','Frontend Engineer','Product','Remote','Full-time','Build delightful hiring tools and accessible interfaces.','JavaScript, React, CSS, product sense','2027-12-31',2,'open'),
            ('demo-job-2','Software Engineer','Engineering','Hybrid · Nowshera','Full-time','Design reliable services and ship thoughtful product features.','Python, APIs, databases, teamwork','2027-12-31',2,'open'),
            ('demo-job-3','AI Automation Engineer','Automation','Remote','Full-time','Connect AI workflows to useful, human-reviewed business automation.','APIs, n8n, Python, prompt safety','2027-12-31',1,'open')
        ]
        for jid,title,department,location,job_type,description,requirements,deadline,openings,status in job_seed:
            con.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)',(jid,title,department,location,job_type,description,requirements,deadline,openings,status,now()))
    con.commit(); con.close()
def hashpw(v): return hashlib.sha256(v.encode()).hexdigest()
def now(): return datetime.utcnow().isoformat()
def rowdict(r): return dict(r) if r else None
def current_user(authorization: Optional[str]):
    if not authorization or not authorization.startswith('Bearer '): raise HTTPException(401,'Sign in required')
    uid=authorization[7:]; con=db(); u=con.execute('SELECT * FROM users WHERE id=? AND active=1',(uid,)).fetchone(); con.close()
    if not u: raise HTTPException(401,'Invalid session')
    return rowdict(u)
def require(user, *roles):
    if user['role'] not in roles: raise HTTPException(403,'You do not have permission for this action')
def get_app(con, aid):
    r=con.execute('''SELECT a.*, j.title, j.department, j.location, j.requirements, j.status job_status, j.deadline, u.name candidate_name, u.email candidate_email FROM applications a JOIN jobs j ON j.id=a.job_id JOIN users u ON u.id=a.candidate_id WHERE a.id=?''',(aid,)).fetchone()
    return rowdict(r)

class Signup(BaseModel): name:str; phone:str=''; email:EmailStr; password:str=Field(min_length=6)
class Login(BaseModel): email:EmailStr; password:str
class JobIn(BaseModel): title:str; department:str; location:str; job_type:str; description:str; requirements:str; deadline:date; openings:int=Field(ge=1)
class NoteIn(BaseModel): note:str
class StageIn(BaseModel): stage:str
class InterviewIn(BaseModel): starts_at:datetime; location:str=''; meeting_link:str=''
class AssignIn(BaseModel): recruiter_id:str
class RecruiterIn(BaseModel): name:str; email:EmailStr; phone:str=''

@app.on_event('startup')
def startup(): init_db()
@app.get('/')
def home(): return FileResponse(ROOT/'static'/'index.html')
@app.post('/api/auth/signup')
def signup(x:Signup):
    con=db(); uid=str(uuid.uuid4())
    try: con.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?)',(uid,x.name,x.phone,x.email,hashpw(x.password),'candidate',1,None,now())); con.commit()
    except sqlite3.IntegrityError: raise HTTPException(409,'Email already registered')
    finally: con.close()
    return {'token':uid,'user':{'id':uid,'name':x.name,'email':x.email,'role':'candidate'}}
@app.post('/api/auth/login')
def login(x:Login):
    email=str(x.email).strip().lower(); con=db(); u=con.execute('SELECT * FROM users WHERE lower(email)=? AND password=? AND active=1',(email,hashpw(x.password))).fetchone(); con.close()
    if not u: raise HTTPException(401,'Invalid email or password')
    return {'token':u['id'],'user':{'id':u['id'],'name':u['name'],'email':u['email'],'role':u['role']}}
@app.get('/api/me')
def me(authorization:Optional[str]=Header(None)): return current_user(authorization)
@app.post('/api/candidate/cv')
async def upload_cv(file:UploadFile=File(...), authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'candidate')
    if file.content_type!='application/pdf': raise HTTPException(400,'CV must be a PDF')
    data=await file.read()
    if len(data)>2*1024*1024: raise HTTPException(400,'CV must be 2 MB or smaller')
    path=UPLOADS/(u['id']+'.pdf'); path.write_bytes(data)
    con=db(); con.execute('UPDATE users SET cv_path=? WHERE id=?',(str(path),u['id'])); con.commit(); con.close(); return {'message':'CV uploaded'}
@app.get('/api/jobs')
def jobs(authorization:Optional[str]=Header(None)):
    con=db(); con.execute("UPDATE jobs SET status='closed' WHERE status='open' AND deadline<date('now')"); con.commit(); rows=con.execute("SELECT * FROM jobs WHERE status='open' AND deadline>=date('now') ORDER BY deadline").fetchall(); con.close(); return [rowdict(r) for r in rows]
@app.post('/api/admin/jobs')
def create_job(x:JobIn, authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'admin'); jid=str(uuid.uuid4()); con=db(); con.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)',(jid,x.title,x.department,x.location,x.job_type,x.description,x.requirements,x.deadline.isoformat(),x.openings,'draft',now())); con.commit(); con.close(); return {'id':jid}
@app.post('/api/admin/jobs/{jid}/open')
def open_job(jid:str, authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'admin'); con=db(); con.execute("UPDATE jobs SET status='open' WHERE id=?",(jid,)); con.commit(); con.close(); return {'message':'Job opened'}
@app.post('/api/admin/jobs/{jid}/close')
def close_job(jid:str, authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'admin'); con=db(); con.execute("UPDATE jobs SET status='closed' WHERE id=?",(jid,)); con.commit(); con.close(); return {'message':'Job closed'}
@app.post('/api/admin/jobs/{jid}/assign')
def assign(jid:str,x:AssignIn,authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'admin'); con=db(); con.execute('INSERT OR IGNORE INTO assignments VALUES (?,?)',(jid,x.recruiter_id)); con.commit(); con.close(); return {'message':'Recruiter assigned'}
@app.get('/api/admin/recruiters')
def recruiters(authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'admin'); con=db(); rows=con.execute("SELECT id,name,email,phone,active,created_at FROM users WHERE role='recruiter' ORDER BY created_at DESC").fetchall(); con.close(); return [rowdict(r) for r in rows]
@app.post('/api/admin/recruiters')
def add_recruiter(x:RecruiterIn,authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'admin'); con=db(); uid=str(uuid.uuid4())
    try: con.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?)',(uid,x.name,x.phone,x.email,hashpw('password'),'recruiter',1,None,now())); con.commit()
    except sqlite3.IntegrityError: raise HTTPException(409,'A user with this email already exists')
    finally: con.close()
    return {'id':uid,'message':'Recruiter created. Password setup email should be sent by your email provider.'}
@app.post('/api/admin/recruiters/{rid}/deactivate')
def deactivate_recruiter(rid:str,authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'admin'); con=db(); con.execute("UPDATE users SET active=0 WHERE id=? AND role='recruiter'",(rid,)); con.commit(); con.close(); return {'message':'Recruiter deactivated'}
@app.post('/api/applications/{jid}')
def apply(jid:str, background_tasks:BackgroundTasks, authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'candidate'); con=db(); job=con.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
    if not job or job['status']!='open' or job['deadline']<str(date.today()): raise HTTPException(400,'This job is closed or past its deadline')
    if not u['cv_path']: raise HTTPException(400,'Upload your PDF CV first')
    existing=con.execute("SELECT stage FROM applications WHERE job_id=? AND candidate_id=? AND stage<>'Withdrawn'",(jid,u['id'])).fetchone()
    if existing: raise HTTPException(409,'You already have an active application for this job')
    aid=str(uuid.uuid4()); con.execute('INSERT INTO applications VALUES (?,?,?,?,?,?,?,?,?,?)',(aid,jid,u['id'],u['cv_path'],'Applied','Summary not available',None,now(),now())); con.commit(); con.close()
    common={'event_type':'application_received','application_id':aid,'recipient':u['email'],'candidate':{'id':u['id'],'name':u['name'],'email':u['email']},'job':{'id':job['id'],'title':job['title'],'requirements':job['requirements']},'cv_path':u['cv_path']}
    background_tasks.add_task(send_ai_summary,aid,{**common,'event_type':'ai_summary_requested'})
    background_tasks.add_task(post_n8n,N8N_EMAIL_WEBHOOK,common)
    return {'id':aid,'message':'Application received'}
@app.get('/api/candidate/applications')
def my_apps(authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'candidate'); con=db(); rows=con.execute('''SELECT a.*,j.title,j.department,j.location,i.starts_at,i.location interview_location,i.meeting_link FROM applications a JOIN jobs j ON j.id=a.job_id LEFT JOIN interviews i ON i.application_id=a.id WHERE a.candidate_id=? ORDER BY a.created_at DESC''',(u['id'],)).fetchall(); con.close(); return [rowdict(r) for r in rows]
@app.post('/api/applications/{aid}/withdraw')
def withdraw(aid:str,authorization:Optional[str]=Header(None)):
    u=current_user(authorization); con=db(); a=con.execute('SELECT * FROM applications WHERE id=?',(aid,)).fetchone()
    if not a or a['candidate_id']!=u['id']: raise HTTPException(404,'Application not found')
    if a['stage'] in ('Hired','Rejected','Withdrawn'): raise HTTPException(400,'This application can no longer be withdrawn')
    con.execute("UPDATE applications SET stage='Withdrawn',updated_at=? WHERE id=?",(now(),aid)); con.commit(); con.close(); return {'message':'Application withdrawn'}
@app.get('/api/recruiter/applications')
def recruiter_apps(authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'recruiter','admin'); con=db()
    if u['role']=='admin': rows=con.execute('SELECT * FROM applications').fetchall()
    else: rows=con.execute('''SELECT a.* FROM applications a JOIN assignments x ON x.job_id=a.job_id WHERE x.recruiter_id=?''',(u['id'],)).fetchall()
    result=[]
    for r in rows: result.append(get_app(con,r['id']))
    con.close(); return result
@app.post('/api/applications/{aid}/note')
def note(aid:str,x:NoteIn,authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'recruiter','admin'); con=db(); a=get_app(con,aid)
    if not a: raise HTTPException(404,'Application not found')
    if not recruiter_can_access(con,u,aid): con.close(); raise HTTPException(403,'This job is not assigned to you')
    if not recruiter_can_access(con,u,aid): con.close(); raise HTTPException(403,'This job is not assigned to you')
    con.execute('UPDATE applications SET note=?,updated_at=? WHERE id=?',(x.note,now(),aid)); con.commit(); con.close(); return {'message':'Private note saved'}
@app.post('/api/applications/{aid}/summary/retry')
def retry_summary(aid:str,authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'recruiter','admin'); con=db(); a=get_app(con,aid)
    if not a: raise HTTPException(404,'Application not found')
    if not recruiter_can_access(con,u,aid): con.close(); raise HTTPException(403,'This job is not assigned to you')
    payload={'event_type':'ai_summary_requested','application_id':aid,'candidate':{'name':a['candidate_name'],'email':a['candidate_email']},'job':{'title':a['title'],'requirements':a.get('requirements','') if isinstance(a,dict) else ''},'cv_path':a.get('cv_path') if isinstance(a,dict) else None}
    con.close(); result=post_n8n(N8N_AI_WEBHOOK,payload); ok=save_ai_result(aid,result)
    if not ok:
        con=db(); con.execute("UPDATE applications SET ai_summary='Summary not available',updated_at=? WHERE id=?",(now(),aid)); con.commit(); con.close(); raise HTTPException(502,'AI summary is not available. Try again when the AI workflow is running.')
    return {'message':'AI summary regenerated'}
@app.get('/api/applications/{aid}/cv')
def open_cv(aid:str,authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'recruiter','admin'); con=db(); a=con.execute('SELECT a.cv_path,x.recruiter_id FROM applications a LEFT JOIN assignments x ON x.job_id=a.job_id WHERE a.id=?',(aid,)).fetchone(); con.close()
    if not a: raise HTTPException(404,'Application not found')
    if not recruiter_can_access(con,u,aid): raise HTTPException(403,'This job is not assigned to you')
    p=Path(a['cv_path'])
    if not p.exists(): raise HTTPException(404,'CV file is not available')
    return FileResponse(p,media_type='application/pdf',filename='candidate-cv.pdf')
@app.post('/api/applications/{aid}/stage')
def stage(aid:str,x:StageIn,background_tasks:BackgroundTasks,authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'recruiter','admin'); order=['Applied','Shortlisted','Interview','Offer','Hired','Rejected']; con=db(); a=con.execute('SELECT a.*,u.email candidate_email FROM applications a JOIN users u ON u.id=a.candidate_id WHERE a.id=?',(aid,)).fetchone()
    if not a: raise HTTPException(404,'Application not found')
    if a['stage'] in ('Hired','Rejected','Withdrawn'): raise HTTPException(400,'Final applications cannot change stage')
    job=con.execute('SELECT status,openings FROM jobs WHERE id=?',(a['job_id'],)).fetchone()
    if job and job['status']=='closed' and x.stage!='Rejected': raise HTTPException(400,'This job is closed; active applications can only be rejected')
    if x.stage not in order or (x.stage not in ('Rejected',) and order.index(x.stage)!=order.index(a['stage'])+1): raise HTTPException(400,'Stages must move forward one step at a time')
    con.execute('UPDATE applications SET stage=?,updated_at=? WHERE id=?',(x.stage,now(),aid)); con.execute('INSERT INTO stage_events VALUES (?,?,?,?,?,?)',(str(uuid.uuid4()),aid,a['stage'],x.stage,u['id'],now()))
    if x.stage=='Hired' and job and con.execute("SELECT COUNT(*) FROM applications WHERE job_id=? AND stage='Hired'",(a['job_id'],)).fetchone()[0]>=job['openings']:
        con.execute("UPDATE jobs SET status='closed' WHERE id=?",(a['job_id'],))
    con.commit(); con.close()
    if x.stage in ('Hired','Rejected'):
        background_tasks.add_task(post_n8n,N8N_EMAIL_WEBHOOK,{'event_type':'decision','application_id':aid,'stage':x.stage,'candidate_email':a['candidate_email'] if 'candidate_email' in a.keys() else None})
    return {'message':'Stage updated'}
@app.post('/api/applications/{aid}/interview')
def interview(aid:str,x:InterviewIn,background_tasks:BackgroundTasks,authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'recruiter','admin'); con=db(); a=con.execute('SELECT a.*,u.email candidate_email FROM applications a JOIN users u ON u.id=a.candidate_id WHERE a.id=?',(aid,)).fetchone()
    if not a or a['stage']!='Shortlisted': raise HTTPException(400,'Only shortlisted applicants can be scheduled')
    if not recruiter_can_access(con,u,aid): con.close(); raise HTTPException(403,'This job is not assigned to you')
    if x.starts_at <= datetime.utcnow(): raise HTTPException(400,'Interview must be scheduled in the future')
    end=x.starts_at+timedelta(hours=1); conflict=con.execute('''SELECT starts_at FROM interviews WHERE starts_at < ? AND datetime(starts_at,'+1 hour') > ?''',(end.isoformat(),x.starts_at.isoformat())).fetchone()
    if conflict: raise HTTPException(409,'Interview overlaps another interview')
    con.execute('INSERT INTO interviews VALUES (?,?,?,?,?,?)',(str(uuid.uuid4()),aid,x.starts_at.isoformat(),x.location,x.meeting_link,now())); con.execute("UPDATE applications SET stage='Interview',updated_at=? WHERE id=?",(now(),aid)); con.commit(); con.close()
    background_tasks.add_task(post_n8n,N8N_EMAIL_WEBHOOK,{'event_type':'interview_scheduled','application_id':aid,'candidate_email':a['candidate_email'],'starts_at':x.starts_at.isoformat(),'location':x.location,'meeting_link':x.meeting_link})
    return {'message':'Interview scheduled'}
@app.get('/api/admin/dashboard')
def dashboard(authorization:Optional[str]=Header(None)):
    u=current_user(authorization); require(u,'admin'); con=db(); jobs=con.execute('SELECT id,title,status,openings FROM jobs ORDER BY created_at DESC').fetchall(); counts=con.execute('SELECT job_id,stage,COUNT(*) total FROM applications GROUP BY job_id,stage').fetchall(); con.close(); return {'jobs':[rowdict(r) for r in jobs],'counts':[rowdict(r) for r in counts]}

