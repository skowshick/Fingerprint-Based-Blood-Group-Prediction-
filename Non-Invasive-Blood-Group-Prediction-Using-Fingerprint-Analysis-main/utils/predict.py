import os
from pathlib import Path
import numpy as np
import cv2

# Configure TensorFlow to reduce warnings and improve performance
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce TensorFlow logging
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN custom ops warnings

import tensorflow as tf
from collections import Counter

# Set memory growth for GPU if available
physical_devices = tf.config.list_physical_devices('GPU')
if physical_devices:
    try:
        for gpu in physical_devices:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError:
        pass

MODEL_PATH = Path(__file__).parent.parent / "model" / "final_best_efficientnetb0_model_final.keras"
_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading model from {MODEL_PATH}...")
        _model = tf.keras.models.load_model(MODEL_PATH)
        print("Model loaded successfully!")
    return _model

CLASS_LABELS = ['A+', 'A-', 'AB+', 'AB-', 'B+', 'B-', 'O+', 'O-']
TARGET_SIZE = (103, 96)

# Image quality thresholds
MIN_SHARPNESS = 50.0  # Laplacian variance threshold
MIN_CONTRAST = 30.0   # Standard deviation threshold
MIN_BRIGHTNESS = 20.0 # Mean brightness threshold
MAX_BRIGHTNESS = 235.0 # Maximum brightness threshold

def check_image_quality(img_path):
    try:
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            return False, 0.0, ["Unable to read image file"]
        
        issues = []
        quality_score = 100.0
        
        # 1. Check sharpness using Laplacian variance
        laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
        if laplacian_var < MIN_SHARPNESS:
            issues.append("Image is too blurry")
            quality_score -= 30
        
        # 2. Check contrast (standard deviation)
        std_dev = np.std(img)
        if std_dev < MIN_CONTRAST:
            issues.append("Image has low contrast")
            quality_score -= 25
        
        # 3. Check brightness
        mean_brightness = np.mean(img)
        if mean_brightness < MIN_BRIGHTNESS:
            issues.append("Image is too dark")
            quality_score -= 25
        elif mean_brightness > MAX_BRIGHTNESS:
            issues.append("Image is overexposed")
            quality_score -= 25
        
        # 4. Check image size
        height, width = img.shape
        if width < 50 or height < 50:
            issues.append("Image resolution is too low")
            quality_score -= 20
        
        # Image is considered clear if quality score is above 60%
        is_clear = quality_score >= 60 and len(issues) == 0
        
        return is_clear, max(0, quality_score), issues
        
    except Exception as e:
        return False, 0.0, [f"Error checking image quality: {str(e)}"]

# Preprocess a single fingerprint image
def preprocess_image(img_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, TARGET_SIZE)
    img = img.astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=-1)
    img = np.repeat(img, 3, axis=-1)
    img = np.expand_dims(img, axis=0)
    return img

# Flexible prediction system (1-10 fingerprints)
def predict_flexible(image_dir, filenames=None):

    predictions = []
    quality_issues = []
    files_to_process = filenames or []
    
    if not files_to_process:
        files_to_process = [f for f in sorted(os.listdir(image_dir)) 
                          if f.lower().endswith(('.bmp', '.jpg', '.jpeg', '.png'))]
    
    # First, check quality of all images
    for filename in files_to_process:
        if filename.lower().endswith(('.bmp', '.jpg', '.jpeg', '.png')):
            full_path = os.path.join(image_dir, filename)
            if os.path.exists(full_path):
                is_clear, quality_score, issues = check_image_quality(full_path)
                
                if not is_clear:
                    quality_issues.append({
                        'filename': filename,
                        'quality_score': quality_score,
                        'issues': issues
                    })
    
    # If more than 50% of images have quality issues, reject the batch
    if len(quality_issues) > len(files_to_process) * 0.5:
        error_details = "\n".join([
            f"• {item['filename']}: {', '.join(item['issues'])} (Quality: {item['quality_score']:.1f}%)"
            for item in quality_issues[:3]  # Show first 3 problematic images
        ])
        raise ValueError(
            f"Image quality check failed. {len(quality_issues)} out of {len(files_to_process)} images are not clear enough for prediction.\n\n"
            f"Issues detected:\n{error_details}\n\n"
            f"Please upload clearer fingerprint images with:\n"
            f"• Good lighting and focus\n"
            f"• High contrast\n"
            f"• Minimal blur\n"
            f"• Adequate resolution"
        )
    
    # Process images that passed quality check
    for filename in files_to_process:
        if filename.lower().endswith(('.bmp', '.jpg', '.jpeg', '.png')):
            full_path = os.path.join(image_dir, filename)
            if os.path.exists(full_path):
                # Skip images that failed quality check
                if any(item['filename'] == filename for item in quality_issues):
                    continue
                    
                img_tensor = preprocess_image(full_path)
                model = get_model()
                preds = model.predict(img_tensor, verbose=0)[0]
                label = CLASS_LABELS[np.argmax(preds)]
                max_confidence = float(np.max(preds))

                predictions.append({
                    "filename": filename,
                    "label": label,
                    "confidence": preds.tolist(),
                    "max_confidence": max_confidence
                })
    
    if not predictions:
        return {
            'final_prediction': 'Unknown',
            'predictions': [],
            'confidence_details': {}
        }
    
    # Enhanced majority voting with confidence weighting
    final_prediction = enhanced_majority_prediction(predictions)
    
    return {
        'final_prediction': final_prediction,
        'predictions': predictions,
        'confidence_details': get_confidence_analysis(predictions)
    }

