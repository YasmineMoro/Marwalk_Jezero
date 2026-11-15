import sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'.deps')]
os.chdir(ROOT)
import pytest
raise SystemExit(pytest.main(['tests','-q','--junitxml=docs/test-results.xml']))
