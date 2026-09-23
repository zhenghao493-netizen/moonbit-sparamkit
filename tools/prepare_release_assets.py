#!/usr/bin/env python3
"""Select release downloads from a successfully verified submission bundle."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    version = tomllib.loads((ROOT / 'moon.mod').read_text(encoding='utf-8'))['version']
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?', version):
        raise ValueError('Invalid release version')
    status = json.loads((ROOT / '_build/submission/submission-check.json').read_text(encoding='utf-8'))
    name = f'SParamKit-{version}-submission.zip'
    if status.get('status') != 'passed' or status.get('archive') != name or not status.get('delivered_archive_verified'):
        raise ValueError('A freshly verified submission ZIP is required')
    archive = ROOT / '_build/submission' / name
    if hashlib.sha256(archive.read_bytes()).hexdigest() != status['archive_sha256']:
        raise ValueError('Submission ZIP changed after verification')
    prefix = f'SParamKit-{version}/'
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP member')
        for info in bundle.infolist():
            path = PurePosixPath(info.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in info.filename or not info.filename.startswith(prefix):
                raise ValueError('Unexpected ZIP path')
            if info.is_dir() or stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError('Expected regular payload files')
        manifest = json.loads(bundle.read(prefix + 'manifest.json'))
        if manifest['version'] != version or manifest['source_commit'] != status['source_commit']:
            raise ValueError('Version or source identity mismatch')
        if os.environ.get('GITHUB_SHA') and manifest['source_commit'] != os.environ['GITHUB_SHA']:
            raise ValueError('Release artifact does not match the current checkout')
        payload = manifest['sha256']
        if set(names) != {prefix + n for n in payload} | {prefix + 'manifest.json'}:
            raise ValueError('Manifest does not cover the exact bundle contents')
        for member, expected in payload.items():
            if hashlib.sha256(bundle.read(prefix + member)).hexdigest() != expected:
                raise ValueError('Payload hash mismatch: ' + member)
        html = bundle.read(prefix + 'workbench/index.html')
        config = tomllib.loads(bundle.read(prefix + 'source/moon.mod').decode('utf-8'))
        if config['version'] != version:
            raise ValueError('Bundled source version mismatch')
    out = ROOT / '_build/release'; out.mkdir(parents=True, exist_ok=True)
    allowed = {name, f'SParamKit-{version}.html', 'SHA256SUMS.txt', 'RELEASE_NOTES.md'}
    if any(p.name not in allowed or p.is_symlink() or not p.is_file() for p in out.iterdir()):
        raise ValueError('Move unrelated entries out of _build/release')
    shutil.copyfile(archive, out / name)
    (out / f'SParamKit-{version}.html').write_bytes(html)
    shutil.copyfile(ROOT / 'RELEASE_NOTES.md', out / 'RELEASE_NOTES.md')
    hashes = [f'{hashlib.sha256((out / n).read_bytes()).hexdigest()}  {n}'
              for n in sorted((name, f'SParamKit-{version}.html'))]
    (out / 'SHA256SUMS.txt').write_text('\n'.join(hashes) + '\n', encoding='utf-8')
    stable = str(bool(re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version))).lower()
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as handle:
            handle.write(f'version={version}\nstable={stable}\n')
    print(json.dumps({'version': version, 'source_commit': status['source_commit'],
                      'verified_payload_files': len(payload), 'downloads': sorted(allowed)}, indent=2))

if __name__ == '__main__':
    main()
