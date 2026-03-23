import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote_plus
from html.parser import HTMLParser

KEYWORDS_ENV = os.environ.get("KEYWORDS", "technologist")
KEYWORDS = [k.strip() for k in KEYWORDS_ENV.split(",") if k.strip()]
OUTPUT_FILE = "docs/results.json"
BASE_URL = "https://www.jobs.ac.uk/search/"

class JobParser(HTMLParser):
    """Minimal parser to extract job listings from jobs.ac.uk search results."""

    def __init__(self):
        super().__init__()
        self.jobs = []
        self._in_article = False
        self._in_title = False
        self._in_employer = False
        self._in_location = False
        self._in_salary = False
        self._current = {}
        self._depth = 0
        self._article_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self._depth += 1

        # Detect job article cards
        if tag == "article":
            classes = attrs.get("class", "")
            if "j-search-result" in classes or "search-result" in classes:
                self._in_article = True
                self._article_depth = self._depth
                self._current = {"title": "", "employer": "", "location": "", "salary": "", "url": ""}

        if not self._in_article:
            return

        # Job title link
        if tag == "a" and "j-search-result__title" in attrs.get("class", ""):
            self._in_title = True
            href = attrs.get("href", "")
            if href:
                if href.startswith("http"):
                    self._current["url"] = href
                else:
                    self._current["url"] = "https://www.jobs.ac.uk" + href

        # Employer / institution
        if tag in ("span", "div") and "j-search-result__employer" in attrs.get("class", ""):
            self._in_employer = True

        # Location
        if tag in ("span", "div") and "j-search-result__location" in attrs.get("class", ""):
            self._in_location = True

        # Salary
        if tag in ("span", "div") and "j-search-result__salary" in attrs.get("class", ""):
            self._in_salary = True

    def handle_endtag(self, tag):
        if self._in_article and tag == "article" and self._depth == self._article_depth:
            if self._current.get("title") and self._current.get("url"):
                self.jobs.append(dict(self._current))
            self._in_article = False
            self._in_title = False
            self._in_employer = False
            self._in_location = False
            self._in_salary = False
            self._current = {}
        self._depth -= 1

        # End inline flags
        if tag in ("a", "span", "div"):
            self._in_title = False
            self._in_employer = False
            self._in_location = False
            self._in_salary = False

    def handle_data(self, data):
        text = data.strip()
        if not text or not self._in_article:
            return
        if self._in_title and not self._current["title"]:
            self._current["title"] = text
        elif self._in_employer and not self._current["employer"]:
            self._current["employer"] = text
        elif self._in_location and not self._current["location"]:
            self._current["location"] = text
        elif self._in_salary and not self._current["salary"]:
            self._current["salary"] = text


def fetch_jobs(keyword, max_pages=3):
    """Fetch up to max_pages of results for a keyword."""
    all_jobs = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-GB,en;q=0.9",
    }

    for page in range(1, max_pages + 1):
        params = {"keywords": keyword, "pageSize": "25"}
        if page > 1:
            params["startIndex"] = str((page - 1) * 25 + 1)

        url = BASE_URL + "?" + urlencode(params)
        print(f"  Fetching page {page}: {url}")

        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            break

        parser = JobParser()
        parser.feed(html)

        if not parser.jobs:
            # Try a looser extraction using regex as fallback
            jobs = regex_extract(html)
            if not jobs:
                print(f"  No jobs found on page {page}, stopping.")
                break
            all_jobs.extend(jobs)
        else:
            all_jobs.extend(parser.jobs)

        # Avoid hammering the server
        if page < max_pages:
            time.sleep(2)

    # Deduplicate by URL
    seen = set()
    unique = []
    for j in all_jobs:
        if j["url"] not in seen:
            seen.add(j["url"])
            unique.append(j)

    return unique


def regex_extract(html):
    """Fallback: extract job links and titles with regex."""
    jobs = []
    # Match job links like /job/technologist-12345/
    pattern = re.findall(
        r'href="(/job/[^"]+)"[^>]*>([^<]{5,120})',
        html
    )
    for href, title in pattern:
        title = title.strip()
        if not title or len(title) < 5:
            continue
        jobs.append({
            "title": title,
            "employer": "",
            "location": "",
            "salary": "",
            "url": "https://www.jobs.ac.uk" + href,
        })
    return jobs[:25]


def main():
    print(f"Scraping jobs.ac.uk for keywords: {KEYWORDS}")
    results = {}
    for kw in KEYWORDS:
        print(f"\nKeyword: '{kw}'")
        jobs = fetch_jobs(kw)
        results[kw] = {
            "jobs": jobs,
            "count": len(jobs),
            "search_url": BASE_URL + "?" + urlencode({"keywords": kw}),
        }
        print(f"  Found {len(jobs)} jobs for '{kw}'")
        time.sleep(1)

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "keywords": results,
    }

    os.makedirs("docs", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved results to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
