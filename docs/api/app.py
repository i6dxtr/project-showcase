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

# model now loads once, globally
print("Loading model...", file=sys.stderr)
MODEL_PATH = '/home/i6dxtr/docs/api/model/my_product_classifier_BETTER.h5' # DO NOT CHANGE THIS PATH
MAPPING_PATH = os.path.join(os.path.dirname(__file__), '..', 'lib_mdl', 'class_mapping.json')
model = tf.keras.models.load_model(MODEL_PATH)

# Load class mapping
with open(MAPPING_PATH, 'r') as f:
    index_to_class = json.load(f)

def predict_image(image_array):
    """Predict using same preprocessing as frontend"""
    # Convert to RGB
    img = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    # Resize to 224x224
    img_resized = cv2.resize(img, (224, 224))
    # Scale pixel values
    img_array = np.expand_dims(img_resized / 255.0, axis=0)

    # Predict
    predictions = model.predict(img_array)
    predicted_class_index = np.argmax(predictions, axis=1)[0]
    # Convert index to string for json serialization
    predicted_class_index = str(predicted_class_index)
    predicted_label = index_to_class[predicted_class_index]

@app.route('/predict', methods=['POST'])
def predict():
    print("Predict endpoint called", file=sys.stderr)
    print(f"Files in request: {request.files}", file=sys.stderr)
    print(f"Content Type: {request.content_type}", file=sys.stderr)
    print(f"Headers: {request.headers}", file=sys.stderr)
    
    try:
        if 'image' not in request.files:
            print("No image in request.files", file=sys.stderr)
            return jsonify({'error': 'No image provided'}), 400
            
        # file = request.files['image']
        # print(f"Received file: {file.filename}", file=sys.stderr)
        
        # if file.filename == '':
        #     return jsonify({'error': 'No selected file'}), 400

        # file = request.files['image']
        # nparr = np.frombuffer(file.read(), np.uint8)
        # img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # img_resized = cv2.resize(img, (224, 224))
        # img_array = np.expand_dims(img_resized / 255.0, axis=0)

        # predictions = model.predict(img_array)
        # predicted_class_index = np.argmax(predictions, axis=1)[0]
        # # predicted_label = index_to_class[predicted_class_index] # who knows

        file = request.files['image']
        # one shot
        file_bytes = file.read()
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # batch process image transformations
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img, (224, 224))
        img_array = np.expand_dims(img_resized / 255.0, axis=0)

        # t/o for predictions
        predictions = model.predict(img_array, batch_size=1)
        predicted_class_index = np.argmax(predictions, axis=1)[0]
        
        return jsonify({
            'prediction': int(predicted_class_index) # these are just numbers for now
        })
    
    except Exception as e:
        return jsonify({
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