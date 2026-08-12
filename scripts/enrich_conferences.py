#!/usr/bin/env python3
"""Add conference metadata from arXiv's category listing pages.

The daily arXiv RSS feeds omit the ``arxiv:comment`` field used by MyArxiv's
conference highlighter.  Category listing pages expose the author-supplied
Comments field, so this script fetches one page per configured category,
recognizes known conference names, updates cache.json, and adds the chip to the
HTML generated in the same workflow run.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ARXIV_ID_RE = re.compile(r"(?:arxiv\.org/abs/|arXiv:)?([^/]+?)(?:v\d+)?$")
LIST_ITEM_RE = re.compile(r"(?s)<dt>(.*?)</dt>\s*<dd>(.*?)</dd>")
LIST_ID_RE = re.compile(r"href\s*=\s*['\"]/abs/([^'\"]+)")
COMMENT_RE = re.compile(
    r"(?s)<div\s+class=['\"]list-comments\s+mathjax['\"]>(.*?)</div>"
)
TAG_RE = re.compile(r"(?s)<[^>]+>")
ARTICLE_RE = re.compile(
    r'(?s)(<details class="article-expander">)(.*?)(</details>)'
)
ARTICLE_ID_RE = re.compile(r'href="https://arxiv\.org/abs/([^"]+)"')


def arxiv_id(value: str) -> str:
    match = ARXIV_ID_RE.search(value.strip())
    if not match:
        return value.strip()
    return re.sub(r"v\d+$", "", match.group(1))


def configured_categories(config_path: Path) -> list[str]:
    text = config_path.read_text(encoding="utf-8")
    return list(dict.fromkeys(re.findall(r'^\s*category\s*=\s*"([^"]+)"', text, re.M)))


def configured_conferences(rhai_path: Path) -> list[str]:
    text = rhai_path.read_text(encoding="utf-8")
    block = re.search(r"(?s)let\s+conferences\s*=\s*\[(.*?)\];", text)
    if not block:
        raise ValueError(f"Cannot find conferences in {rhai_path}")
    names = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', block.group(1))
    return list(dict.fromkeys(json.loads(f'"{name}"') for name in names))


def conference_pattern(names: list[str]) -> tuple[re.Pattern[str], dict[str, str]]:
    # Longest first keeps ACM MM ahead of shorter aliases. Very short names are
    # intentionally excluded because tokens such as SP/SC cause false labels in
    # ordinary author comments.
    safe_names = sorted((name for name in names if len(name) > 2), key=len, reverse=True)
    canonical = {name.casefold(): name for name in safe_names}
    alternatives = "|".join(re.escape(name).replace(r"\ ", r"\s+") for name in safe_names)
    pattern = re.compile(
        rf"(?<![A-Za-z0-9])(?P<venue>{alternatives})"
        r"(?:[\s'’\-]*(?P<year>20\d{2}|\d{2}))?(?![A-Za-z0-9])",
        re.I,
    )
    return pattern, canonical


def plain_text(fragment: str) -> str:
    text = TAG_RE.sub(" ", fragment)
    return " ".join(html.unescape(text).split())


def fetch_listing(category: str, attempts: int = 3) -> str:
    url = f"https://arxiv.org/list/{quote(category, safe='.')}/recent?skip=0&show=2000"
    request = Request(
        url,
        headers={
            "User-Agent": "MyArxiv/1.0 (personal research feed; conference metadata)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    for attempt in range(1, attempts + 1):
        try:
            with urlopen(request, timeout=45) as response:
                return response.read().decode("utf-8", errors="replace")
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == attempts:
                raise
        except URLError:
            if attempt == attempts:
                raise
        time.sleep(3 * attempt)
    return ""


def listing_comments(page: str) -> dict[str, str]:
    comments: dict[str, str] = {}
    for dt, dd in LIST_ITEM_RE.findall(page):
        id_match = LIST_ID_RE.search(dt)
        comment_match = COMMENT_RE.search(dd)
        if not id_match or not comment_match:
            continue
        comment = plain_text(comment_match.group(1))
        if comment:
            comments[arxiv_id(id_match.group(1))] = comment
    return comments


def recognized_venue(
    comment: str, pattern: re.Pattern[str], canonical: dict[str, str]
) -> str | None:
    match = pattern.search(comment)
    if not match:
        return None
    venue = canonical[match.group("venue").casefold()]
    year = match.group("year")
    if year and len(year) == 2:
        year = f"20{year}"
    return f"{venue} {year}" if year else venue


def enrich_cache(
    cache_path: Path, comments: dict[str, str]
) -> tuple[dict[str, str], int]:
    data = json.loads(cache_path.read_text(encoding="utf-8"))
    matched: dict[str, str] = {}
    updated_ids: set[str] = set()
    for subjects in data.values():
        for papers in subjects.values():
            for paper in papers:
                paper_id = arxiv_id(paper.get("id", ""))
                if paper_id not in comments:
                    continue
                paper["comment"] = comments[paper_id]
                matched[paper_id] = comments[paper_id]
                updated_ids.add(paper_id)
    cache_path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return matched, len(updated_ids)


def enrich_html(html_path: Path, venues: dict[str, str]) -> int:
    source = html_path.read_text(encoding="utf-8")
    inserted = 0

    def add_chip(match: re.Match[str]) -> str:
        nonlocal inserted
        body = match.group(2)
        id_match = ARTICLE_ID_RE.search(body)
        if not id_match:
            return match.group(0)
        venue = venues.get(arxiv_id(id_match.group(1)))
        summary_end = body.find("</summary>")
        if not venue or summary_end < 0 or 'class="chip"' in body[:summary_end]:
            return match.group(0)
        chip = f' <span class="chip">{html.escape(venue)}</span>'
        body = body[:summary_end] + chip + body[summary_end:]
        inserted += 1
        return match.group(1) + body + match.group(3)

    enriched = ARTICLE_RE.sub(add_chip, source)
    html_path.write_text(enriched, encoding="utf-8")
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config.toml"))
    parser.add_argument(
        "--conference-config", type=Path, default=Path("scripts/config.rhai")
    )
    parser.add_argument("--cache", type=Path, default=Path("target/cache.json"))
    parser.add_argument("--html", type=Path, default=Path("target/index.html"))
    args = parser.parse_args()

    names = configured_conferences(args.conference_config)
    pattern, canonical = conference_pattern(names)
    comments: dict[str, str] = {}
    for category in configured_categories(args.config):
        try:
            category_comments = listing_comments(fetch_listing(category))
            comments.update(category_comments)
            print(f"{category}: found {len(category_comments)} author comments")
        except (HTTPError, URLError, TimeoutError) as error:
            # Conference enrichment should never prevent the daily feed itself
            # from deploying; cached labels survive future successful runs.
            print(f"warning: could not enrich {category}: {error}", file=sys.stderr)

    conference_comments = {
        paper_id: comment
        for paper_id, comment in comments.items()
        if recognized_venue(comment, pattern, canonical)
    }
    matched_comments, cache_count = enrich_cache(args.cache, conference_comments)
    venues = {
        paper_id: venue
        for paper_id, comment in matched_comments.items()
        if (venue := recognized_venue(comment, pattern, canonical))
    }
    html_count = enrich_html(args.html, venues)
    print(
        f"Conference enrichment complete: {cache_count} cached papers, "
        f"{html_count} HTML labels"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
