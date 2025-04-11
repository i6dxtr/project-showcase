import cv2
import os
import numpy as np
from tensorflow.keras.models import load_model
from announce_product import announce_product
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
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

def predict_image(model, img_path):
    """Predict the class of an image."""
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img, (224, 224))
    img_array = np.expand_dims(img_resized / 255.0, axis=0)

    predictions = model.predict(img_array)
    predicted_class_index = np.argmax(predictions, axis=1)[0]
    predicted_label = index_to_class[predicted_class_index]

    return predicted_label

# Initialize webcam
cap = None

class WebcamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vision Gap Bridge")
        self.root.configure(bg='black')
        self.root.state('zoomed')
        self.webcam_running = False
        self.is_processing = False

        # GUI Setup
        self.setup_gui()

    def setup_gui(self):
        """Setup all GUI elements."""
        self.main_container = tk.Frame(self.root, bg='black')
        self.main_container.pack(expand=True, fill='both')

        self.header = tk.Label(self.main_container, text="Vision Gap Bridge",
                             font=("Arial", 24), fg="white", bg="black")
        self.header.pack(pady=10)

        self.webcam_frame = tk.Frame(self.main_container, bg='black')
        self.webcam_frame.pack(expand=True, fill='both', padx=20, pady=10)

        self.label = tk.Label(self.webcam_frame, bg="black")
        self.label.pack(expand=True, fill='both')

        self.status_label = tk.Label(self.main_container,
                                   text="Press 'Start Webcam' to begin.",
                                   font=("Arial", 14), fg="white", bg="black")
        self.status_label.pack(pady=5)

        self.setup_buttons()
        self.setup_bindings()

    def setup_buttons(self):
        """Setup button controls."""
        self.button_frame = tk.Frame(self.main_container, bg="black")
        self.button_frame.pack(pady=10)

        self.start_button = tk.Button(self.button_frame, text="Start Webcam",
                                    font=("Arial", 12), command=self.start_webcam)
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.capture_button = tk.Button(self.button_frame, text="Capture Image",
                                      font=("Arial", 12), command=self.capture_image,
                                      state=tk.DISABLED)
        self.capture_button.pack(side=tk.LEFT, padx=10)

        self.quit_button = tk.Button(self.button_frame, text="Quit",
                                   font=("Arial", 12), command=self.quit)
        self.quit_button.pack(side=tk.RIGHT, padx=10)

    def setup_bindings(self):
        """Setup keyboard bindings."""
        self.root.bind('c', self.capture_image_keypress)
        self.root.bind('q', self.quit_keypress)

    def start_webcam(self):
        """Initialize and start the webcam."""
        global cap
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open webcam.")
            return
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        self.webcam_running = True
        self.status_label.config(text="Running!", fg="green")
        self.capture_button.config(state=tk.NORMAL)
        self.start_button.config(state=tk.DISABLED)
        self.update_webcam_feed()

    def capture_image(self):
        """Capture image button handler."""
        self.capture_image_keypress()

    def process_image_async(self, frame, image_path):
        """Process the captured image in a separate thread."""
        try:
            cv2.imwrite(image_path, frame)
            self.status_label.config(text=f"Image saved to {image_path}", fg="blue")
            
            prediction = predict_image(model, image_path)
            self.status_label.config(text=f"Predicted: {prediction}", fg="green")
            
            announce_product(prediction)
            
        finally:
            self.is_processing = False

    def capture_image_keypress(self, event=None):
        """Handle image capture from keyboard or button."""
        if not self.webcam_running or self.is_processing:
            return

        ret, frame = cap.read()
        if ret:
            self.is_processing = True
            image_path = os.path.join(capture_folder, 'captured_image.jpg')
            
            thread = threading.Thread(
                target=self.process_image_async,
                args=(frame.copy(), image_path)
            )
            thread.daemon = True
            thread.start()
        else:
            messagebox.showerror("Error", "Failed to capture image.")

    def update_webcam_feed(self):
        """Update the webcam feed display."""
        if self.webcam_running and cap is not None:
            try:
                ret, frame = cap.read()
                if ret:
                    window_width = self.webcam_frame.winfo_width()
                    window_height = self.webcam_frame.winfo_height()
                    frame_height, frame_width = frame.shape[:2]
                    aspect_ratio = frame_width / frame_height
                    
                    new_width = window_width
                    new_height = int(window_width / aspect_ratio)
                    if new_height > window_height:
                        new_height = window_height
                        new_width = int(window_height * aspect_ratio)
                    
                    frame = cv2.resize(frame, (new_width, new_height))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    imgtk = ImageTk.PhotoImage(image=img)
                    self.label.imgtk = imgtk
                    self.label.config(image=imgtk)
            except Exception as e:
                print(f"Error updating webcam feed: {e}")

            self.root.after(10, self.update_webcam_feed)

    def quit(self):
        """Quit button handler."""
        self.quit_keypress()

    def quit_keypress(self, event=None):
        """Handle application quit from keyboard or button."""
        self.webcam_running = False
        global cap
        if cap is not None:
            cap.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WebcamApp(root)
    root.mainloop()