from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from PIL import Image, ImageEnhance, ImageFilter
import json
from datetime import datetime
import pytesseract
import cv2
import numpy as np
import sys
import platform
from googletrans import Translator

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Google Translator
translator = Translator()

# Configure Tesseract path based on operating system
def configure_tesseract():
    """Configure Tesseract path for different operating systems"""
    system = platform.system().lower()
    
    if system == "windows":
        # Common Windows installation paths
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\Lenovo\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', '')),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"✅ Tesseract found at: {path}")
                return True
                
    elif system == "darwin":  # macOS
        # Common macOS installation paths
        possible_paths = [
            "/usr/local/bin/tesseract",
            "/opt/homebrew/bin/tesseract",
            "/usr/bin/tesseract"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"✅ Tesseract found at: {path}")
                return True
                
    else:  # Linux
        # Common Linux installation paths
        possible_paths = [
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/snap/bin/tesseract"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"✅ Tesseract found at: {path}")
                return True
    
    print("⚠️  Tesseract not found in common locations")
    return False

def test_tesseract():
    """Test if Tesseract is working properly"""
    try:
        # Create a simple test image
        test_image = Image.new('RGB', (200, 50), color='white')
        # You can add text to this image or just test with the blank image
        
        # Try to run OCR
        result = pytesseract.image_to_string(test_image, config='--psm 6')
        print("✅ Tesseract is working correctly")
        return True
    except Exception as e:
        print(f"❌ Tesseract test failed: {str(e)}")
        return False

def test_google_translate():
    """Test if Google Translate is working properly"""
    try:
        # Test translation
        result = translator.translate("Hello", dest='bn')
        print(f"✅ Google Translate is working: 'Hello' -> '{result.text}'")
        return True
    except Exception as e:
        print(f"❌ Google Translate test failed: {str(e)}")
        return False

def translate_text_to_bengali(text):
    """Translate text to Bengali using Google Translate API"""
    try:
        if not text or text.strip() == '':
            return {
                'bengali_text': '',
                'original_text': text,
                'translation_success': False,
                'error': 'Empty text provided'
            }
        
        # Clean the text
        clean_text = text.strip()
        
        # Skip translation if text is too short or seems like OCR error
        if len(clean_text) < 2:
            return {
                'bengali_text': clean_text,
                'original_text': text,
                'translation_success': False,
                'error': 'Text too short to translate'
            }
        
        print(f"🌐 Translating text: '{clean_text[:50]}...' to Bengali")
        
        # Perform translation
        result = translator.translate(clean_text, dest='bn', src='auto')
        
        bengali_text = result.text
        detected_lang = result.src
        
        print(f"✅ Translation successful: '{clean_text[:30]}...' -> '{bengali_text[:30]}...'")
        print(f"🔍 Detected source language: {detected_lang}")
        
        return {
            'bengali_text': bengali_text,
            'original_text': text,
            'detected_language': detected_lang,
            'translation_success': True,
            'translator_service': 'Google Translate'
        }
        
    except Exception as e:
        print(f"❌ Translation failed: {str(e)}")
        return {
            'bengali_text': text,  # Return original text if translation fails
            'original_text': text,
            'translation_success': False,
            'error': str(e)
        }

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        original_filename = request.form.get('filename', file.filename)
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(original_filename):
            return jsonify({'error': 'Only JPG files are allowed'}), 400
        
        # Secure the filename
        filename = secure_filename(original_filename)
        
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"
        
        # Save file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get basic file info
        file_info = get_file_info(filepath, original_filename)
        
        # Extract text from image using OCR
        extracted_text = extract_text_from_image(filepath)
        file_info['extracted_text'] = extracted_text
        
        # Translate extracted text to Bengali
        translation_result = None
        if isinstance(extracted_text, dict) and extracted_text.get('best_text'):
            best_text = extracted_text['best_text']
            if best_text and not best_text.startswith('Error extracting text:'):
                print(f"🌐 Starting translation for extracted text...")
                translation_result = translate_text_to_bengali(best_text)
                extracted_text['translation'] = translation_result
        
        print(f"✅ File received and saved: {filepath}")
        print(f"📊 File info: {file_info}")
        
        if isinstance(extracted_text, dict) and extracted_text.get('best_text'):
            preview = extracted_text['best_text'][:100] + '...' if len(extracted_text['best_text']) > 100 else extracted_text['best_text']
            print(f"📝 Extracted text: {preview}")
            
            if translation_result and translation_result.get('translation_success'):
                bengali_preview = translation_result['bengali_text'][:100] + '...' if len(translation_result['bengali_text']) > 100 else translation_result['bengali_text']
                print(f"🌐 Bengali translation: {bengali_preview}")
        else:
            print(f"📝 Text extraction result: {extracted_text}")
        
        return jsonify({
            'message': 'File uploaded, text extracted, and translated successfully',
            'filename': filename,
            'original_name': original_filename,
            'path': filepath,
            'info': file_info,
            'extracted_text': extracted_text
        })
        
    except Exception as e:
        print(f"❌ Error processing file: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/translate', methods=['POST'])
def translate_text():
    """Endpoint to translate any text to Bengali"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data['text']
        target_language = data.get('target_language', 'bn')  # Default to Bengali
        
        if target_language == 'bn':
            translation_result = translate_text_to_bengali(text)
        else:
            # For other languages (future enhancement)
            try:
                result = translator.translate(text, dest=target_language, src='auto')
                translation_result = {
                    'translated_text': result.text,
                    'original_text': text,
                    'detected_language': result.src,
                    'target_language': target_language,
                    'translation_success': True,
                    'translator_service': 'Google Translate'
                }
            except Exception as e:
                translation_result = {
                    'translated_text': text,
                    'original_text': text,
                    'translation_success': False,
                    'error': str(e)
                }
        
        return jsonify({
            'message': 'Translation completed',
            'translation': translation_result
        })
        
    except Exception as e:
        print(f"❌ Translation error: {str(e)}")
        return jsonify({'error': f'Translation error: {str(e)}'}), 500

def extract_text_from_image(filepath):
    """Extract text from image using OCR with preprocessing"""
    try:
        print(f"🔍 Starting text extraction from: {filepath}")
        
        # Verify file exists and is readable
        if not os.path.exists(filepath):
            return create_error_result("File not found")
        
        # Try to read the image file
        try:
            # First try with PIL
            pil_img = Image.open(filepath)
            print(f"📷 Image loaded: {pil_img.size}, mode: {pil_img.mode}")
        except Exception as e:
            print(f"❌ Failed to load image with PIL: {e}")
            return create_error_result(f"Failed to load image: {str(e)}")
        
        # Convert to RGB if necessary
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
            print("🔄 Converted image to RGB")
        
        text_results = []
        
        # Method 1: Direct OCR on original image
        try:
            print("🔍 Trying direct OCR...")
            text1 = pytesseract.image_to_string(pil_img, config='--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ')
            text_results.append(("Original", text1.strip()))
            print(f"✅ Direct OCR result: {len(text1.strip())} characters")
        except Exception as e:
            print(f"❌ Direct OCR failed: {e}")
            text_results.append(("Original", f"Error: {str(e)}"))
        
        # Method 2: Grayscale conversion
        try:
            print("🔍 Trying grayscale OCR...")
            gray_img = pil_img.convert('L')
            text2 = pytesseract.image_to_string(gray_img, config='--psm 6')
            text_results.append(("Grayscale", text2.strip()))
            print(f"✅ Grayscale OCR result: {len(text2.strip())} characters")
        except Exception as e:
            print(f"❌ Grayscale OCR failed: {e}")
            text_results.append(("Grayscale", f"Error: {str(e)}"))
        
        # Method 3: Enhanced contrast and brightness
        try:
            print("🔍 Trying enhanced OCR...")
            enhanced_img = ImageEnhance.Contrast(pil_img).enhance(1.5)
            enhanced_img = ImageEnhance.Brightness(enhanced_img).enhance(1.1)
            text3 = pytesseract.image_to_string(enhanced_img, config='--psm 6')
            text_results.append(("Enhanced", text3.strip()))
            print(f"✅ Enhanced OCR result: {len(text3.strip())} characters")
        except Exception as e:
            print(f"❌ Enhanced OCR failed: {e}")
            text_results.append(("Enhanced", f"Error: {str(e)}"))
        
        # Method 4: OpenCV preprocessing
        try:
            print("🔍 Trying OpenCV preprocessed OCR...")
            # Convert PIL to OpenCV format
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            processed_img = preprocess_image_for_ocr(cv_img)
            
            # Convert back to PIL for OCR
            if len(processed_img.shape) == 2:  # Grayscale
                processed_pil = Image.fromarray(processed_img, mode='L')
            else:  # Color
                processed_pil = Image.fromarray(cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB))
            
            text4 = pytesseract.image_to_string(processed_pil, config='--psm 6')
            text_results.append(("Preprocessed", text4.strip()))
            print(f"✅ Preprocessed OCR result: {len(text4.strip())} characters")
        except Exception as e:
            print(f"❌ Preprocessed OCR failed: {e}")
            text_results.append(("Preprocessed", f"Error: {str(e)}"))
        
        # Method 5: Different PSM mode
        try:
            print("🔍 Trying PSM 3 OCR...")
            text5 = pytesseract.image_to_string(pil_img, config='--psm 3')
            text_results.append(("PSM 3", text5.strip()))
            print(f"✅ PSM 3 OCR result: {len(text5.strip())} characters")
        except Exception as e:
            print(f"❌ PSM 3 OCR failed: {e}")
            text_results.append(("PSM 3", f"Error: {str(e)}"))
        
        # Filter out error results and find the best one
        valid_results = [(method, text) for method, text in text_results if not text.startswith("Error:")]
        
        if not valid_results:
            error_messages = [text for _, text in text_results if text.startswith("Error:")]
            return create_error_result(f"All OCR methods failed. Last error: {error_messages[-1] if error_messages else 'Unknown error'}")
        
        # Find the result with the most meaningful text
        best_result = max(valid_results, key=lambda x: len(x[1].strip()))
        
        print(f"🔍 OCR Results Summary:")
        for method, text in text_results:
            status = "✅" if not text.startswith("Error:") else "❌"
            char_count = len(text.strip()) if not text.startswith("Error:") else 0
            print(f"  {status} {method}: {char_count} characters")
        
        print(f"🏆 Best result: {best_result[0]} with {len(best_result[1].strip())} characters")
        
        result = {
            'best_text': best_result[1],
            'method_used': best_result[0],
            'all_results': {method: text for method, text in valid_results},
            'confidence': get_text_confidence(best_result[1]),
            'total_methods_tried': len(text_results),
            'successful_methods': len(valid_results)
        }
        
        return result
        
    except Exception as e:
        print(f"❌ Critical error in text extraction: {e}")
        import traceback
        traceback.print_exc()
        return create_error_result(f"Critical error: {str(e)}")

def create_error_result(error_message):
    """Create a standardized error result"""
    return {
        'best_text': f'Error extracting text: {error_message}',
        'method_used': 'Error',
        'all_results': {},
        'confidence': 0,
        'total_methods_tried': 0,
        'successful_methods': 0,
        'error': error_message
    }

def preprocess_image_for_ocr(img):
    """Preprocess image to improve OCR accuracy"""
    try:
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up the image
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
        
        return processed
        
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        return img

def get_text_confidence(text):
    """Calculate a simple confidence score based on text characteristics"""
    if not text or len(text.strip()) == 0:
        return 0
    
    # Remove error messages from confidence calculation
    if text.startswith('Error extracting text:'):
        return 0
    
    # Simple heuristics for text quality
    score = 0
    clean_text = text.strip()
    
    # Length bonus (more text usually means better detection)
    if len(clean_text) > 50:
        score += 40
    elif len(clean_text) > 20:
        score += 25
    elif len(clean_text) > 5:
        score += 15
    
    # Word count bonus
    words = clean_text.split()
    if len(words) > 10:
        score += 30
    elif len(words) > 5:
        score += 20
    elif len(words) > 1:
        score += 10
    
    # Alphanumeric ratio (good text should have reasonable letters/numbers)
    if len(clean_text) > 0:
        alphanumeric = sum(c.isalnum() for c in clean_text)
        ratio = alphanumeric / len(clean_text)
        score += int(ratio * 30)  # Max 30 points for good character ratio
    
    return min(score, 100)  # Cap at 100%

def get_file_info(filepath, original_name):
    """Get basic information about the uploaded file"""
    try:
        # Open image with PIL to get dimensions
        with Image.open(filepath) as img:
            info = {
                'filename': original_name,
                'saved_path': filepath,
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height,
                'file_size_bytes': os.path.getsize(filepath),
                'upload_time': datetime.now().isoformat()
            }
            return info
    except Exception as e:
        print(f"Error getting file info: {e}")
        return {'error': str(e)}

@app.route('/extract_text/<filename>', methods=['POST'])
def extract_text_from_specific_file(filename):
    """Extract text from a specific uploaded file"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        extracted_text = extract_text_from_image(filepath)
        
        return jsonify({
            'filename': filename,
            'extracted_text': extracted_text,
            'message': 'Text extraction completed'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/files', methods=['GET'])
def list_files():
    """List all uploaded files"""
    try:
        files = []
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename.lower().endswith(('.jpg', '.jpeg')):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                files.append({
                    'filename': filename,
                    'path': filepath,
                    'size': os.path.getsize(filepath),
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                })
        
        return jsonify({'files': files, 'count': len(files)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/file/<filename>', methods=['GET'])
def get_file_details(filename):
    """Get details of a specific file"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        file_info = get_file_info(filepath, filename)
        
        return jsonify({
            'filename': filename,
            'info': file_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test', methods=['GET'])
def test_server():
    """Test endpoint to check if server, OCR, and translation are working"""
    tesseract_working = test_tesseract()
    translate_working = test_google_translate()
    
    return jsonify({
        'message': 'Server is running',
        'tesseract_configured': pytesseract.pytesseract.tesseract_cmd is not None,
        'tesseract_path': pytesseract.pytesseract.tesseract_cmd,
        'tesseract_working': tesseract_working,
        'google_translate_working': translate_working,
        'upload_folder': os.path.abspath(UPLOAD_FOLDER),
        'upload_folder_exists': os.path.exists(UPLOAD_FOLDER)
    })

if __name__ == '__main__':
    print("🚀 Starting Python Flask server with Google Translate...")
    print(f"📁 Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    
    # Configure and test Tesseract
    print("\n🔧 Configuring Tesseract OCR...")
    tesseract_configured = configure_tesseract()
    
    if tesseract_configured:
        tesseract_working = test_tesseract()
        if not tesseract_working:
            print("⚠️  Tesseract may not be working properly")
    else:
        print("❌ Tesseract not found! Please install Tesseract OCR:")
        print("   Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("   macOS: brew install tesseract")
        print("   Linux: sudo apt-get install tesseract-ocr")
    
    # Test Google Translate
    print("\n🌐 Testing Google Translate...")
    translate_working = test_google_translate()
    if not translate_working:
        print("⚠️  Google Translate may not be working properly")
        print("   Make sure you have internet connection")
        print("   Install googletrans: pip install googletrans==4.0.0-rc1")
    
    print(f"\n🌐 Server running on http://localhost:5000")
    print("\n📋 Available endpoints:")
    print("  POST /upload              - Upload JPG files, extract and translate text")
    print("  POST /translate           - Translate any text to Bengali")
    print("  GET  /files               - List uploaded files")
    print("  GET  /file/<filename>     - Get file details")
    print("  POST /extract_text/<filename> - Extract text from specific file")
    print("  GET  /test                - Test server, OCR, and translation status")
    
    app.run(debug=True, host='0.0.0.0', port=5000)