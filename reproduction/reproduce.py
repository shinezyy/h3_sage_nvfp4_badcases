#!/usr/bin/env python3
"""Print a case request; --submit explicitly runs it against an existing server."""
import argparse,hashlib,json,time,urllib.request,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('case',choices=['A02','A04','B06']);p.add_argument('--submit',action='store_true');p.add_argument('--base-url',default='http://127.0.0.1:30010');p.add_argument('--run-dir');a=p.parse_args()
request=json.loads((ROOT/'cases'/a.case/'request.json').read_text())
assert request['prompt']==(ROOT/'cases'/a.case/'prompt.txt').read_text()
if not a.submit:print(json.dumps(request,ensure_ascii=False,indent=2));raise SystemExit(0)
work=Path(a.run_dir) if a.run_dir else ROOT/'runs'/a.case;work.mkdir(parents=True,exist_ok=True)
def save(path,value):
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2));tmp.replace(path)
def api(url,payload=None):
 req=urllib.request.Request(url,data=json.dumps(payload).encode() if payload is not None else None,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=120) as response:return json.load(response)
f=work/'request.json'
if f.exists() and json.loads(f.read_text())!=request:raise SystemExit('Run directory belongs to a different request; choose another --run-dir.')
save(f,request);jobfile=work/'job.json';base=a.base_url.rstrip('/')+'/v1/videos'
if not jobfile.exists():
 # Exclusive reservation: ambiguous POST failures are never blindly retried.
 with jobfile.open('x') as stream:json.dump({'phase':'submission_attempted'},stream)
 save(jobfile,api(base,request))
job=json.loads(jobfile.read_text())
if not job.get('id'):raise SystemExit('Submission outcome unknown. Inspect server jobs; do not resubmit blindly.')
url=base+'/'+urllib.parse.quote(job['id'],safe='');deadline=time.monotonic()+7200
while True:
 job=api(url);save(jobfile,job);print(job.get('status'),job.get('progress'),flush=True)
 if job.get('status')=='completed':break
 if job.get('status') in ['failed','cancelled','canceled']:raise SystemExit(json.dumps(job))
 if time.monotonic()>deadline:raise SystemExit('Wait timed out; same run directory resumes polling.')
 time.sleep(15)
with urllib.request.urlopen(url+'/content',timeout=120) as response:data=response.read()
if not data:raise SystemExit('Empty video response')
temp=work/'output.mp4.part';temp.write_bytes(data);temp.replace(work/'output.mp4')
save(work/'result.json',{'job_id':job['id'],'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
print(work/'output.mp4')
