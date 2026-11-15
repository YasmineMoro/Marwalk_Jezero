"""Resumable downloader for a caller-selected official product, never a fallback generator."""
import argparse,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.deps'))
import httpx
def download(url,target,sha256=None,max_bytes=400_000_000):
 target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists() and (not sha256 or hashlib.sha256(target.read_bytes()).hexdigest()==sha256):return target
 part=target.with_suffix(target.suffix+'.part');offset=part.stat().st_size if part.exists() else 0
 with httpx.Client(follow_redirects=True,timeout=60) as client:
  with client.stream('GET',url,headers={'Range':f'bytes={offset}-'} if offset else {}) as r:
   r.raise_for_status()
   append=offset>0 and r.status_code==206 and r.headers.get('content-range','').startswith(f'bytes {offset}-')
   if offset and r.status_code==206 and not append:raise RuntimeError('Incorrect Content-Range; cache retained')
   total=offset if append else 0
   with part.open('ab' if append else 'wb') as out:
    for chunk in r.iter_bytes(1024*256):
     total+=len(chunk)
     if total>max_bytes:raise RuntimeError('Download size cap exceeded')
     out.write(chunk)
 if sha256 and hashlib.sha256(part.read_bytes()).hexdigest()!=sha256:raise RuntimeError('Checksum mismatch; .part retained')
 part.replace(target);return target
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('url');p.add_argument('target');p.add_argument('--sha256');p.add_argument('--max-bytes',type=int,default=400_000_000);a=p.parse_args()
 print(download(a.url,a.target,a.sha256,a.max_bytes))
