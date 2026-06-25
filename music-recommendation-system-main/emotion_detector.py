import streamlit as st
from ultralytics import YOLO
from PIL import Image
import numpy as np
import config

@st.cache_resource
def load_model(model_path: str):
    """
    Loads the YOLO emotion detection model. Caches the loaded model in resource memory
    so it is not reloaded on every rerun.
    """
    try:
        return YOLO(model_path)
    except Exception as e:
        st.error(f"Error loading YOLO model from path '{model_path}': {e}")
        return None

def detect_faces_and_emotions(image_input):
    """
    Processes the input image through YOLO to detect faces and predict emotions.
    
    Args:
        image_input: Can be a PIL Image, numpy array, or uploaded bytes.
        
    Returns:
        A list of dicts containing:
        - 'box': (x1, y1, x2, y2) bounding box
        - 'emotion': detected emotion label (str)
        - 'confidence': confidence score (float)
        - 'cropped_image': PIL Image of the cropped face
    """
    model = load_model(config.YOLO_MODEL_PATH)
    if model is None:
        return []

    # Ensure we have a PIL Image for cropping
    if isinstance(image_input, np.ndarray):
        pil_img = Image.fromarray(image_input)
    elif isinstance(image_input, Image.Image):
        pil_img = image_input
    else:
        # Fallback / attempt conversion
        pil_img = Image.open(image_input).convert("RGB")

    # Run detection
    try:
        results = model(pil_img, conf=config.CONFIDENCE_THRESHOLD, verbose=False)
    except Exception as e:
        st.error(f"YOLO Inference failed: {e}")
        return []

    detections = []
    
    if len(results) == 0:
        return []

    result = results[0]
    boxes = result.boxes

    if boxes is not None and len(boxes) > 0:
        for box in boxes:
            # Box attributes
            coords = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            conf = float(box.conf[0])
            class_id = int(box.cls[0])
            
            emotion = config.YOLO_CLASS_MAP.get(class_id, "neutral")

            # Extract coordinates and clamp to image dimensions
            w, h = pil_img.size
            x1 = max(0, int(coords[0]))
            y1 = max(0, int(coords[1]))
            x2 = min(w, int(coords[2]))
            y2 = min(h, int(coords[3]))

            # Crop the detected face
            try:
                cropped_img = pil_img.crop((x1, y1, x2, y2))
            except Exception:
                # If crop fails, fall back to full image
                cropped_img = pil_img

            detections.append({
                "box": (x1, y1, x2, y2),
                "emotion": emotion,
                "confidence": conf,
                "cropped_image": cropped_img
            })

    return detections
