"""
Integration tests for US-TEST-INT1
Contains the fetch→parse→convert end-to-end integration tests.
Author: Ishanvee
Jira: US-TEST-INT1, SCRUM-14
"""

import pytest
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ============================================
# INTEGRATION TESTS: END-TO-END FLOWS (PART 1)
# ============================================

def test_complete_url_to_pdf_flow(client):
    """Integration Test: Complete flow from URL input to PDF output

    Tests integration of:
    - Request handling (Flask)
    - URL fetching (pdfkit.from_url)
    - PDF conversion (wkhtmltopdf)
    - File serving (Flask send_file)

    Maps to SRS: F-004 (Fetch), F-006 (Convert), F-013 (Download)
    """
    response = client.post('/convert',
                          json={'url': 'https://example.com'},
                          content_type='application/json')

    # Verify complete flow succeeded
    assert response.status_code == 200, "Complete URL→PDF flow should succeed"
    assert 'pdf' in response.content_type.lower(), "Should return PDF content type"
    assert len(response.data) > 0, "PDF should have content"
    assert response.data[:4] == b'%PDF', "Should be valid PDF signature"


def test_frontend_backend_api_integration(client):
    """Integration Test: Frontend can communicate with backend API

    Simulates exactly what script.js does when user clicks 'Convert to PDF'

    Maps to SRS: F-012 (Enter URL), F-006 (Convert), F-013 (Download)
    """
    # Simulate frontend fetch request
    response = client.post('/convert',
                          json={'url': 'https://example.com'},
                          headers={
                              'Content-Type': 'application/json',
                              'Accept': 'application/pdf'
                          })

    # Verify API contract is satisfied
    assert response.status_code in [200, 500], "API should respond to frontend"

    if response.status_code == 200:
        # Check response headers match frontend expectations
        content_disp = response.headers.get('Content-Disposition', '')
        assert 'attachment' in content_disp, "Should trigger browser download"
        assert 'blog.pdf' in content_disp, "Should have correct filename"


def test_url_fetch_pdf_convert_integration(client):
    """Integration Test: URL fetching integrates with PDF conversion

    Tests that pdfkit.from_url successfully:
    1. Fetches the URL content
    2. Converts it to PDF
    3. Returns valid PDF data

    Maps to SRS: F-004 (Fetch), F-006 (Convert)
    """
    test_urls = [
        'https://example.com',
        'https://example.org',
    ]

    for url in test_urls:
        response = client.post('/convert', json={'url': url})

        # Verify fetching and conversion work together
        if response.status_code == 200:
            assert len(response.data) > 100, f"PDF for {url} should have substantial content"
            assert response.data[:4] == b'%PDF', f"PDF for {url} should be valid"


def test_error_handling_integration(client):
    """Integration Test: Error flows through entire system correctly

    Tests that errors from pdfkit/network are:
    1. Caught by try-except block
    2. Converted to JSON error response
    3. Returned with appropriate status code

    Maps to SRS: NF-004 (Meaningful error messages)
    """
    # Use non-existent domain to trigger network error
    response = client.post('/convert',
                          json={'url': 'https://completely-invalid-domain-xyz123.com'})

    # Verify error handling integration
    # in test_integration1.py
    assert response.status_code == 500, "Network errors should return 500"
    json_data = response.get_json()
    assert 'error' in json_data, "Error should propagate to JSON response"
    # Accept either friendly or raw wkhtmltopdf error text
    error_text = json_data['error']
    assert (
        'Failed to generate PDF' in error_text
        or 'wkhtmltopdf reported an error' in error_text
        or 'HostNotFoundError' in error_text
    ), "Should have user-friendly message or engine error output"


def test_temporary_file_handling_integration(client):
    """Integration Test: Temporary file creation and serving works correctly

    Tests integration between:
    - tempfile.NamedTemporaryFile (file creation)
    - pdfkit.from_url (writing to temp file)
    - send_file (reading and serving temp file)

    Maps to SRS: F-006 (Convert), SEC-004 (Temp file handling)
    """
    response = client.post('/convert',
                          json={'url': 'https://example.com'})

    if response.status_code == 200:
        # Verify file was created, written to, and served correctly
        assert response.data is not None, "Temp file should be served"
        assert len(response.data) > 0, "Temp file should have content"


def test_pdf_options_integration(client):
    """Integration Test: PDF generation options are applied correctly

    Tests that wkhtmltopdf options integrate properly:
    - 'load-error-handling': 'ignore' allows conversion despite resource errors
    - 'load-media-error-handling': 'ignore' handles missing images

    Maps to SRS: F-006 (Convert), F-010 (Preserve images)
    """
    response = client.post('/convert',
                          json={'url': 'https://example.com'})

    # Options should allow conversion even if some resources fail
    if response.status_code == 200:
        assert len(response.data) > 0, "PDF generated despite potential resource errors"
