# API Reference — Citation Network

## Semantic Scholar Graph API

Base URL: `https://api.semanticscholar.org/graph/v1`

Rate limit: **1 request/second** without API key; 10 req/s with key.

### Single Paper + References + Citations

```
GET /paper/{paperId}?fields=paperId,title,authors,year,venue,citationCount,externalIds,references.paperId,references.title,references.authors,references.year,references.citationCount,references.externalIds,citations.paperId,citations.title,citations.authors,citations.year,citations.citationCount,citations.externalIds
```

**paperId formats:**
| Format | Example |
|---|---|
| DOI | `DOI:10.1038/s41586-023-06221-2` |
| PubMed | `PMID:12345678` |
| Corpus ID | `CorpusId:456789` |
| S2 native | `649def34f8be52c8b66281af98ae884c09aef38b` |

**Response shape (relevant fields):**
```json
{
  "paperId": "string",
  "title": "string",
  "authors": [{"authorId": "string", "name": "string"}],
  "year": 2023,
  "venue": "Nature",
  "citationCount": 150,
  "externalIds": {"DOI": "10.1038/...", "ArXiv": "2301.12345"},
  "references": [{"paperId": "...", "title": "...", "authors": [...], "year": 2020, "citationCount": 50, "externalIds": {...}}],
  "citations": [{"paperId": "...", "title": "...", "authors": [...], "year": 2024, "citationCount": 10, "externalIds": {...}}]
}
```

### Title Search

```
GET /paper/search?query={url_encoded_title}&limit=1&fields=paperId,title,authors,year,citationCount,externalIds
```

Returns `{"data": [{"paperId": "...", ...}]}`. Use `data[0].paperId` for subsequent requests.

### Batch Paper Lookup (efficient)

```
POST /paper/batch
Content-Type: application/json
Body: {"ids": ["DOI:10.1...", "DOI:10.2..."]}
?fields=title,authors,year,citationCount,externalIds
```

- Maximum **500 IDs** per request.
- Prefer batch requests when resolving multiple papers to reduce API calls.

## OpenCitations COCI API

Base URL: `https://opencitations.net/index/api/v2`

Rate limit: No strict limit, but use responsibly (1-2 req/s recommended).

### Citations of a Paper

```
GET /citations/{doi}
```

### References of a Paper

```
GET /references/{doi}
```

**Response shape (both endpoints):**
```json
[
  {
    "citing": "10.1234/abc",
    "cited": "10.5678/def",
    "creation": "2023-01-15",
    "timespan": "P2Y"
  }
]
```

## OpenAlex API (Fallback)

Base URL: `https://api.openalex.org`

Use as fallback when Semantic Scholar returns no results.

### Paper Lookup by DOI

```
GET /works/https://doi.org/{doi}
```

### Title Search

```
GET /works?search={title}&per_page=1
```

**Response shape (relevant fields):**
```json
{
  "id": "https://openalex.org/W1234567890",
  "doi": "https://doi.org/10.1234/abc",
  "title": "string",
  "publication_year": 2023,
  "cited_by_count": 150,
  "authorships": [{"author": {"display_name": "string"}}]
}
```
