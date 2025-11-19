#!/usr/bin/env python3
import argparse
import json
import sqlite3
import base64
import secrets
from datetime import datetime
from pathlib import Path
import qrcode
from nacl.signing import SigningKey
from nacl.encoding import Base64Encoder
import config

def generate_keys():
    """Generate Ed25519 key pair and save private key"""
    signing_key = SigningKey.generate()
    
    # Save private key
    with open(config.KEY_PATH, 'wb') as f:
        f.write(signing_key.encode())
    
    # Print public key in base64url format
    public_key_b64 = base64.urlsafe_b64encode(signing_key.verify_key.encode()).decode().rstrip('=')
    print(f"Keys generated successfully!")
    print(f"Private key saved to: {config.KEY_PATH}")
    print(f"Public key (base64url): {public_key_b64}")
    return public_key_b64

def init_database():
    """Initialize SQLite database with schema"""
    Path("db").mkdir(exist_ok=True)
    
    with open("db/schema.sql", 'r') as f:
        schema = f.read()
    
    conn = sqlite3.connect(config.DB_PATH)
    conn.executescript(schema)
    conn.close()
    print(f"Database initialized: {config.DB_PATH}")

def load_signing_key():
    """Load private signing key"""
    if not Path(config.KEY_PATH).exists():
        raise FileNotFoundError(f"Private key not found. Run --gen-keys first.")
    
    with open(config.KEY_PATH, 'rb') as f:
        return SigningKey(f.read())

def create_qr_item(product, serial, batch):
    """Create signed QR code item"""
    # Generate payload
    payload = {
        "v": 1,
        "p": product,
        "s": serial,
        "b": batch,
        "m": datetime.now().strftime("%Y-%m-%d"),
        "r": base64.urlsafe_b64encode(secrets.token_bytes(16)).decode().rstrip('=')
    }
    
    # Encode message
    message_json = json.dumps(payload, separators=(',', ':'))
    message_bytes = message_json.encode('utf-8')
    message_b64 = base64.urlsafe_b64encode(message_bytes).decode().rstrip('=')
    
    # Sign message
    signing_key = load_signing_key()
    signature = signing_key.sign(message_bytes).signature
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
    
    # Create QR content
    qr_content = f"{message_b64}.{signature_b64}"
    
    # Generate QR code PNG
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=config.QR_BOX_SIZE,
        border=config.QR_BORDER,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = f"sample_data/qr_{serial}.png"
    img.save(qr_path)
    
    # Store in database
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("""
        INSERT OR REPLACE INTO items 
        (serial, product, batch, mfg, nonce, message, signature, qr_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (serial, product, batch, payload["m"], payload["r"], 
          message_b64, signature_b64, qr_path))
    conn.commit()
    conn.close()
    
    print(f"QR code created: {qr_path}")
    print(f"Serial: {serial}")
    print(f"QR content: {qr_content[:50]}...")
    return qr_path

def main():
    parser = argparse.ArgumentParser(description="Anti-counterfeit QR generator")
    parser.add_argument("--gen-keys", action="store_true", help="Generate Ed25519 key pair")
    parser.add_argument("--init-db", action="store_true", help="Initialize database")
    parser.add_argument("--create", nargs=3, metavar=("PRODUCT", "SERIAL", "BATCH"), 
                       help="Create signed QR code")
    
    args = parser.parse_args()
    
    if args.gen_keys:
        generate_keys()
    elif args.init_db:
        init_database()
    elif args.create:
        product, serial, batch = args.create
        create_qr_item(product, serial, batch)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()