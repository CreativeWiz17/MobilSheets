#!/usr/bin/env python3
"""
MobilSheets - Unified Sheet Music to MIDI Converter
A single Flask application that serves both frontend and backend functionality.

This application:
1. Serves the beautiful frontend UI from frontend/index.html
2. Handles file uploads and sheet music to MIDI conversion
3. Uses Audiveris for real conversion or demo mode for videos
4. Perfect for creating bass clarinet demonstration videos!

Usage:
    python mobilsheets_app.py

Then open: http://localhost:5000
"""

import os
import sys
import logging
import subprocess
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from pathlib import Path
import tempfile

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import the audiveris converter
try:
    from audiveris_converter import AudiverisConverter
    AUDIVERIS_AVAILABLE = True
except ImportError:
    AUDIVERIS_AVAILABLE = False
    print("⚠️  Audiveris converter not available - running in demo mode")

app = Flask(__name__, 
            static_folder='frontend/static',
            template_folder='frontend')

# Configure CORS for development
CORS(app, origins=['*'])

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create necessary directories
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'backend/output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize Audiveris converter if available
audiveris = None
if AUDIVERIS_AVAILABLE:
    try:
        audiveris = AudiverisConverter()
        logger.info("✅ Audiveris converter initialized")
    except Exception as e:
        logger.warning(f"⚠️  Could not initialize Audiveris: {e}")
        audiveris = None

@app.route('/')
def index():
    """Serve the main frontend page"""
    return render_template('index.html')

@app.route('/scripts/<path:filename>')
def serve_scripts(filename):
    """Serve JavaScript files"""
    return send_from_directory('frontend/scripts', filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, images, audio)"""
    return send_from_directory('frontend/static', filename)

@app.route('/convert', methods=['POST'])
def convert_sheet_music():
    """Handle sheet music to MIDI conversion"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        logger.info(f"Processing file: {file.filename}")
        
        # Basic file validation
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
            logger.warning(f"❌ Unsupported file type: {file.filename}")
            return jsonify({
                'error': 'Please upload an image file (PNG, JPG, JPEG, TIFF, or BMP) containing sheet music.'
            }), 400
        
        # Save uploaded file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        
        # Try to convert with Audiveris
        global audiveris
        
        # Initialize Audiveris if not already done
        if not audiveris:
            try:
                audiveris = AudiverisConverter()
                if not audiveris.setup():
                    logger.warning("Audiveris setup failed")
            except Exception as e:
                logger.warning(f"Could not initialize Audiveris: {e}")
        
        midi_path = None
        
        if audiveris:
            logger.info("🎼 Converting with Audiveris...")
            try:
                # Force setup if needed
                if not audiveris.audiveris_path:
                    audiveris.setup()
                
                midi_path = audiveris.convert_image_to_midi(file_path, OUTPUT_FOLDER)
                if midi_path and os.path.exists(midi_path):
                    logger.info(f"✅ Audiveris conversion successful: {midi_path}")
                else:
                    logger.error("❌ Audiveris could not detect sheet music in this image")
                    return jsonify({
                        'error': 'Could not detect readable sheet music in this image. Please ensure the image contains clear musical notation with staff lines and notes.'
                    }), 400
            except Exception as e:
                logger.error(f"❌ Audiveris error: {e}")
                return jsonify({'error': f'Transcription failed: {str(e)}'}), 500
        else:
            logger.error("❌ Audiveris not available")
            return jsonify({'error': 'Music transcription service not available'}), 500
        
        # Return the MIDI file
        if midi_path and os.path.exists(midi_path):
            return send_file(
                midi_path, 
                as_attachment=True,
                download_name=f"converted_{Path(file.filename).stem}.mid",
                mimetype='audio/midi'
            )
        else:
            return jsonify({'error': 'Conversion failed'}), 500
            
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    java_available = check_java()
    audiveris_available = audiveris is not None and audiveris.audiveris_path is not None
    
    return jsonify({
        'status': 'ok',
        'java_available': java_available,
        'audiveris_available': audiveris_available,
        'demo_mode': not audiveris_available,
        'message': 'MobilSheets is ready for your bass clarinet demo!' if not audiveris_available else 'Ready for real sheet music conversion!'
    })

def check_java():
    """Check if Java is available"""
    try:
        result = subprocess.run(['java', '-version'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

if __name__ == '__main__':
    print("🎼 MobilSheets - Sheet Music to MIDI Converter")
    print("=" * 50)
    print("🎷 Real sheet music transcription for your videos!")
    print()
    
    # Check system status
    if check_java():
        print("✅ Java is available")
    else:
        print("⚠️  Java not found - transcription may not work")
    
    # Try to initialize Audiveris
    if not audiveris:
        try:
            audiveris = AudiverisConverter()
            if audiveris.setup():
                print("✅ Audiveris is ready for real transcription")
            else:
                print("⚠️  Audiveris setup incomplete")
        except Exception as e:
            print(f"⚠️  Audiveris initialization failed: {e}")
    else:
        print("✅ Audiveris is ready for real transcription")
    
    print()
    print("🚀 Starting server...")
    print("🌐 Open your browser to: http://localhost:5000")
    print("📱 Upload your testimage.png and get real transcription!")
    print("� No fake results - only real music transcription!")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
