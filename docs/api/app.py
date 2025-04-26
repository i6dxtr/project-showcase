# docs/api/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
import cv2, numpy as np, os, sys, json

app = Flask(__name__)
CORS(app, origins=['https://i6dxtr.github.io'])

model = None
index_to_class = None

@app.before_first_request
def load_and_warm_model():
    global model, index_to_class
    
    print("Loading model and mapping...")
    MODEL_PATH = '/home/i6dxtr/docs/api/model/my_product_classifier_BETTER.h5' # DO NOT CHANGE THIS PATH
    MAPPING_PATH = '/home/i6dxtr/lib_mdl/class_mapping.json' 
    
    # Load model
    model = tf.keras.models.load_model(MODEL_PATH)

    print("⏳ Loading class mapping…", file=sys.stderr)
    with open(MAPPING_PATH, 'r') as f:
        index_to_class = json.load(f)

    # **Warm-up** so that the first real request isn’t building the TF graph
    dummy = np.zeros((1, 224, 224, 3), dtype=np.float32)
    _ = model.predict(dummy, verbose=0)

    print("✅ Model loaded and warmed up!", file=sys.stderr)

def predict_image(image_array):
    # same as before…
    img = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224))
    arr = np.expand_dims(img / 255.0, axis=0)
    preds = model.predict(arr)
    idx  = str(np.argmax(preds, axis=1)[0])
    return index_to_class[idx]

@app.route('/predict', methods=['POST'])
def predict():
    try:
        file = request.files['image']
        buf  = np.frombuffer(file.read(), np.uint8)
        img  = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify(error="Invalid image"), 400

        label = predict_image(img)
        return jsonify(success=True, prediction=label)

    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

@app.route('/')
def index():
    return jsonify(status='API is running', endpoints={'predict':'/predict (POST)'})

if __name__ == '__main__':
    # For production you’ll run under Gunicorn or uWSGI, *not* flask’s dev server.
    app.run(host='0.0.0.0', port=5000)
