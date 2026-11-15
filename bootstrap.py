import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / '.deps'))
env=Path(__file__).parent/'.env'
if env.exists():
    import os
    for line in env.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key,value=line.split('=',1)
            if key.strip() in ('MARSWALK_DATA','MARSWALK_DB','MARSWALK_RUNTIME'):os.environ.setdefault(key.strip(),value.strip().strip('"').strip("'"))
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('backend.app:app', host='127.0.0.1', port=8000)
