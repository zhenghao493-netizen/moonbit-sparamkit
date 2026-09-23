#!/usr/bin/env python3
"""Compile the published Markdown examples and check local documentation links."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
FENCES = re.compile(r'^```([^\n]*)\n(.*?)^```[ \t]*$', re.M | re.S)
LINKS = re.compile(r'\[[^\]\n]*\]\(([^\s)]+)(?:[ \t]+"[^"\n]*")?\)')


def check_links() -> tuple[int, int]:
    """Check inline local targets, not remote URLs or Markdown heading anchors."""
    documents = [ROOT/'README.md', *sorted((ROOT/'docs').rglob('*.md'))]
    count = 0
    for document in documents:
        text = FENCES.sub('', document.read_text(encoding='utf-8'))
        for raw in LINKS.findall(text):
            url = urlsplit(raw)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (document.parent/unquote(url.path)).resolve()
            if not target.is_relative_to(ROOT.resolve()) or not target.exists():
                raise ValueError(f'{document.relative_to(ROOT)}: missing local link {raw}')
            count += 1
    return len(documents), count


def moonbit_blocks(path: Path) -> list[str]:
    return [body for language, body in FENCES.findall(path.read_text(encoding='utf-8'))
            if language.strip() == 'moonbit']


def main() -> int:
    report = {'status': 'failed', 'commands': [], 'examples': []}
    try:
        documents, links = check_links()
        version = tomllib.loads((ROOT/'moon.mod').read_text(encoding='utf-8'))['version']
        if f'版本：`{version}`' not in (ROOT/'README.md').read_text(encoding='utf-8'):
            raise ValueError('README version does not match moon.mod')
        readme = moonbit_blocks(ROOT/'README.md')
        library = moonbit_blocks(ROOT/'docs/LIBRARY.md')
        if len(readme) != 2 or len(library) != 4:
            raise ValueError('Update the documentation test when the example structure changes')
        # LIBRARY.md supplies moon.work, moon.mod, moon.pkg and main.mbt verbatim.
        if f'ttxiangshang/sparamkit@{version}' not in library[1]:
            raise ValueError('LIBRARY.md dependency version does not match moon.mod')
        cases = [('README.md', readme[0], readme[1], math.hypot(.8, -.1), 4),
                 ('docs/LIBRARY.md', library[2], library[3], .5, 2)]
        for name, package, main_source, expected_magnitude, expected_rows in cases:
            with tempfile.TemporaryDirectory(prefix='sparamkit-docs-') as temp:
                work = Path(temp)/'文档示例 with spaces'
                module, client = work/'moonbit-sparamkit', work/'client'
                module.mkdir(parents=True); client.mkdir()
                for source in ROOT.glob('*.mbt'):
                    if not source.name.endswith(('_test.mbt', '_wbtest.mbt')):
                        shutil.copyfile(source, module/source.name)
                for filename in ('moon.mod', 'moon.pkg', 'pkg.generated.mbti', 'LICENSE'):
                    shutil.copyfile(ROOT/filename, module/filename)
                for path, text in [(work/'moon.work', library[0]), (client/'moon.mod', library[1]),
                                   (client/'moon.pkg', package), (client/'main.mbt', main_source)]:
                    path.write_text(text, encoding='utf-8', newline='\n')
                for target in ('js', 'wasm-gc'):
                    for verb in ('check', 'build', 'run'):
                        args = ['moon', verb, '.', '--target', target, '--deny-warn']
                        proc = subprocess.run(args, cwd=client, capture_output=True, text=True,
                                              encoding='utf-8', timeout=180)
                        report['commands'].append({'example': name, 'command': args,
                                                   'exit_code': proc.returncode,
                                                   'stdout': proc.stdout, 'stderr': proc.stderr})
                        if proc.returncode:
                            raise RuntimeError(f'{name}: {args}\n{proc.stdout}\n{proc.stderr}')
                        if verb != 'run':
                            continue
                        magnitude, csv_text = proc.stdout.strip().split('\n', 1)
                        if not math.isclose(float(magnitude), expected_magnitude, rel_tol=1e-12):
                            raise ValueError(f'{name}: unexpected example magnitude')
                        rows = list(csv.DictReader(io.StringIO(csv_text)))
                        if len(rows) != expected_rows or not all(float(r['reference_ohms']) == 50 for r in rows):
                            raise ValueError(f'{name}: unexpected CSV output')
                        report['examples'].append({'source': name, 'target': target,
                                                   'status': 'passed', 'csv_rows': len(rows),
                                                   'main_sha256': hashlib.sha256(main_source.encode()).hexdigest()})
        report.update(status='passed', documents=documents, local_links=links,
                      distinct_examples=2, executed_targets=['js', 'wasm-gc'])
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    directory = ROOT/'verification'; directory.mkdir(exist_ok=True)
    (directory/'documentation-tests.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'commands'}, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
