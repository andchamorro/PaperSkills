# Literature Search API Reference

Detailed API endpoints and parameters for the lit-search skill.

## Semantic Scholar API

**Base URL:** `https://api.semanticscholar.org/graph/v1`

### Paper Search

```
GET /paper/search?query={query}&limit={limit}&fields={fields}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| query | string | required | Search query |
| limit | int | 10 | Max results (max 100) |
| fields | string | title,authors | Comma-separated: title,authors,year,venue,citationCount,abstract,externalIds,openAccessPdf |

**Example:**
```
https://api.semanticscholar.org/graph/v1/paper/search?query=machine%20learning&limit=20&fields=title,authors,year,venue,citationCount,abstract,externalIds,openAccessPdf
```

**Rate Limit:** 1 request/second (100 requests/day without key)

### Paper Details

```
GET /paper/{paperId}?fields={fields}
```

**paperId** can be DOI (e.g., `10.1038/nature14539`), arXiv ID, or Semantic Scholar paper ID.

---

## OpenAlex API

**Base URL:** `https://api.openalex.org`

### Work Search

```
GET /works?search={query}&per_page={per_page}&sort={sort}&mailto={email}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| search | string | required | Search query |
| per_page | int | 25 | Results per page (max 200) |
| sort | string | cited_by_count:desc | Sort field |
| mailto | string | required | Contact email (rate limit etiquette) |

**Example:**
```
https://api.openalex.org/works?search=machine%20learning&per_page=20&sort=cited_by_count:desc&mailto=paperskills@example.com
```

**Rate Limit:** 100,000 requests/day (requires email)

---

## PubMed API (NCBI)

**Base URL:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`

### Search

```
GET /esearch.fcgi?db=pubmed&term={query}&retmax={retmax}&retmode=json
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| db | string | pubmed | Database |
| term | string | required | Search query |
| retmax | int | 20 | Max results |
| retmode | string | json | Response format |

**Example:**
```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=cancer%20immunotherapy&retmax=20&retmode=json
```

### Summary

```
GET /esummary.fcgi?db=pubmed&id={pmids}&retmode=json
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| db | string | pubmed | Database |
| id | string | required | Comma-separated PMIDs |
| retmode | string | json | Response format |

**Example:**
```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=34567890,34567891&retmode=json
```

**Rate Limit:** 3 requests/second (合理使用)

---

## arXiv API

**Base URL:** `https://export.arxiv.org/api/query`

### Search

```
GET /query?search_query=all:{query}&max_results={max_results}&sortBy={sortBy}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| search_query | string | required | Search query (prefix with `all:` for general search) |
| max_results | int | 10 | Max results |
| sortBy | string | relevance | Options: relevance, lastUpdatedDate, submittedDate |

**Example:**
```
https://export.arxiv.org/api/query?search_query=all:transformer&max_results=20&sortBy=relevance
```

**Response Format:** Atom XML — parse `<entry>` elements for:
- `id` (arXiv URL)
- `title`
- `summary` (abstract)
- `author` (name)
- `published` (date)
- `arxiv:category` (subject)

**Rate Limit:** 1 request/3 seconds

---

## DOI Handling

### Normalization

```python
def normalize_doi(doi):
    if not doi:
        return None
    doi = doi.lower().strip()
    # Strip URL prefix
    for prefix in ['https://doi.org/', 'http://doi.org/', 'doi:']:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi if doi.startswith('10.') else None
```

### Deduplication Logic

```
1. Extract all DOIs from results
2. Normalize to lowercase, strip prefixes
3. Group by DOI → keep richest metadata record
4. For papers without DOI:
   - Tokenize title, remove stopwords
   - Compare with Levenshtein similarity > 80%
   - Group similar titles, keep highest-cited
```

---

## Response Parsing

### Semantic Scholar JSON

```json
{
  "data": [
    {
      "paperId": "...",
      "title": "...",
      "authors": [{"name": "..."}],
      "year": 2023,
      "venue": "...",
      "citationCount": 1234,
      "abstract": "...",
      "externalIds": {"DOI": "10.xxx/yyy"},
      "openAccessPdf": {"url": "..."}
    }
  ]
}
```

### OpenAlex JSON

```json
{
  "results": [
    {
      "id": "https://openalex.org/W123456",
      "doi": "10.xxx/yyy",
      "title": "...",
      "publication_year": 2023,
      "cited_by_count": 1234,
      "authorships": [{"author": {"display_name": "..."}}],
      "primary_location": {"source": {"display_name": "..."}}
    }
  ]
}
```

### PubMed JSON (esummary)

```json
{
  "result": {
    "uids": ["12345"],
    "12345": {
      "uid": "12345",
      "title": "...",
      "pubdate": "2023",
      "authors": [{"name": "..."}],
      "source": "..."
    }
  }
}
```

### arXiv XML

```xml
<feed>
  <entry>
    <id>http://arxiv.org/abs/2301.12345</id>
    <title>...</title>
    <summary>...</summary>
    <author><name>...</name></author>
    <published>2023-01-15T00:00:00Z</published>
    <category term="cs.LG"/>
  </entry>
</feed>
```