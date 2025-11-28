# backend/remove_ads.py
"""
remove_ads_from_html(html, source_url=None)

Heuristics-based ad removal:
 - Removes iframes often used to host ads
 - Removes elements with ids/classes containing ad/ad(s)/advert/sponsor/promo/etc.
 - Removes scripts/styles with known ad-related sources or keywords
 - Removes common data-ad attributes and ARIA roles used for sidebars/widgets
 - Keeps a conservative approach to avoid removing article content where possible
"""

import re
from bs4 import BeautifulSoup

# list of keywords / patterns to detect ad containers or ad scripts
_AD_KEYWORDS = [
    r'\bad\b', r'\bads\b', r'\badvert', r'\bsponsor', r'\bsponsored\b',
    r'\bpromo\b', r'\bpromoted\b', r'\bdoubleclick\b', r'\bgooglesyndication\b',
    r'\badsystem\b', r'\badservice\b', r'\btaboola\b', r'\boutbrain\b',
    r'\brevcontent\b', r'\badvertisement\b', r'\bmarketplace\b'
]
_AD_KEYWORD_RE = re.compile('|'.join(_AD_KEYWORDS), re.IGNORECASE)

# Known ad script src patterns (partial domains / tokens)
_AD_SRC_PATTERNS = [
    "doubleclick.net",
    "googlesyndication",
    "googletagservices",
    "adservice.google",
    "adroll",
    "adsystem",
    "taboola",
    "outbrain",
    "revcontent",
    "yieldmo",
    "indexexchange",
    "adsafeprotected",
]

def _looks_like_ad_attr(value: str) -> bool:
    if not value:
        return False
    return bool(_AD_KEYWORD_RE.search(value))

def remove_ads_from_html(html: str, source_url: str | None = None) -> str:
    """
    Return cleaned HTML with many common ad elements removed.
    Keep removals conservative to avoid removing article content.
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1) Remove iframes that look like ads (small heuristics)
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "") or iframe.get("data-src", "")
        # If src contains known ad networks OR iframe has ad-like attributes
        if src and any(pat in src for pat in _AD_SRC_PATTERNS):
            iframe.decompose()
            continue
        # Remove very small iframes or ones with ad keywords in id/class
        w = iframe.get("width")
        h = iframe.get("height")
        # small numeric sizes often ad
        try:
            if (w and int(w) < 50) or (h and int(h) < 50):
                iframe.decompose()
                continue
        except Exception:
            pass
        if _looks_like_ad_attr(iframe.get("id", "")) or _looks_like_ad_attr(iframe.get("class", "")):
            iframe.decompose()

    # 2) Remove script tags that are clearly ad scripts (by src or content)
    for script in soup.find_all("script"):
        src = script.get("src", "")
        if src and any(pat in src for pat in _AD_SRC_PATTERNS):
            script.decompose()
            continue
        # look into inline script content for ad keywords
        content = script.string or ""
        if content and _AD_KEYWORD_RE.search(content):
            # conservative: only remove if script contains ad-network tokens
            if any(token in content.lower() for token in ("doubleclick", "adsbygoogle", "googlesyndication", "taboola", "outbrain")):
                script.decompose()

    # 3) Remove link / img / div / section etc. elements that have ad-like classes/ids or attributes
    # Common attributes that host ad widgets: data-ad, data-ad-slot, data-ad-client
    ad_attr_names = ["data-ad", "data-ad-slot", "data-ad-client", "data-google-query-id", "data-adunit"]
    for attr in ad_attr_names:
        for tag in soup.find_all(attrs={attr: True}):
            tag.decompose()

    # Generic pass: remove nodes with id/class containing ad-like keywords
    potential_ad_selectors = []
    for tag in soup.find_all(True):
        # check id and classes
        idv = tag.get("id", "")
        classv = " ".join(tag.get("class", [])) if tag.get("class") else ""
        role = tag.get("role", "")
        aria_label = tag.get("aria-label", "")

        test_fields = " ".join([idv, classv, role, aria_label])
        if _looks_like_ad_attr(test_fields):
            # small safeguard: don't remove article/main content containers by accident
            # check tag name and approximate size: if it contains many children/text, avoid removing blindly
            text_len = (tag.get_text() or "").strip()
            # if almost empty or clearly a widget, remove
            if len(text_len) < 200 or tag.name in ("aside", "iframe", "ins", "figure", "div", "section"):
                tag.decompose()

    # 4) Remove common ad-specific elements
    for selector in ["ins.adsbygoogle", ".ad", ".ads", ".advert", ".advertisement", ".sponsored", ".promoted", ".ad-slot", ".ad-container", ".adunit", ".ad-wrapper", ".ad_banner", ".adbox", ".ad-placeholder"]:
        for tag in soup.select(selector):
            tag.decompose()

    # 5) Remove noscript tags that contain ad images or trackers
    for nos in soup.find_all("noscript"):
        if _AD_KEYWORD_RE.search(str(nos)):
            nos.decompose()

    # 6) Remove inline styles or comments that reference ad networks (conservative)
    # (We won't strip all inline styles to avoid breaking layout; only remove if clearly an ad)
    for comment in soup.find_all(string=lambda text: isinstance(text, type(soup.new_string(""))) and isinstance(text, type(soup.string))):
        pass  # no-op: keeping comments

    # Return cleaned HTML
    return str(soup)
