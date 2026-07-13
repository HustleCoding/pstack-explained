#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..', '..');
const indexPath = process.argv[2] || path.join(repoRoot, 'index.html');

const html = fs.readFileSync(indexPath, 'utf8');
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) {
  console.error('No <script> block found in index.html');
  process.exit(1);
}

const script = scriptMatch[1];
// Data declarations are at the top, before the DOM helpers begin.
const splitMarker = script.match(/\nconst\s+\$\s*=/)?.index;
const dataCode = splitMarker ? script.slice(0, splitMarker) : script;

const code = `${dataCode.trim()}\nreturn {PLAYBOOKS, SKILLS, GROUPS, PRINCIPLES, MODELS, KEYWORDS, EXAMPLES, EXAMPLE_CHIPS};`;
const fn = new Function(code);
console.log(JSON.stringify(fn(), null, 2));
