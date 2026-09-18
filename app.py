from flask import Flask, render_template, request, send_file
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
        return 'No file uploaded', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400
    
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_path)
        
        docx_path = pdf_path.replace('.pdf', '.docx')
        cv = Converter(pdf_path)
        cv.convert(docx_path)
        cv.close()
        
        return send_file(docx_path, as_attachment=True)
    
    return 'Only PDF files allowed', 400

# Feature 2: PDF par Text/Sign Add Karein
@app.route('/edit-pdf', methods=['POST'])
def edit_pdf():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['file']
    text_to_add = request.form.get('text_to_add', '')
    
    if file.filename == '':
        return 'No file selected', 400
    
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_path)
        
        # PDF open karein aur text add karein
        doc = fitz.open(pdf_path)
        page = doc[0]  # Pehle page par
        # Position: X=50, Y=50 (Top-Left corner), Color: Red, Size: 12
        page.insert_text((50, 50), text_to_add, fontsize=12, color=(1, 0, 0))
        
        edited_path = pdf_path.replace('.pdf', '_edited.pdf')
        doc.save(edited_path)
        doc.close()
        
        return send_file(edited_path, as_attachment=True)
    
    return 'Only PDF files allowed', 400

if __name__ == '__main__':
    app.run(debug=True)
    