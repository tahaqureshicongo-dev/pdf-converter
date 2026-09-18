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

# Feature 3: PDF par Sign/Stamp Lagayein (NAYA FEATURE)
@app.route('/sign-pdf', methods=['POST'])
def sign_pdf():
    if 'pdf_file' not in request.files or 'sign_image' not in request.files:
        return jsonify({'success': False, 'error': 'PDF aur Signature dono upload karein'})
    
    pdf_file = request.files['pdf_file']
    sign_image = request.files['sign_image']
    page_num = int(request.form.get('page_num', 1)) - 1 # User 1 se start karta hai, Python 0 se
    position = request.form.get('position', 'bottom-right')
    
    if pdf_file.filename.endswith('.pdf') and sign_image.filename.endswith(('.png', '.jpg', '.jpeg')):
        pdf_filename = secure_filename(pdf_file.filename)
        sign_filename = secure_filename(sign_image.filename)
        
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        sign_path = os.path.join(app.config['UPLOAD_FOLDER'], sign_filename)
        
        pdf_file.save(pdf_path)
        sign_image.save(sign_path)
        
        doc = fitz.open(pdf_path)
        
        # Check karein ki page number valid hai ya nahi
        if page_num >= len(doc):
            page_num = len(doc) - 1
            
        page = doc[page_num]
        page_width = page.rect.width
        page_height = page.rect.height
        
        # Position ke hisaab se image ka size aur jagah set karein
        img_width, img_height = 150, 80 # Signature ka size
        
        if position == 'bottom-right':
            rect = fitz.Rect(page_width - img_width - 20, page_height - img_height - 20, page_width - 20, page_height - 20)
        elif position == 'bottom-left':
            rect = fitz.Rect(20, page_height - img_height - 20, img_width + 20, page_height - 20)
        elif position == 'top-right':
            rect = fitz.Rect(page_width - img_width - 20, 20, page_width - 20, img_height + 20)
        else: # center
            rect = fitz.Rect((page_width - img_width)/2, (page_height - img_height)/2, (page_width + img_width)/2, (page_height + img_height)/2)
            
        page.insert_image(rect, filename=sign_path)
        
        signed_path = pdf_path.replace('.pdf', '_signed.pdf')
        doc.save(signed_path)
        doc.close()
        
        return jsonify({'success': True, 'download_file': os.path.basename(signed_path)})
    
    return jsonify({'success': False, 'error': 'PDF aur Image (PNG/JPG) format check karein'})

# Download Route
@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)