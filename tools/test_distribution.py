#!/usr/bin/env python3
"""Exercise runtime packaging with clean, reused and contaminated output folders."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    checks, skipped = [], []
    result = {'status': 'failed'}
    try:
        with tempfile.TemporaryDirectory(prefix='sparamkit-dist-') as temporary:
            project = Path(temporary)/'project'
            project.mkdir()
            for name in ('tools', 'web', 'samples'):
                shutil.copytree(ROOT/name, project/name, ignore=shutil.ignore_patterns('__pycache__'))
            for name in ('moon.mod', 'LICENSE'):
                shutil.copyfile(ROOT/name, project/name)
            bridge = '_build/js/release/build/bridge/bridge.js'
            (project/bridge).parent.mkdir(parents=True)
            shutil.copyfile(ROOT/bridge, project/bridge)
            dist = project/'dist'

            def snapshot():
                return {p.relative_to(dist).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in dist.rglob('*') if p.is_file() and not p.is_symlink()}

            def build(expect_success=True):
                proc = subprocess.run([sys.executable, str(project/'tools/build_web.py')],
                                      capture_output=True, text=True, encoding='utf-8', timeout=30)
                if expect_success:
                    assert proc.returncode == 0, proc.stderr
                    verify = subprocess.run([sys.executable, str(dist/'verify_download.py')],
                                            capture_output=True, text=True, encoding='utf-8', timeout=15)
                    assert verify.returncode == 0, verify.stderr
                else:
                    assert proc.returncode != 0, 'Contaminated output was accepted'
                return proc

            build(); checks.append('clean output builds and verifies')
            original = snapshot()
            build(); assert snapshot() == original
            checks.append('rebuild of clean output preserves deterministic payload bytes')
            for name in ('local-analysis.txt', '.env', 'samples/old-measurement.s1p'):
                path = dist/name
                path.write_text('local file; not a distribution asset\n', encoding='utf-8')
                before = snapshot()
                assert 'Unexpected output entry' in build(False).stderr
                assert snapshot() == before
                path.unlink()
                checks.append('refuse unrelated ' + name + ' without modifying files')
            directory = dist/'old-report'; directory.mkdir()
            before = snapshot(); build(False); assert snapshot() == before and directory.is_dir()
            directory.rmdir(); checks.append('refuse unrelated empty directories without deleting them')
            foreign = project/'outside.txt'; foreign.write_text('must remain unchanged', encoding='utf-8')
            link = dist/'core.cjs'; original_core = link.read_bytes(); link.unlink()
            try:
                link.symlink_to(foreign)
            except OSError:
                skipped.append('symlink test: host does not permit symlink creation')
            else:
                assert 'symlink' in build(False).stderr
                assert foreign.read_text(encoding='utf-8') == 'must remain unchanged'
                link.unlink(); checks.append('refuse output symlinks without following them')
            link.write_bytes(original_core)
            source = project/bridge; source.unlink()
            before = snapshot()
            assert 'Refusing stale' in build(False).stderr
            assert snapshot() == before
            checks.append('missing bridge does not alter existing runtime files')
            shutil.copyfile(ROOT/bridge, source)
            (project/'LICENSE').unlink()
            before = snapshot(); build(False); assert snapshot() == before
            shutil.copyfile(ROOT/'LICENSE', project/'LICENSE')
            checks.append('missing license refuses rebuild without modifying files')
            build(); assert snapshot() == original
            checks.append('clean recovery after rejected rebuilds')
        result.update(status='passed')
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
    result.update(checks=len(checks), details=checks, skipped=skipped)
    out = ROOT/'verification'; out.mkdir(exist_ok=True)
    (out/'distribution-tests.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