def enhanced_majority_prediction(predictions):
    if not predictions:
        return 'Unknown'
    
    weighted_votes = {}
    for pred in predictions:
        label = pred['label']
        confidence = pred['max_confidence']
        
        if label not in weighted_votes:
            weighted_votes[label] = 0
        weighted_votes[label] += confidence
    
    if weighted_votes:
        return max(weighted_votes, key=weighted_votes.get)
    
    labels = [p['label'] for p in predictions]
    return Counter(labels).most_common(1)[0][0]

def calculate_confidence(prediction_result):
    predictions = prediction_result.get('predictions', [])
    
    if not predictions:
        return 0.0
    
    final_label = prediction_result.get('final_prediction')
    
    # Get confidences for the final predicted label
    matching_confidences = [
        p['max_confidence'] for p in predictions 
        if p['label'] == final_label
    ]
    
    if not matching_confidences:
        return 0.0
    
    # Base confidence is average of matching predictions
    base_confidence = np.mean(matching_confidences)
    
    # Boost confidence based on consistency (how many fingerprints agree)
    consistency_factor = len(matching_confidences) / len(predictions)
    
    # Boost confidence based on number of fingerprints used
    fingerprint_boost = min(len(predictions) / 10, 1.0)  # Max boost at 10 fingerprints
    
    # Combined confidence calculation
    final_confidence = base_confidence * (0.7 + 0.2 * consistency_factor + 0.1 * fingerprint_boost)
    
    return min(final_confidence * 100, 99.9)  # Convert to percentage, cap at 99.9%

def get_confidence_analysis(predictions):
    """
    Provide detailed confidence analysis
    """
    if not predictions:
        return {}
    
    # Count predictions by label
    label_counts = Counter(p['label'] for p in predictions)
    
    # Calculate average confidence per label
    label_confidences = {}
    for label in label_counts.keys():
        confidences = [p['max_confidence'] for p in predictions if p['label'] == label]
        label_confidences[label] = {
            'count': label_counts[label],
            'avg_confidence': np.mean(confidences),
            'max_confidence': max(confidences)
        }
    
    return {
        'total_fingerprints': len(predictions),
        'label_analysis': label_confidences,
        'consistency': max(label_counts.values()) / len(predictions),
        'recommendations': get_recommendations(len(predictions), label_counts)
    }

def get_recommendations(num_fingerprints, label_counts):
    """
    Provide recommendations based on prediction analysis
    """
    recommendations = []
    
    if num_fingerprints < 5:
        recommendations.append("Consider uploading more fingerprints for higher accuracy")
    
    max_count = max(label_counts.values())
    if max_count / num_fingerprints < 0.6:
        recommendations.append("Results show inconsistency - recommend uploading clearer fingerprint images")
    
    if num_fingerprints >= 8 and max_count / num_fingerprints >= 0.8:
        recommendations.append("High confidence prediction with excellent consistency")
    
    return recommendations

# Legacy functions for backward compatibility
def predict_all(image_dir):
    """Legacy function - now uses flexible prediction"""
    result = predict_flexible(image_dir)
    return result['predictions']

def majority_prediction(predictions):
    """Legacy function - simple majority voting"""
    if not predictions:
        return 'Unknown'
    labels = [p['label'] for p in predictions]
    return Counter(labels).most_common(1)[0][0]

# Predict a single image (enhanced)
def predict_single_softmax(img_path):
    img_tensor = preprocess_image(img_path)
    model = get_model()
    preds = model.predict(img_tensor, verbose=0)[0]
    label_index = int(np.argmax(preds))
    label = CLASS_LABELS[label_index]
    
    return {
        'filename': os.path.basename(img_path),
        'label': label,
        'confidence': preds.tolist(),
        'max_confidence': float(np.max(preds))
    }
