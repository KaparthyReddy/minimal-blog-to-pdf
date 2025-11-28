"""
US-F001: URL Format Validation
------------------------------
Validates whether the provided URL matches supported blog platforms:
- Medium
- WordPress
- Blogger
"""

import re

def is_valid_blog_url(url: str) -> bool:
    """Return True if URL belongs to supported platforms, else False"""
    if not url or not isinstance(url, str):
        return False

    pattern = r"^(https?:\/\/)?(www\.)?(medium\.com|[\w-]+\.wordpress\.com|blogger\.com)"
    return re.match(pattern, url) is not None


if __name__ == "__main__":
    test_urls = [
        "https://medium.com/some-article",
        "http://example.wordpress.com/blog",
        "https://blogger.com/post/123",
        "ftp://randomsite.com/post",
        "https://unknownsite.com/post"
    ]

    for url in test_urls:
        print(f"{url} → {is_valid_blog_url(url)}")
