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
    print("/predict called", file=sys.stderr)
    try:
        # Test the tunnel connection first
        print("Testing tunnel connection...", file=sys.stderr)
        test_response = requests.get('http://localhost:8000/')
        print(f"Tunnel test response: {test_response.text}", file=sys.stderr)
        
        # Forward the actual request
        print("Forwarding prediction request...", file=sys.stderr)
        response = requests.post(
            'http://localhost:8000/predict',
            files={'image': request.files['image']},
            timeout=10
        )
        print(f"Got response: {response.text}", file=sys.stderr)
        
        return response.json()
    except requests.exceptions.ConnectionError as ce:
        print(f"Connection error details: {str(ce)}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': f'Tunnel connection error: {str(ce)}'
        }), 503
    except Exception as e:
        print(f"Error type: {type(e)}", file=sys.stderr)
        print(f"Error details: {str(e)}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': f'{type(e).__name__}: {str(e)}'
        }), 500