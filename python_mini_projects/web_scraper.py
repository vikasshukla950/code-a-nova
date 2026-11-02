#!/usr/bin/env python3
"""
Web Scraper  (Level 1c)
-----------------------
Scrapes data from websites using Requests + BeautifulSoup, follows
pagination automatically, and saves the results as CSV or JSON.

Built-in practice sites (made for scraping, so they're safe to use):
    quotes  ->  https://quotes.toscrape.com/   (quote, author, tags)
    books   ->  https://books.toscrape.com/    (title, price, rating, availability)

Usage:
    python web_scraper.py                                   # quotes -> quotes.csv
    python web_scraper.py --site books --format json        # books  -> books.json
    python web_scraper.py --site quotes --max-pages 3       # only first 3 pages
    python web_scraper.py --site quotes --output my_data.json --format json

To scrape another site, write a parse_* function (see below) and add it to SITES.
Always check a site's robots.txt / terms of service before scraping it.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (educational-web-scraper/1.0)"}


# ---------- parsers: one per site, each returns a list of dicts ----------

def parse_quotes(soup: BeautifulSoup, page_url: str) -> list[dict]:
    items = []
    for block in soup.select("div.quote"):
        items.append({
            "quote": block.select_one("span.text").get_text(strip=True),
            "author": block.select_one("small.author").get_text(strip=True),
            "tags": [tag.get_text(strip=True) for tag in block.select("div.tags a.tag")],
        })
    return items


def parse_books(soup: BeautifulSoup, page_url: str) -> list[dict]:
    items = []
    for book in soup.select("article.product_pod"):
        link = book.select_one("h3 a")
        rating_classes = book.select_one("p.star-rating")["class"]  # e.g. ["star-rating", "Three"]
        items.append({
            "title": link["title"],
            "price": book.select_one("p.price_color").get_text(strip=True),
            "rating": next((c for c in rating_classes if c != "star-rating"), ""),
            "availability": book.select_one("p.availability").get_text(strip=True),
            "url": urljoin(page_url, link["href"]),
        })
    return items


SITES = {
    "quotes": {"start_url": "https://quotes.toscrape.com/", "parser": parse_quotes},
    "books": {"start_url": "https://books.toscrape.com/", "parser": parse_books},
}


# ---------- fetching & pagination ----------

def fetch_page(session: requests.Session, url: str, retries: int = 3, timeout: float = 10.0):
    """GET a page, retrying with backoff on network errors / 5xx. Returns Response or None."""
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code >= 500:
                raise requests.HTTPError(f"Server error {response.status_code}")
            response.raise_for_status()
            return response
        except requests.RequestException as err:
            print(f"  ! Attempt {attempt}/{retries} failed ({type(err).__name__})")
            if attempt < retries:
                time.sleep(2 * attempt)
    return None


def find_next_page(soup: BeautifulSoup, page_url: str) -> str | None:
    """Return the absolute URL of the 'Next' page link, or None on the last page."""
    link = soup.select_one("li.next a")
    return urljoin(page_url, link["href"]) if link and link.get("href") else None


def scrape(start_url: str, parser, max_pages: int | None = None, delay: float = 1.0) -> list[dict]:
    """Scrape start_url and keep following 'Next' links, collecting all items."""
    session = requests.Session()
    session.headers.update(HEADERS)

    all_items: list[dict] = []
    visited: set[str] = set()
    url: str | None = start_url
    page_number = 0

    while url and url not in visited:
        if max_pages is not None and page_number >= max_pages:
            break

        visited.add(url)
        page_number += 1
        print(f"Page {page_number}: {url}")

        response = fetch_page(session, url)
        if response is None:
            print("  Giving up on this page; stopping.")
            break

        # Pass raw bytes so BeautifulSoup detects the encoding itself (avoids 'Â£' glitches).
        soup = BeautifulSoup(response.content, "html.parser")
        items = parser(soup, url)
        all_items.extend(items)
        print(f"  found {len(items)} items (total: {len(all_items)})")

        url = find_next_page(soup, url)
        if url:
            time.sleep(delay)  # be polite to the server

    return all_items


# ---------- saving ----------

def save_csv(data: list[dict], path: str) -> None:
    # Lists (like tags) can't live in a CSV cell, so join them with '|'.
    rows = [{k: "|".join(v) if isinstance(v, list) else v for k, v in row.items()} for row in data]
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:  # utf-8-sig opens cleanly in Excel
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def save_json(data: list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape a website and save the data as CSV or JSON.")
    parser.add_argument("--site", choices=SITES, default="quotes", help="Which built-in scraper to use")
    parser.add_argument("--url", help="Override the starting URL (same page layout as --site)")
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format")
    parser.add_argument("--output", help="Output file name (default: <site>.<format>)")
    parser.add_argument("--max-pages", type=int, help="Stop after this many pages (default: all)")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between requests (default: 1)")
    args = parser.parse_args()

    site = SITES[args.site]
    start_url = args.url or site["start_url"]
    output = args.output or f"{args.site}.{args.format}"

    print(f"Scraping '{args.site}' starting at {start_url}\n")
    data = scrape(start_url, site["parser"], args.max_pages, args.delay)

    if not data:
        print("\nNo data scraped; nothing saved.")
        return 1

    (save_csv if args.format == "csv" else save_json)(data, output)
    print(f"\nSaved {len(data)} records to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
