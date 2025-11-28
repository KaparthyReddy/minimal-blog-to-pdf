# backend/metadata.py

import re
from typing import Optional, Dict
from bs4 import BeautifulSoup
import dateutil.parser as dateparser

# -------------------------------
# Normalization helpers
# -------------------------------

def normalize_author(author: Optional[str]) -> str:
    if not author:
        return "Unknown"
    author = re.sub(r"\s+", " ", author).strip()
    return author.title()  # Standard consistent formatting


def normalize_date(date_str: Optional[str]) -> str:
    if not date_str:
        return "Unknown date"

    try:
        dt = dateparser.parse(date_str)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return "Unknown date"


# -------------------------------
# Metadata extraction
# -------------------------------

def extract_metadata(html: str, source_url: Optional[str] = None) -> Dict[str, str]:
    """
    Extracts:
    - author
    - publication date
    - title
    - source URL
    Handles missing metadata gracefully.
    """

    soup = BeautifulSoup(html, "html.parser")

    # ---- Title ----
    title = None
    og_title = soup.find("meta", property="og:title")
    if og_title:
        title = og_title.get("content")

    if not title and soup.title:
        title = soup.title.get_text().strip()

    title = title if title else "Untitled"

    # ---- Author ----
    author = None
    author_selectors = [
        ('meta', {'name': 'author'}),
        ('meta', {'property': 'article:author'}),
        ('meta', {'name': 'article:author'}),
        ('meta', {'property': 'byline'}),
        ('meta', {'name': 'byline'}),
        ('a', {'rel': 'author'}),
    ]

    for tag_name, attrs in author_selectors:
        tag = soup.find(tag_name, attrs=attrs)
        if tag:
            author = tag.get("content") or tag.get_text()
            break

    # schema.org itemprop
    if not author:
        tag = soup.find(attrs={"itemprop": "author"})
        if tag:
            author = tag.get("content") or tag.get_text()

    author = normalize_author(author)

    # ---- Publication Date ----
    date = None

    date_selectors = [
        ('meta', {'property': 'article:published_time'}),
        ('meta', {'name': 'pubdate'}),
        ('meta', {'name': 'publishdate'}),
        ('meta', {'name': 'date'}),
        ('meta', {'property': 'og:updated_time'}),
    ]

    for tag_name, attrs in date_selectors:
        tag = soup.find(tag_name, attrs=attrs)
        if tag:
            date = tag.get("content") or tag.get("value")
            break

    # HTML5 <time> tag
    if not date:
        t = soup.find("time")
        if t:
            date = t.get("datetime") or t.get_text()

    # Try text-based fallback: "Published on April 3, 2023"
    if not date:
        text_preview = (soup.get_text() or "")[:2000]
        m = re.search(r"(Published on|Posted on)\s+([A-Za-z0-9, ]+)", text_preview, re.IGNORECASE)
        if m:
            date = m.group(2)

    date = normalize_date(date)

    # ---- URL ----
    og_url = soup.find("meta", property="og:url")
    if og_url and og_url.get("content"):
        url = og_url.get("content")
    else:
        url = source_url or "Unknown source"

    return {
        "title": title,
        "author": author,
        "date": date,
        "url": url
    }
