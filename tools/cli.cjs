#!/usr/bin/env node
'use strict';
// File/argument handling only. Parsing, conversion and serialization are MoonBit.
const fs = require('node:fs');
const path = require('node:path');
const { TextDecoder } = require('node:util');
const LIMIT = 2 * 1024 * 1024;

function readInput(file) {
  // Check the opened descriptor too, and cap the read if a file grows meanwhile.
  if (!fs.statSync(file).isFile()) throw new Error('Input must be a regular file');
  const fd = fs.openSync(file, 'r');
  try {
    const stat = fs.fstatSync(fd);
    if (!stat.isFile() || stat.size > LIMIT) {
      throw new Error('Input must be a regular file no larger than 2 MiB');
    }
    const bytes = Buffer.alloc(LIMIT + 1);
    let size = 0;
    while (size <= LIMIT) {
      const count = fs.readSync(fd, bytes, size, bytes.length - size, null);
      if (count === 0) break;
      size += count;
    }
    if (size > LIMIT) throw new Error('Input grew beyond 2 MiB');
    return new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes.subarray(0, size));
  } finally {
    fs.closeSync(fd);
  }
}

function saveOutput(file, content) {
  // Exclusive creation protects existing results, input files and symlink targets.
  let fd;
  try {
    fd = fs.openSync(file, 'wx');
  } catch (error) {
    if (error.code === 'EEXIST') throw new Error(`Output already exists: ${file}. Choose another filename.`);
    throw error;
  }
  try {
    fs.writeFileSync(fd, content, { encoding: 'utf8' });
    fs.closeSync(fd);
    fd = undefined;
  } catch (error) {
    if (fd !== undefined) { try { fs.closeSync(fd); } catch {} }
    // Only remove the output created by this operation after a failed write.
    try { fs.unlinkSync(file); } catch {}
    throw error;
  }
}

function main(args) {
  const separator = args.indexOf('--');
  const options = separator === -1 ? args : args.slice(0, separator);
  if (options.includes('--help') || args.length === 0) {
    console.log('SParamKit\nUsage: node cli.cjs FILE.s1p|FILE.s2p [--ports 1|2] [--format json|csv] [--output FILE]\n\n--output, -o  Save a UTF-8 result to a new file (never overwrite).\n--            Treat the remaining argument as the input filename.\n\nWithout --output, write the result to stdout. Invalid input returns diagnostic JSON on stdout and does not create an output file.\nLimits: UTF-8, 2 MiB, 20000 samples.');
    return 0;
  }
  let file, ports, output, format = 'json', positional = false;
  const seen = new Set();
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (!positional && arg === '--') { positional = true; continue; }
    if (!positional && ['--ports', '--format', '--output', '-o'].includes(arg)) {
      const key = arg === '-o' ? '--output' : arg;
      if (seen.has(key)) throw new Error(`Repeated option: ${key}`);
      seen.add(key);
      const value = args[++i];
      if (value === undefined || value.length === 0 || value.startsWith('-')) {
        throw new Error(`${key} requires a value (prefix a dash-leading path with ./)`);
      }
      if (key === '--ports') {
        if (!['1', '2'].includes(value)) throw new Error('--ports requires 1 or 2');
        ports = Number(value);
      } else if (key === '--format') {
        if (!['json', 'csv'].includes(value)) throw new Error('--format requires json or csv');
        format = value;
      } else output = value;
    } else if (!positional && arg.startsWith('-')) throw new Error(`Unknown option: ${arg}`);
    else if (file === undefined) file = arg;
    else throw new Error('Supply exactly one input file');
  }
  if (!file) throw new Error('Missing input file');
  if (!ports) {
    const match = /\.s([12])p$/i.exec(file);
    if (!match) throw new Error('Use .s1p/.s2p or specify --ports');
    ports = Number(match[1]);
  }
  const source = readInput(file);
  require(path.join(__dirname, 'core.cjs'));
  const result = JSON.parse(globalThis.SParamKit[format === 'csv' ? 'csv' : 'analyze'](source, ports));
  if (!result.ok) {
    process.stdout.write(JSON.stringify(result) + '\n');
    return 1;
  }
  const content = format === 'csv' ? result.csv : JSON.stringify(result) + '\n';
  if (output !== undefined) saveOutput(output, content);
  else process.stdout.write(content);
  return 0;
}
try { process.exitCode = main(process.argv.slice(2)); }
catch (error) { console.error(`SParamKit: ${error.message}`); process.exitCode = 2; }
