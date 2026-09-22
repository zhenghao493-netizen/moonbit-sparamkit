#!/usr/bin/env python3
"""Check delivered bytes against manifest.json; checksums are NOT signatures."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


def verify(directory: Path) -> dict:
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate manifest key: ' + key)
            result[key] = value
        return result

    manifest = json.loads((directory/'manifest.json').read_text(encoding='utf-8'),
                          object_pairs_hook=unique_object)
    if manifest.get('schema_version') != 1 or manifest.get('project') != 'SParamKit':
        raise ValueError('Unsupported manifest')
    expected = manifest.get('sha256')
    if not isinstance(expected, dict) or not expected:
        raise ValueError('Missing checksum map')
    for name, digest in expected.items():
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or '..' in path.parts or ':' in name or
                '\\' in name or path.as_posix() != name or name == 'manifest.json'):
            raise ValueError('Unsafe manifest path: ' + name)
        target = directory / name
        if any(p.is_symlink() for p in (target, *target.parents)):
            raise ValueError('Symlinks are not supported: ' + name)
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError('Invalid checksum: ' + name)
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError('Missing or changed file: ' + name)
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*')
              if p.is_file() and p != directory/'manifest.json'}
    if actual != set(expected):
        raise ValueError('Unlisted files in tool directory: ' + str(sorted(actual-set(expected))))
    return {'status':'passed', 'version':manifest['version'],
            'source_commit':manifest['source_commit'], 'files_checked':len(expected)}


def main() -> int:
    try:
        directory = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(__file__).resolve().parent
        if len(sys.argv) > 2:
            raise ValueError('Usage: python verify_download.py [tool-directory]')
        print(json.dumps(verify(directory), ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('Integrity check failed: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
