from flask import Flask, request, jsonify
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys
from gtts import gTTS
import sqlite3
from googletrans import Translator

app = Flask(__name__)

def create_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.headers.update({'Connection': 'close'})  # Force connection close
    return session

@app.route('/predict', methods=['POST'])
def predict():
    print("🔍 /predict called", file=sys.stderr)
    try:
        session = create_session()
        
        # Forward the request directly without testing connection
        files = {'image': (
            request.files['image'].filename,
            request.files['image'].stream,
            request.files['image'].content_type
        )}
        
        response = session.post(
            'http://localhost:8080/predict',
            files=files,
            timeout=30,
            headers={'Connection': 'close'}
        )
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': f'Connection error: {str(e)}'
        }), 503
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/query', methods=['POST'])
def query():
    """
    Handle SQL queries and return results with optional TTS.
    """
    try:
        data = request.json
        product_name = data.get('product_name')
        query_type = data.get('query_type')  # e.g., 'nutrition', 'allergen', 'price'
        language = data.get('language', 'en')  # Default to English

        if not product_name or not query_type:
            return jsonify(success=False, error="Missing product_name or query_type"), 400

        # Query the database
        connection = sqlite3.connect('products.db')
        cursor = connection.cursor()

        if query_type == 'nutrition':
            query = '''
                SELECT calories, total_fat, cholesterol, sodium, total_carbs, fiber, sugar, protein
                FROM nutritional_info
                JOIN products ON products.id = nutritional_info.product_id
                WHERE products.name = ?
            '''
        elif query_type == 'allergen':
            query = '''
                SELECT allergy
                FROM nutritional_info
                JOIN products ON products.id = nutritional_info.product_id
                WHERE products.name = ?
            '''
        elif query_type == 'price':
            query = '''
                SELECT cost
                FROM products
                WHERE name = ?
            '''
        else:
            return jsonify(success=False, error="Invalid query_type"), 400

        cursor.execute(query, (product_name,))
        result = cursor.fetchone()
        connection.close()

        if not result:
            return jsonify(success=False, error="Product not found"), 404

        # Translate and generate TTS
        detail_text = f"{query_type.capitalize()} for {product_name}: {result}"
        if language == 'es':  # Translate to Spanish if selected
            translator = Translator()
            detail_text = translator.translate(detail_text, src='en', dest='es').text

        tts = gTTS(text=detail_text, lang=language)
        audio_file = f"static/{product_name.replace(' ', '_')}_{query_type}.mp3"
        tts.save(audio_file)

        return jsonify(success=True, details=result, audio_url=f"/{audio_file}")

    except Exception as e:
        print(f"❌ Error in /query: {e}", file=sys.stderr)
        return jsonify(success=False, error=str(e)), 500