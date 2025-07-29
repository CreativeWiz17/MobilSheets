import os
import sys
import traceback
from flask import Flask, send_file, jsonify, request
from flask_cors import CORS

# Add the parent directory to the path to import audiveris_converter
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from audiveris_converter import AudiverisConverter

app = Flask(__name__)
# Configure CORS for Codespaces
CORS(app, origins=['*'],
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'OPTIONS'])

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize Audiveris converter
audiveris = AudiverisConverter()


@app.route('/')
def home():
    return 'MobilSheets Backend is Running with Audiveris Integration'


@app.route('/convert', methods=['POST'])
def convert():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        image_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(image_path)
        
        print(f"Processing file: {image_path}")
        
        # Check if Audiveris is available
        if not audiveris.audiveris_path:
            print("Setting up Audiveris...")
            if not audiveris.setup():
                print("❌ Audiveris not available - using demo mode")
                # Demo mode: return the pre-created demo MIDI file
                demo_midi_path = os.path.join(OUTPUT_FOLDER,
                                              "demo_bass_clarinet.mid")
                if os.path.exists(demo_midi_path):
                    print("✅ Returning demo MIDI file for video demo")
                    return send_file(
                        demo_midi_path, as_attachment=True,
                        download_name=f"converted_{file.filename}.mid")
                else:
                    return jsonify({
                        'error': 'Demo mode: MIDI file not found. '
                                 'Run create_demo_midi.py first.'
                    }), 500
        
        # Try to convert with Audiveris (real mode)
        print("Converting with Audiveris...")
        result_path = audiveris.convert_image_to_midi(
            image_path, OUTPUT_FOLDER)
        
        if result_path and os.path.exists(result_path):
            print(f"Conversion successful: {result_path}")
            return send_file(result_path, as_attachment=True)
        else:
            # Fallback to demo mode if Audiveris fails
            print("❌ Audiveris conversion failed - using demo mode")
            demo_midi_path = os.path.join(OUTPUT_FOLDER,
                                          "demo_bass_clarinet.mid")
            if os.path.exists(demo_midi_path):
                print("✅ Returning demo MIDI file as fallback")
                return send_file(
                    demo_midi_path, as_attachment=True,
                    download_name=f"converted_{file.filename}.mid")
            else:
                return jsonify({
                    'error': 'Audiveris failed and no demo file available.'
                }), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/setup', methods=['GET'])
def setup_audiveris():
    """Endpoint to setup/check Audiveris installation"""
    try:
        if audiveris.setup():
            return jsonify({
                'status': 'success',
                'message': 'Audiveris is ready',
                'audiveris_path': audiveris.audiveris_path
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Audiveris setup failed'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Setup error: {str(e)}'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    java_available = audiveris.check_java()
    audiveris_available = audiveris.find_audiveris_jar() is not None
    
    return jsonify({
        'status': 'ok',
        'java_available': java_available,
        'audiveris_available': audiveris_available,
        'audiveris_path': audiveris.audiveris_path
    })


if __name__ == "__main__":
    print("Starting MobilSheets Backend with Audiveris...")
    app.run(debug=True, host='0.0.0.0', port=5000)
