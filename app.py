from flask import Flask, request, render_template, send_file, jsonify
from gtts import gTTS
from pdf2image import convert_from_path
import pytesseract
import os
import pdfplumber
from pathlib import Path

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def pdf_to_mp3(file_path, language='en'):
    text = ""
    # Extract text using pdfplumber
    with pdfplumber.PDF(open(file_path, 'rb')) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    
    # If text is empty, use OCR
    if not text.strip():
        images = convert_from_path(file_path)
        for image in images:
            text += pytesseract.image_to_string(image, lang=language)
    
    text = text.replace('\n', ' ')
    if not text.strip():
        return None  # No text extracted
    
    # Convert text to speech
    file_name = Path(file_path).stem
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_name}.mp3")
    my_audio = gTTS(text=text, lang=language, slow=False)
    my_audio.save(output_path)
    return output_path

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    language = request.form.get('language', 'en')

    if file and allowed_file(file.filename):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        result = pdf_to_mp3(file_path, language=language)
        if result:
            return jsonify({"success": True, "file_url": f"/download/{Path(result).name}"})
        else:
            return jsonify({"error": "Failed to extract text from the PDF"}), 500
    return jsonify({"error": "Invalid file type. Only PDFs are allowed."}), 400

@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Update for your system
    app.run(debug=True)
