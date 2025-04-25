# docs/api/app.py
from flask import Flask, request, jsonify  # needs flask
from flask_cors import CORS               # needs flask-cors (missing, apparently?)
import tensorflow as tf                   # needs tensorflow
import cv2                               # needs opencv-python-headless
import numpy as np                       # needs numpy

app = Flask(__name__)
CORS(app, origins=['https://i6dxtr.github.io']) # do not change this

# Load model
model = tf.keras.models.load_model('model/my_product_classifier.h5')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        file = request.files['image']
        nparr = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img, (224, 224))
        img_array = np.expand_dims(img_resized / 255.0, axis=0)

        predictions = model.predict(img_array)
        predicted_class_index = np.argmax(predictions, axis=1)[0]
        predicted_label = index_to_class[predicted_class_index]
        
        return jsonify({
            'prediction': predicted_label
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)