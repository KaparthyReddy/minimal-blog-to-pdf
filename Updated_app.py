# backend/app.py
from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import pdfkit
import tempfile
import os
import requests   # <--- keep imports together
import re
from pathlib import Path

# import your standalone metadata helper and injector
from metadata import extract_metadata
from metadata_injector import inject_metadata_into_html

# ✅ Correct order: first create the Flask app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ✅ wkhtmltopdf path (update if needed)
# Make sure this path exists in your system (run `where wkhtmltopdf` to verify)
path_to_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
if os.path.exists(path_to_wkhtmltopdf):
    config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
else:
    config = None  # assume wkhtmltopdf is on PATH

# ✅ Serve the frontend HTML
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

# ✅ Serve static files (script.js, styles, etc.)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(FRONTEND_DIR, path)

# ------------------------------
# New: /convert route with metadata injection
# ------------------------------
@app.route('/convert', methods=['POST'])
def convert_blog_to_pdf():
    try:
        data = request.get_json()
        blog_url = data.get("url")

        if not blog_url:
            return jsonify({"error": "No URL provided"}), 400

        # Fetch page HTML (we still show your existing logs & timeout behavior)
        try:
            print(f"[US-F003] Fetching content from: {blog_url}")
            resp = requests.get(blog_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            print(f"[US-F003] Timeout occurred while fetching: {blog_url}")
            return jsonify({"error": "Request timed out while loading the blog."}), 504
        except requests.exceptions.RequestException as e:
            print(f"[US-F003] Failed to fetch URL: {e}")
            return jsonify({"error": f"Failed to fetch blog: {e}"}), 400

        html = resp.text

        # Extract metadata (title, author, date, url) using your metadata.py
        metadata = extract_metadata(html, source_url=blog_url)
        print("[US-F003] Extracted metadata:", metadata)

        # Inject header/footer into the HTML so wkhtmltopdf renders metadata on every page
        enriched_html = inject_metadata_into_html(html, metadata)

        # pdfkit/wkhtmltopdf options (tolerant + allow local file access + UA)
        options = {
            'enable-local-file-access': None,
            'load-error-handling': 'ignore',
            'load-media-error-handling': 'ignore',
            'no-stop-slow-scripts': None,
            'quiet': '',
            'javascript-delay': 1500,
            'margin-top': '40mm',      # leave room for header
            'margin-bottom': '30mm',   # leave room for footer
            'margin-left': '15mm',
            'margin-right': '15mm',
            # pass a realistic User-Agent so servers don't block wkhtmltopdf
            'custom-header': [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')],
            'custom-header-propagation': None,
        }

        # Create a temporary pdf file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf_path = tmp_pdf.name

        # Try creating PDF from string first; fallback to write-file + from_file() if that fails
        try:
            pdfkit.from_string(enriched_html, tmp_pdf_path, configuration=config, options=options)
        except OSError as e:
            # fallback to writing an intermediate HTML file with a <base href="..."> so relative URLs resolve
            print("[US-F003] pdfkit.from_string failed — trying fallback write-to-file + from_file().")
            print("[US-F003] Original error:", str(e))
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp_html:
                base_tag = f'<base href="{blog_url}">'
                content = enriched_html
                if re.search(r'<head[^>]*>', content, flags=re.IGNORECASE):
                    content = re.sub(r'(<head[^>]*>)', r'\1' + base_tag, content, count=1, flags=re.IGNORECASE)
                else:
                    # ensure a head exists
                    content = content.replace('<html>', f'<html><head>{base_tag}</head>', 1)
                tmp_html.write(content)
                tmp_html_path = tmp_html.name

            try:
                pdfkit.from_file(tmp_html_path, tmp_pdf_path, configuration=config, options=options)
            finally:
                # remove the temporary HTML file (we keep the PDF to serve)
                try:
                    os.remove(tmp_html_path)
                except Exception:
                    pass

        print(f"[US-F003] Successfully generated PDF for: {blog_url} -> {tmp_pdf_path}")

        # send_file will stream the PDF to the client
        return send_file(tmp_pdf_path, as_attachment=True, download_name="blog.pdf")
    except Exception as e:
        print(f"[US-F003] Unexpected error in /convert: {str(e)}")
        return jsonify({"error": "Internal server error during conversion."}), 500


if __name__ == '__main__':
    app.run(debug=True, port=3000, host='127.0.0.1')
