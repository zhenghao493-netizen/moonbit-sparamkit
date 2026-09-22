#!/usr/bin/env node
'use strict';
// File/argument handling only. Parsing, conversion and CSV serialization are MoonBit.
const fs = require('node:fs');
const path = require('node:path');
const { TextDecoder } = require('node:util');
const LIMIT = 2 * 1024 * 1024;
function main(args) {
  if (args.includes('--help') || args.length === 0) {
    console.log('SParamKit\nUsage: node cli.cjs FILE.s1p|FILE.s2p [--ports 1|2] [--format json|csv]\nLimits: UTF-8, 2 MiB, 20000 samples. Strict Touchstone S-parameter subset.');
    return 0;
  }
  let file, ports, format = 'json';
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--ports') {
      const value = args[++i];
      if (!['1', '2'].includes(value)) throw new Error('--ports requires 1 or 2');
      ports = Number(value);
    } else if (arg === '--format') {
      format = args[++i];
      if (!['json', 'csv'].includes(format)) throw new Error('--format requires json or csv');
    } else if (arg.startsWith('--')) throw new Error(`Unknown option: ${arg}`);
    else if (!file) file = arg;
    else throw new Error('Supply exactly one input file');
  }
  if (!file) throw new Error('Missing input file');
  if (!ports) {
    const match = /\.s([12])p$/i.exec(file);
    if (!match) throw new Error('Use .s1p/.s2p or specify --ports');
    ports = Number(match[1]);
  }
  const stat = fs.statSync(file);
  if (!stat.isFile() || stat.size > LIMIT) throw new Error('Input must be a regular file no larger than 2 MiB');
  const data = fs.readFileSync(file);
  if (data.length > LIMIT) throw new Error('Input grew beyond 2 MiB');
  const source = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(data);
  require(path.join(__dirname, 'core.cjs'));
  const result = JSON.parse(globalThis.SParamKit[format === 'csv' ? 'csv' : 'analyze'](source, ports));
  if (!result.ok) {
    process.stdout.write(JSON.stringify(result) + '\n');
    return 1;
  }
  process.stdout.write(format === 'csv' ? result.csv : JSON.stringify(result) + '\n');
  return 0;
}
try { process.exitCode = main(process.argv.slice(2)); }
catch (error) { console.error(`SParamKit: ${error.message}`); process.exitCode = 2; }
