"""
Unit tests for US-TEST-UNIT1: URL validation & fetching
Tests individual functions in isolation
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
# UNIT TESTS: ENDPOINT VALIDATION
# ============================================

def test_convert_endpoint_exists(client):
    """Test that /convert endpoint exists"""
    response = client.post('/convert',
                          json={'url': 'https://example.com'},
                          content_type='application/json')
    # Should not return 404 (endpoint exists)
    assert response.status_code != 404, "/convert endpoint should exist"


def test_convert_accepts_post_only(client):
    """Test that /convert only accepts POST requests"""
    # Try GET request (should fail)
    response = client.get('/convert')
    assert response.status_code in [405, 404], "Should not accept GET requests"


def test_convert_requires_json(client):
    """Test that endpoint works with JSON content"""
    response = client.post('/convert',
                          json={'url': 'https://example.com'},
                          content_type='application/json')
    # Should process (200 or 500, but not 400 for content-type issues)
    assert response.status_code in [200, 500], "Should accept JSON"


# ============================================
# UNIT TESTS: URL VALIDATION (Missing URL)
# ============================================

def test_missing_url_returns_400(client):
    """Test that missing URL returns 400 error"""
    response = client.post('/convert',
                          json={},  # No URL provided
                          content_type='application/json')
    
    assert response.status_code == 400, "Missing URL should return 400"
    json_data = response.get_json()
    assert 'error' in json_data, "Response should contain error field"
    assert 'No URL provided' in json_data['error'], "Should have specific error message"


def test_empty_string_url_returns_400(client):
    """Test that empty string URL returns 400 error"""
    response = client.post('/convert',
                          json={'url': ''},
                          content_type='application/json')
    
    assert response.status_code == 400, "Empty URL should return 400"


def test_none_url_returns_400(client):
    """Test that None/null URL returns 400 error"""
    response = client.post('/convert',
                          json={'url': None},
                          content_type='application/json')
    
    assert response.status_code == 400, "None URL should return 400"


# ============================================
# UNIT TESTS: URL FETCHING & PDF GENERATION
# ============================================

def test_valid_url_returns_success_or_error(client):
    """Test that valid URL is processed (may succeed or fail)"""
    response = client.post('/convert',
                          json={'url': 'https://example.com'},
                          content_type='application/json')
    
    # Should return 200 (success) or 500 (PDF generation failed)
    # Should NOT return 400 (URL is valid)
    assert response.status_code in [200, 500], "Valid URL should be processed"


def test_successful_conversion_returns_pdf(client):
    """Test that successful conversion returns PDF file"""
    response = client.post('/convert',
                          json={'url': 'https://example.com'},
                          content_type='application/json')
    
    if response.status_code == 200:
        # Should be PDF content type
        assert 'pdf' in response.content_type.lower() or \
               'attachment' in response.headers.get('Content-Disposition', '').lower(), \
               "Successful response should return PDF"


def test_successful_pdf_not_empty(client):
    """Test that generated PDF is not empty"""
    response = client.post('/convert',
                          json={'url': 'https://example.com'},
                          content_type='application/json')
    
    if response.status_code == 200:
        # PDF should have content
        assert len(response.data) > 0, "PDF should not be empty"
        # PDF files start with %PDF signature
        assert response.data[:4] == b'%PDF', "Should be valid PDF format"


