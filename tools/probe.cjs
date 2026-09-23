'use strict';
// SPDX-License-Identifier: Apache-2.0
// File/JSON transport only; all parsing runs in the compiled MoonBit probe.
const fs = require('node:fs');
const path = require('node:path');
try {
  require(path.resolve(process.argv[2]));
  const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
  if (!Array.isArray(cases)) throw new Error('Expected an array of source cases');
  const results = cases.map(item => {
    if (typeof item.name !== 'string' || typeof item.source !== 'string') throw new Error('Invalid source case');
    const parses = {};
    for (const [engine, name] of ['handrolled', 'moonyacc', 'cst'].entries()) {
      parses[name] = JSON.parse(ParserCheck.parse(item.source, engine, false));
      parses[name + '_loc'] = JSON.parse(ParserCheck.parse(item.source, engine, true));
    }
    return {name: item.name, parses};
  });
  process.stdout.write(JSON.stringify(results));
} catch (error) {
  process.stderr.write(String(error.stack || error) + '\n');
  process.exitCode = 1;
}
