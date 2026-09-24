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
async function postWebhook(url,payload){try{const r=await fetch(url,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(payload)});console.log('n8n',r.status,url.split('/').pop())}catch(e){console.log('n8n webhook unavailable',e.message)}}
const jobs = [{id:'demo-job-1',title:'Frontend Engineer',department:'Product',location:'Remote',job_type:'Full-time',description:'Build delightful hiring tools.',requirements:'JavaScript and product sense',deadline:'2027-12-31',openings:2,status:'open'}];
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
    if(u.pathname==='/api/auth/login'&&req.method==='POST'){const found=users[String(data.email||'').trim().toLowerCase()];if(!found||(found.password||'password')!==data.password)return json(res,401,{detail:'This email is not registered in the local app, or the password is incorrect.'});return json(res,200,{token:found.id,user:{id:found.id,name:found.name,email:found.email,role:found.role}})}
    if(u.pathname==='/api/auth/signup'&&req.method==='POST'){const created={id:'candidate-'+Date.now(),name:data.name,email:data.email,role:'candidate'};users[data.email]=created;return json(res,200,{token:created.id,user:created})}
    if(u.pathname==='/api/jobs'&&req.method==='GET')return json(res,200,jobs);
    if(u.pathname==='/api/candidate/applications'&&req.method==='GET')return json(res,200,applications.filter(x=>x.candidate_id===user(req)?.id));
    if(u.pathname==='/api/recruiter/applications'&&req.method==='GET')return json(res,200,applications);
    if(u.pathname==='/api/admin/dashboard'&&req.method==='GET')return json(res,200,{jobs,counts:[]});
    if(u.pathname==='/api/candidate/cv'&&req.method==='POST')return json(res,200,{message:'CV uploaded in demo mode'});
    const apply=u.pathname.match(/^\/api\/applications\/([^/]+)$/);if(apply&&req.method==='POST'){const aid='app-'+Date.now(),candidate=user(req);const record={id:aid,job_id:apply[1],candidate_id:candidate?.id,title:'Frontend Engineer',department:'Product',stage:'Applied'};applications.push(record);const common={event_type:'application_received',application_id:aid,candidate:{id:candidate?.id,name:candidate?.name,email:candidate?.email},job:{id:apply[1],title:'Frontend Engineer',requirements:'Python, APIs, teamwork'},cv_path:'synthetic://demo-cv.pdf'};postWebhook(aiWebhook,{...common,event_type:'ai_summary_requested'});postWebhook(emailWebhook,common);return json(res,200,{message:'Application received'});}
    return json(res,200,{message:'Demo mode endpoint ready'});
  }
  let file=u.pathname==='/'?path.join(staticDir,'index.html'):path.join(staticDir,u.pathname.replace('/static/',''));
  if(!file.startsWith(staticDir))return json(res,404,{detail:'Not found'});
  if(!fs.existsSync(file))return json(res,404,{detail:'Not found'});
  const ext=path.extname(file);const types={'.html':'text/html','.js':'text/javascript','.css':'text/css'};res.writeHead(200,{'Content-Type':types[ext]||'application/octet-stream'});fs.createReadStream(file).pipe(res);
});
server.listen(8000,'127.0.0.1',()=>console.log('Nowshera HireOS demo server running at http://127.0.0.1:8000'));
