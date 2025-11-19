#!/usr/bin/env python3
import json
import sqlite3
import base64
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import config
import image_compare
import base64

app = Flask(__name__)

def load_public_key():
    """Load public key from config or private key file"""
    if config.PUBLIC_KEY_B64:
        # Use environment override
        key_bytes = base64.urlsafe_b64decode(config.PUBLIC_KEY_B64 + '==')
        return VerifyKey(key_bytes)
    
    # Extract from private key file
    if not Path(config.KEY_PATH).exists():
        raise FileNotFoundError("No public key found. Set PUBLIC_KEY_B64 or generate keys.")
    
    from nacl.signing import SigningKey
    with open(config.KEY_PATH, 'rb') as f:
        signing_key = SigningKey(f.read())
    return signing_key.verify_key

@app.route('/verify', methods=['POST'])
def verify_qr():
    """Verify QR code signature and record scan"""
    try:
        data = request.get_json()
        if not data or 'qr' not in data:
            return jsonify({"ok": False, "error": "bad_qr", "detail": "Missing QR data"})
        
        qr_content = data['qr']
        device = data.get('device', 'unknown')
        meta = json.dumps(data.get('meta', {}))
        
        # Parse MSG.SIG format
        if '.' not in qr_content:
            return jsonify({"ok": False, "error": "bad_qr", "detail": "Invalid QR format"})
        
        message_b64, signature_b64 = qr_content.split('.', 1)
        
        # Decode message and signature
        try:
            message_bytes = base64.urlsafe_b64decode(message_b64 + '==')
            signature_bytes = base64.urlsafe_b64decode(signature_b64 + '==')
        except Exception as e:
            return jsonify({"ok": False, "error": "bad_qr", "detail": f"Base64 decode error: {str(e)}"})
        
        # Verify signature
        try:
            public_key = load_public_key()
            public_key.verify(message_bytes, signature_bytes)
        except BadSignatureError:
            return jsonify({"ok": False, "error": "invalid_signature", "detail": "Signature verification failed"})
        except Exception as e:
            return jsonify({"ok": False, "error": "verify_error", "detail": str(e)})
        
        # Parse payload
        try:
            payload = json.loads(message_bytes.decode('utf-8'))
            serial = payload.get('s')
            if not serial:
                return jsonify({"ok": False, "error": "bad_qr", "detail": "Missing serial in payload"})
        except Exception as e:
            return jsonify({"ok": False, "error": "bad_qr", "detail": f"Payload parse error: {str(e)}"})
        
        # Check database for serial
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM items WHERE serial = ?", (serial,))
        item = cursor.fetchone()
        
        if not item:
            conn.close()
            return jsonify({"ok": False, "error": "unknown_serial", "detail": f"Serial {serial} not found"})
        
        # Image comparison (if image provided)
        similarity = 1.0
        visual_tamper = False
        
        # Check for uploaded image (multipart or base64 in meta)
        uploaded_image = None
        if 'image' in request.files and request.files['image']:
            # Multipart upload
            uploaded_image = request.files['image'].read()
        elif 'meta' in data and isinstance(data['meta'], dict) and 'image' in data['meta']:
            # Base64 in meta
            try:
                image_b64 = data['meta']['image']
                if image_b64.startswith('data:image/'):
                    # Remove data URL prefix
                    image_b64 = image_b64.split(',', 1)[1]
                uploaded_image = base64.b64decode(image_b64)
            except Exception as e:
                print(f"Base64 image decode error: {e}")
        
        if uploaded_image:
            # Get canonical image path from database
            canonical_path = item[7]  # qr_path column
            if canonical_path and Path(canonical_path).exists():
                comparison_result = image_compare.compare_images(canonical_path, uploaded_image)
                similarity = comparison_result['similarity']
                visual_tamper = comparison_result['visual_tamper']
        
        # Record scan with detailed image comparison results
        phash_distance = None
        orb_ratio = None
        if uploaded_image:
            phash_distance = comparison_result.get('phash_distance')
            orb_ratio = comparison_result.get('orb_ratio')
        
        cursor.execute("""
            INSERT INTO scans (serial, device, meta, similarity, visual_flag, phash_distance, orb_ratio)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (serial, device, meta, similarity, 1 if visual_tamper else 0, phash_distance, orb_ratio))
        
        # Count total scans
        cursor.execute("SELECT COUNT(*) FROM scans WHERE serial = ?", (serial,))
        scan_count = cursor.fetchone()[0]
        
        # Check if flagged
        flagged = scan_count > config.SCAN_FLAG_THRESHOLD
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "ok": True,
            "serial": serial,
            "scans": scan_count,
            "flagged": flagged,
            "payload": payload,
            "visual_tamper": visual_tamper,
            "similarity": similarity
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": "server_error", "detail": str(e)})

@app.route('/admin')
def admin_panel():
    """Admin panel showing recent scans and flagged items"""
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    # Recent scans
    cursor.execute("""
        SELECT s.id, s.serial, s.ts, s.device, s.similarity, s.visual_flag,
               i.product, i.batch
        FROM scans s
        LEFT JOIN items i ON s.serial = i.serial
        ORDER BY s.ts DESC
        LIMIT 50
    """)
    recent_scans = cursor.fetchall()
    
    # Flagged items (high scan count)
    cursor.execute("""
        SELECT s.serial, COUNT(*) as scan_count, 
               MAX(s.ts) as last_scan,
               i.product, i.batch
        FROM scans s
        LEFT JOIN items i ON s.serial = i.serial
        GROUP BY s.serial
        HAVING scan_count > ?
        ORDER BY scan_count DESC
    """, (config.SCAN_FLAG_THRESHOLD,))
    flagged_items = cursor.fetchall()
    
    conn.close()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Anti-Counterfeit Admin Panel</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .flagged { background-color: #ffe6e6; }
            .visual-tamper { background-color: #fff2e6; }
            h2 { color: #333; }
        </style>
    </head>
    <body>
        <h1>Anti-Counterfeit Admin Panel</h1>
        
        <h2>Flagged Items (High Scan Count)</h2>
        <table>
            <tr>
                <th>Serial</th>
                <th>Product</th>
                <th>Batch</th>
                <th>Scan Count</th>
                <th>Last Scan</th>
            </tr>
            {% for item in flagged_items %}
            <tr class="flagged">
                <td>{{ item[0] }}</td>
                <td>{{ item[3] or 'N/A' }}</td>
                <td>{{ item[4] or 'N/A' }}</td>
                <td>{{ item[1] }}</td>
                <td>{{ item[2] }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <h2>Recent Scans</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Serial</th>
                <th>Product</th>
                <th>Batch</th>
                <th>Device</th>
                <th>Timestamp</th>
                <th>Similarity</th>
                <th>Visual Tamper</th>
            </tr>
            {% for scan in recent_scans %}
            <tr class="{% if scan[5] %}visual-tamper{% endif %}">
                <td>{{ scan[0] }}</td>
                <td>{{ scan[1] }}</td>
                <td>{{ scan[6] or 'N/A' }}</td>
                <td>{{ scan[7] or 'N/A' }}</td>
                <td>{{ scan[3] }}</td>
                <td>{{ scan[2] }}</td>
                <td>{{ "%.3f"|format(scan[4]) }}</td>
                <td>{{ "Yes" if scan[5] else "No" }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    
    return render_template_string(html, recent_scans=recent_scans, flagged_items=flagged_items)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/')
def index():
    """Root route with basic info"""
    return jsonify({
        "service": "Anti-Counterfeit QR Verification",
        "endpoints": ["/verify", "/admin", "/static/*"],
        "status": "running"
    })

if __name__ == '__main__':
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.DEBUG)