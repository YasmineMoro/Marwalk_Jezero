"""Paths are portable; overrides may be absolute or relative to this project."""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
env=ROOT/'.env'
if env.exists():
    for line in env.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key,value=line.split('=',1)
            if key.strip() in ('MARSWALK_DATA','MARSWALK_DB','MARSWALK_RUNTIME'):
                os.environ.setdefault(key.strip(),value.strip().strip('"').strip("'"))
def configured(name,default):
    path=Path(os.environ.get(name,default));return (path if path.is_absolute() else ROOT/path).resolve()
PACK=configured('MARSWALK_DATA','data/MarsWalk_Data_Release')
RUNTIME=configured('MARSWALK_RUNTIME','runtime')
DATABASE=configured('MARSWALK_DB','runtime/missions.sqlite')
