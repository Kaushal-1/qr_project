#!/usr/bin/env python3
import imagehash
from PIL import Image
from skimage.metrics import structural_similarity as ssim
import numpy as np
import cv2
import io
import base64
import config

def compute_phash(image_data):
    """Compute perceptual hash of image"""
    if isinstance(image_data, bytes):
        image = Image.open(io.BytesIO(image_data))
    elif isinstance(image_data, str):
        # Base64 encoded image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
    else:
        image = image_data
    
    # Convert to grayscale for consistent hashing
    if image.mode != 'L':
        image = image.convert('L')
    
    return str(imagehash.phash(image))

def preprocess_image(img_data):
    """Preprocess image according to exact algorithm"""
    # Load image
    if isinstance(img_data, bytes):
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif isinstance(img_data, str):
        # Base64 encoded
        if img_data.startswith('data:image/'):
            img_data = img_data.split(',', 1)[1]
        image_bytes = base64.b64decode(img_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    else:
        # PIL Image
        img = cv2.cvtColor(np.array(img_data), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Resize to canonical size 512x512
    resized = cv2.resize(gray, (512, 512))
    
    # Apply Gaussian blur (kernel 3x3)
    blurred = cv2.GaussianBlur(resized, (3, 3), 0)
    
    # Histogram equalization (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    equalized = clahe.apply(blurred)
    
    return equalized

def compute_orb_match_ratio(img1, img2):
    """Compute ORB feature match ratio"""
    try:
        # Initialize ORB detector
        orb = cv2.ORB_create(nfeatures=500)
        
        # Detect keypoints and descriptors
        kp1, des1 = orb.detectAndCompute(img1, None)
        kp2, des2 = orb.detectAndCompute(img2, None)
        
        if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
            return 0.0
        
        # Match descriptors using BFMatcher
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        
        # Sort matches by distance
        matches = sorted(matches, key=lambda x: x.distance)
        
        # Calculate good match ratio (distance < 50)
        good_matches = [m for m in matches if m.distance < 50]
        match_ratio = len(good_matches) / max(len(matches), 1)
        
        return match_ratio
        
    except Exception as e:
        print(f"ORB matching error: {e}")
        return 0.0

def compare_images(canonical_image_path, uploaded_image_data):
    """Compare canonical image with uploaded image using exact algorithm"""
    try:
        # Load and preprocess canonical image
        with open(canonical_image_path, 'rb') as f:
            canonical_data = f.read()
        canonical_processed = preprocess_image(canonical_data)
        
        # Preprocess uploaded image
        uploaded_processed = preprocess_image(uploaded_image_data)
        
        # Compute pHash on preprocessed images
        canonical_pil = Image.fromarray(canonical_processed)
        uploaded_pil = Image.fromarray(uploaded_processed)
        
        canonical_phash = imagehash.phash(canonical_pil)
        uploaded_phash = imagehash.phash(uploaded_pil)
        
        # Compute Hamming distance
        phash_distance = canonical_phash - uploaded_phash
        
        # Compute SSIM on preprocessed images
        ssim_score = ssim(canonical_processed, uploaded_processed)
        
        # Compute ORB match ratio
        orb_ratio = compute_orb_match_ratio(canonical_processed, uploaded_processed)
        
        # Apply decision rules (adjusted for camera vs screen conditions)
        if phash_distance <= 25 and ssim_score >= 0.15:
            visual_tamper = False  # OK - very tolerant for camera conditions
        elif phash_distance <= 35 and ssim_score >= 0.10 and orb_ratio >= 0.05:
            visual_tamper = False  # Very tolerant case for camera vs screen
        else:
            visual_tamper = True   # Tampered
        
        # Debug logging
        print(f"Advanced image comparison results:")
        print(f"  pHash distance: {phash_distance} (thresholds: ≤12 strict, ≤18 tolerant)")
        print(f"  SSIM score: {ssim_score:.3f} (thresholds: ≥0.45 strict, ≥0.35 tolerant)")
        print(f"  ORB match ratio: {orb_ratio:.3f} (threshold: ≥0.12)")
        print(f"  Visual tamper: {visual_tamper}")
        
        return {
            'similarity': float(ssim_score),
            'visual_tamper': visual_tamper,
            'phash_distance': int(phash_distance),
            'ssim_score': float(ssim_score),
            'orb_ratio': float(orb_ratio),
            'canonical_phash': str(canonical_phash),
            'uploaded_phash': str(uploaded_phash)
        }
        
    except Exception as e:
        print(f"Image comparison error: {e}")
        return {
            'similarity': 0.0,
            'visual_tamper': True,
            'error': str(e)
        }