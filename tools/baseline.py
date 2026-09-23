#!/usr/bin/env python3
"""Record a pinned upstream baseline without changing or accepting test snapshots."""
from pathlib import Path
import argparse
import datetime
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('upstream', type=Path)
    args = parser.parse_args()
    upstream = args.upstream.resolve()
    expected = json.loads((ROOT/'upstream.lock.json').read_text(encoding='utf-8'))['commit']
    out = ROOT/'reports'; out.mkdir(exist_ok=True)
    report = {'status':'failed', 'upstream_commit':expected, 'steps':[],
              'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=upstream,text=True).strip()
        if head != expected:
            raise ValueError('Upstream commit does not match upstream.lock.json')
        dirty = subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=upstream,text=True)
        if dirty.strip():
            raise ValueError('Upstream tracked sources have local changes')
        commands = [
            ('toolchain',['moon','version','--all']),
            ('dependencies',['moon','update']),
            ('check',['moon','check','--deny-warn']),
            ('test',['moon','test','--target','all']),
        ]
        for label, command in commands:
            print('$ '+' '.join(command), flush=True)
            start = time.monotonic()
            with (out/(label+'.log')).open('w',encoding='utf-8') as log:
                proc = subprocess.run(command,cwd=upstream,stdout=log,stderr=subprocess.STDOUT,
                                      timeout=480,check=False)
            report['steps'].append({'name':label,'command':command,'exit_code':proc.returncode,
                                    'seconds':round(time.monotonic()-start,3),'log':label+'.log'})
            if proc.returncode:
                raise RuntimeError(label+' failed; inspect '+label+'.log')
        changes = subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=upstream,text=True)
        report['tracked_changes'] = changes.splitlines()
        if changes.strip():
            raise RuntimeError('Baseline changed tracked upstream files')
        report['status']='passed'
    except Exception as exc:
        report['error']=str(exc)
    report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (out/'baseline.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['status']=='passed' else 1

if __name__=='__main__':
    sys.exit(main())
