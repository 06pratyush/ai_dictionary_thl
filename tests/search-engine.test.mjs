/**
 * Search engine conformance tests.
 *
 * Each case names the rule from Series 700 it protects. Run with `npm test`.
 * No test framework — this ships as a zero-dependency static site and the test
 * runner should not be the one exception.
 */
import assert from 'node:assert/strict';
import {
  SearchEngine,
  normalize,
  parseQuery,
  metaphone,
  damerauLevenshtein,
  editBudget,
  keyProximity
} from '../assets/js/search-engine.js';

const FIXTURE = {
  sections: {
    'ai-mathematics': { id: 'ai-mathematics', title: 'AI & Mathematics' },
    'software-engineering': { id: 'software-engineering', title: 'Software Engineering Core' }
  },
  entries: [
    {
      lid: 'AIM-00001', term: 'Gradient Descent', slug: 'gradient-descent',
      section: 'ai-mathematics', domain: 'Optimization', pos: 'noun',
      abbr: ['GD'], inflections: ['gradient descents'], variants: [],
      synonyms: ['steepest descent'],
      gloss: 'an iterative procedure that reduces a differentiable objective.',
      defText: 'an iterative procedure that reduces a differentiable objective.',
      tags: [], flags: [], frequency: 96
    },
    {
      lid: 'AIM-00002', term: 'Entropy', slug: 'entropy',
      section: 'ai-mathematics', domain: 'Information Theory', pos: 'noun',
      abbr: [], inflections: ['entropies'], variants: [], synonyms: [],
      gloss: 'the average surprise carried by draws from a distribution.',
      defText: 'the average surprise carried by draws from a distribution. used in physics too.',
      tags: [], flags: [], frequency: 80
    },
    {
      lid: 'AIM-00003', term: 'Phlegm Model', slug: 'phlegm-model',
      section: 'ai-mathematics', domain: 'Humours', pos: 'noun',
      abbr: [], inflections: [], variants: [], synonyms: [],
      gloss: 'a discarded pre-modern account of temperament.',
      defText: 'a discarded pre-modern account of temperament.',
      tags: [], flags: ['Archaic'], frequency: 5
    },
    {
      lid: 'SWE-00001', term: 'Technical Debt', slug: 'technical-debt',
      section: 'software-engineering', domain: 'Craft', pos: 'noun',
      abbr: ['tech debt'], inflections: [], variants: ['technical-debt'],
      synonyms: ['design debt'],
      gloss: 'the future cost incurred by choosing an expedient implementation.',
      defText: 'the future cost incurred by choosing an expedient implementation. gradient of decay.',
      tags: [], flags: [], frequency: 93
    },
    {
      lid: 'SWE-00002', term: 'Topology', slug: 'topology',
      section: 'software-engineering', domain: 'Distributed Systems', pos: 'noun',
      abbr: [], inflections: [], variants: [], synonyms: [],
      gloss: 'the arrangement of nodes and the links between them.',
      defText: 'the arrangement of nodes and the links between them.',
      tags: [], flags: [], frequency: 60
    }
  ]
};

const engine = new SearchEngine(FIXTURE);
const results = (q, opts) => engine.search(q, opts).results.map((r) => r.slug);

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    passed += 1;
  } catch (error) {
    failed += 1;
    console.error(`FAIL  ${name}\n      ${error.message}`);
  }
}

/* ---------------- Series 70.A — normalization ---------------- */

test('Rule 701 — queries are case-folded', () => {
  assert.equal(normalize('GRADIENT'), 'gradient');
  assert.deepEqual(results('GRADIENT DESCENT'), results('gradient descent'));
});

test('Rule 702 — diacritics are stripped on both sides', () => {
  assert.equal(normalize('café'), 'cafe');
  assert.equal(normalize('résumé'), 'resume');
});

test('Rule 703 — hyphens and punctuation flatten to spaces', () => {
  assert.equal(normalize('mother-in-law'), 'mother in law');
  assert.equal(normalize('Bayes’ Theorem'), 'bayes theorem');
  // A hyphenated variant must still resolve to its entry.
  assert.ok(results('technical-debt').includes('technical-debt'));
});

test('Rule 704 — surrounding and repeated whitespace collapses', () => {
  assert.equal(normalize('   gradient    descent  '), 'gradient descent');
});

test('Rule 705 — stop words are dropped from polygram queries', () => {
  const parsed = parseQuery('the arrangement of the nodes');
  assert.ok(!parsed.terms.includes('the'));
  assert.ok(parsed.terms.includes('arrangement'));
});

/* ---------------- Series 70.B — fuzzy matching ---------------- */

