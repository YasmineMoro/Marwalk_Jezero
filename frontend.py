"""Portable build driver; uses pnpm, npm, or the Codex-bundled pnpm."""
import argparse,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['install','build','dev']);a=p.parse_args()
 node=shutil.which('node')
 if not node:raise SystemExit('Node.js required to build; prebuilt frontend/dist can be served without Node.')
 pnpm=shutil.which('pnpm');npm=shutil.which('npm')
 bundled=Path(node).parent.parent/'node_modules/pnpm/bin/pnpm.cjs'
 command=[pnpm] if pnpm else [npm] if npm else [node,str(bundled)] if bundled.exists() else None
 if command is None:raise SystemExit('Install pnpm or npm alongside Node.js')
 args=['install'] if a.action=='install' else ['run',a.action]
 if a.action=='install' and (ROOT/'frontend/pnpm-lock.yaml').exists() and (pnpm or not npm):args+=['--frozen-lockfile']
 raise SystemExit(subprocess.call(command+args,cwd=ROOT/'frontend'))
if __name__=='__main__':main()
