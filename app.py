from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import pdfkit
import tempfile
import os

# Get the absolute path to frontend folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Your wkhtmltopdf path
path_to_wkhtmltopdf = "/usr/local/bin/wkhtmltopdf"
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

# Serve the frontend HTML
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

# Serve other static files (like script.js)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(FRONTEND_DIR, path)

# API endpoint for conversion
@app.route('/convert', methods=['POST'])
def convert_blog_to_pdf():
    try:
        data = request.get_json()
        blog_url = data.get("url")

        if not blog_url:
            return jsonify({"error": "No URL provided"}), 400

        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            options = {
                'enable-local-file-access': None,
                'load-error-handling': 'ignore',
                'load-media-error-handling': 'ignore',
                'quiet': ''
            }
            # Convert directly from URL instead of fetching HTML first
            pdfkit.from_url(blog_url, tmp_file.name, configuration=config, options=options)
            tmp_file_path = tmp_file.name

        return send_file(tmp_file_path, as_attachment=True, download_name="blog.pdf")

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=3000, host='127.0.0.1')
