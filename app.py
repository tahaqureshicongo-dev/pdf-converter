from flask import Flask, render_template, request, send_file, jsonify
import os
import base64
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

# Feature 2: PDF Preview (pages images mein convert karke bhejna)
@app.route('/preview-pdf', methods=['POST'])
def preview_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        file = request.files['file']
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(pdf_path)
            
            doc = fitz.open(pdf_path)
            pages_data = []
            max_pages = min(len(doc), 10) # Sirf 10 pages preview ke liye (memory bachane ke liye)
            for i in range(max_pages):
                page = doc[i]
                # Resolution 0.8x (memory aur speed ka balance)
                pix = page.get_pixmap(matrix=fitz.Matrix(0.8, 0.8))
                img_bytes = pix.tobytes("png")
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                pages_data.append({
                    'page_num': i + 1,
                    'image': f"data:image/png;base64,{img_base64}",
                    'width': pix.width,
                    'height': pix.height
                })
            total_pages = len(doc)
            doc.close()
            return jsonify({'success': True, 'pages': pages_data, 'pdf_filename': filename, 'total_pages': total_pages})
        return jsonify({'success': False, 'error': 'Only PDF allowed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Feature 3: Drag & Drop Sign PDF
@app.route('/sign-pdf-drag', methods=['POST'])
def sign_pdf_drag():
    if 'pdf_file' not in request.files or 'sign_image' not in request.files:
        return jsonify({'success': False, 'error': 'PDF aur Signature dono upload karein'})
    
    pdf_file = request.files['pdf_file']
    sign_image = request.files['sign_image']
    
    page_num = int(request.form.get('page_num', 1)) - 1
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
        
        if page_num < 0 or page_num >= len(doc):
            page_num = 0
        
        page = doc[page_num]
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