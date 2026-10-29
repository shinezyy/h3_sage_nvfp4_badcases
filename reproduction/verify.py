#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];count=0
for line in (root/'SHA256SUMS').read_text().splitlines():
 digest,name=line.split('  ',1);path=root/name
 assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==digest,name
 count+=1
for case in ['A02','A04','B06']:
 d=root/'cases'/case;r=json.loads((d/'request.json').read_text())
 assert r['prompt']==(d/'prompt.txt').read_text(),case
 assert [c['frame_index'] for c in r['conditions']]==[0,-1]
 for c in r['conditions']:assert c['uri'].startswith(f'file:///cases/{case}/') and (d/Path(c['uri']).name).is_file()
 assert hashlib.sha256((d/'output.mp4').read_bytes()).hexdigest()==json.loads((d/'result.json').read_text())['sha256']
print(f'{count} file hashes and all three requests verified.')
