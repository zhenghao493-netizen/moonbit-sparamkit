#!/usr/bin/env node
'use strict';
// Host I/O only. MoonBit implements parsing, conversion and report serialization.
const fs = require('node:fs');
const path = require('node:path');
const { TextDecoder } = require('node:util');
const LIMIT = 2 * 1024 * 1024;
const HELP = `SParamKit
Usage: node cli.cjs INPUT [--ports 1|2] [--format json|csv] [-o OUTPUT]
       node cli.cjs - --ports 1|2 [--format json|csv] [-o OUTPUT]

  --ports 1|2       Override the port count inferred from .s1p/.s2p
  --format json|csv Output format (default: json)
  -o, --output PATH Save UTF-8 output to a new file; '-' means stdout
  --                Treat the remaining argument as a literal input path
  -h, --help        Show help
  --version         Show the packaged version

Use '-' for piped stdin (explicit --ports required).
Existing output files are never overwritten. Input: UTF-8, <=2 MiB,
<=20000 frequency samples. Exit codes: 0 success, 1 data error, 2 I/O or usage error.
`;

function parseArgs(args) {
  let file, ports, output, format = 'json', literal = false;
  const seen = new Set();
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (!literal && arg === '--') { literal = true; continue; }
    if (!literal && ['--ports', '--format', '--output', '-o'].includes(arg)) {
      const key = arg === '-o' ? '--output' : arg;
      if (seen.has(key)) throw new Error(`Repeated option: ${key}`);
      seen.add(key);
      const value = args[++i];
      if (value === undefined || value === '') throw new Error(`${key} requires a value`);
      if (key === '--ports') {
        if (!['1', '2'].includes(value)) throw new Error('--ports requires 1 or 2');
        ports = Number(value);
      } else if (key === '--format') {
        if (!['json', 'csv'].includes(value)) throw new Error('--format requires json or csv');
        format = value;
      } else {
        if (value.startsWith('-') && value !== '-') throw new Error('Use ./ before an output path beginning with a dash');
        output = value;
      }
    } else if (!literal && arg.startsWith('-') && arg !== '-') {
      throw new Error(`Unknown option: ${arg}`);
    } else if (file === undefined) file = arg;
    else throw new Error('Supply exactly one input file');
  }
  if (!file) throw new Error('Missing input file');
  if (!ports) {
    const match = /\.s([12])p$/i.exec(file);
    if (!match) throw new Error(file === '-' ? 'stdin requires --ports 1 or 2' : 'Use .s1p/.s2p or specify --ports');
    ports = Number(match[1]);
  }
  return { file, ports, format, output };
}

function readFileBounded(file) {
  // Nonblocking open lets us reject FIFOs before waiting for a writer.
  const flags = fs.constants.O_RDONLY | (process.platform === 'win32' ? 0 : fs.constants.O_NONBLOCK);
  const fd = fs.openSync(file, flags);
  try {
    const stat = fs.fstatSync(fd);
    if (!stat.isFile() || stat.size > LIMIT) throw new Error('Input must be a regular file no larger than 2 MiB');
    // Check the opened descriptor and bound every read, even if the file grows.
    const chunks = [];
    let total = 0;
    while (true) {
      const chunk = Buffer.allocUnsafe(Math.min(65536, LIMIT + 1 - total));
      const size = fs.readSync(fd, chunk, 0, chunk.length, null);
      if (!size) break;
      total += size;
      if (total > LIMIT) throw new Error('Input grew beyond 2 MiB');
      chunks.push(chunk.subarray(0, size));
    }
    return Buffer.concat(chunks, total);
  } finally { fs.closeSync(fd); }
}

async function readStdinBounded() {
  if (process.stdin.isTTY) throw new Error('Pipe UTF-8 data into stdin, or provide an input file');
  const chunks = [];
  let total = 0;
  for await (const chunk of process.stdin) {
    total += chunk.length;
    if (total > LIMIT) throw new Error('stdin exceeds 2 MiB');
    chunks.push(chunk);
  }
  return Buffer.concat(chunks, total);
}

function writeNewFile(file, text) {
  // Open exclusively after successful analysis: never truncate an existing path.
  const fd = fs.openSync(file, 'wx');
  let identity;
  let closed = false;
  try {
    identity = fs.fstatSync(fd);
    fs.writeFileSync(fd, text, 'utf8');
    fs.closeSync(fd); closed = true;
  } catch (error) {
    if (!closed) { try { fs.closeSync(fd); } catch (_) {} }
    // Best-effort cleanup of our partial file, not a replacement made by others.
    try {
      const now = fs.lstatSync(file);
      if (identity && now.isFile() && now.dev === identity.dev && now.ino === identity.ino) fs.unlinkSync(file);
    } catch (_) {}
    throw error;
  }
}

async function writeStdout(text) {
  await new Promise((resolve, reject) => {
    process.stdout.write(text, 'utf8', error => error ? reject(error) : resolve());
  });
}

async function main(args) {
  if (!args.length || (args.length === 1 && ['--help', '-h'].includes(args[0]))) {
    await writeStdout(HELP); return 0;
  }
  if (args.length === 1 && args[0] === '--version') {
    const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, 'manifest.json'), 'utf8'));
    if (typeof manifest.version !== 'string') throw new Error('Missing packaged version');
    await writeStdout(`SParamKit ${manifest.version}\n`); return 0;
  }
  const { file, ports, format, output } = parseArgs(args);
  const data = file === '-' ? await readStdinBounded() : readFileBounded(file);
  const source = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(data);
  require(path.join(__dirname, 'core.cjs'));
  const result = JSON.parse(globalThis.SParamKit[format === 'csv' ? 'csv' : 'analyze'](source, ports));
  if (!result.ok) {
    const diagnostic = JSON.stringify(result) + '\n';
    // Preserve the stdout error contract unless the caller selected a file.
    if (output && output !== '-') process.stderr.write(diagnostic);
    else await writeStdout(diagnostic);
    return 1;
  }
  const text = format === 'csv' ? result.csv : JSON.stringify(result) + '\n';
  if (output && output !== '-') writeNewFile(output, text);
  else await writeStdout(text);
  return 0;
}

// Stream errors also emit events after the write callback has reported them.
process.stdout.on('error', () => {});
process.stderr.on('error', () => { process.exitCode = 2; });
main(process.argv.slice(2)).then(code => { process.exitCode = code; }).catch(error => {
  console.error(`SParamKit: ${error.code === 'EPIPE' ? 'Output pipe closed before all data was written' : error.message}`);
  process.exitCode = 2;
});
