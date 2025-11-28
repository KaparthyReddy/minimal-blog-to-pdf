# tests/system_part1.py
"""
Part 1 — unit-style system tests:
- Mock external network and pdf generation
- Test ad-removal logic, metadata extraction, and that /convert calls pdf generator
- Flexible imports with helpful skips if a module/function isn't present
"""


import io
import os
import pytest
import sys
import os, sys


TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---- helper to import app ----------
try:
    # common location in this project
    from backend.app import app as flask_app
except Exception:
    try:
        from app import app as flask_app
    except Exception:
        flask_app = None  # tests that need it will skip with message

# ---- flexible import helpers for modules/functions we expect from your work ----
def locate_module(*names):
    """Try several import paths; return the first module found or None."""
    for name in names:
        try:
            mod = __import__(name, fromlist=['*'])
            return mod
        except Exception:
            continue
    return None

# attempt to find metadata extractor module and function
metadata_mod = locate_module("metadata", "metadata_injector")
extract_metadata = None
if metadata_mod:
    extract_metadata = getattr(metadata_mod, "extract_metadata", None) or getattr(metadata_mod, "get_metadata", None)

# attempt to find ad removal function
cleaner_mod = locate_module("backend.cleaner", "backend.clean_html", "utils.cleaner", "cleaner", "backend.app","backend.remove_ads")
remove_ads = None
if cleaner_mod:
    # try a few common names
    remove_ads = getattr(cleaner_mod, "remove_ads", None) or getattr(cleaner_mod, "remove_ads_from_html", None)
    # If not found, maybe function is in app module
    if remove_ads is None and flask_app:
        try:
            # import backend.app and see if function exists there
            import backend.app as backend_app_mod  # may raise
            remove_ads = getattr(backend_app_mod, "remove_ads", None) or getattr(backend_app_mod, "strip_ads", None)
        except Exception:
            pass

# Sample HTML with an "ad" element and embedded metadata (title/author)
SAMPLE_HTML_WITH_AD_AND_META = """
<html>
<head>
  <title>Sample Post Title</title>
  <meta name="author" content="Test Author">
  <meta name="date" content="2025-11-01">
</head>
<body>
  <article>
    <h1>Sample Post Title</h1>
    <div class="content">This is the real content.</div>
    <div class="ad">Buy our stuff!</div>
  </article>
</body>
</html>
"""

# For mocking network responses
class DummyResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
        self.content = text.encode("utf-8")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error {self.status_code}")

# ---- fixtures ----------
@pytest.fixture
def client():
    if not flask_app:
        pytest.skip("Could not import Flask app (backend.app or app). Adjust import path in tests.")
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as c:
        yield c

# ---- tests for ad removal function directly ----------
def test_remove_ads_function_exists_and_removes_ad():
    if remove_ads is None:
        pytest.skip("No ad-removal function found (expected 'remove_ads' or 'strip_ads' in backend.cleaner / backend.app).")
    cleaned = remove_ads(SAMPLE_HTML_WITH_AD_AND_META)
    assert "class=\"ad\"" not in cleaned and "<div class=\"ad\"" not in cleaned, "ad HTML should be removed by remove_ads"
    # content must still be present
    assert "This is the real content." in cleaned

# ---- tests for metadata extractor ----------
def test_metadata_extractor_returns_expected_fields():
    if extract_metadata is None:
        pytest.skip("No metadata extractor found (expected 'extract_metadata' or 'get_metadata' in backend.metadata).")
    meta = extract_metadata(SAMPLE_HTML_WITH_AD_AND_META)
    assert isinstance(meta, dict), "metadata extractor should return a dict"
    # expect at least title/author/date if extractor implemented sensibly
    assert any(k in meta for k in ("title", "Title")), "metadata should include title"
    assert any(k in meta for k in ("author", "Author")), "metadata should include author or similar"

