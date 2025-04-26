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

    # 1. Load the Keras .h5 once
    MODEL_PATH = '/home/i6dxtr/docs/api/model/my_product_classifier_BETTER.h5'  # DO NOT CHANGE
    model = tf.keras.models.load_model(MODEL_PATH)
    print("✅ Model loaded", file=sys.stderr)

    # 2. Load your class-mapping JSON once
    MAPPING_PATH = os.path.join(os.path.dirname(__file__), '..', 'lib_mdl', 'class_mapping.json')
    with open(MAPPING_PATH, 'r') as f:
        index_to_class = json.load(f)
    print("✅ Class mapping loaded", file=sys.stderr)

    # 3. Warm up TF graph (avoids first-request slowness)
    dummy = np.zeros((1, 224, 224, 3), dtype=np.float32)
    _ = model.predict(dummy, verbose=0)
    print("✅ Model warmed up", file=sys.stderr)

def predict_image(image_array):
    """Preprocess OpenCV image & run inference on global model."""
    rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (224, 224))
    batch   = np.expand_dims(resized / 255.0, axis=0)
    preds   = model.predict(batch)
    idx     = str(np.argmax(preds, axis=1)[0])
    return index_to_class.get(idx, "unknown")

@app.route('/predict', methods=['POST'])
def predict():
    try:
        file = request.files.get('image')
        if not file:
            return jsonify(success=False, error="No image file provided"), 400

        data = np.frombuffer(file.read(), np.uint8)
        img  = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify(success=False, error="Invalid image data"), 400

        label = predict_image(img)
        return jsonify(success=True, prediction=label)

    except Exception as e:
        print(f"❌ Error in /predict: {e}", file=sys.stderr)
        return jsonify(success=False, error=str(e)), 500

@app.route('/')
def index():
    return jsonify(status='API is running',
                   endpoints={'predict': '/predict (POST form-data: image)'})

if __name__ == '__main__':
    # In production, use Gunicorn with --preload instead of flask's dev server:
    #   gunicorn --workers 4 --threads 4 --timeout 120 --preload -b 0.0.0.0:5000 docs.api.app:app
    app.run(host='0.0.0.0', port=5000)
