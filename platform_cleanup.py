# backend/platform_cleanup.py

from bs4 import BeautifulSoup
import re

def clean_platform_specific(html: str, source_url: str) -> str:
    """Platform-specific cleanup for major blog sites as required by US-F002."""

    soup = BeautifulSoup(html, "html.parser")

    url = source_url.lower()

    if "medium.com" in url:
        remove_classes = [
            "metabar", "js-stickyFooter", "branch-journeys-top",
            "paywallButton", "meteredContent", "promo", "upvoteButton"
        ]
        for cls in remove_classes:
            for tag in soup.find_all(class_=re.compile(cls)):
                tag.decompose()

    if "wordpress.com" in url or "wp-content" in html:
        remove_classes = [
            "sidebar", "widget-area", "comment-list", "comments", "site-footer",
            "wp-block-group", "navigation", "header", "footer"
        ]
        for cls in remove_classes:
            for tag in soup.find_all(class_=re.compile(cls)):
                tag.decompose()

    if "blogspot." in url:
        remove_classes = [
            "header-inner", "footer", "navbar", "profile", "sidebar", "comments"
        ]
        for cls in remove_classes:
            for tag in soup.find_all(class_=re.compile(cls)):
                tag.decompose()

    if "substack.com" in url:
        remove_ids = [
            "subscribe-button", "paywall", "newsletter-subscribe",
            "post-meta", "subscription-widget"
        ]
        for id_ in remove_ids:
            el = soup.find(id=id_)
            if el:
                el.decompose()

    return str(soup)
