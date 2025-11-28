# backend/test/system_part2.py

import os
import tempfile
import pytest

# Path fix so imports work
import sys
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import app and dependencies
from app import app
import requests

# Dummy response used in tests
class DummyResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
        self.content = text.encode("utf-8")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.RequestException(f"Status {self.status_code}")

@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c


# -------------------------------------------------------
# 1. No URL provided (covers line 35)
# -------------------------------------------------------
def test_convert_no_url(client):
    resp = client.post("/convert", json={})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


# -------------------------------------------------------
# 2. RequestException branch (covers line 57)
# -------------------------------------------------------
def test_convert_request_exception(monkeypatch, client):
    def fake_get(*a, **k):
        raise requests.exceptions.RequestException("boom")

    monkeypatch.setattr("requests.get", fake_get)

    resp = client.post("/convert", json={"url": "http://x.com"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


# -------------------------------------------------------
# 3. Timeout branch (covers line 40)
# -------------------------------------------------------
def test_convert_timeout(monkeypatch, client):
    def fake_get(*a, **k):
        raise requests.exceptions.Timeout("slow")

    monkeypatch.setattr("requests.get", fake_get)

    resp = client.post("/convert", json={"url": "http://slow.com"})
    assert resp.status_code == 504


# -------------------------------------------------------
# 4. remove_ads_from_html failure branch (covers lines 67-69)
# -------------------------------------------------------
def test_remove_ads_failure(monkeypatch, client):
    def fake_get(*a, **k):
        return DummyResponse("<html><body>hello</body></html>")

    monkeypatch.setattr("requests.get", fake_get)

    # Force ad removal to fail
    def boom(*a, **k):
        raise Exception("ads fail")

    import remove_ads
    monkeypatch.setattr(remove_ads, "remove_ads_from_html", boom)

    # Fake pdfkit output
    def fake_pdf(html, output_path, **k):
        with open(output_path, "wb") as f:
            f.write(b"%PDF-1.4")
        return output_path

    import pdfkit
    monkeypatch.setattr(pdfkit, "from_string", fake_pdf)

    resp = client.post("/convert", json={"url": "http://example.com"})
    assert resp.status_code == 200


# -------------------------------------------------------
# 5. CSS file branch (covers lines 75-77)
# -------------------------------------------------------
def test_css_file_used(monkeypatch, client, tmp_path):
    css_file = tmp_path / "pdf-style.css"
    css_file.write_text("body { color: red; }", encoding="utf-8")

    # Override CSS_FILE
    import app as backend_app
    monkeypatch.setattr(backend_app, "CSS_FILE", str(css_file))

    def fake_get(*a, **k):
        return DummyResponse("<html><body>hello</body></html>")

    monkeypatch.setattr("requests.get", fake_get)

    # Fake pdfkit output
    def fake_pdf(html, output_path, **k):
        with open(output_path, "wb") as f:
            f.write(b"%PDF-1.4")
        return output_path

    import pdfkit
    monkeypatch.setattr(pdfkit, "from_string", fake_pdf)

    resp = client.post("/convert", json={"url": "http://example.com"})
    assert resp.status_code == 200


# -------------------------------------------------------
# 6. pdfkit.from_string → OSError fallback path (covers 86-87 + 130-148)
# -------------------------------------------------------
def test_pdfkit_fallback(monkeypatch, client):
    def fake_get(*a, **k):
        return DummyResponse("<html><body>hello</body></html>")

    monkeypatch.setattr("requests.get", fake_get)

    # Force from_string to fail
    def fake_from_string(*a, **k):
        raise OSError("wkhtmltopdf error")

    import pdfkit
    monkeypatch.setattr(pdfkit, "from_string", fake_from_string)

    # Make from_file succeed
    def fake_from_file(input_html, output_pdf, **k):
        with open(output_pdf, "wb") as f:
            f.write(b"%PDF-1.4 fallback")
        return output_pdf

    monkeypatch.setattr(pdfkit, "from_file", fake_from_file)

    resp = client.post("/convert", json={"url": "http://example.com"})
    assert resp.status_code == 200
    assert resp.data.startswith(b"%PDF-1.4")


# -------------------------------------------------------
# 7. Global exception handler (covers line 160)
# -------------------------------------------------------
def test_global_exception_handler(monkeypatch, client):
    def fake_get(*a, **k):
        return DummyResponse("<html><body>hello</body></html>")

    monkeypatch.setattr("requests.get", fake_get)

    # Force metadata extraction to blow up
    import app as backend_app
    def explode(*a, **k):
        raise RuntimeError("big boom")
    monkeypatch.setattr(backend_app, "extract_metadata", explode)

    resp = client.post("/convert", json={"url": "http://example.com"})
    assert resp.status_code == 500
    assert "error" in resp.get_json()
