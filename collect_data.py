"""Collect the Nobel laureates for the medallion (bronze / silver / gold) lab.

Everything is saved untouched in data/bronze : this folder IS the bronze layer's source.

    python collect_data.py                    # all laureates, 100 per file

The Nobel Prize API is public: no account and no key needed.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests 

BRONZE = Path(os.environ.get("BRONZE_DIR", "data/bronze"))
NOBEL_API = os.environ.get("NOBEL_API", "https://api.nobelprize.org/2.1")

SESSION = requests.Session()
SESSION.headers["User-Agent"] = "data-warehousing-course"


def save_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def nobel_get(path, params):
    for attempt in range(3):
        try:
            r = SESSION.get(f"{NOBEL_API}{path}", params=params, timeout=60)
        except (requests.ConnectionError, requests.Timeout) as e:
            print(f"  network problem ({e.__class__.__name__}), retrying in {2 ** attempt}s")
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            print(f"  HTTP {r.status_code}, retrying in {2 ** attempt}s")
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r.json()
    sys.exit("  The Nobel Prize API is not answering. Try again later.")


def collect_nobel(page_size=100):
    """The API is paginated: ask for `limit` laureates 
    starting at `offset`, until `meta.count` is reached."""
    offset, total = 0, None
    while total is None or offset < total:
        payload = nobel_get("/laureates", {"offset": offset, "limit": page_size})
        total = payload["meta"]["count"]
        n = len(payload.get("laureates", []))
        if n == 0:
            break
        path = save_json(BRONZE / f"laureates_offset{offset:04d}.json", payload)
        print(f"laureates {offset}-{offset + n - 1} of {total} -> {path}")
        offset += n
        time.sleep(0.5)
    print(f"done: {offset} laureates saved in {BRONZE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--page-size", type=int, default=100, help="laureates per request / per file (default 100)")
    args = parser.parse_args()
    collect_nobel(max(1, args.page_size))
