from flask import Flask, request, jsonify
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys

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
            'http://localhost:8000/predict',
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