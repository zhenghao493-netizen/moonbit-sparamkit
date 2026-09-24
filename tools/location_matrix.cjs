'use strict';
// SPDX-License-Identifier: Apache-2.0
// JSON transport only: ASTs and source slices come from the MoonBit visitor.
const fs = require('node:fs');
const path = require('node:path');
try {
  if (process.argv.length !== 3) throw new Error('Usage: node location_matrix.cjs <compiled-probe>');
  require(path.resolve(process.argv[2]));
  const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
  if (!Array.isArray(cases) || cases.length > 1000) throw new Error('Expected at most 1000 cases');
  const names = new Set();
  const results = cases.map(item => {
    if (typeof item.name !== 'string' || typeof item.source !== 'string' || names.has(item.name)) {
      throw new Error('Invalid or duplicate case');
    }
    names.add(item.name);
    const parses = {};
    ['handrolled', 'moonyacc', 'cst'].forEach((engine, index) => {
      parses[engine] = JSON.parse(ParserCheckMatrix.inspect(item.source, index));
    });
    return {name: item.name, parses};
  });
  process.stdout.write(JSON.stringify(results));
} catch (error) {
  process.stderr.write(String(error.stack || error) + '\n');
  process.exitCode = 1;
}
