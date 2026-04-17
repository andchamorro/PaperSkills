# API Reference — Paper Tracker

This file contains endpoint templates for the three APIs used by the paper-tracker skill. All URLs use placeholder variables in `{braces}`.

**Always include `mailto=paperskills@example.com`** in every OpenAlex request to get the polite pool (~10 req/s).

---

## OpenAlex

Base URL: `https://api.openalex.org`

### Authors — resolve name to ID

```
GET /authors?search={author_name}&per_page=5&mailto=paperskills@example.com
```

Response fields of interest: `id`, `display_name`, `last_known_institutions`, `works_count`.

### Institutions — resolve name to ID

```
GET /institutions?search={institution_name}&per_page=5&mailto=paperskills@example.com
```

Response fields of interest: `id`, `display_name`, `country_code`, `type`.

### Sources (Journals / Venues) — resolve name to ID

```
GET /sources?search={journal_name}&per_page=5&mailto=paperskills@example.com
```

Response fields of interest: `id`, `display_name`, `type`, `issn`.

### Works — filtered by entity and date window

**By author:**
```
GET /works?filter=author.id:{author_id},from_publication_date:{start},to_publication_date:{end}&sort=publication_date:desc&per_page=50&mailto=paperskills@example.com
```

**By institution:**
```
GET /works?filter=institutions.id:{institution_id},from_publication_date:{start},to_publication_date:{end}&sort=publication_date:desc&per_page=50&mailto=paperskills@example.com
```

**By journal / venue:**
```
GET /works?filter=primary_location.source.id:{source_id},from_publication_date:{start},to_publication_date:{end}&sort=publication_date:desc&per_page=50&mailto=paperskills@example.com
```

**By keyword / domain (full-text search):**
```
GET /works?search={query}&filter=from_publication_date:{start},to_publication_date:{end}&sort=publication_date:desc&per_page=50&mailto=paperskills@example.com
```

### Pagination

OpenAlex returns `meta.count` and supports `page` / `per_page` (max 200). For large result sets, paginate until all pages are consumed or the token budget is exceeded.

---

## Semantic Scholar

Base URL: `https://api.semanticscholar.org/graph/v1`

### Paper search (fallback for abstracts)

```
GET /paper/search?query={title_or_doi}&limit=1&fields=title,abstract,authors,year,venue,externalIds,openAccessPdf
```

### Paper lookup by DOI

```
GET /paper/DOI:{doi}?fields=title,abstract,authors,year,venue,externalIds,openAccessPdf
```

Rate limit: 1 request/second without API key. On 429, wait 5 seconds and retry once.

---

## CrossRef

Base URL: `https://api.crossref.org`

### Works search (fallback for missing DOI or publication date)

```
GET /works?query.title={title}&rows=3
```

Response fields of interest: `DOI`, `title`, `published-print` or `published-online`, `container-title`, `author`.

Rate limit: ~50 req/s for polite pool (include `User-Agent` or `mailto` header). Keep requests ≤5/s to be safe.

---

## General Notes

- Always prefer OpenAlex as the primary source. Use Semantic Scholar only when OpenAlex lacks an abstract. Use CrossRef only when DOI or publication date is missing.
- Normalize all DOIs to lowercase with no URL prefix before comparison.
- When an API returns an error or empty result, log the issue to stderr and continue with remaining sources.
