from flask import Flask, request, jsonify, send_from_directory, make_response, url_for, current_app
from flask_cors import CORS
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys
import pyttsx3
import sqlite3
from googletrans import Translator
import os
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ------------------------------------------------------------------------
# GLOBAL TTS ENGINE (initialized once)
# ------------------------------------------------------------------------
engine = pyttsx3.init()
voices = engine.getProperty('voices')
print(f"Found {len(voices)} voices: {[v.name for v in voices]}", file=sys.stderr)

# ------------------------------------------------------------------------
# Helper: create a requests session with retry logic
# ------------------------------------------------------------------------
def create_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.headers.update({'Connection': 'close'})
    return session

# ------------------------------------------------------------------------
# Root endpoint
# ------------------------------------------------------------------------
@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to the Product Information API',
        'endpoints': {
            '/predict': 'POST image for prediction',
            '/query':   'POST product queries'
        }
    })

# ------------------------------------------------------------------------
# /predict: forward image to model server
# ------------------------------------------------------------------------
@app.route('/predict', methods=['POST'])
def predict():
    try:
        print("Starting /predict", file=sys.stderr)
        print("Request Headers:", request.headers, file=sys.stderr)

        file = request.files.get('image')
        if not file:
            return jsonify(success=False, error="No image file provided"), 400

        print(f"Uploaded file size: {file.content_length} bytes", file=sys.stderr)
        session = create_session()
        files = {'image': (file.filename, file.stream, file.content_type)}

        print("Forwarding request to the internal prediction service...", file=sys.stderr)
        response = session.post('http://localhost:8080/predict', files=files, timeout=30)
        print(f"Received response status code: {response.status_code}", file=sys.stderr)

        data = response.json()
        if not data.get('success', False):
            return jsonify(success=False, error="Model server error: " + data.get('error')), 500

        label = data.get('prediction', 'unknown')
        resp = make_response(jsonify({
            'success':    True,
            'prediction': label,
            'message':    "Classification successful!"
        }))
        resp.headers['Content-Type'] = 'application/json'
        return resp

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}", file=sys.stderr)
        return jsonify(success=False, error=f"Connection error: {e}"), 503
    except Exception as e:
        print(f"Error in prediction: {e}", file=sys.stderr)
        return jsonify(success=False, error=str(e)), 500

# ------------------------------------------------------------------------
# /query: fetch nutrition/allergen/price and generate TTS
# ------------------------------------------------------------------------
@app.route('/query', methods=['POST'])
def query():
    try:
        data = request.json
        if not data:
            return jsonify(success=False, error="No data provided"), 400
        
        product_name = data.get('product_name')
        query_type = data.get('query_type')
        language = data.get('language', 'en')

        # Get the query details based on type
        details = get_product_details(product_name, query_type, language)
        
        # Generate audio file
        try:
            # Ensure static directory exists
            static_dir = os.path.join(os.path.dirname(__file__), 'static')
            os.makedirs(static_dir, exist_ok=True)

            # Create unique filename
            timestamp = int(time.time())
            safe_name = product_name.replace(' ', '_').lower()
            filename = f"{safe_name}_{query_type}_{language}_{timestamp}.mp3"
            filepath = os.path.join(static_dir, filename)

            # Generate speech file
            tts = gTTS(text=details, lang=language)
            tts.save(filepath)

            # Clean up old files
            for old_file in os.listdir(static_dir):
                if old_file.endswith('.mp3'):
                    old_path = os.path.join(static_dir, old_file)
                    if time.time() - os.path.getctime(old_path) > 3600:  # Remove files older than 1 hour
                        os.remove(old_path)

            return jsonify({
                'success': True,
                'details': details,
                'audio_url': f"/static/{filename}",
                'language': language
            })

        except Exception as e:
            print(f"TTS Error: {e}", file=sys.stderr)
            # Return text-only response if audio fails
            return jsonify({
                'success': True,
                'details': details,
                'error': f"Audio generation failed: {str(e)}",
                'language': language
            })

    except Exception as e:
        print(f"Query error: {e}", file=sys.stderr)
        return jsonify(success=False, error=str(e)), 500
# ------------------------------------------------------------------------
# Route to test DB connectivity
# ------------------------------------------------------------------------
@app.route('/test-db', methods=['GET'])
def test_db():
    return jsonify({"message": "Check server logs for database test results"})

# ------------------------------------------------------------------------
# Serve static files (TTS output)
# ------------------------------------------------------------------------
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# ------------------------------------------------------------------------
# App entry point
# ------------------------------------------------------------------------
if __name__ == '__main__':
    # ensure static/ exists
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(host='0.0.0.0', port=5000, debug=True)
