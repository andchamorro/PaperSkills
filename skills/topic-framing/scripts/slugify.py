#!/usr/bin/env python3
"""
Generate a URL-safe slug from a topic string.

Usage:
    python scripts/slugify.py "LLM Fairness in Hiring"
    # → llm-fairness-in-hiring

    python scripts/slugify.py "AI Search Ads and Advertiser Strategy"
    # → ai-search-ads-and-advertiser-strategy

Exit codes:
    0: success (slug printed to stdout)
    1: empty input or error
"""

import re
import sys
import unicodedata


def slugify(text: str) -> str:
    """Convert a topic string to a URL-safe slug."""
    text = text.strip()
    if not text:
        return ""

    slug = unicodedata.normalize("NFKD", text)
    slug = slug.encode("ascii", "ignore").decode("ascii")
    slug = slug.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")

    return slug


def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print(
            'ERROR: No input provided. Usage: python slugify.py "Topic Name"',
            file=sys.stderr,
        )
        sys.exit(1)

    topic = " ".join(sys.argv[1:])
    result = slugify(topic)

    if not result:
        print("ERROR: Could not generate slug from input.", file=sys.stderr)
        sys.exit(1)

    print(result)


if __name__ == "__main__":
    main()
