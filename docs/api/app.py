from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys
import pyttsx3  # Changed from gTTS to pyttsx3
import sqlite3
from googletrans import Translator
import os


app = Flask(__name__)
CORS(app)

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

        if not product_name or not query_type:
            return jsonify(success=False, error="Missing product_name or query_type"), 400

        # Construct database path
        db_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'products.db')
        print(f"Database path: {db_path}", file=sys.stderr)

        # Connect to database
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        # Select appropriate query based on type
        if query_type == 'nutrition':
            query = '''
                SELECT 
                    calories, total_fat, cholesterol, sodium, 
                    total_carbs, fiber, sugar, protein
                FROM nutritional_info
                JOIN products ON products.id = nutritional_info.product_id
                WHERE products.name = ?
            '''
            cursor.execute(query, (product_name,))
            result = cursor.fetchone()
            
            if result:
                detail_text = f"Calories: {result[0]}, Fat: {result[1]}, "
                detail_text += f"Cholesterol: {result[2]}, Sodium: {result[3]}, "
                detail_text += f"Carbs: {result[4]}, Fiber: {result[5]}, "
                detail_text += f"Sugar: {result[6]}, Protein: {result[7]}"

        elif query_type == 'allergen':
            query = '''
                SELECT allergy
                FROM nutritional_info
                JOIN products ON products.id = nutritional_info.product_id
                WHERE products.name = ?
            '''
            cursor.execute(query, (product_name,))
            result = cursor.fetchone()
            
            if result:
                detail_text = f"Allergen Information: {result[0]}"

        elif query_type == 'price':
            query = '''
                SELECT cost
                FROM products
                WHERE name = ?
            '''
            cursor.execute(query, (product_name,))
            result = cursor.fetchone()
            
            if result:
                detail_text = f"Price: ${result[0]:.2f}"

        else:
            connection.close()
            return jsonify(success=False, error="Invalid query_type"), 400

        connection.close()

        if not result:
            return jsonify(success=False, error="Product not found"), 404

        # Translate if Spanish is requested
        if language == 'es':
            try:
                translator = Translator()
                detail_text = translator.translate(detail_text, src='en', dest='es').text
            except Exception as e:
                print(f"Translation error: {e}", file=sys.stderr)
                # Continue with English if translation fails
                pass

        # Generate TTS audio
        try:
            engine = pyttsx3.init()
            
            # Configure voice based on language
            voices = engine.getProperty('voices')
            if language == 'es':
                spanish_voice = next((v for v in voices if 'spanish' in v.name.lower()), None)
                if spanish_voice:
                    engine.setProperty('voice', spanish_voice.id)
            else:  # Default to English
                english_voice = next((v for v in voices if 'english' in v.name.lower()), None)
                if english_voice:
                    engine.setProperty('voice', english_voice.id)

            # Generate unique filename
            filename = f"{product_name.replace(' ', '_')}_{query_type}_{language}.wav"
            audio_path = os.path.join('static', filename)
            
            # Create static directory if it doesn't exist
            os.makedirs('static', exist_ok=True)
            
            # Generate audio file
            engine.save_to_file(detail_text, audio_path)
            engine.runAndWait()

            return jsonify({
                'success': True,
                'details': detail_text,
                'audio_url': f"/static/{filename}"
            })

        except Exception as e:
            print(f"TTS error: {e}", file=sys.stderr)
            # Return text only if audio generation fails
            return jsonify({
                'success': True,
                'details': detail_text,
                'error': "Audio generation failed"
            })

    except Exception as e:
        print(f"Query error: {e}", file=sys.stderr)
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
