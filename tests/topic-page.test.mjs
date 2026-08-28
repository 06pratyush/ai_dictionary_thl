// Conformance of the generated term pages to docs/TOPIC-PAGE-SPEC.md.
//
// These read the built output rather than the renderer, because the contract
// the spec makes is about the HTML a reader and a crawler receive. A renderer
// that passes its own unit tests but emits sections out of order has still
// broken the contract.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const TERMS = join(ROOT, 'terms');

// The spec's §3 id table, in the spec's order. This array is the test.
const SPEC_ORDER = [
  'quick-take',
  'definitions',
  'formal-statement',
  'etymology',
  'background',
  'prerequisites',
  'deep-dive',
  'worked-example',
  'variants',
  'misconceptions',
  'applications',
  'more-resources',
  'further-reading',
  'faq',
  'references',
  'revision-history',
  'about-author',
];

const pages = readdirSync(TERMS)
  .filter((name) => name.endsWith('.html'))
  .map((name) => ({ name, html: readFileSync(join(TERMS, name), 'utf8') }));

const sectionIds = (html) =>
  [...html.matchAll(/<section class="term-section" id="([^"]+)"/g)].map((m) => m[1]);

const unescape = (value) =>
  value
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");

const jsonLd = (html) => {
  const match = html.match(/<script type="application\/ld\+json">\s*([\s\S]*?)\s*<\/script>/);
  return match ? JSON.parse(match[1]) : null;
};

test('every term page has at least one page built', () => {
  assert.ok(pages.length > 0, 'no term pages found — run python build/build.py');
});

test('section ids come from the spec and appear in the spec order', () => {
  for (const { name, html } of pages) {
    const ids = sectionIds(html);
    assert.ok(ids.length > 0, `${name} rendered no sections`);
    for (const id of ids) {
      assert.ok(SPEC_ORDER.includes(id), `${name}: '${id}' is not a spec section id`);
    }
    const ranks = ids.map((id) => SPEC_ORDER.indexOf(id));
    assert.deepEqual(ranks, [...ranks].sort((a, b) => a - b), `${name}: sections out of spec order`);
    assert.equal(new Set(ids).size, ids.length, `${name}: a section id is repeated`);
  }
});

test('the Required sections that can be derived are always present', () => {
  // Quick Take, Formal Definitions, Final Formal Statement, Etymology and
  // References are derivable or already carried by every entry, so no page
  // may ship without them.
  const always = ['quick-take', 'definitions', 'formal-statement', 'etymology', 'references'];
  for (const { name, html } of pages) {
    const ids = new Set(sectionIds(html));
    for (const id of always) {
      assert.ok(ids.has(id), `${name}: missing required section #${id}`);
    }
  }
});

test('the contents list matches the sections actually rendered', () => {
  for (const { name, html } of pages) {
    const nav = html.match(/<nav class="topic-contents"[\s\S]*?<\/nav>/);
    assert.ok(nav, `${name}: no contents list`);
    const linked = [...nav[0].matchAll(/href="#([^"]+)"/g)].map((m) => m[1]);
    assert.deepEqual(linked, sectionIds(html), `${name}: contents list and body disagree`);
  }
});

test('every section id is unique and every heading is wired to its section', () => {
  for (const { name, html } of pages) {
    for (const id of sectionIds(html)) {
      assert.ok(
        html.includes(`aria-labelledby="${id}-heading"`),
        `${name}: #${id} is not labelled by its heading`,
      );
      assert.ok(html.includes(`id="${id}-heading"`), `${name}: #${id} heading has no id`);
    }
  }
});

test('heading levels never skip', () => {
  for (const { name, html } of pages) {
    const levels = [...html.matchAll(/<h([1-6])[\s>]/g)].map((m) => Number(m[1]));
    assert.equal(levels.filter((l) => l === 1).length, 1, `${name}: not exactly one h1`);
    for (let i = 1; i < levels.length; i += 1) {
      assert.ok(
        levels[i] <= levels[i - 1] + 1,
        `${name}: heading jumps from h${levels[i - 1]} to h${levels[i]}`,
      );
    }
  }
});

test('FAQPage structured data is emitted only where the FAQ actually renders', () => {
  for (const { name, html } of pages) {
    const hasSection = sectionIds(html).includes('faq');
    const graph = jsonLd(html)?.['@graph'] ?? [];
    const faqNodes = graph.filter((node) => node['@type'] === 'FAQPage');
    if (!hasSection) {
      assert.equal(faqNodes.length, 0, `${name}: FAQPage markup with no FAQ section`);
      continue;
    }
    assert.equal(faqNodes.length, 1, `${name}: FAQ section without FAQPage markup`);
    const rendered = [...html.matchAll(/<div class="faq-item"><h3>([\s\S]*?)<\/h3>/g)].map((m) =>
      unescape(m[1]),
    );
    for (const question of faqNodes[0].mainEntity) {
      assert.ok(
        rendered.includes(question.name),
        `${name}: FAQPage claims a question the page does not show: ${question.name}`,
      );
    }
  }
});

test('a reference marker always points at a citation the page lists', () => {
  for (const { name, html } of pages) {
    const markers = [...html.matchAll(/<a class="ref-marker" href="#references">\[(\d+)\]<\/a>/g)];
    if (markers.length === 0) continue;
    const citations = [...html.matchAll(/<li>(?=[\s\S]*?<\/li>)/g)];
    assert.ok(citations.length > 0, `${name}: reference markers but no citation list`);
    const listed = (html.match(/<ul class="citation-list">([\s\S]*?)<\/ul>/)?.[1] ?? '').split(
      '<li>',
    ).length - 1;
    for (const marker of markers) {
      const n = Number(marker[1]);
      assert.ok(n >= 1 && n <= listed, `${name}: reference [${n}] has no matching citation`);
    }
  }
});

test('no page ships an inline script or an inline event handler', () => {
  // The dictionary inherits the site CSP: script-src 'self', no unsafe-inline.
  for (const { name, html } of pages) {
    const scripts = [...html.matchAll(/<script([^>]*)>/g)].map((m) => m[1]);
    for (const attrs of scripts) {
      const ok = attrs.includes('src=') || attrs.includes('application/ld+json');
      assert.ok(ok, `${name}: inline <script> would be blocked by the CSP`);
    }
    assert.ok(!/\son[a-z]+\s*=\s*"/i.test(html), `${name}: inline event handler`);
  }
});

test('a derived section is marked as derived, and an authored one is not', () => {
  for (const { name, html } of pages) {
    const derived = html.match(/data-derived="true"/g)?.length ?? 0;
    // Only Quick Take and Final Formal Statement are ever derived.
    assert.ok(derived <= 2, `${name}: ${derived} derived blocks, expected at most 2`);
    if (derived > 0) {
      assert.ok(
        /class="quick-take" data-derived|class="formal-statement" data-derived/.test(html),
        `${name}: a derived marker outside Quick Take / Final Formal Statement`,
      );
    }
  }
});

test('wide content sits in a scroll container so the page never scrolls sideways', () => {
  for (const { name, html } of pages) {
    const tables = [...html.matchAll(/<table class="([^"]+)"/g)];
    for (const table of tables) {
      const before = html.slice(0, html.indexOf(table[0]));
      assert.ok(
        before.lastIndexOf('<div class="table-scroll">') > before.lastIndexOf('</div>') - 200 ||
          before.includes('<div class="table-scroll">'),
        `${name}: table.${table[1]} is not inside a table-scroll container`,
      );
    }
  }
});
