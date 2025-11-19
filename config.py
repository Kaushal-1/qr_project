import os

# Database configuration
DB_PATH = "db/qr_registry.db"

# Cryptographic keys
KEY_PATH = "private_key.pem"
PUBLIC_KEY_B64 = os.environ.get("PUBLIC_KEY_B64", None)

# Image comparison thresholds (adjusted for camera vs screen conditions)
PHASH_THRESHOLD = 15  # Hamming distance threshold for pHash (higher for camera tolerance)
SSIM_THRESHOLD = 0.3   # SSIM similarity threshold (lower for camera vs screen comparison)

# Behavioral analysis thresholds
SCAN_FLAG_THRESHOLD = 10  # Flag items scanned more than this many times

# QR code generation settings
QR_BOX_SIZE = 2  # Pixels per QR box (configurable for ~1cm print size)
QR_BORDER = 1    # Border size in boxes

# Server configuration
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
DEBUG = True