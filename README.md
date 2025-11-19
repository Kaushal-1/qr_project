# Anti-Counterfeit QR Code System

A complete prototype for generating and verifying signed QR codes with visual tamper detection.

## 🚀 Quick Setup (For New Users)

### Prerequisites
- Python 3.10+ installed
- Git installed
- ngrok account (free) for mobile testing

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/Kaushal-1/qr_project.git
cd qr_project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize System
```bash
# Generate cryptographic keys
python generator.py --gen-keys

# Initialize database
python generator.py --init-db

# Run database migration (adds new columns)
python migrate_db.py
```

### 3. Generate Demo QR Codes
```bash
# Create authentic product (will be in database)
python generator.py --create DEMO SERGenuine B001

# Create fake product (for testing unknown serial)
python generator.py --create DEMO SERFake B001

# Remove fake from database (so it shows as unknown)
python reset_demo.py
```

### 4. Start Server
```bash
python server.py
```
Server runs at: http://localhost:5000

### 5. Setup Mobile Access (ngrok)
```bash
# Install ngrok: https://ngrok.com/download
# In new terminal:
ngrok http 5000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

## 📱 Demo Instructions

### Test Scenarios

**1. Authentic Product (✅ AUTHENTIC)**
- Open `sample_data/qr_SERGenuine.png` on laptop screen
- On phone: Go to `https://your-ngrok-url/static/cam-scanner.html`
- Scan QR → Should show "AUTHENTIC"

**2. Unknown Product (❌ NOT AUTHENTIC)**
- Open `sample_data/qr_SERFake.png` on laptop screen
- Scan QR → Should show "NOT AUTHENTIC - unknown serial"

**3. Signature Tampering (❌ NOT AUTHENTIC)**
- Use manual entry in scanner
- Paste QR text and change any character
- Should show "NOT AUTHENTIC - invalid signature"

**4. Clone Detection (⚠️ FLAGGED)**
- Scan same QR 10+ times from different devices
- Should show "FLAGGED - SUSPICIOUS ACTIVITY"
- Check admin panel: `https://your-ngrok-url/admin`

### Admin Panel
View scan logs and flagged items: `https://your-ngrok-url/admin`

## 🛠️ System Architecture

### Files Overview
- `generator.py` - CLI for key generation and QR creation
- `server.py` - Flask API server with verification endpoints
- `static/cam-scanner.html` - Mobile camera scanner interface
- `image_compare.py` - Visual tamper detection (pHash + SSIM + ORB)
- `config.py` - System configuration and thresholds
- `migrate_db.py` - Database migration script
- `reset_demo.py` - Demo reset utility

### Security Layers
1. **Cryptographic**: Ed25519 digital signatures
2. **Registry**: Product database lookup
3. **Behavioral**: Clone detection via scan frequency
4. **Visual**: Image comparison for tamper detection

### QR Format
```
QR Content: BASE64(message).BASE64(signature)
Message: {"v":1,"p":"PRODUCT","s":"SERIAL","b":"BATCH","m":"DATE","r":"NONCE"}
```

## 🔧 Troubleshooting

**Camera not working?**
- Use manual entry in scanner
- Ensure HTTPS (ngrok) for camera access

**"Visual tampering" on genuine QR?**
- Normal for camera vs screen comparison
- System uses tolerant thresholds for demo

**Database errors?**
- Run: `python migrate_db.py`
- Reinitialize: `python generator.py --init-db`

**Import errors?**
- Ensure virtual environment is activated
- Run: `pip install -r requirements.txt`

## 📋 Production Notes

**Security Improvements for Production:**
- Move private key to HSM/KMS
- Use PostgreSQL instead of SQLite
- Add rate limiting and authentication
- Implement proper logging and monitoring
- Add HTTPS certificates

**Scaling Considerations:**
- Database indexing for large scan volumes
- CDN for static assets
- Load balancing for multiple servers
- Caching for frequently accessed data

## 🎯 Demo Success Criteria

✅ Generate signed QR codes  
✅ Local signature verification  
✅ Server-side registry lookup  
✅ Visual tamper detection  
✅ Clone detection via scan frequency  
✅ Mobile camera scanning  
✅ Admin audit interface  

**Perfect for demonstrating multi-layer anti-counterfeiting security!**