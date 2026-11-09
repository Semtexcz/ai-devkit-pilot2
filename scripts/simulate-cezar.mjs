// Offline assertions against Cezar's own loader, walker and template renderer.
// No runner, server, shell check, or model is executed by this script.
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';

const dist = process.env.CEZAR_DIST;
assert.ok(dist, 'Set CEZAR_DIST to the installed Cezar dist directory');
const native = async (file) => import(pathToFileURL(`${dist}/${file}`).href);
const { loadWorkflows } = await native('workflows/load.js');
const { advance, enterGraph, parseVerdict, renderNodeRefs } = await native('workflows/graph.js');
const catalog = await loadWorkflows(process.cwd());
assert.deepEqual(catalog.issues, []);
const workflow = catalog.workflows.find(w => w.name === 'pilot-cross-review');
assert.equal(workflow?.source, 'file');
const graph = workflow.graph;
assert.ok(graph);
assert.ok(graph.nodes.every(n => !n.type.startsWith('github.') && !['git.push', 'git.sync-base'].includes(n.type)));
for (const n of graph.nodes.filter(n => n.type === 'agent')) {
  assert.equal(n.session, undefined);
  assert.equal(n.runner, n.id === 'review' ? 'codex' : 'opencode');
  assert.equal(n.model, n.id === 'review' ? 'gpt-6.1-sol' : 'deepseek/deepseek-flash');
}
const findings = '[blocking] F1 — main.py:1 — reproducible defect';
const outputs = new Map([['review', { summary: findings }], ['snapshot', { output: 'b'.repeat(40) }]]);
const prompt = renderNodeRefs(graph.nodes.find(n => n.id === 'repair').prompt, outputs);
assert.ok(prompt.includes(findings));
assert.ok(prompt.includes('b'.repeat(40)));
assert.equal(parseVerdict('APPROVE\nCEZ:VERDICT approve', ['approve', 'changes']), 'approve');
assert.equal(parseVerdict('REQUEST CHANGES\nCEZ:VERDICT changes', ['approve', 'changes']), 'changes');
assert.equal(parseVerdict('APPROVE', ['approve', 'changes']), null);

function simulate(name, overrides = {}, reviews = ['approve'], end = 'accepted', repairs = 0) {
  const counters = new Map();
  const visited = [];
  let reviewCount = 0;
  let latest = '';
  let step = enterGraph(graph, counters);
  while (step.kind === 'node') {
    assert.ok(visited.length < 100, 'simulation failed to terminate');
    const n = step.node;
    visited.push(n.id);
    let port;
    if (n.id in overrides) port = overrides[n.id];
    else if (n.id === 'review') port = latest = reviews[reviewCount++];
    else if (n.type === 'check') port = 'pass';
    else if (n.type === 'git.commit') port = 'nothing';
    else if (n.type === 'if') port = latest === 'approve' ? 'true' : 'false';
    else if (n.type === 'gate.human') port = 'approve';
    else port = 'done';
    assert.ok(port, `missing simulated outcome: ${n.id}`);
    step = advance(graph, n.id, port, counters);
  }
  assert.equal(step.endNode, end, name);
  assert.equal(visited.filter(id => id === 'repair').length, repairs, name);
  if (end !== 'accepted' && !('human' in overrides)) assert.ok(!visited.includes('human'), `${name}: cannot reach acceptance`);
  console.log(`PASS ${name}: ${visited.join(' -> ')} -> ${end}`);
}

simulate('approval');
simulate('rejection then repair', {}, ['changes', 'approve'], 'accepted', 1);
simulate('second repair succeeds', {}, ['changes', 'changes', 'approve'], 'accepted', 2);
simulate('two unsuccessful repairs', {}, ['changes', 'changes', 'changes'], 'exhausted', 2);
for (const id of ['preflight', 'check', 'snapshot', 'audit', 'final-check', 'final-audit']) {
  simulate(`${id} failure`, { [id]: 'fail' }, ['approve'], 'stopped');
}
for (const id of ['implement', 'repair', 'commit', 'review']) {
  simulate(`${id} infrastructure failure`, { [id]: 'failed' }, id === 'repair' ? ['changes'] : ['approve'], 'stopped', id === 'repair' ? 1 : 0);
}
simulate('human rejection', { human: 'reject' }, ['approve'], 'stopped');
simulate('human timeout', { human: 'timeout' }, ['approve'], 'stopped');
simulate('unverifiable review', {}, ['unverifiable'], 'stopped');
simulate('missing verdict after native reminder', { review: 'failed' }, [], 'stopped');
console.log('PASS native load, graph bounds, model/session pins, verdict mapping, findings interpolation, no delivery nodes');
