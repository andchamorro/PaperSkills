# API Reference

API endpoints, parameters, and fallback chains for research-gap skill.

## Semantic Scholar

**Base URL:** `https://api.semanticscholar.org/graph/v1`

**Rate limit:** Medium — use politely, cache when possible.

### Paper Search

```
GET /paper/search
```

| Parameter | Value | Notes |
|-----------|-------|-------|
| `query` | string | Search query |
| `limit` | 1-100 | Default 10 |
| `offset` | int | For pagination |
| `fields` | comma-separated | See field list below |
| `year` | YYYY-YYYY | Optional range filter |

**Recommended fields:** `title,authors,year,venue,citationCount,abstract,fieldsOfStudy,openAccessPdf`

**Example:**
```
GET /paper/search?query=LLM%20fairness&limit=40&fields=title,authors,year,venue,citationCount,abstract,fieldsOfStudy&year=2019-2026
```

### Recommendations

```
GET /recommendations/v1/papers/forpaper/{paperId}
```

Returns related papers for a given paper ID. Useful for building literature clusters.

```
GET /recommendations/v1/papers/forpaper/{paperId}?limit=20&fields=title,authors,year,citationCount,abstract
```

## OpenAlex

**Base URL:** `https://api.openalex.org`

**Rate limit:** Low — always include `mailto` parameter.

**Fallback:** Use when Semantic Scholar fails or is rate-limited.

### Works Search

```
GET /works?search={topic}&{filters}&sort={field}:{direction}&per_page={n}&mailto={email}
```

| Parameter | Value | Notes |
|-----------|-------|-------|
| `search` | string | Search terms |
| `filter` | filter expressions | year, venue, type, open_access |
| `sort` | field:direction | cited_by_count:desc, publication_year:desc |
| `per_page` | 1-200 | Default 25 |
| `mailto` | email | Required for higher rate limits |

**Filter syntax:**
```
publication_year:2023-2026
venue: journals/Journal-name
open_access.is_oa:true
type: journal-article
```

### Group By (Trends)

Use `group_by` to aggregate works by a dimension:

```
GET /works?search={topic}&group_by=publication_year&mailto=paperskills@example.com
```

Returns paper counts per year. Useful for temporal gap analysis.

**Common group_by dimensions:**
- `publication_year` — papers per year
- `type` — by document type
- `open_access.is_oa` — OA vs non-OA
- `authorships.countries.count` — geographic spread
- `concepts.id` — concept distribution

### Concepts

```
GET /concepts?search={topic}&mailto=paperskills@example.com
```

Returns related concepts with `works_count`, `description`, and `level`.

```
GET /concepts?search={topic}&mailto=paperskills@example.com
```

### Concept Works

```
GET /concepts/{concept_id}/works?sort=cited_by_count:desc&per_page=25&mailto=paperskills@example.com
```

## Rate Limit Handling

Both APIs enforce rate limits. Apply exponential backoff on HTTP 429 responses:

1. First retry: wait 1 second
2. Second retry: wait 2 seconds
3. Third retry: wait 4 seconds
4. After 3 retries: switch to fallback API

**Semantic Scholar** returns HTTP 429 with a `Retry-After` header. Respect the header value if present.

**OpenAlex** rate limits are lower when `mailto` is included (polite pool). Always include `mailto=paperskills@example.com`.

### Python Fetch Helper Template

Agents can copy this pattern for API calls:

```python
import json
import time
import urllib.request


def fetch_json(url: str, retries: int = 3) -> dict | None:
    """Fetch JSON from URL with exponential backoff."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2**attempt)
            else:
                print(f"ERROR: Failed to fetch {url}: {e}", file=__import__("sys").stderr)
                return None
    return None
```

## Fallback Chain

When calling APIs in sequence:

1. **Primary:** Semantic Scholar paper search (limit 40, recent+highly cited)
2. **Fallback 1:** OpenAlex works search (limit 20, recent)
3. **Fallback 2:** OpenAlex works search (limit 20, highly cited, older)
4. **Fallback 3:** OpenAlex concepts (to find related terms)
5. **Last resort:** Note gap in data, proceed with available evidence

If both APIs fail:
- Report the failure to the user
- Offer to proceed with manual literature input
- Suggest narrowing the topic

## Output Schema

After running the landscape subagent, collect:

```
LANDSCAPE_COLLECT:
- paper_count_per_year: {year: count} from OpenAlex group_by
- top_30_cited: [{title, authors, year, citations, abstract}] from Semantic Scholar
- top_20_recent: [{title, authors, year, citations}] from OpenAlex recent filter
- top_venues: [{venue, count}] from OpenAlex
- key_authors: [{name, paper_count, total_citations}] from OpenAlex
- related_concepts: [{name, works_count, description}] from OpenAlex concepts
- abstract_corpus: [extracted themes from top 30 abstracts]
```

Pass this as structured input to the gap identification subagent.
