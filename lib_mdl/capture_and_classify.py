import cv2
import os
import numpy as np
from tensorflow.keras.models import load_model
from announce_product import announce_product
import threading # this does... something?

# Load the trained model
model = load_model('my_product_classifier_BETTER.h5')

# Define the folder to save captured images
capture_folder = '../data/captured_images'
os.makedirs(capture_folder, exist_ok=True)

# Load class indices from the training generator
class_indices = {'morton coarse kosher salt': 0,
                 'kroger creamy peanut butter': 1,
                 'great value twist and shout cookies': 2,
                 'great value cheddar cheese cracklers': 3}
index_to_class = {v: k for k, v in class_indices.items()}

# Function to predict the class of an image
def predict_image(model, img_path):
    # Read the image (OpenCV reads BGR)
    img = cv2.imread(img_path)
    # Convert to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # Resize to 224x224
    img_resized = cv2.resize(img, (224, 224))
    # Scale pixel values (same as training scale)
    img_array = np.expand_dims(img_resized / 255.0, axis=0)

    # Predict
    predictions = model.predict(img_array)
    predicted_class_index = np.argmax(predictions, axis=1)[0]
    predicted_label = index_to_class[predicted_class_index]

    return predicted_label

def process_image(image_path, frame):
    """Process the captured image and announce results"""
    cv2.imwrite(image_path, frame)
    print(f"Image saved to {image_path}")
    
    prediction = predict_image(model, image_path)
    print("Predicted:", prediction)
    
    announce_product(prediction)

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Press 'c' to capture an image or 'q' to quit.")
    processing_thread = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break

        cv2.imshow('Webcam', frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            if processing_thread and processing_thread.is_alive():
                print("Still processing previous image...")
                continue
                
            image_path = os.path.join(capture_folder, 'captured_image.jpg')
            processing_thread = threading.Thread(
                target=process_image,
                args=(image_path, frame.copy())  # Use frame.copy() to avoid reference issues
            )
            processing_thread.daemon = True
            processing_thread.start()

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
