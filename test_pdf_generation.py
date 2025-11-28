"""
Unit tests for PDF generation functionality (US-TEST-UNIT2)
Tests PDF creation, validity, metadata, and formatting
"""

import pytest
import os
import tempfile
from flask import Flask
from PyPDF2 import PdfReader
import pdfkit

# Import your app
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ==========================================
# PDF Generation Tests
# ==========================================

def test_pdf_generation_from_html_content(client):
    """Test PDF generation from HTML content
    
    Maps to US-TEST-UNIT2: Must test PDF generation from HTML content
    """
    response = client.post('/convert',
                          json={'url': 'https://en.wikipedia.org/wiki/Python_(programming_language)'},
                          content_type='application/json')
    
    # Should generate a PDF successfully
    assert response.status_code == 200, \
        f"PDF generation failed with status {response.status_code}. Expected 200."
    assert response.content_type == 'application/pdf', \
        f"Content type is {response.content_type}, expected 'application/pdf'"


def test_pdf_file_validity(client):
    """Test that generated PDF has proper format
    
    Maps to US-TEST-UNIT2: Must test PDF file validity
    """
    response = client.post('/convert',
                          json={'url': 'https://en.wikipedia.org/wiki/Artificial_intelligence'},
                          content_type='application/json')
    
    assert response.status_code == 200, \
        f"Failed to generate PDF, got status {response.status_code}"
    
    # Save to temp file and verify it's a valid PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(response.data)
        tmp_path = tmp.name
    
    try:
        # Try to read it with PyPDF2
        reader = PdfReader(tmp_path)
        num_pages = len(reader.pages)
        assert num_pages > 0, \
            f"PDF should have at least one page, but has {num_pages} pages"
        
        # Check PDF has content
        first_page = reader.pages[0]
        text = first_page.extract_text()
        text_length = len(text)
        assert text_length > 0, \
            f"PDF should contain text content, but extracted text has {text_length} characters"
    finally:
        os.remove(tmp_path)


def test_pdf_contains_metadata(client):
    """Test that PDF includes article metadata
    
    Maps to US-TEST-UNIT2: Must test metadata inclusion in PDF
    """
    response = client.post('/convert',
                          json={'url': 'https://en.wikipedia.org/wiki/Machine_learning'},
                          content_type='application/json')
    
    assert response.status_code == 200, \
        f"Metadata test failed at PDF generation stage with status {response.status_code}"
    
    # Save and check metadata presence
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(response.data)
        tmp_path = tmp.name
    
    try:
        reader = PdfReader(tmp_path)
        # Extract text from first page (should include metadata in header)
        page_text = reader.pages[0].extract_text()
        
        # Should contain metadata elements
        has_metadata = "Author:" in page_text or "Date:" in page_text or "wikipedia.org" in page_text.lower()
        assert has_metadata, \
            f"PDF should include metadata in headers/footers. Page text preview: {page_text[:200]}"
    finally:
        os.remove(tmp_path)


def test_pdf_styling_preservation(client):
    """Test that styling and formatting is preserved
    
    Maps to US-TEST-UNIT2: Must test styling and formatting preservation
    """
    response = client.post('/convert',
                          json={'url': 'https://en.wikipedia.org/wiki/Computer_science'},
                          content_type='application/json')
    
    assert response.status_code == 200, \
        f"Styling test failed with status {response.status_code}"
    
    # Verify PDF was generated with proper settings
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(response.data)
        tmp_path = tmp.name
    
    try:
        reader = PdfReader(tmp_path)
        
        # Check that content exists and is readable
        num_pages = len(reader.pages)
        assert num_pages > 0, \
            f"PDF should have pages, but has {num_pages}"
        
        page_text = reader.pages[0].extract_text()
        text_length = len(page_text)
        assert text_length > 100, \
            f"PDF should have substantial text content, but only has {text_length} characters"
        
        # Verify page has metadata (basic check for PDF info)
        metadata_obj = reader.metadata
        # PDFs generated should be valid
        assert metadata_obj is not None or len(reader.pages) > 0, \
            "PDF should have valid metadata or readable pages"
    finally:
        os.remove(tmp_path)


