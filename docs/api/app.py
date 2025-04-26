# docs/api/app.py
# these are necessary imports for the backend too, please indicate if any have been added
from flask import Flask, request, jsonify  # needs flask -- done
from flask_cors import CORS               # needs flask-cors -- done
import tensorflow as tf                   # needs tensorflow -- done
import cv2                               # needs opencv-python-headless -- done
import numpy as np                       # needs numpy -- done
import os
import sys
import json

app = Flask(__name__)
CORS(app, origins=['https://i6dxtr.github.io']) # do not change this
global model, index_to_class

def load_model_and_mapping():
    """Load model and mapping once at startup"""
    global model, index_to_class
    
    print("Loading model and mapping...")
    MODEL_PATH = '/home/i6dxtr/docs/api/model/my_product_classifier_BETTER.h5' # DO NOT CHANGE THIS PATH
    MAPPING_PATH = '/home/i6dxtr/lib_mdl/class_mapping.json' 
    
    # Load model
    model = tf.keras.models.load_model(MODEL_PATH)
    
    # Load class mapping
    with open(MAPPING_PATH, 'r') as f:
        index_to_class = json.load(f)
    
    print("Model and mapping loaded successfully!")

# Load model and mapping at startup
load_model_and_mapping()

def predict_image(image_array):
    """Predict using same preprocessing as frontend"""
    global model, index_to_class
    
    # Convert to RGB
    img = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    # Resize to 224x224
    img_resized = cv2.resize(img, (224, 224))
    # Scale pixel values
    img_array = np.expand_dims(img_resized / 255.0, axis=0)

    # Predict using global model
    predictions = model.predict(img_array)
    predicted_class_index = str(np.argmax(predictions, axis=1)[0])
    predicted_label = index_to_class[predicted_class_index]

    return predicted_label

@app.route('/predict', methods=['POST'])
def predict():
    print("Predict endpoint called", file=sys.stderr)
    print(f"Files in request: {request.files}", file=sys.stderr)
    print(f"Content Type: {request.content_type}", file=sys.stderr)
    print(f"Headers: {request.headers}", file=sys.stderr)
    
    try:
                # Get image from request
        file = request.files['image']
        # Convert to numpy array
        nparr = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'error': 'Invalid image'}), 400

        # Get prediction using loaded model
        prediction = predict_image(img)
        
        return jsonify({
            'success': True,
            'prediction': prediction
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/')
def index():
    return jsonify({
        'status': 'API is running',
        'endpoints': {
            'predict': '/predict (POST) - Send an image for classification'
        }
    })

if __name__ == '__main__':
    app.run(debug=True)