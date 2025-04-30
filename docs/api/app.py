from flask import Flask, request, jsonify
import requests
import sys

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        'status': 'API is running',
        'endpoints': {
            'predict': '/predict (POST) - Send an image for classification'
        }
    })

@app.route('/predict', methods=['POST'])
def predict():
    print("🔍 /predict called", file=sys.stderr)
    try:
        # Forward the request to local tunnel
        response = requests.post(
            'http://localhost:8000/predict',  # This forwards to your local machine through SSH tunnel
            files={'image': request.files['image']},
            timeout=10
        )
        return response.json()
    except requests.exceptions.ConnectionError:
        print("Could not connect to local prediction server", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': 'Could not connect to local prediction server'
        }), 503
    except Exception as e:
        print(f"Error in /predict: {e}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
