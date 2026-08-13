# Integrating the dictionary into thehallucinatedlab.space

The dictionary is built as a self-contained directory so it can be dropped into
the main site without touching anything else. It expects to live at
`/dictionary/`.

## 1. Copy the directory

Copy this repository's output into the site root as `dictionary/`:

```
thehallucinatedlab.space/
  index.html
  styles.css
  dictionary/
    index.html
    terms/
    assets/
    data/
    sitemap.xml
```

Everything the pages load is either relative (`assets/…`, `data/…`) or an
absolute link back to the site root, so no path rewriting is needed.

## 2. Add the navbar item

The navbar carries seven items today. The dictionary makes eight, which is why
`tokens.css` collapses the nav at 1024px rather than 768px — the same threshold
the design language already specifies, for the same reason.

Insert between Media and Certification, so the two content sections sit together:

```html
<li><a href="/dictionary/">Dictionary</a></li>
```

Apply this to every page's navbar. On the dictionary's own pages the link
carries `aria-current="page"`, which the existing CSS already styles gold.

If the eighth item crowds the bar at intermediate widths, the cheapest fix is
dropping the nav link font-size from `0.85rem` to `0.82rem` — measured to fit at
1024px without changing the breakpoint.

## 3. Reconcile the stylesheets

`assets/css/tokens.css` is a faithful subset of the site's `styles.css`. Once
the dictionary lives inside the site, you have two options:

**Option A — share the site stylesheet (preferred).** Replace the `tokens.css`
link in the generated `<head>` with the site's `styles.css`, and keep
`dictionary.css`. Edit `head_html()` in `build/build.py`, then rebuild. One
palette, one navbar implementation, no drift.

**Option B — keep tokens.css.** Simpler to deploy, but the two files must be
kept in sync by hand. Choose this only if the dictionary ships before the main
site's next release.

Under Option A, note the contrast difference: this project defines
`--text-muted: #827b74` (4.60:1, AA pass) where the site ships `#5a5550`
(2.60:1, fail). Adopting the site's stylesheet reintroduces the failure across
every dictionary page, which affects real content — entry metadata, breadcrumbs,
citation sources. Lifting the token site-wide is the better fix; it is the
change already recommended in section 2b of the design language.

## 4. Wire up search from elsewhere on the site

The hub accepts a `?q=` parameter and runs the search on load, which is what the
`SearchAction` in its JSON-LD advertises. Any search box on the site can hand
off with:

```html
<form action="/dictionary/" method="get">
  <input type="search" name="q" placeholder="Search the dictionary">
</form>
```

Scope can be preselected in the same way if needed — the scope buttons read
`data-scope="all" | "ai-mathematics" | "software-engineering"`.

## 5. Sitemap and structured data

- Merge `dictionary/sitemap.xml` into the site's sitemap index, or reference it
  from `robots.txt`.
- The hub declares `WebSite` with `@id` `https://thehallucinatedlab.space/#website`,
  matching the identity graph the home page already publishes. It references
  that node rather than restating it, per the site's structured-data convention.
- Each term page publishes a `DefinedTerm` inside a `DefinedTermSet`, plus a
  four-level `BreadcrumbList`. This is the shape search engines and AI crawlers
  expect for glossary content, and it is why each term is a real page rather
  than a client-side route.

## 6. What to check after deploying

- The navbar highlights Dictionary on `/dictionary/` and on every term page.
- `/dictionary/?q=gradient` loads with results already rendered.
- A term page opened directly (no referrer) renders fully with JavaScript off.
- No horizontal overflow at 375, 414, 768, 1024, 1280 and 1920px — the corpus
  grid uses `minmax(min(320px, 100%), 1fr)` specifically to satisfy the design
  language's critical grid rule.
