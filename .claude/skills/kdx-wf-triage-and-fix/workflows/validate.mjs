// Replicates the Workflow runtime's own gate on a script, verbatim from the
// checks the 2.1.212 binary applies before it will launch one:
//   - plain JS, parsed with allowAwaitOutsideFunction + allowReturnOutsideFunction
//   - `export const meta` is the FIRST statement
//   - meta is a pure literal: no interpolation, no spread, no computed keys
//   - meta.name and meta.description are non-empty strings
//   - Date.now / Math.random / new Date() are absent (they throw at runtime)
//   - no import(), no `with`
// Run: node workflows/validate.mjs workflows/triage-and-fix.js

import { readFileSync } from 'node:fs';
import { parse } from 'acorn';
import { simple } from 'acorn-walk';

const path = process.argv[2];
const src = readFileSync(path, 'utf8');
const fail = [];
const ok = [];

let ast;
try {
  ast = parse(src, {
    ecmaVersion: 'latest',
    sourceType: 'module',
    allowAwaitOutsideFunction: true,
    allowReturnOutsideFunction: true,
  });
  ok.push('parses as plain JS under the runtime\'s acorn options');
} catch (e) {
  console.error('FAIL parse: ' + e.message);
  process.exit(1);
}

const first = ast.body[0];
if (!first || first.type !== 'ExportNamedDeclaration') {
  fail.push('`export const meta` must be the FIRST statement');
} else {
  ok.push('`export const meta` is the first statement');
  const init = first.declaration?.declarations?.[0]?.init;
  const pure = (n) => {
    if (!n) return false;
    if (n.type === 'Literal') return true;
    if (n.type === 'TemplateLiteral') return n.expressions.length === 0 || 'interp';
    if (n.type === 'ArrayExpression') return n.elements.every((e) => e && pure(e) === true);
    if (n.type === 'ObjectExpression') {
      return n.properties.every(
        (p) => p.type === 'Property' && !p.computed && !p.method && pure(p.value) === true,
      );
    }
    return false;
  };
  if (pure(init) === true) ok.push('meta is a pure literal');
  else fail.push('meta is not a pure literal (interpolation, spread, computed key, or call)');

  const props = Object.fromEntries(
    (init?.properties ?? []).map((p) => [p.key.name ?? p.key.value, p.value]),
  );
  for (const k of ['name', 'description']) {
    const v = props[k];
    if (v?.type === 'Literal' && typeof v.value === 'string' && v.value.length) {
      ok.push(`meta.${k} is a non-empty string`);
    } else fail.push(`meta.${k} must be a non-empty string`);
  }
  if (props.phases?.type === 'ArrayExpression') {
    ok.push(`meta.phases declares ${props.phases.elements.length} phases`);
  }
}

// Determinism: these are unavailable in the VM and throw, breaking resume.
const banned = [];
simple(ast, {
  MemberExpression(n) {
    const o = n.object?.name;
    const p = n.property?.name;
    if (o === 'Date' && p === 'now') banned.push('Date.now()');
    if (o === 'Math' && p === 'random') banned.push('Math.random()');
  },
  NewExpression(n) {
    if (n.callee?.name === 'Date') banned.push('new Date()');
  },
  ImportExpression() {
    banned.push('import()');
  },
  WithStatement() {
    banned.push('with statement');
  },
});
if (banned.length) fail.push('non-deterministic / unsupported: ' + [...new Set(banned)].join(', '));
else ok.push('no Date.now / Math.random / new Date / import() / with');

// parallel() takes thunks, not promises — the runtime rejects promises at run time.
let parallelCalls = 0;
let badParallel = 0;
simple(ast, {
  CallExpression(n) {
    if (n.callee?.name !== 'parallel') return;
    parallelCalls++;
    const arr = n.arguments[0];
    if (arr?.type !== 'ArrayExpression') return void badParallel++;
    for (const el of arr.elements) {
      if (el?.type !== 'ArrowFunctionExpression' && el?.type !== 'FunctionExpression') badParallel++;
    }
  },
});
if (badParallel) fail.push(`parallel() passed ${badParallel} non-thunk element(s) — wrap each: () => agent(...)`);
else if (parallelCalls) ok.push(`${parallelCalls} parallel() call(s), all thunks`);

// Every agent() with a schema can return null when the subagent dies.
const agents = [];
simple(ast, {
  CallExpression(n) {
    if (n.callee?.name !== 'agent') return;
    const opts = n.arguments[1];
    const o = Object.fromEntries(
      (opts?.properties ?? []).map((p) => [p.key.name ?? p.key.value, p.value]),
    );
    agents.push({
      label: o.label?.value ?? '?',
      agentType: o.agentType?.value ?? '(session default)',
      effort: o.effort?.value ?? '-',
      schema: o.schema?.name ?? null,
    });
  },
});
ok.push(`${agents.length} agent() call(s) declared`);
for (const a of agents) {
  if (!a.schema) fail.push(`agent "${a.label}" has no schema — its output is unvalidated free text`);
}

console.log('--- ' + path);
for (const o of ok) console.log('  ok   ' + o);
for (const f of fail) console.log('  FAIL ' + f);
console.log('\n  agent calls:');
for (const a of agents) {
  console.log(`    ${a.label.padEnd(18)} ${a.agentType.padEnd(16)} effort=${a.effort.padEnd(7)} schema=${a.schema}`);
}
console.log(fail.length ? `\n${fail.length} problem(s).` : '\nClean.');
process.exit(fail.length ? 1 : 0);
