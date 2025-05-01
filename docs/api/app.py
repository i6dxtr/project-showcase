from flask import Flask, request, jsonify, send_from_directory
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys
import pyttsx3  # Changed from gTTS to pyttsx3
import sqlite3
from googletrans import Translator
import os

app = Flask(__name__)

# Add root route handler
@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to the Product Information API',
        'endpoints': {
            '/predict': 'POST image for prediction',
            '/query': 'POST product queries'
        }
    })

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

@app.route('/predict', methods=['POST'])
def predict():
    print("/predict called")
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
            
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400

        # Reset file pointer and read into memory
        image_file.seek(0)
        image_bytes = image_file.read()
        
        # Verify reasonable size (e.g., 5MB max)
        if len(image_bytes) > 5 * 1024 * 1024:
            return jsonify({'success': False, 'error': 'Image too large (max 5MB)'}), 400

        files = {
            'image': (image_file.filename, image_bytes, image_file.content_type)
        }

        session = create_session()
        response = session.post(
            'https://i6dxtr.pythonanywhere.com/predict',
            files=files,
            timeout=60,  # Increase timeout to 60 seconds
            headers={'Connection': 'close'}
        )

        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f"Prediction service error: {response.status_code}",
                'details': response.text[:200]  # Include first 200 chars of response
            }), 500

        return response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f"Unexpected error: {str(e)}"}), 500

@app.route('/query', methods=['POST'])
def query():
    """
    Handle SQL queries and return results with optional TTS using eSpeak/pyttsx3
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

        # Translate if needed
        detail_text = f"{query_type.capitalize()} for {product_name}: {result}"
        if language == 'es':  # Translate to Spanish if selected
            translator = Translator()
            detail_text = translator.translate(detail_text, src='en', dest='es').text

        # Generate TTS using pyttsx3 (eSpeak backend)
        engine = pyttsx3.init()
        
        # Set language if possible (note: eSpeak language support is limited)
        try:
            voices = engine.getProperty('voices')
            if language == 'es':
                for voice in voices:
                    if 'spanish' in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
            else:  # Default to English
                for voice in voices:
                    if 'english' in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
        except Exception as e:
            print(f"⚠️ Couldn't set voice language: {e}", file=sys.stderr)

        # Save to file
        audio_file = f"static/{product_name.replace(' ', '_')}_{query_type}.wav"  # Changed to WAV format
        engine.save_to_file(detail_text, audio_file)
        engine.runAndWait()  # This generates the file

        return jsonify(success=True, details=result, audio_url=f"/{audio_file}")

    except Exception as e:
        print(f"❌ Error in /query: {e}", file=sys.stderr)
        return jsonify(success=False, error=str(e)), 500

# Add route to serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(host='0.0.0.0', port=5000, debug=True)