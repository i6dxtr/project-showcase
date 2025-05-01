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
        query_type   = data.get('query_type')
        language     = data.get('language', 'en')

        if not product_name or not query_type:
            return jsonify(success=False, error="Missing product_name or query_type"), 400

        # --- Database setup ---
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db', 'products.db'))
        print(f"Database path: {db_path}", file=sys.stderr)
        print(f"Querying for product: {product_name}, type: {query_type}, language: {language}", file=sys.stderr)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # --- Map raw labels to real names ---
        product_mapping = {
            'product-a': 'Kroger Creamy Peanut Butter',
            'product-b': 'Great Value Twist and Shout Cookies',
            'product-c': 'Morton Coarse Kosher Salt',
            'product-d': 'Kroger Extra Virgin Olive Oil',
        }
        normalized = product_mapping.get(product_name.lower().strip(), product_name)
        print(f"Normalized product name: {normalized}", file=sys.stderr)

        # Debug: list products
        cursor.execute("SELECT id, name FROM products")
        all_p = cursor.fetchall()
        for p in all_p:
            print(f"ID: {p['id']}, Name: {p['name']}", file=sys.stderr)

        # Build name→ID map
        id_map = {p['name'].lower(): p['id'] for p in all_p}
        print("Product ID mapping:", id_map, file=sys.stderr)

        # --- Fetch details ---
        detail_text = ""
        result      = None

        if query_type == 'nutrition':
            sql = """
                SELECT calories, total_fat, cholesterol, sodium,
                       total_carbs, fiber, sugar, protein
                  FROM nutritional_info
                  JOIN products ON products.id = nutritional_info.product_id
                 WHERE LOWER(products.name) = LOWER(?)
            """
            cursor.execute(sql, (normalized,))
            result = cursor.fetchone()
            if result:
                detail_text = (
                    f"Calories: {result['calories']}, Fat: {result['total_fat']}, "
                    f"Cholesterol: {result['cholesterol']}, Sodium: {result['sodium']}, "
                    f"Carbs: {result['total_carbs']}, Fiber: {result['fiber']}, "
                    f"Sugar: {result['sugar']}, Protein: {result['protein']}"
                )

        elif query_type == 'allergen':
            sql = """
                SELECT allergy
                  FROM nutritional_info
                  JOIN products ON products.id = nutritional_info.product_id
                 WHERE LOWER(products.name) = LOWER(?)
            """
            cursor.execute(sql, (normalized,))
            result = cursor.fetchone()
            if result:
                detail_text = f"Allergen Information: {result['allergy']}"

        elif query_type == 'price':
            sql = "SELECT cost FROM products WHERE LOWER(name) = LOWER(?)"
            cursor.execute(sql, (normalized,))
            result = cursor.fetchone()
            if result:
                detail_text = f"Price: ${result['cost']:.2f}"

        else:
            conn.close()
            return jsonify(success=False, error="Invalid query_type"), 400

        # Fallback ID-based lookup if no result
        if not result and product_name.startswith('product-'):
            letter = product_name.split('-')[-1]
            pid    = ord(letter) - ord('a') + 1
            print(f"Direct lookup ID={pid}", file=sys.stderr)

            if query_type == 'nutrition':
                cursor.execute("SELECT * FROM nutritional_info WHERE product_id = ?", (pid,))
            elif query_type == 'allergen':
                cursor.execute("SELECT allergy FROM nutritional_info WHERE product_id = ?", (pid,))
            else:
                cursor.execute("SELECT cost FROM products WHERE id = ?", (pid,))
            result = cursor.fetchone()
            if result:
                # rebuild detail_text same as above
                if query_type == 'nutrition':
                    detail_text = (
                        f"Calories: {result['calories']}, Fat: {result['total_fat']}, "
                        f"Cholesterol: {result['cholesterol']}, Sodium: {result['sodium']}, "
                        f"Carbs: {result['total_carbs']}, Fiber: {result['fiber']}, "
                        f"Sugar: {result['sugar']}, Protein: {result['protein']}"
                    )
                elif query_type == 'allergen':
                    detail_text = f"Allergen Information: {result['allergy']}"
                else:
                    detail_text = f"Price: ${result['cost']:.2f}"

        if not result:
            conn.close()
            return jsonify(success=False, error=f"Product not found: {product_name}"), 404

        conn.close()

        # --- Translate if needed ---
        if language == 'es':
            print("Translating to Spanish...", file=sys.stderr)
            translator = Translator()
            try:
                translation = translator.translate(detail_text, src='en', dest='es')
                detail_text = translation.text
            except Exception as e:
                print(f"Translation error: {e}", file=sys.stderr)
                # fallback: simple replacements
                for en, es in {
                    "Calories": "Calorías", "Fat": "Grasa",
                    "Cholesterol": "Colesterol", "Sodium": "Sodio",
                    "Carbs": "Carbohidratos", "Fiber": "Fibra",
                    "Sugar": "Azúcar", "Protein": "Proteína",
                    "Price": "Precio", "Allergen Information": "Información de Alérgenos"
                }.items():
                    detail_text = detail_text.replace(en, es)

        # --- Generate TTS ---
        safe_name = re.sub(r'\W+', '_', normalized)
        fn        = f"{safe_name}_{query_type}_{language}.wav"
        static_d  = current_app.static_folder
        os.makedirs(static_d, exist_ok=True)
        audio_fp  = os.path.join(static_d, fn)

        # Select voice
        if language == 'es':
            sp = next((v for v in voices if 'spanish' in v.name.lower()), None)
            if sp: engine.setProperty('voice', sp.id)
        else:
            en = next((v for v in voices if 'english' in v.name.lower()), None)
            if en: engine.setProperty('voice', en.id)

        engine.save_to_file(detail_text, audio_fp)
        try:
            engine.runAndWait()
        except RuntimeError:
            # loop already running → pump once
            engine.iterate()

        return jsonify({
            'success':      True,
            'details':      detail_text,
            'audio_url':    url_for('static', filename=fn),
            'product_name': normalized,
            'language':     language
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
