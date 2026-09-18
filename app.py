from flask import Flask, render_template, request, send_file, jsonify
import os
from pdf2docx import Converter
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

# Feature 1: PDF to Word
@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    file = request.files['file']
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_path)
        docx_path = pdf_path.replace('.pdf', '.docx')
        cv = Converter(pdf_path)
        cv.convert(docx_path)
        cv.close()
        return jsonify({'success': True, 'download_file': os.path.basename(docx_path)})
    return jsonify({'success': False, 'error': 'Only PDF files allowed'})

# Feature 2: Drag & Drop Sign PDF
@app.route('/sign-pdf-drag', methods=['POST'])
def sign_pdf_drag():
    if 'pdf_file' not in request.files or 'sign_image' not in request.files:
        return jsonify({'success': False, 'error': 'PDF aur Signature dono upload karein'})
    
    pdf_file = request.files['pdf_file']
    sign_image = request.files['sign_image']
    
    x_percent = float(request.form.get('x_percent', 50))
    y_percent = float(request.form.get('y_percent', 50))
    width_percent = float(request.form.get('width_percent', 20))
    
    if pdf_file.filename.endswith('.pdf') and sign_image.filename.endswith(('.png', '.jpg', '.jpeg')):
        pdf_filename = secure_filename(pdf_file.filename)
        sign_filename = secure_filename(sign_image.filename)
        
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        sign_path = os.path.join(app.config['UPLOAD_FOLDER'], sign_filename)
        
        pdf_file.save(pdf_path)
        sign_image.save(sign_path)
        
        doc = fitz.open(pdf_path)
        page = doc[0]
        page_width = page.rect.width
        page_height = page.rect.height
        
        img_width = (width_percent / 100) * page_width
        img_height = img_width * 0.4
        
        x = (x_percent / 100) * page_width - (img_width / 2)
        y = (y_percent / 100) * page_height - (img_height / 2)
        
        rect = fitz.Rect(x, y, x + img_width, y + img_height)
        page.insert_image(rect, filename=sign_path)
        
        signed_path = pdf_path.replace('.pdf', '_signed.pdf')
        doc.save(signed_path)
        doc.close()
        
        return jsonify({'success': True, 'download_file': os.path.basename(signed_path)})
    
    return jsonify({'success': False, 'error': 'File format check karein'})

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)