# ---- tests for convert route calling pdfkit with cleaned html ----------
def test_convert_calls_pdfkit_with_cleaned_html(monkeypatch, client):
    """
    - Patch requests.get to return sample html (with ad)
    - Patch pdfkit.from_string to behave like real pdfkit: if output_path provided write bytes to file and return path
    - Assert ads removed and response contains PDF bytes
    """
    import requests
    import tempfile

    # patch requests.get
    def fake_get(url, timeout=10, headers=None):
        return DummyResponse(SAMPLE_HTML_WITH_AD_AND_META)

    monkeypatch.setattr("requests.get", fake_get)

    # capture html passed to pdfkit
    called = {}

    def fake_from_string(html_string, output_path=None, options=None, configuration=None):
        """
        If output_path provided -> write fake PDF bytes to that path and return path
        Else -> return bytes (some apps accept bytes)
        """
        called['html'] = html_string
        fake_pdf_bytes = b"%PDF-1.4\n%fakepdf\n%%EOF"
        if output_path:
            # ensure parent dir exists
            out_dir = os.path.dirname(output_path) or tempfile.gettempdir()
            os.makedirs(out_dir, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(fake_pdf_bytes)
            return output_path
        return fake_pdf_bytes

    # Patch pdfkit.from_string in the pdfkit module if available
    patched = False
    try:
        import pdfkit
        monkeypatch.setattr(pdfkit, "from_string", fake_from_string)
        patched = True
    except Exception:
        patched = False

    # Also patch backend.app.pdfkit.from_string if present (some apps import pdfkit into module)
    try:
        import backend.app as ba
        if hasattr(ba, "pdfkit"):
            # If ba.pdfkit is a module-like object, patch its from_string
            try:
                monkeypatch.setattr(ba.pdfkit, "from_string", fake_from_string)
                patched = True
            except Exception:
                # ba.pdfkit might be a module name string or something else; fallback:
                monkeypatch.setattr(ba, "pdfkit", type("P", (), {"from_string": fake_from_string}))
                patched = True
        else:
            # create a pdfkit-like object on backend.app
            monkeypatch.setattr(ba, "pdfkit", type("P", (), {"from_string": fake_from_string}))
            patched = True
    except Exception:
        # backend.app not importable here (client fixture would have skipped earlier), ignore
        pass

    if not patched:
        pytest.skip("Could not patch pdfkit; adapt tests to your pdf wrapper.")

    # call route
    resp = client.post("/convert", json={"url": "http://example.com/post"})

    assert resp.status_code == 200, "Expected 200 OK from /convert on happy path"

    # Ensure response contains PDF bytes (Flask test client returns bytes)
    assert resp.data and resp.data.startswith(b"%PDF-1.4"), "Response should be PDF bytes"

    # Ensure pdfkit was called and ad markup removed
    assert 'html' in called, "pdfkit.from_string should have been called"
    assert "class=\"ad\"" not in called['html'] and "<div class=\"ad\"" not in called['html'], "ad element should have been removed before conversion"


def test_convert_handles_fetch_errors_gracefully(monkeypatch, client):
    import requests
    # simulate timeout
    def fake_get_raises(url, timeout=10, headers=None):
        raise requests.exceptions.Timeout("Simulated")
    monkeypatch.setattr("requests.get", fake_get_raises)
    resp = client.post("/convert", json={"url": "http://example.com/timeout"})
    assert resp.status_code != 200
    j = resp.get_json()
    assert j is not None and ("error" in j or "message" in j)

def test_convert_handles_pdf_generation_error(monkeypatch, client):
    # patch requests.get to return normal html
    def fake_get(url, timeout=10, headers=None):
        return DummyResponse(SAMPLE_HTML_WITH_AD_AND_META)
    monkeypatch.setattr("requests.get", fake_get)

    # patch pdfkit.from_string to raise an exception
    def fake_from_string_raises(html_string, output_path=None, options=None, configuration=None):
        raise RuntimeError("pdfkit failed")

    try:
        import pdfkit
        monkeypatch.setattr(pdfkit, "from_string", fake_from_string_raises)
    except Exception:
        try:
            import backend.app as ba
            monkeypatch.setattr(ba, "pdfkit", type("P", (), {"from_string": fake_from_string_raises}))
        except Exception:
            pytest.skip("pdfkit not importable and backend.app.pdfkit not patchable; adapt tests.")

    resp = client.post("/convert", json={"url": "http://example.com/failpdf"})
    assert resp.status_code != 200
    j = resp.get_json()
    assert j is not None and ("error" in j or "message" in j)
