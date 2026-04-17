#!/usr/bin/env python3
"""
Generate a URL-safe slug from a topic string.
Handles English, Chinese, and mixed-language input.

Usage:
    python scripts/slugify.py "LLM Fairness in Hiring"
    # → llm-fairness-in-hiring

    python scripts/slugify.py "平台算法治理"
    # → ping-tai-suan-fa-zhi-li  (if pypinyin installed)
    # → 53ef298f                  (hash fallback)

    python scripts/slugify.py "AI搜索广告 and Advertiser Strategy"
    # → ai-sou-suo-guang-gao-and-advertiser-strategy  (if pypinyin)
    # → ai-and-advertiser-strategy-b3a1c7e2           (hash fallback)

Exit codes:
    0: success (slug printed to stdout)
    1: empty input or error
"""

import hashlib
import re
import sys
import unicodedata


def _is_cjk(char: str) -> bool:
    """Check if a character is in the CJK Unified Ideographs block."""
    cp = ord(char)
    return (
        0x4E00 <= cp <= 0x9FFF
        or 0x3400 <= cp <= 0x4DBF
        or 0x20000 <= cp <= 0x2A6DF
        or 0x2A700 <= cp <= 0x2B73F
        or 0x2B740 <= cp <= 0x2B81F
        or 0xF900 <= cp <= 0xFAFF
    )


def _has_cjk(text: str) -> bool:
    """Check if text contains any CJK characters."""
    return any(_is_cjk(c) for c in text)


def _pinyin_slugify(text: str) -> str:
    """Convert text with CJK characters using pypinyin. Returns empty string if pypinyin unavailable."""
    try:
        from pypinyin import lazy_pinyin

        parts = []
        buffer = ""
        prev_was_cjk = False

        for char in text:
            if _is_cjk(char):
                if buffer and not prev_was_cjk:
                    parts.append(buffer.strip())
                    buffer = ""
                pinyin = lazy_pinyin(char)
                parts.extend(pinyin)
                prev_was_cjk = True
            else:
                if prev_was_cjk and buffer == "":
                    pass
                buffer += char
                prev_was_cjk = False

        if buffer.strip():
            parts.append(buffer.strip())

        return "-".join(p for p in parts if p)
    except ImportError:
        return ""


def _hash_fallback(text: str) -> str:
    """Generate a short hash for CJK text when pypinyin is unavailable."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:8]


def slugify(text: str) -> str:
    """Convert a topic string to a URL-safe slug.

    Strategy:
    1. If text has CJK chars and pypinyin is available: transliterate to pinyin
    2. If text has CJK chars and no pypinyin: strip CJK, keep ASCII, append hash
    3. Pure ASCII: normalize directly
    """
    text = text.strip()
    if not text:
        return ""

    if _has_cjk(text):
        pinyin_result = _pinyin_slugify(text)
        if pinyin_result:
            slug = pinyin_result
        else:
            ascii_part = re.sub(r"[^\x00-\x7F]+", " ", text).strip()
            h = _hash_fallback(text)
            slug = f"{ascii_part}-{h}" if ascii_part else h
    else:
        slug = text

    slug = unicodedata.normalize("NFKD", slug)
    slug = slug.encode("ascii", "ignore").decode("ascii")
    slug = slug.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")

    if not slug:
        slug = _hash_fallback(text)

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
