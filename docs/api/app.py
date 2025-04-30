from flask import Flask, request, jsonify
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import sys

app = Flask(__name__)

# Create a session with retry strategy
def create_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504]
    )
    session.mount('http://', HTTPAdapter(max_retries=retry))
    return session

@app.route('/predict', methods=['POST'])
def predict():
    print("/predict called", file=sys.stderr)
    try:
        session = create_session()
        
        # Test connection first
        print("Testing tunnel connection...", file=sys.stderr)
        test_response = session.get('http://localhost:8000/', timeout=5)
        print(f"Tunnel test response: {test_response.text}", file=sys.stderr)
        
        # Forward the actual request
        print("Forwarding prediction request...", file=sys.stderr)
        files = {'image': (request.files['image'].filename, request.files['image'].stream, 
                          request.files['image'].content_type)}
        
        response = session.post(
            'http://localhost:8000/predict',
            files=files,
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