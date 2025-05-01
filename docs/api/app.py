from flask import Flask, request, jsonify, send_from_directory, make_response 
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
    print("Starting /predict", file=sys.stderr)
    try:
        # Log the incoming request headers
        print("Request Headers:", request.headers, file=sys.stderr)

        # Get the image file from the request
        file = request.files.get('image')
        if not file:
            print("No image file provided.", file=sys.stderr)
            return jsonify(success=False, error="No image file provided"), 400

        # Log the size of the uploaded file
        print(f"Uploaded file size: {file.content_length} bytes", file=sys.stderr)

        # Create a session for the downstream request
        session = create_session()

        # Prepare files for the request
        files = {
            'image': (file.filename, file.stream, file.content_type)
        }

        print("Forwarding request to the internal prediction service...", file=sys.stderr)

        # Send the file to the downstream service
        response = session.post(
            'http://localhost:8080/predict',  # Ensure the model server is running on this endpoint
            files=files,
            timeout=30
        )

        # Log response status code
        print(f"Received response status code: {response.status_code}", file=sys.stderr)

        # Parse the response from the model server
        response_data = response.json()

        # Check if the model server returned a successful prediction
        if not response_data.get('success', False):
            return jsonify(success=False, error="Model server error: " + response_data.get('error')), 500

        # Get the predicted label from the model response
        label = response_data.get('prediction', 'unknown')  # Adjust based on your model server's response

        # Return consistent response format matching frontend expectations
        response = make_response(jsonify({
            'success': True,
            'prediction': label,
            'message': "Classification successful!"
        }))
        response.headers['Content-Type'] = 'application/json'
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': f'Connection error: {str(e)}'
        }), 503
    except Exception as e:
        print(f"Error in prediction: {str(e)}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/query', methods=['POST'])
def query():
    """
    Handle product queries and return results with translations and TTS audio
    """
    try:
        # Get and validate request data
        data = request.json
        if not data:
            return jsonify(success=False, error="No data provided"), 400
        
        product_name = data.get('product_name')
        query_type = data.get('query_type')
        language = data.get('language', 'en')

<<<<<<< HEAD
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
=======
        if not product_name or not query_type:
            return jsonify(success=False, error="Missing product_name or query_type"), 400

        # Construct database path
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db', 'products.db'))
        print(f"Database path: {db_path}", file=sys.stderr)
        print(f"Querying for product: {product_name}, type: {query_type}, language: {language}", file=sys.stderr)

        # Connect to database
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row  # This allows us to access columns by name
        cursor = connection.cursor()

        # Map prediction labels to actual product names in the database
        product_mapping = {
            'product-a': 'Kroger Creamy Peanut Butter',  # Example mapping for product-a
            'product-b': 'Great Value Twist and Shout Cookies',  # Replace with actual product name from database
            'product-c': 'Morton Coarse Kosher Salt',  # Replace with actual product name from database
            'product-d': 'Kroger Extra Virgin Olive Oil',  # Replace with actual product name from database
            # Add more mappings as needed
        }
        
        # Normalize product name to match database entries
        normalized_product = product_mapping.get(product_name.lower().strip(), product_name)
        print(f"Normalized product name: {normalized_product}", file=sys.stderr)
        
        # Debug: List all products in the database
        cursor.execute("SELECT id, name FROM products")
        all_products = cursor.fetchall()
        print("Available products in database:", file=sys.stderr)
        for p in all_products:
            print(f"ID: {p['id']}, Name: {p['name']}", file=sys.stderr)
            
        # Create reverse mapping from predictions back to product IDs for faster lookup
        product_id_mapping = {}
        for p in all_products:
            product_id_mapping[p['name'].lower()] = p['id']
        print("Product ID mapping:", product_id_mapping, file=sys.stderr)

        # Initialize detail_text
        detail_text = ""
        result = None

        # Select appropriate query based on type
        if query_type == 'nutrition':
            query = '''
                SELECT 
                    calories, total_fat, cholesterol, sodium, 
                    total_carbs, fiber, sugar, protein
                FROM nutritional_info
                JOIN products ON products.id = nutritional_info.product_id
                WHERE LOWER(products.name) = LOWER(?)
            '''
            cursor.execute(query, (normalized_product,))
            result = cursor.fetchone()
            
            if result:
                detail_text = f"Calories: {result['calories']}, Fat: {result['total_fat']}, "
                detail_text += f"Cholesterol: {result['cholesterol']}, Sodium: {result['sodium']}, "
                detail_text += f"Carbs: {result['total_carbs']}, Fiber: {result['fiber']}, "
                detail_text += f"Sugar: {result['sugar']}, Protein: {result['protein']}"

        elif query_type == 'allergen':
            query = '''
                SELECT allergy
                FROM nutritional_info
                JOIN products ON products.id = nutritional_info.product_id
                WHERE LOWER(products.name) = LOWER(?)
            '''
            cursor.execute(query, (normalized_product,))
            result = cursor.fetchone()
            
            if result:
                detail_text = f"Allergen Information: {result['allergy']}"

        elif query_type == 'price':
            query = '''
                SELECT cost
                FROM products
                WHERE LOWER(name) = LOWER(?)
            '''
            cursor.execute(query, (normalized_product,))
            result = cursor.fetchone()
            
            if result:
                detail_text = f"Price: ${result['cost']:.2f}"

        else:
            connection.close()
            return jsonify(success=False, error="Invalid query_type"), 400

        # If no result found, try direct query by ID if this is a prediction label
        if not result and product_name.startswith('product-'):
            # Extract the letter from product-X format
            product_letter = product_name.split('-')[-1]
            product_number = ord(product_letter) - ord('a') + 1  # Convert a->1, b->2, etc.
            
            print(f"Trying direct ID lookup for {product_name} -> ID: {product_number}", file=sys.stderr)
            
            # Adjust the queries to use direct ID
            if query_type == 'nutrition':
                query = '''
                    SELECT 
                        calories, total_fat, cholesterol, sodium, 
                        total_carbs, fiber, sugar, protein
                    FROM nutritional_info
                    WHERE product_id = ?
                '''
                cursor.execute(query, (product_number,))
                result = cursor.fetchone()
                
                if result:
                    detail_text = f"Calories: {result['calories']}, Fat: {result['total_fat']}, "
                    detail_text += f"Cholesterol: {result['cholesterol']}, Sodium: {result['sodium']}, "
                    detail_text += f"Carbs: {result['total_carbs']}, Fiber: {result['fiber']}, "
                    detail_text += f"Sugar: {result['sugar']}, Protein: {result['protein']}"
            
            elif query_type == 'allergen':
                query = '''
                    SELECT allergy
                    FROM nutritional_info
                    WHERE product_id = ?
                '''
                cursor.execute(query, (product_number,))
                result = cursor.fetchone()
                
                if result:
                    detail_text = f"Allergen Information: {result['allergy']}"
                    
            elif query_type == 'price':
                query = '''
                    SELECT cost
                    FROM products
                    WHERE id = ?
                '''
                cursor.execute(query, (product_number,))
                result = cursor.fetchone()
                
                if result:
                    detail_text = f"Price: ${result['cost']:.2f}"
        
        # If still no result, log detailed info and return error
        if not result:
            print(f"No result found for product: {normalized_product}", file=sys.stderr)
            connection.close()
            return jsonify(success=False, error=f"Product not found: {product_name}"), 404

        connection.close()

        # Create a translated version if Spanish is requested
        original_text = detail_text  # Store the original English text
        translated_text = detail_text  # Default to the original text
        
        if language == 'es':
            print(f"Translating text to Spanish: {detail_text}", file=sys.stderr)
            try:
                # Method 1: Use googletrans library
                translator = Translator()
                
                # Log the original text for debugging
                print(f"Original text for translation: {detail_text}", file=sys.stderr)
                
                # Perform the translation
                translation = translator.translate(detail_text, src='en', dest='es')
                translated_text = translation.text
                
                # Log the translated result
                print(f"Translated text from API: {translated_text}", file=sys.stderr)
                
                # Apply manual corrections for common food terms that might not translate well
                # This ensures more accurate and consistent translations
                translations_map = {
                    "Calories": "Calorías",
                    "Fat": "Grasa",
                    "Cholesterol": "Colesterol", 
                    "Sodium": "Sodio",
                    "Carbs": "Carbohidratos",
                    "Fiber": "Fibra",
                    "Sugar": "Azúcar",
                    "Protein": "Proteína",
                    "Price": "Precio",
                    "Allergen Information": "Información de Alérgenos",
                    "contains": "contiene",
                    "may contain": "puede contener",
                    "free from": "libre de",
                    "No allergens listed": "No se enumeran alérgenos"
                }
                
                # If the translation failed or seems incorrect, use our manual dictionary
                if not translated_text or translated_text == detail_text:
                    print("Translation API failed, using dictionary fallback", file=sys.stderr)
                    translated_text = detail_text
                    for en_term, es_term in translations_map.items():
                        translated_text = translated_text.replace(en_term, es_term)
                else:
                    # Apply corrections to the API translation for consistency
                    for en_term, es_term in translations_map.items():
                        if en_term in detail_text:
                            pattern = re.compile(re.escape(en_term), re.IGNORECASE)
                            translated_text = pattern.sub(es_term, translated_text)
                
            except Exception as e:
                print(f"Translation error: {str(e)}", file=sys.stderr)
                
                # Method 2: Fallback to dictionary-based translation if the API fails
                translated_text = detail_text
                
                # Apply simple dictionary-based translations
                translations = {
                    'Calories': 'Calorías',
                    'Fat': 'Grasa',
                    'Cholesterol': 'Colesterol',
                    'Sodium': 'Sodio',
                    'Carbs': 'Carbohidratos',
                    'Fiber': 'Fibra',
                    'Sugar': 'Azúcar',
                    'Protein': 'Proteína',
                    'Price': 'Precio',
                    'Allergen Information': 'Información de Alérgenos',
                    'contains': 'contiene',
                    'may contain': 'puede contener',
                    'free from': 'libre de',
                    'No allergens listed': 'No se enumeran alérgenos'
                }
                
                for en_term, es_term in translations.items():
                    translated_text = translated_text.replace(en_term, es_term)
                
                print(f"Fallback translation: {translated_text}", file=sys.stderr)
        
        # Use the translated text for detail_text if in Spanish mode
        detail_text = translated_text

        # Generate TTS audio
        try:
            engine = pyttsx3.init()
            
            voices = engine.getProperty('voices')
            print(f"Found {len(voices)} voices:", [v.name for v in voices], file=sys.stderr)


            # Configure voice based on language
            voices = engine.getProperty('voices')
            if language == 'es':
                # Find a Spanish voice if available
                spanish_voice = next((v for v in voices if 'spanish' in v.name.lower()), None)
                if spanish_voice:
                    engine.setProperty('voice', spanish_voice.id)
                    print(f"Using Spanish voice: {spanish_voice.name}", file=sys.stderr)
                else:
                    print("No Spanish voice found, using default voice", file=sys.stderr)
            else:  # Default to English
                english_voice = next((v for v in voices if 'english' in v.name.lower()), None)
                if english_voice:
                    engine.setProperty('voice', english_voice.id)

            # Generate unique filename
            safe_product_name = normalized_product.replace(' ', '_').replace('-', '_')
            filename = f"{safe_product_name}_{query_type}_{language}.wav"
            audio_path = os.path.join('static', filename)
            
            # Create static directory if it doesn't exist
            os.makedirs('static', exist_ok=True)
            
            # Generate audio file with the translated text
            engine.save_to_file(detail_text, audio_path)
            engine.runAndWait()

            # Add debugging code here
            print(f"Audio file generated at: {audio_path}", file=sys.stderr)
            if os.path.exists(audio_path):
                print(f"File size: {os.path.getsize(audio_path)} bytes", file=sys.stderr)
            else:
                print(f"Warning: Audio file was not created", file=sys.stderr)

            # Return both the text and audio URL
            return jsonify({
                'success': True,
                'details': detail_text,
                'audio_url': f"/static/{filename}",
                'product_name': normalized_product,
>>>>>>> b18126b6ed279059af7d198e343701e238c927d5
                'language': language
            })

        except Exception as e:
<<<<<<< HEAD
            print(f"TTS Error: {e}", file=sys.stderr)
            # Return text-only response if audio fails
            return jsonify({
                'success': True,
                'details': details,
                'error': f"Audio generation failed: {str(e)}",
=======
            print(f"TTS error: {e}", file=sys.stderr)
            # Return text only if audio generation fails
            return jsonify({
                'success': True,
                'details': detail_text,
                'error': "Audio generation failed",
                'product_name': normalized_product,
>>>>>>> b18126b6ed279059af7d198e343701e238c927d5
                'language': language
            })

    except Exception as e:
        print(f"Query error: {e}", file=sys.stderr)
        return jsonify(success=False, error=str(e)), 500
<<<<<<< HEAD
# ------------------------------------------------------------------------
# Route to test DB connectivity
# ------------------------------------------------------------------------
=======

# Add this route to test the database
>>>>>>> b18126b6ed279059af7d198e343701e238c927d5
@app.route('/test-db', methods=['GET'])
def test_db():
    return jsonify({"message": "Check server logs for database test results"})

# Add route to serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Create static directory if it doesn't exist
    # test_db_connection()  # Test DB before starting server
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(host='0.0.0.0', port=5000, debug=True)