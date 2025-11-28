# backend/metadata_injector.py
"""
Utilities to inject article metadata (author, date, title, url) into an HTML
string so wkhtmltopdf/pdfkit will render the header and footer consistently
on every PDF page.

Usage:
    from metadata import extract_metadata
    from metadata_injector import inject_metadata_into_html

    meta = extract_metadata(html, source_url=url)
    new_html = inject_metadata_into_html(html, meta)
    pdfkit.from_string(new_html, out_path, configuration=config, options=options)
"""

import html as html_lib
from typing import Dict

# Minimal, self-contained CSS to place header and footer on each printed page.
_DEFAULT_CSS = """
<style>
  @page {
    margin: 40mm 15mm 25mm 15mm; /* top right bottom left */
  }
  /* Header */
  .btp-header {
    position: fixed;
    top: -30mm; /* sits in the page margin area (negative to move into @page margin) */
    left: 0;
    right: 0;
    height: 30mm;
    padding: 6mm 10mm 4mm 10mm;
    font-family: "Helvetica", Arial, sans-serif;
    font-size: 11px;
    border-bottom: 1px solid #ddd;
    background: white;
  }
  .btp-header .title {
    font-size: 14px;
    font-weight: bold;
    margin-bottom: 4px;
  }
  .btp-header .meta {
    font-size: 10px;
    color: #333;
  }

  /* Footer */
  .btp-footer {
    position: fixed;
    bottom: -20mm; /* inside bottom margin */
    left: 0;
    right: 0;
    height: 20mm;
    padding: 6px 10mm;
    font-family: "Helvetica", Arial, sans-serif;
    font-size: 9px;
    color: #333;
    border-top: 1px solid #eee;
    background: white;
    text-align: center;
  }

  /* page number (wkhtmltopdf will not auto-replace JS placeholders,
     but we include a fallback for visible numbering via CSS counters when supported) */
  .btp-footer .page-number {
    float: right;
    font-size: 9px;
    color: #666;
  }

  /* Make sure main content doesn't get hidden behind header/footer */
  body {
    box-sizing: border-box;
  }
</style>
"""

def _render_header_html(metadata: Dict[str, str]) -> str:
    title = html_lib.escape(metadata.get("title", "Untitled"))
    author = html_lib.escape(metadata.get("author", "Unknown"))
    date = html_lib.escape(metadata.get("date", "Unknown date"))

    header_html = f"""
    <div class="btp-header" aria-hidden="true">
      <div class="title">{title}</div>
      <div class="meta"><strong>Author:</strong> {author} &nbsp;&nbsp; <strong>Date:</strong> {date}</div>
    </div>
    """
    return header_html

def _render_footer_html(metadata: Dict[str, str]) -> str:
    url = html_lib.escape(metadata.get("url", "Unknown source"))
    # page number placeholder — wkhtmltopdf supports some replacements like [page] but pdfkit/wkhtmltopdf behavior varies.
    # We'll include a visible URL and also a simple JS fallback to try and write page numbers if wkhtmltopdf executes JS.
    footer_html = f"""
    <div class="btp-footer" aria-hidden="true">
      <span class="source-url">{url}</span>
      <span class="page-number">Page <span class="page-counter">[page]</span></span>
    </div>
    """
    return footer_html

def inject_metadata_into_html(html: str, metadata: Dict[str, str], css: str = None) -> str:
    """
    Return a new HTML string with injected CSS, header and footer.
    - html: original HTML (string)
    - metadata: dict with keys title, author, date, url
    - css: optional additional CSS string to include
    """
    if css is None:
        css = _DEFAULT_CSS

    header = _render_header_html(metadata)
    footer = _render_footer_html(metadata)

    # We want to inject CSS + header right after <head> (or create head if missing),
    # and inject the footer at the start of <body> (so it will be included on every page).
    html_lower = html.lower()
    has_head = '<head' in html_lower
    has_body = '<body' in html_lower

    new_html = html

    # Ensure there's an HTML skeleton if missing
    if not ('<html' in html_lower):
        # wrap content
        new_html = f"<html><head></head><body>{html}</body></html>"
        html_lower = new_html.lower()
        has_head = True
        has_body = True

    # Inject CSS into <head>
    if has_head:
        # insert css immediately after the opening <head...> tag
        import re
        new_html = re.sub(r'(<head[^>]*>)', r'\1' + css, new_html, count=1, flags=re.IGNORECASE)
    else:
        # create a head with css
        new_html = new_html.replace('<html>', f"<html><head>{css}</head>", 1)

    # Inject header and footer inside body
    if has_body:
        # place header and footer at beginning of body
        import re
        new_html = re.sub(r'(<body[^>]*>)', r'\1' + header + footer, new_html, count=1, flags=re.IGNORECASE)
    else:
        # append a body with header/footer
        new_html = new_html.replace('</head>', f"</head><body>{header}{footer}", 1)
        new_html += "</body>"

    return new_html
