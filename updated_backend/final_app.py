from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import pdfkit
import tempfile
import os
import requests
import re
from pathlib import Path

from remove_ads import remove_ads_from_html
from platform_cleanup import clean_platform_specific   # <-- NEW (US-F002)

# metadata + injector
from metadata import extract_metadata
from metadata_injector import inject_metadata_into_html

# ------------------ Paths ------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
CSS_FILE = os.path.join(STATIC_DIR, 'pdf-style.css')

app = Flask(__name__)
CORS(app)

# wkhtmltopdf config
path_to_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf) if os.path.exists(path_to_wkhtmltopdf) else None

# ------------------ Routing ------------------

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(FRONTEND_DIR, path)

# ------------------ Convert Route ------------------

@app.route('/convert', methods=['POST'])
def convert_blog_to_pdf():
    try:
        data = request.get_json()
        blog_url = data.get("url")

        if not blog_url:
            return jsonify({"error": "No URL provided"}), 400

        # Fetch HTML
        try:
            print(f"[US-F003] Fetching content from: {blog_url}")
            resp = requests.get(blog_url, timeout=15,
                                headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            return jsonify({"error": "Request timed out while loading the blog."}), 504
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Failed to fetch blog: {e}"}), 400

        html = resp.text

        # 1) Remove ads (conservative cleanup)
        try:
            html = remove_ads_from_html(html, source_url=blog_url)
        except Exception as e:
            print("[US-F003] remove_ads_from_html failed:", str(e))

        # 2) US-F002 platform-specific cleanup (Medium, WP, Blogger, Substack)
        try:
            html = clean_platform_specific(html, blog_url)
        except Exception as e:
            print("[US-F002] Platform cleanup failed:", str(e))

        # 3) Metadata extraction
        metadata = extract_metadata(html, source_url=blog_url)
        print("[US-F005] Extracted metadata:", metadata)

        # 4) Load custom styling (US-F007)
        custom_css = ""
        if os.path.exists(CSS_FILE):
            with open(CSS_FILE, 'r', encoding='utf-8') as f:
                custom_css = f"<style>{f.read()}</style>"

        # 5) Inject header/footer + CSS
        enriched_html = inject_metadata_into_html(html, metadata, css=custom_css)

        # wkhtmltopdf options
        options = {
            'enable-local-file-access': None,
            'load-error-handling': 'ignore',
            'load-media-error-handling': 'ignore',
            'no-stop-slow-scripts': None,
            'quiet': '',
            'javascript-delay': 1500,

            # Margins (header/footer space)
            'margin-top': '40mm',
            'margin-bottom': '30mm',
            'margin-left': '20mm',
            'margin-right': '20mm',

            # PDF Layout (US-F007)
            'page-size': 'A4',
            'encoding': 'UTF-8',
            'minimum-font-size': 12,
            'image-quality': 95,
            'image-dpi': 300,

            'enable-javascript': None,
            'print-media-type': None,
            'custom-header': [('User-Agent', 'Mozilla/5.0')],
            'custom-header-propagation': None,
        }

        # Create temp output file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf_path = tmp_pdf.name

        # Direct PDF generation
        try:
            pdfkit.from_string(enriched_html, tmp_pdf_path, configuration=config, options=options)
        except OSError as e:
            print("[US-F003] from_string failed, fallback to file:", str(e))
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp_html:
                base_tag = f'<base href="{blog_url}">'
                content = enriched_html
                if re.search(r'<head[^>]*>', content, flags=re.IGNORECASE):
                    content = re.sub(r'(<head[^>]*>)', r'\1' + base_tag, content, count=1, flags=re.IGNORECASE)
                else:
                    content = content.replace('<html>', f'<html><head>{base_tag}</head>', 1)
                tmp_html.write(content)
                tmp_html_path = tmp_html.name

            try:
                pdfkit.from_file(tmp_html_path, tmp_pdf_path, configuration=config, options=options)
            finally:
                try:
                    os.remove(tmp_html_path)
                except Exception:
                    pass

        print(f"[US-F003] Successfully generated PDF: {tmp_pdf_path}")
        return send_file(tmp_pdf_path, as_attachment=True, download_name="blog.pdf")

    except Exception as e:
        print("[ERROR] Unexpected:", str(e))
        return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=3000, host='127.0.0.1')
