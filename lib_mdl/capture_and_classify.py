import cv2
import os
import numpy as np
from tensorflow.keras.models import load_model
from announce_product import announce_product  # Import from the new file

# Load the trained model
model = load_model('my_product_classifier.h5')

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

# Initialize webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

print("Press 'c' to capture an image or 'q' to quit.")

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    if not ret:
        print("Error: Failed to capture image.")
        break

    # Display the frame
    cv2.imshow('Webcam', frame)

    # Wait for key press
    key = cv2.waitKey(1) & 0xFF

    # Capture image on 'c' key press
    if key == ord('c'):
        # Save the captured image
        image_path = os.path.join(capture_folder, 'captured_image.jpg')
        cv2.imwrite(image_path, frame)
        print(f"Image saved to {image_path}")

        # Predict the class of the captured image
        prediction = predict_image(model, image_path)
        print("Predicted:", prediction)

        # Announce the product
        announce_product(prediction)

    # Exit on 'q' key press
    elif key == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()