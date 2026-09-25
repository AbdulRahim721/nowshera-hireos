import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const staticDir = path.join(root, 'app', 'static');
const envFile = path.join(root, '.env');
if (fs.existsSync(envFile)) for (const line of fs.readFileSync(envFile,'utf8').split(/\r?\n/)) { const m=line.match(/^([A-Z0-9_]+)=(.*)$/); if(m&&!process.env[m[1]]) process.env[m[1]]=m[2]; }
const aiWebhook=process.env.N8N_AI_WEBHOOK||'https://ai-skool-n8n-57b1748669d9.herokuapp.com/webhook-test/ats-ai-summary';
const emailWebhook=process.env.N8N_EMAIL_WEBHOOK||'https://ai-skool-n8n-57b1748669d9.herokuapp.com/webhook-test/ats-email-event';
const supabaseUrl=process.env.SUPABASE_URL||'';
const supabaseKey=process.env.SUPABASE_KEY||'';
async function postWebhook(url,payload){try{const r=await fetch(url,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(payload)});console.log('n8n',r.status,url.split('/').pop())}catch(e){console.log('n8n webhook unavailable',e.message)}}
async function supabase(path,options={}){if(!supabaseUrl||!supabaseKey)throw Error('Supabase is not configured');const r=await fetch(supabaseUrl+path,{...options,headers:{apikey:supabaseKey,authorization:options.authorization||'Bearer '+supabaseKey,'content-type':'application/json',...(options.headers||{})}});const text=await r.text();let data={};try{data=text?JSON.parse(text):{}}catch{data={message:text}};if(!r.ok)throw Error(data.msg||data.message||data.error_description||'Supabase request failed');return data}
async function supabaseSignup(data){const auth=await supabase('/auth/v1/signup',{method:'POST',body:JSON.stringify({email:String(data.email).trim().toLowerCase(),password:data.password,data:{name:String(data.name).trim(),phone:String(data.phone||'')}})});const uid=auth.user?.id;if(uid&&auth.access_token){await supabase('/rest/v1/profiles',{method:'POST',headers:{Prefer:'return=minimal',authorization:'Bearer '+auth.access_token},body:JSON.stringify({id:uid,name:String(data.name).trim(),phone:String(data.phone||''),email:String(data.email).trim().toLowerCase(),role:'candidate',active:true})})}return {auth,uid}}
async function supabaseLogin(data){const email=String(data.email).trim().toLowerCase();const auth=await supabase('/auth/v1/token?grant_type=password',{method:'POST',body:JSON.stringify({email,password:data.password})});const uid=auth.user?.id;let profile=null;if(uid){const rows=await supabase(`/rest/v1/profiles?id=eq.${encodeURIComponent(uid)}&select=id,name,email,role,active,cv_path`,{headers:{authorization:'Bearer '+auth.access_token}});profile=Array.isArray(rows)?rows[0]:null}if(uid)users[email]={id:uid,name:profile?.name||auth.user.user_metadata?.name||email.split('@')[0],email,role:profile?.role||'candidate',password:data.password,cv_path:profile?.cv_path||null,supabase_token:auth.access_token};return auth}
const jobs = [
  {id:'demo-job-1',title:'Frontend Engineer',department:'Product',location:'Remote',job_type:'Full-time',description:'Build delightful hiring tools and accessible interfaces.',requirements:'JavaScript, React, CSS, product sense',deadline:'2027-12-31',openings:2,status:'open'},
  {id:'demo-job-2',title:'Software Engineer',department:'Engineering',location:'Hybrid · Nowshera',job_type:'Full-time',description:'Design reliable services and ship thoughtful product features.',requirements:'Python, APIs, databases, teamwork',deadline:'2027-12-31',openings:2,status:'open'},
  {id:'demo-job-3',title:'AI Automation Engineer',department:'Automation',location:'Remote',job_type:'Full-time',description:'Connect AI workflows to useful, human-reviewed business automation.',requirements:'APIs, n8n, Python, prompt safety',deadline:'2027-12-31',openings:1,status:'open'}
];
const supabaseJobIds={'demo-job-1':'00000000-0000-0000-0000-000000000001','demo-job-2':'00000000-0000-0000-0000-000000000002','demo-job-3':'00000000-0000-0000-0000-000000000003'};
const users = {
  'admin@hireflow.local': {id:'admin-1',name:'Ayesha Admin',email:'admin@hireflow.local',role:'admin'},
  'recruiter@hireflow.local': {id:'recruiter-1',name:'Hamza Recruiter',email:'recruiter@hireflow.local',role:'recruiter'},
  'candidate@hireflow.local': {id:'candidate-1',name:'Sara Candidate',email:'candidate@hireflow.local',role:'candidate'}
};
if(process.env.ADMIN_EMAIL&&process.env.ADMIN_PASSWORD) users[process.env.ADMIN_EMAIL.trim().toLowerCase()]={id:'configured-admin',name:'Admin',email:process.env.ADMIN_EMAIL.trim().toLowerCase(),role:'admin',password:process.env.ADMIN_PASSWORD};
if(process.env.RECRUITER_EMAIL&&process.env.RECRUITER_PASSWORD) users[process.env.RECRUITER_EMAIL.trim().toLowerCase()]={id:'configured-recruiter',name:'Recruiter',email:process.env.RECRUITER_EMAIL.trim().toLowerCase(),role:'recruiter',password:process.env.RECRUITER_PASSWORD};
const applications = [];
function json(res, status, data){res.writeHead(status, {'Content-Type':'application/json','Access-Control-Allow-Origin':'*'});res.end(JSON.stringify(data));}
function body(req){return new Promise(resolve=>{let b='';req.on('data',c=>b+=c);req.on('end',()=>{try{resolve(b?JSON.parse(b):{})}catch{resolve({})}})})}
function user(req){const id=(req.headers.authorization||'').replace('Bearer ','');return Object.values(users).find(x=>x.id===id)||null}
const server=http.createServer(async (req,res)=>{
  const u=new URL(req.url,'http://127.0.0.1:8000');
  if(req.method==='OPTIONS'){res.writeHead(204);return res.end()}
  if(u.pathname.startsWith('/api/')){
    const data=await body(req);
    if(u.pathname==='/api/auth/login'&&req.method==='POST'){const email=String(data.email||'').trim().toLowerCase();let found=users[email];if(!found||((found.password||'password')!==data.password)){try{await supabaseLogin(data);found=users[email]}catch{return json(res,401,{detail:'Invalid email or password'})}}return json(res,200,{token:found.id,user:{id:found.id,name:found.name,email:found.email,role:found.role}})}
    if(u.pathname==='/api/auth/signup'&&req.method==='POST'){const email=String(data.email||'').trim().toLowerCase();if(!email||!data.name||String(data.password||'').length<6)return json(res,400,{detail:'Name, email, and a password of at least 6 characters are required.'});if(users[email])return json(res,409,{detail:'An account with this email already exists.'});try{const result=await supabaseSignup(data);if(!result.uid)return json(res,202,{detail:'Account created. Check your email to confirm your Supabase account, then sign in.'});const created={id:result.uid,name:String(data.name).trim(),email,role:'candidate',password:data.password,cv_path:null,supabase_token:result.auth.access_token};users[email]=created;return json(res,200,{token:created.id,user:{id:created.id,name:created.name,email,role:'candidate'}})}catch(e){return json(res,400,{detail:e.message})}}
    if(u.pathname==='/api/jobs'&&req.method==='GET')return json(res,200,jobs);
    if(u.pathname==='/api/candidate/applications'&&req.method==='GET')return json(res,200,applications.filter(x=>x.candidate_id===user(req)?.id));
    if(u.pathname==='/api/recruiter/applications'&&req.method==='GET')return json(res,200,applications);
    if(u.pathname==='/api/admin/dashboard'&&req.method==='GET')return json(res,200,{jobs,counts:[]});
    if(u.pathname==='/api/candidate/cv'&&req.method==='POST'){const candidate=user(req);if(!candidate||candidate.role!=='candidate')return json(res,403,{detail:'Candidate sign-in required'});candidate.cv_path='synthetic://demo-cv.pdf';if(candidate.supabase_token)await supabase('/rest/v1/profiles?id=eq.'+candidate.id,{method:'PATCH',headers:{Prefer:'return=minimal',authorization:'Bearer '+candidate.supabase_token},body:JSON.stringify({cv_path:candidate.cv_path})});return json(res,200,{message:'CV uploaded successfully'});}
    const withdraw=u.pathname.match(/^\/api\/applications\/([^/]+)\/withdraw$/);if(withdraw&&req.method==='POST'){const candidate=user(req),record=applications.find(x=>x.id===withdraw[1]);if(!candidate||candidate.role!=='candidate')return json(res,403,{detail:'Candidate sign-in required'});if(!record||record.candidate_id!==candidate.id)return json(res,404,{detail:'Application not found'});if(['Hired','Rejected','Withdrawn'].includes(record.stage))return json(res,400,{detail:'This application can no longer be withdrawn'});if(candidate.supabase_token)await supabase('/rest/v1/applications?id=eq.'+record.id,{method:'PATCH',headers:{Prefer:'return=minimal',authorization:'Bearer '+candidate.supabase_token},body:JSON.stringify({stage:'Withdrawn',updated_at:new Date().toISOString()})});record.stage='Withdrawn';record.updated_at=new Date().toISOString();return json(res,200,{message:'Application withdrawn'});}
    const apply=u.pathname.match(/^\/api\/applications\/([^/]+)$/);if(apply&&req.method==='POST'){const aid='app-'+Date.now(),candidate=user(req),job=jobs.find(x=>x.id===apply[1]);if(!candidate||candidate.role!=='candidate')return json(res,403,{detail:'Candidate sign-in required'});if(!job||job.status!=='open'||job.deadline<new Date().toISOString().slice(0,10))return json(res,400,{detail:'This job is closed or past its deadline'});if(!candidate.cv_path)return json(res,400,{detail:'Upload your PDF CV first'});if(applications.some(x=>x.job_id===job.id&&x.candidate_id===candidate.id&&x.stage!=='Withdrawn'))return json(res,409,{detail:'You already have an active application for this job'});let supabaseId=null;if(candidate.supabase_token){const saved=await supabase('/rest/v1/applications',{method:'POST',headers:{Prefer:'return=representation',authorization:'Bearer '+candidate.supabase_token},body:JSON.stringify({job_id:supabaseJobIds[job.id],candidate_id:candidate.id,cv_path:candidate.cv_path,stage:'Applied',ai_summary:null})});supabaseId=Array.isArray(saved)?saved[0]?.id:saved?.id}const record={id:supabaseId||aid,job_id:job.id,candidate_id:candidate.id,title:job.title,department:job.department,stage:'Applied',cv_path:candidate.cv_path,created_at:new Date().toISOString(),updated_at:new Date().toISOString()};applications.push(record);const common={event_type:'application_received',application_id:record.id,recipient:candidate.email,candidate:{id:candidate.id,name:candidate.name,email:candidate.email},job:{id:job.id,title:job.title,requirements:job.requirements},cv_path:candidate.cv_path};postWebhook(aiWebhook,{...common,event_type:'ai_summary_requested'});postWebhook(emailWebhook,common);return json(res,200,{message:'Application received'});}
    if(u.pathname==='/api/candidate/applications'&&req.method==='GET')return json(res,200,applications.filter(x=>x.candidate_id===user(req)?.id));
    return json(res,200,{message:'Demo mode endpoint ready'});
  }
  let file=u.pathname==='/'?path.join(staticDir,'index.html'):path.join(staticDir,u.pathname.replace('/static/',''));
  if(!file.startsWith(staticDir))return json(res,404,{detail:'Not found'});
  if(!fs.existsSync(file))return json(res,404,{detail:'Not found'});
  const ext=path.extname(file);const types={'.html':'text/html','.js':'text/javascript','.css':'text/css'};res.writeHead(200,{'Content-Type':types[ext]||'application/octet-stream'});fs.createReadStream(file).pipe(res);
});
server.listen(8000,'127.0.0.1',()=>console.log('Nowshera HireOS demo server running at http://127.0.0.1:8000'));

