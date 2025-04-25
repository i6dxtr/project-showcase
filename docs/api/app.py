# docs/api/app.py
# these are necessary imports for the backend too, please indicate if any have been added
from flask import Flask, request, jsonify  # needs flask -- done
from flask_cors import CORS               # needs flask-cors -- done
import tensorflow as tf                   # needs tensorflow -- done
import cv2                               # needs opencv-python-headless -- done
import numpy as np                       # needs numpy -- done

app = Flask(__name__)
CORS(app, origins=['https://i6dxtr.github.io']) # do not change this

# place the classifier inside same directory
model = tf.keras.models.load_model('/docs/api/model/my_product_classifier_BETTER.h5') # emphasis on 'better'

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
        # predicted_label = index_to_class[predicted_class_index] # who knows
        
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