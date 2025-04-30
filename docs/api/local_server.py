from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import json
import sys

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def index():
    response = make_response(jsonify({'status': 'Local server is running'}))
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/predict', methods=['POST'])
def predict():
    try:
        file = request.files.get('image')
        if not file:
            return jsonify(success=False, error="No image file provided"), 400

        # Convert file to OpenCV format (reusing your existing code from docs/api/app.py)
        data = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify(success=False, error="Invalid image data"), 400

        # Process image (reusing your predict_image logic)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (224, 224))
        batch = np.expand_dims(resized / 255.0, axis=0)
        preds = model.predict(batch)
        idx = str(np.argmax(preds, axis=1)[0])
        label = index_to_class.get(idx, "unknown")

        response = make_response(jsonify(success=True, prediction=label))
        response.headers['Content-Type'] = 'application/json'
        return response

    except Exception as e:
        print(f"Error in prediction: {e}", file=sys.stderr)
        return jsonify(success=False, error=str(e)), 500

if __name__ == '__main__':
    print("Starting local prediction server...")
    # Change to port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)