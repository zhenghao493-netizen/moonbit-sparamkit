#!/usr/bin/env python3
"""Exercise CLI I/O failures against real files and the compiled MoonBit core."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 2 * 1024 * 1024
SOURCE = b'# Hz S RI R 50\n1 .3 -.4\n2 0 0\n'

PRELUDE = r'''
const fs = require('node:fs');
const original = {open:fs.openSync, close:fs.closeSync, stat:fs.fstatSync,
                  read:fs.readSync, write:fs.writeFileSync};
let inputFd, outputFd;
const state = {inputClosed:false, outputClosed:false, readBytes:0, maxBuffer:0};
fs.openSync = function(file, ...args) {
  const fd = original.open(file, ...args);
  if (file === config.input && typeof args[0] === 'number') inputFd = fd;
  if (file === config.output && args[0] === 'wx') outputFd = fd;
  return fd;
};
fs.closeSync = function(fd) {
  const result = original.close(fd);
  if (fd === inputFd) state.inputClosed = true;
  if (fd === outputFd) state.outputClosed = true;
  return result;
};
fs.readSync = function(fd, buffer, offset, length, position) {
  const count = original.read(fd, buffer, offset, length, position);
  if (fd === inputFd) {
    state.readBytes += count;
    state.maxBuffer = Math.max(state.maxBuffer, buffer.length);
  }
  return count;
};
process.on('exit', () => original.write(config.record, JSON.stringify(state), 'utf8'));
'''

HOOKS = {
    'growth': r'''
let grown = false;
fs.fstatSync = function(fd) {
  const result = original.stat(fd);
  if (fd === inputFd && !grown) {
    grown = true;
    fs.appendFileSync(config.input, Buffer.alloc(4 * 1024 * 1024, 120));
  }
  return result;
};
''',
    'short_reads': r'''
const trackedRead = fs.readSync;
fs.readSync = function(fd, buffer, offset, length, position) {
  return trackedRead(fd, buffer, offset, fd === inputFd ? Math.min(length, 7) : length, position);
};
''',
    'read_failure': r'''
const trackedRead = fs.readSync;
fs.readSync = function(fd, ...args) {
  if (fd === inputFd) throw new Error('injected input read failure');
  return trackedRead(fd, ...args);
};
''',
    'output_metadata_failure': r'''
fs.fstatSync = function(fd) {
  if (fd === outputFd) throw new Error('injected output metadata failure');
  return original.stat(fd);
};
''',
    'write_failure': r'''
fs.writeFileSync = function(file, ...args) {
  if (file === outputFd) {
    original.write(file, 'partial', 'utf8');
    throw new Error('injected output write failure');
  }
  return original.write(file, ...args);
};
''',
    'replacement_on_failure': r'''
fs.writeFileSync = function(file, ...args) {
  if (file === outputFd) {
    original.write(file, 'partial', 'utf8');
    fs.closeSync(file);
    fs.renameSync(config.output, config.output + '.partial');
    original.write(config.output, 'replacement from another writer', 'utf8');
    throw new Error('injected write failure after replacement');
  }
  return original.write(file, ...args);
};
''',
}


def main() -> int:
    details = []
    result = {'status': 'failed', 'checks': 0, 'details': details}
    try:
        with tempfile.TemporaryDirectory(prefix='sparamkit-faults-') as tmp:
            tmp = Path(tmp)
            for name, hook in HOOKS.items():
                directory = tmp / name
                directory.mkdir()
                source = directory / 'input.s1p'
                output = directory / 'output.json'
                record = directory / 'record.json'
                source.write_bytes(SOURCE)
                config = {'input': str(source), 'output': str(output), 'record': str(record)}
                script = directory / 'fault.cjs'
                script.write_text('const config = ' + json.dumps(config) + ';\n' + PRELUDE + hook,
                                  encoding='utf-8')
                proc = subprocess.run(['node', '--require', str(script), str(ROOT / 'dist/cli.cjs'),
                                       str(source), '--output', str(output)],
                                      capture_output=True, encoding='utf-8', timeout=20)
                state = json.loads(record.read_text(encoding='utf-8'))
                assert proc.returncode == (0 if name == 'short_reads' else 2), (name, proc.stderr)
                assert proc.stdout == '', (name, proc.stdout)
                assert state['inputClosed'], (name, state)
                if name == 'growth':
                    assert 'grew beyond' in proc.stderr
                    assert state['readBytes'] == LIMIT + 1 and state['maxBuffer'] <= 65536, state
                    assert not output.exists()
                else:
                    assert source.read_bytes() == SOURCE, name
                    if name == 'short_reads':
                        report = json.loads(output.read_text(encoding='utf-8'))
                        assert report['sample_count'] == 2
                        assert report['samples'][0]['values'][0]['im'] == -.4
                        assert state['outputClosed'] and state['readBytes'] == len(SOURCE)
                    elif name == 'read_failure':
                        assert 'injected input read failure' in proc.stderr and not output.exists()
                    else:
                        assert state['outputClosed'], (name, state)
                        if name == 'output_metadata_failure':
                            assert 'injected output metadata failure' in proc.stderr
                            # With no file identity available, cleanup must not unlink the path.
                            assert output.read_bytes() == b''
                        elif name == 'write_failure':
                            assert 'injected output write failure' in proc.stderr and not output.exists()
                        else:
                            assert output.read_bytes() == b'replacement from another writer'
                            assert output.with_name('output.json.partial').read_bytes() == b'partial'
                details.append({'case': name, **state})
        result.update(status='passed', checks=len(details))
    except Exception as error:
        result.update(checks=len(details), error=f'{type(error).__name__}: {error}')
    directory = ROOT / 'verification'
    directory.mkdir(exist_ok=True)
    (directory / 'file-fault-tests.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
