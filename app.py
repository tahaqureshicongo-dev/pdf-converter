from flask import Flask, render_template, request, send_file, jsonify
import os
from pdf2docx import Converter
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from docx2pdf import convert as docx_to_pdf

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
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_path)
        
        docx_path = pdf_path.replace('.pdf', '.docx')
        cv = Converter(pdf_path)
        cv.convert(docx_path)
        cv.close()
        
        # Return JSON with the download filename
        return jsonify({'success': True, 'download_file': os.path.basename(docx_path)})
    
    return jsonify({'success': False, 'error': 'Only PDF files allowed'})

# Feature 2: PDF par Text/Sign Add Karein
@app.route('/edit-pdf', methods=['POST'])
def edit_pdf():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    text_to_add = request.form.get('text_to_add', '')
    position = request.form.get('position', 'top-left')
    
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_path)
        
        doc = fitz.open(pdf_path)
        page = doc[0]
        
        if position == 'top-left':
            x, y = 50, 50
        elif position == 'top-right':
            x, y = 400, 50
        elif position == 'center':
            x, y = 250, 400
        elif position == 'bottom-left':
            x, y = 50, 750
        else:
            x, y = 50, 50
            
        page.insert_text((x, y), text_to_add, fontsize=14, color=(1, 0, 0))
        
        edited_path = pdf_path.replace('.pdf', '_edited.pdf')
        doc.save(edited_path)
        doc.close()
        
        return jsonify({'success': True, 'download_file': os.path.basename(edited_path)})
    
    return jsonify({'success': False, 'error': 'Only PDF files allowed'})

# Naya Route: File Download karne ke liye
@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)