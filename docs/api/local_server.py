from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import json
import sys
import os
import traceback

app = Flask(__name__)
CORS(app)

# Define the model globally
try:
    MODEL_PATH = '../../lib_mdl/my_product_classifier_BETTER.h5'
    MAPPING_PATH = '../../lib_mdl/class_mapping.json'
    
    print(f"Loading model from: {os.path.abspath(MODEL_PATH)}")
    model = load_model(MODEL_PATH)
    
    print(f"Loading class mapping from: {os.path.abspath(MAPPING_PATH)}")
    with open(MAPPING_PATH, 'r') as f:
        index_to_class = json.load(f)
    
    print("Model and mapping loaded successfully")
except Exception as e:
    print(f"Error loading model or mapping: {e}", file=sys.stderr)
    sys.exit(1)

@app.route('/', methods=['GET'])
def index():
    response = make_response(jsonify({'status': 'Local server is running'}))
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/predict', methods=['POST'])
def predict():
    print("/predict called", file=sys.stderr)
    try:
        file = request.files.get('image')
        if not file:
            return jsonify(success=False, error="No image file provided"), 400


        # Convert file to OpenCV format
        data = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify(success=False, error="Invalid image data"), 400

        # Process image
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (224, 224))
        batch = np.expand_dims(resized / 255.0, axis=0)
        
        # Make prediction
        preds = model.predict(batch)
        idx = str(np.argmax(preds, axis=1)[0])
        label = index_to_class.get(idx, "unknown")

        response = make_response(jsonify(success=True, prediction=label))
        response.headers['Content-Type'] = 'application/json'
        return jsonify(success=True, prediction=label)

    except Exception as e:
        print(f"Error in prediction: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)  # Log the stack trace
        return jsonify(success=False, error=str(e)), 500

if __name__ == '__main__':
    print("Starting local prediction server...")
    app.run(host='0.0.0.0', port=8080, debug=True)