test('Rule 706 — edit budget scales with word length', () => {
  assert.equal(editBudget(4), 1);
  assert.equal(editBudget(7), 2);
  assert.equal(editBudget(12), 3);
});

test('Rule 706 — a misspelling still finds its entry', () => {
  assert.ok(results('entropi').includes('entropy'));
});

test('Rule 707 — transposed characters are corrected', () => {
  assert.equal(damerauLevenshtein('etnropy', 'entropy'), 1);
  assert.ok(results('etnropy').includes('entropy'));
});

test('Rule 708 — phonetic fallback routes sound-alikes', () => {
  assert.equal(metaphone('phlegm'), metaphone('flegm'));
  assert.ok(results('flegm').includes('phlegm-model'));
});

test('Rule 709 — adjacent keys cost less than distant ones', () => {
  assert.ok(keyProximity('a', 's') < keyProximity('a', 'm'));
  assert.equal(keyProximity('a', 'a'), 0);
});

/* ---------------- Series 70.C — indexing ---------------- */

test('Rule 711 — edge n-grams drive prefix suggestions', () => {
  const slugs = engine.suggest('gra').map((e) => e.slug);
  assert.ok(slugs.includes('gradient-descent'));
});

test('Rule 712 — the index spans definitions, not just headwords', () => {
  assert.ok(results('surprise').includes('entropy'));
});

test('Rule 713 — inflected forms route to the lemma', () => {
  assert.ok(results('entropies').includes('entropy'));
  assert.ok(results('gradient descents').includes('gradient-descent'));
});

test('abbreviations resolve to their entry', () => {
  assert.equal(results('GD')[0], 'gradient-descent');
});

/* ---------------- Series 70.D — ranking ---------------- */

test('Rules 714/717 — an exact headword outranks a definition mention', () => {
  const ranked = results('gradient');
  assert.equal(ranked[0], 'gradient-descent');
  assert.ok(ranked.indexOf('technical-debt') > 0);
});

test('Rule 716 — an anchor word surfaces its multi-word entry', () => {
  assert.ok(results('descent').includes('gradient-descent'));
});

test('Rule 719 — archaic entries are penalised', () => {
  const { results: hits } = engine.search('model', { scope: 'all' });
  const archaic = hits.find((h) => h.slug === 'phlegm-model');
  if (archaic) {
    assert.ok(archaic._score < 10, 'archaic entry should not score at full weight');
  }
});

test('scope confines results to one section', () => {
  const aiOnly = results('gradient', { scope: 'ai-mathematics' });
  assert.ok(aiOnly.includes('gradient-descent'));
  assert.ok(!aiOnly.includes('technical-debt'));
});

/* ---------------- Series 70.E — query modifiers ---------------- */

test('Rule 720 — wildcards match by pattern', () => {
  const parsed = parseQuery('*ology');
  assert.equal(parsed.wildcards.length, 1);
  assert.ok(results('*ology').includes('topology'));
});

test('Rule 720 — ? matches exactly one character', () => {
  assert.ok(results('entrop?').includes('entropy'));
});

test('Rule 721 — a quoted phrase bypasses fuzzy matching', () => {
  const parsed = parseQuery('"gradient descent"');
  assert.equal(parsed.exact, true);
  assert.deepEqual(parsed.phrases, ['gradient descent']);
  // A typo inside quotes must NOT be corrected.
  assert.deepEqual(results('"etnropy"'), []);
});

test('Rule 722 — NOT excludes matching entries', () => {
  assert.ok(results('entropy').includes('entropy'));
  assert.ok(!results('entropy NOT physics').includes('entropy'));
});

test('Rule 722 — AND requires every term', () => {
  const both = results('gradient AND descent');
  assert.ok(both.includes('gradient-descent'));
  assert.ok(!both.includes('technical-debt'));
});

/* ---------------- Series 70.F — pagination ---------------- */

test('Rule 725 — results are capped and pageable', () => {
  const first = engine.search('e', { limit: 2, offset: 0 });
  assert.ok(first.results.length <= 2);
  if (first.total > 2) {
    const second = engine.search('e', { limit: 2, offset: 2 });
    assert.notEqual(first.results[0].slug, second.results[0].slug);
  }
});

test('Rule 601 — a missed query offers a correction', () => {
  const { suggestion } = engine.search('entropi');
  assert.equal(suggestion, 'entropy');
});

test('an empty query returns nothing rather than everything', () => {
  assert.deepEqual(results(''), []);
  assert.deepEqual(results('   '), []);
});

/* ---------------- summary ---------------- */

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
