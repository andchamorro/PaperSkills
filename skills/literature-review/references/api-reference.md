# Literature Search API Reference

This document describes the literature_scripts Python backend that powers the
literature-review skill.

## Scripts Overview

| Script | Purpose | Coverage | API Key Required |
|--------|---------|----------|----------|-----------------|
| `search_openalex.py` | OpenAlex search | Broad academic | No |
| `search_crossref.py` | CrossRef search | DOI lookup, BibTeX | No |
| `download_arxiv_source.py` | arXiv source | STEM preprints | No |

## search_openalex.py

Self-contained: stdlib only (urllib, json). No external dependencies.

### Usage

```bash
python skills/literature-review/scripts/search_openalex.py \
  --query "QUERY" \
  --max-results 20 \
  --year-range 2020-2026 \
  --min-citations 5 \
  --sort cited_by_count:desc \
  -o results.jsonl
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | required | Search keywords |
| `--max-results` | int | 50 | Max papers to return |
| `--year-range` | string | None | Year filter (e.g. 2020-2026) |
| `--min-citations` | int | 0 | Minimum citation count |
| `--type` | string | None | Work type (article, proceedings-article) |
| `--sort` | string | cited_by_count:desc | Sort order |
| `-o`, `--output` | string | stdout | Output file |

### Output Format (JSONL)

```json
{
  "openalex_id": "https://openalex.org/W123456",
  "doi": "10.1234/abc",
  "arxiv_id": "",
  "title": "Paper Title",
  "authors": ["Author One", "Author Two"],
  "abstract": "Paper abstract...",
  "year": 2023,
  "venue": "Conference Name",
  "citationCount": 1234,
  "pdf_url": "https://...",
  "source": "openalex"
}
```

### Rate Limit

OpenAlex allows 100,000 requests/day with email (handled internally).

---

## search_crossref.py

Self-contained: stdlib only (urllib, json, unicodedata). No external dependencies.

### Usage

```bash
python skills/literature-review/scripts/search_crossref.py \
  --query "QUERY" \
  --rows 20 \
  --bibtex \
  -o refs.bib
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | required | Search keywords |
| `--rows` | int | 10 | Number of results |
| `--bibtex` | flag | False | Output BibTeX format |
| `-o`, `--output` | string | stdout | Output file |
| `--timeout` | int | 30 | Request timeout (seconds) |

### Output Formats

**JSONL (default):**
```json
{
  "title": "Paper Title",
  "authors": "Author One and Author Two",
  "year": "2023",
  "journal": "Journal Name",
  "doi": "10.1234/abc",
  "type": "article",
  "cited_by": 123,
  "bibtex_key": "Author2023paper"
}
```

**BibTeX (with --bibtex flag):**
```bibtex
@article{Author2023paper,
  title = {Paper Title},
  author = {Author One and Author Two},
  journal = {Journal Name},
  year = {2023},
  doi = {10.1234/abc}
}
```

### Rate Limit

CrossRef allows ~50 req/s (handled internally with retry logic).

---

## download_arxiv_source.py

Self-contained: stdlib only (urllib, xml.etree, tarfile, tempfile).

### Usage

```bash
python skills/literature-review/scripts/download_arxiv_source.py \
  --title "Attention Is All You Need" \
  --max-results 3 \
  --output-dir arxiv_papers/
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--title` | string | None | Paper title to search |
| `--arxiv-id` | string | None | Direct arXiv ID |
| `--max-results` | int | 5 | Max search results |
| `--output-dir` | string | arxiv_papers/ | Output directory |
| `--metadata` | flag | False | Also save metadata JSON |

---

## Security Patterns

### Stdlib-Only Networking

All scripts use only:
- `urllib.request` — stdlib HTTP client
- `urllib.parse` — URL encoding
- No `socket` module directly
- No custom network handling
- No raw socket creation

### Request Headers

```python
HEADERS = {
    "User-Agent": "SkillScript/1.0 (mailto:user@example.com)"
}
```

Always include User-Agent for rate limit etiquette.

### Error Handling

Scripts implement:
- Retry logic with exponential backoff
- Timeout handling (default 30s)
- Graceful degradation on network errors

---

## DOI Handling

### Normalization

```python
def normalize_doi(doi):
    doi = doi.lower().strip()
    for prefix in ["https://doi.org/", "http://doi.org/", "doi:"]:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi
```

### Deduplication

1. Extract all DOIs from results
2. Normalize to lowercase, strip prefixes
3. Group by DOI → keep richest metadata
4. For papers without DOI:
   - Tokenize title, remove stopwords
   - Compare with >80% token overlap
   - Keep highest-cited variant

---

## Merging Results

When using multiple scripts, merge with DOI-based deduplication:

```python
def merge_results(openalex_results, crossref_results):
    merged = {}
    for r in openalex_results:
        doi = r.get("doi", "").lower()
        if doi and doi not in merged:
            merged[doi] = r
    for r in crossref_results:
        doi = r.get("doi", "").lower()
        if doi:
            if doi in merged:
                # Keep richer metadata
                if r.get("type") == "article":
                    merged[doi] = r
            else:
                merged[doi] = r
    return list(merged.values())
```