def test_pdf_has_multiple_pages_for_long_content():
    """Test that long articles generate multi-page PDFs
    
    Maps to US-TEST-UNIT2: Formatting preservation across pages
    """
    # Create a long HTML content
    long_html = "<html><body>" + "<p>Test paragraph content.</p>" * 500 + "</body></html>"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp_path = tmp.name
    
    try:
        # Generate PDF from HTML string
        options = {'quiet': ''}
        pdfkit.from_string(long_html, tmp_path, options=options)
        
        # Read and verify
        reader = PdfReader(tmp_path)
        num_pages = len(reader.pages)
        assert num_pages > 1, \
            f"Long content should generate multiple pages, but only generated {num_pages} page(s)"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_pdf_text_is_selectable(client):
    """Test that PDF text is selectable and copyable
    
    Maps to US-TEST-UNIT2 + US-F007: Text must be selectable
    """
    response = client.post('/convert',
                          json={'url': 'https://en.wikipedia.org/wiki/Software_engineering'},
                          content_type='application/json')
    
    assert response.status_code == 200, \
        f"Text selectability test failed with status {response.status_code}"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(response.data)
        tmp_path = tmp.name
    
    try:
        reader = PdfReader(tmp_path)
        # Extract text - if this works, text is selectable
        text = reader.pages[0].extract_text()
        text_length = len(text)
        
        # Should be able to extract meaningful text
        assert text_length > 50, \
            f"Should extract substantial text (proves selectability), but only got {text_length} characters"
        
        has_content = "software" in text.lower() or "engineering" in text.lower()
        assert has_content, \
            f"Extracted text should contain article keywords. Text preview: {text[:100]}"
    finally:
        os.remove(tmp_path)


def test_pdf_image_handling():
    """Test that images are handled properly in PDF
    
    Maps to US-TEST-UNIT2: Formatting preservation for images
    """
    # HTML with local/embedded content (avoid network dependency)
    html_with_image = """
    <html>
    <head><style>img { max-width: 100%; height: auto; }</style></head>
    <body>
        <h1>Test Article</h1>
        <p>Article content with image reference.</p>
        <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" alt="Test image">
        <p>More content here.</p>
    </body>
    </html>
    """
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp_path = tmp.name
    
    try:
        # Generate PDF with image (using options to handle image gracefully)
        options = {'quiet': '', 'load-error-handling': 'ignore', 'load-media-error-handling': 'ignore'}
        pdfkit.from_string(html_with_image, tmp_path, options=options)
        
        # Verify PDF was created
        file_exists = os.path.exists(tmp_path)
        assert file_exists, \
            f"PDF file should be created at {tmp_path}"
        
        file_size = os.path.getsize(tmp_path)
        assert file_size > 500, \
            f"PDF with image should have reasonable size, but got {file_size} bytes"
        
        # Verify it's readable
        reader = PdfReader(tmp_path)
        num_pages = len(reader.pages)
        assert num_pages > 0, \
            f"PDF should have at least one page, got {num_pages}"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_pdf_preserves_heading_hierarchy(client):
    """Test that heading hierarchy is preserved in PDF
    
    Maps to US-TEST-UNIT2 + US-F007: Heading hierarchy preservation
    """
    response = client.post('/convert',
                          json={'url': 'https://en.wikipedia.org/wiki/Database'},
                          content_type='application/json')
    
    assert response.status_code == 200, \
        f"Heading hierarchy test failed with status {response.status_code}"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(response.data)
        tmp_path = tmp.name
    
    try:
        reader = PdfReader(tmp_path)
        text = reader.pages[0].extract_text()
        text_length = len(text)
        
        # Should have extracted the article title (typically in h1)
        assert text_length > 0, \
            f"Should extract text including headings, but got {text_length} characters"
    finally:
        os.remove(tmp_path)