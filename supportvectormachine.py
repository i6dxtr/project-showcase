# Import required libraries
from sklearn.svm import SVC
import numpy as np
from skimage.util import view_as_windows
import pickle

def generate_image_features(image_path, window_size=5, num_samples=300, pct_fg=0.5):
    """
    Generate features from image using sliding window approach
    
    Parameters:
    image_path: str - Path to input image
    window_size: int - Size of sliding window (default 5x5)
    num_samples: int - Number of samples to extract for training
    pct_fg: float - Target percentage of foreground samples (0-1)
    
    Returns:
    DataFrame with image features and target values
    """
    # Load and pad image
    image = imread(image_path)
    height, width = image.shape
    padded_image = np.pad(image, ((window_size-1)//2, (window_size-1)//2), mode='reflect')
    
    # Extract windows and flatten into feature vectors
    image_features = view_as_windows(padded_image, (window_size, window_size))
    flat_features = image_features.reshape(height*width, window_size**2)
    
    return flat_features

def train_svm_segmenter(train_images, train_masks, kernel='rbf', probability=True, **svm_params):
    """
    Train SVM model for image segmentation
    
    Parameters:
    train_images: list - List of training image paths
    train_masks: list - List of corresponding ground truth mask paths
    kernel: str - SVM kernel type ('linear', 'rbf', 'poly', 'sigmoid')
    probability: bool - Whether to enable probability estimates
    svm_params: dict - Additional parameters for sklearn.svm.SVC
    
    Returns:
    Trained SVM model
    """
    # Initialize SVM
    svm = SVC(kernel=kernel, probability=probability, **svm_params)
    
    # Collect features from all training images
    X = []
    y = []
    
    for img_path, mask_path in zip(train_images, train_masks):
        features = generate_image_features(img_path)
        mask = imread(mask_path).flatten()
        X.append(features)
        y.append(mask)
    
    X = np.vstack(X)
    y = np.concatenate(y)
    
    # Train model
    svm.fit(X, y)
    return svm

def segment_image(image_path, model, window_size=5):
    """
    Segment new image using trained SVM model
    
    Parameters:
    image_path: str - Path to image to segment
    model: sklearn.svm.SVC - Trained SVM model
    window_size: int - Size of sliding window (must match training)
    
    Returns:
    Binary segmentation mask
    """
    # Extract features
    features = generate_image_features(image_path, window_size)
    
    # Predict segmentation
    segmentation = model.predict(features)
    
    # Reshape to original image dimensions
    image = imread(image_path)
    mask = segmentation.reshape(image.shape)
    
    return mask

def save_model(model, path):
    """Save trained model to disk"""
    with open(path, 'wb') as f:
        pickle.dump(model, f)

def load_model(path):
    """Load trained model from disk"""
    with open(path, 'rb') as f:
        return pickle.load(f)

# Example usage:
"""
# Train model
train_images = ['path/to/train1.jpg', 'path/to/train2.jpg']
train_masks = ['path/to/mask1.jpg', 'path/to/mask2.jpg']
model = train_svm_segmenter(train_images, train_masks, kernel='rbf', C=1.0)

# Save model
save_model(model, 'segmentation_model.pkl')

# Load model and segment new image
loaded_model = load_model('segmentation_model.pkl')
result = segment_image('path/to/test_image.jpg', loaded_model)
"""
