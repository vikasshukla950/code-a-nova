#!/usr/bin/env python3
"""
URL Status Checker  (Level 2a)
------------------------------
Checks whether multiple websites are up or down by sending HTTP requests
and displaying the response status codes.

Usage:
    python url_status_checker.py                          # type URLs interactively
    python url_status_checker.py google.com github.com    # URLs as arguments
    python url_status_checker.py -f urls.txt              # URLs from a file (one per line)
    python url_status_checker.py -f urls.txt -t 5 -w 20   # 5s timeout, 20 parallel workers

Exit code is 0 if every site is up, 2 if any site is down.
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from http import HTTPStatus

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (URL-Status-Checker/1.0)"}


@dataclass
class Result:
    url: str
    is_up: bool
    status_code: int | None = None
    reason: str = ""
    response_ms: float | None = None


def normalize_url(raw: str) -> str:
    """Add https:// if the user typed a bare domain like 'google.com'."""
    raw = raw.strip()
    if not raw.lower().startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw


def status_phrase(code: int) -> str:
    try:
        return HTTPStatus(code).phrase
    except ValueError:
        return "Unknown"


def check_url(url: str, timeout: float = 10.0) -> Result:
    """Send an HTTP request and report whether the site is up (status < 400)."""
    start = time.perf_counter()
    try:
        # HEAD is lighter than GET, but some servers reject it -> fall back to GET.
        response = requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if response.status_code in (400, 403, 405, 501):
            response = requests.get(url, headers=HEADERS, timeout=timeout,
                                    allow_redirects=True, stream=True)
            response.close()
        elapsed = (time.perf_counter() - start) * 1000
        code = response.status_code
        reason = status_phrase(code)
        if code in (401, 403, 429):
            reason += " (server is reachable but refused this request)"
        return Result(url, code < 400, code, reason, elapsed)

    except requests.exceptions.SSLError:
        return Result(url, False, reason="SSL certificate error")
    except requests.exceptions.ConnectTimeout:
        return Result(url, False, reason="Connection timed out")
    except requests.exceptions.ReadTimeout:
        return Result(url, False, reason="Server took too long to respond")
    except requests.exceptions.ConnectionError:
        return Result(url, False, reason="Could not connect (DNS/network error)")
    except requests.exceptions.TooManyRedirects:
        return Result(url, False, reason="Too many redirects")
    except requests.exceptions.RequestException as err:
        return Result(url, False, reason=f"Request failed: {type(err).__name__}")


def check_all(urls: list[str], timeout: float, workers: int) -> list[Result]:
    """Check all URLs concurrently; results keep the input order."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda u: check_url(u, timeout), urls))


# ---------- input handling ----------

def read_urls_from_file(path: str) -> list[str]:
    with open(path, encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]


def read_urls_interactively() -> list[str]:
    print("Enter URLs one per line. Press Enter on an empty line to start checking.")
    urls = []
    while True:
        line = input("URL> ").strip()
        if not line:
            break
        urls.append(line)
    return urls


def dedupe(urls: list[str]) -> list[str]:
    """Remove duplicates while preserving order."""
    return list(dict.fromkeys(urls))


# ---------- output ----------

def colorize(text: str, color: str) -> str:
    if not sys.stdout.isatty():
        return text
    codes = {"green": "32", "red": "31", "yellow": "33"}
    return f"\033[{codes[color]}m{text}\033[0m"


def print_results(results: list[Result]) -> None:
    width = max(len(r.url) for r in results)
    print(f"\n{'URL':<{width}}  {'STATE':<6}  {'CODE':<5}  {'TIME':>8}  DETAILS")
    print("-" * (width + 40))

    for r in results:
        state = colorize("UP", "green") if r.is_up else colorize("DOWN", "red")
        # Pad manually: ANSI colour codes would otherwise break column widths.
        state_pad = " " * (6 - len("UP" if r.is_up else "DOWN"))
        code = str(r.status_code) if r.status_code else "-"
        timing = f"{r.response_ms:.0f} ms" if r.response_ms is not None else "-"
        print(f"{r.url:<{width}}  {state}{state_pad}  {code:<5}  {timing:>8}  {r.reason}")

    up = sum(r.is_up for r in results)
    print("-" * (width + 40))
    print(f"{up} up, {len(results) - up} down, {len(results)} checked")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether websites are up or down.")
    parser.add_argument("urls", nargs="*", help="URLs to check")
    parser.add_argument("-f", "--file", help="Text file with one URL per line")
    parser.add_argument("-t", "--timeout", type=float, default=10.0,
                        help="Seconds to wait per request (default: 10)")
    parser.add_argument("-w", "--workers", type=int, default=10,
                        help="Parallel requests (default: 10)")
    args = parser.parse_args()

    urls = list(args.urls)
    if args.file:
        try:
            urls += read_urls_from_file(args.file)
        except OSError as err:
            print(f"Error reading '{args.file}': {err}")
            return 1
    if not urls:
        urls = read_urls_interactively()

    urls = dedupe([normalize_url(u) for u in urls])
    if not urls:
        print("No URLs provided.")
        return 1

    print(f"Checking {len(urls)} URL(s)...")
    results = check_all(urls, args.timeout, args.workers)
    print_results(results)
    return 0 if all(r.is_up for r in results) else 2


if __name__ == "__main__":
    sys.exit(main())
