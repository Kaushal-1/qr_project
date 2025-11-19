# Anti-Counterfeit QR Code System

A complete prototype for generating and verifying signed QR codes with visual tamper detection.

## Quick Start

### 1. Setup Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Initialize System
```bash
python generator.py --init  # Creates keys and database
```

### 3. Generate Sample QR Codes
```bash
python generator.py --product "DEMO" --serial "SERGenuine" --batch "B001"
python generator.py --product "DEMO" --serial "SERFake" --batch "B001"
```

### 4. Start Server
```bash
python server.py
```

### 5. Expose via ngrok (for mobile testing)
```bash
ngrok http 5000
```

### 6. Demo Steps
1. Open generated QR PNG on laptop screen
2. Navigate to `https://your-ngrok-url.ngrok.io/static/cam-scanner.html` on phone
3. Scan QR code with phone camera
4. View results and admin panel at `https://your-ngrok-url.ngrok.io/admin`

## File Structure
- `generator.py` - CLI for key generation and QR creation
- `server.py` - Flask API server with verification endpoints
- `static/cam-scanner.html` - Mobile camera scanner interface
- `image_compare.py` - Visual tamper detection functions
- `config.py` - System configuration and thresholds

## Security Features
- Ed25519 digital signatures
- Visual tamper detection (pHash + SSIM)
- Clone detection via scan frequency analysis
- Multi-layer verification (client + server)

## Demo Scenarios
1. **Authentic Scan** - Valid QR shows "AUTHENTIC"
2. **Visual Tampering** - Edited image detected even if QR bits unchanged
3. **Signature Tampering** - Modified QR data fails signature verification
4. **Clone Detection** - Multiple scans from different devices flagged