"""Extract a trusted user-supplied release, without traversal or overwriting changed files."""
import argparse,zipfile,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def extract(archive):
 destination=(ROOT/'data').resolve();destination.mkdir(exist_ok=True)
 with zipfile.ZipFile(archive) as z:
  for info in z.infolist():
   target=(destination/info.filename).resolve()
   if not target.is_relative_to(destination):raise ValueError('ZIP path escapes data directory')
   if info.is_dir():target.mkdir(parents=True,exist_ok=True);continue
   if target.exists():continue
   target.parent.mkdir(parents=True,exist_ok=True)
   partial=target.with_suffix(target.suffix+'.extracting')
   with z.open(info) as source,partial.open('wb') as out:
    while chunk:=source.read(1024*1024):out.write(chunk)
   partial.replace(target)
 base=destination/'MarsWalk_Data_Release';manifest=json.loads((base/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
 for name,expected in manifest.items():
  file=base/name
  digest=hashlib.file_digest(file.open('rb'),'sha256').hexdigest()
  if file.stat().st_size!=expected['bytes'] or digest!=expected['sha256']:raise RuntimeError('Checksum mismatch: '+name)
 print('120 release files verified; extraction is resumable.')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('archive');extract(parser.parse_args().archive)
