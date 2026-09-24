from flask import Flask, render_template, request, send_file, jsonify
import os
import base64
from pdf2docx import Converter
from werkzeug.utils import secure_filename
import fitz

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/blog/pdf-to-word')
def blog_pdf_to_word():
    return render_template('blog_pdf_to_word.html')

@app.route('/blog/sign-pdf-online')
def blog_sign_pdf():
    return render_template('blog_sign_pdf.html')

@app.route('/blog/best-pdf-tools')
def blog_best_tools():
    return render_template('blog_best_tools.html')

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

# Feature 2: PDF Preview
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
            max_pages = min(len(doc), 10)
            for i in range(max_pages):
                page = doc[i]
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
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

# Feature 3: Sign PDF
@app.route('/sign-pdf-drag', methods=['POST'])
def sign_pdf_drag():
    if 'pdf_file' not in request.files or 'sign_image' not in request.files:
        return jsonify({'success': False, 'error': 'PDF and Signature both required'})
    
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
        
        try:
            sign_pix = fitz.Pixmap(sign_path)
            actual_ratio = sign_pix.height / sign_pix.width
        except Exception:
            actual_ratio = 0.5
        
        doc = fitz.open(pdf_path)
        
        if page_num < 0 or page_num >= len(doc):
            page_num = 0
        
        page = doc[page_num]
        page_width = page.rect.width
        page_height = page.rect.height
        
        img_width = (width_percent / 100) * page_width
        img_height = img_width * actual_ratio
        
        x = (x_percent / 100) * page_width - (img_width / 2)
        y = (y_percent / 100) * page_height - (img_height / 2)
        
        rect = fitz.Rect(x, y, x + img_width, y + img_height)
        page.insert_image(rect, filename=sign_path, keep_proportion=True)
        
        signed_path = pdf_path.replace('.pdf', '_signed.pdf')
        doc.save(signed_path, garbage=3, deflate=True)
        doc.close()
        
        return jsonify({'success': True, 'download_file': os.path.basename(signed_path)})
    
    return jsonify({'success': False, 'error': 'File format check karein'})

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

@app.route('/sitemap.xml')
def sitemap():
    return '''<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://pdf-converter-r7sf.onrender.com/</loc><priority>1.0</priority></url>
        <url><loc>https://pdf-converter-r7sf.onrender.com/privacy</loc><priority>0.5</priority></url>
        <url><loc>https://pdf-converter-r7sf.onrender.com/about</loc><priority>0.5</priority></url>
        <url><loc>https://pdf-converter-r7sf.onrender.com/contact</loc><priority>0.5</priority></url>
        <url><loc>https://pdf-converter-r7sf.onrender.com/terms</loc><priority>0.5</priority></url>
        <url><loc>https://pdf-converter-r7sf.onrender.com/blog</loc><priority>0.8</priority></url>
        <url><loc>https://pdf-converter-r7sf.onrender.com/blog/pdf-to-word</loc><priority>0.7</priority></url>
        <url><loc>https://pdf-converter-r7sf.onrender.com/blog/sign-pdf-online</loc><priority>0.7</priority></url>
        <url><loc>https://pdf-converter-r7sf.onrender.com/blog/best-pdf-tools</loc><priority>0.7</priority></url>
    </urlset>''', 200, {'Content-Type': 'application/xml'}

if __name__ == '__main__':
    app.run(debug=True)