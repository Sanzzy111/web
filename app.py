from flask import Flask, request, send_file, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
from docx import Document
from pdf2docx import Converter
from PIL import Image
from fpdf import FPDF
import fitz  # PyMuPDF

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    # Redirect the root URL to /home
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/tools', methods=['GET', 'POST'])
def convert_file():
    if request.method == 'POST':
        # Get the uploaded file and other form data
        file = request.files['file']
        from_format = request.form['from']
        to_format = request.form['to']

        # Create a secure filename and save the uploaded file
        filename = secure_filename(file.filename)
        base_filename = filename.rsplit('.', 1)[0]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Define the converted file's name and path
        converted_filename = f"{base_filename}_converted.{to_format}"
        converted_path = os.path.join(app.config['UPLOAD_FOLDER'], converted_filename)

        try:
            # Perform conversion based on selected formats
            if from_format == 'pdf' and to_format == 'docx':
                cv = Converter(file_path)
                cv.convert(converted_path, start=0, end=None)
                cv.close()

            elif from_format == 'docx' and to_format == 'pdf':
                doc = Document(file_path)
                text = "\n".join([p.text for p in doc.paragraphs])
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("Arial", size=12)
                for line in text.split('\n'):
                    pdf.multi_cell(0, 10, line)
                pdf.output(converted_path)

            elif from_format in ['jpg', 'png'] and to_format in ['jpg', 'png']:
                img = Image.open(file_path)
                img = img.convert('RGB')
                img.save(converted_path)

            elif from_format == 'txt' and to_format == 'pdf':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for line in text.split('\n'):
                    pdf.multi_cell(0, 10, line)
                pdf.output(converted_path)

            elif from_format == 'pdf' and to_format == 'txt':
                doc = fitz.open(file_path)
                text = "".join([page.get_text() for page in doc])
                with open(converted_path, 'w', encoding='utf-8') as f:
                    f.write(text)

            else:
                with open(file_path, 'rb') as f_in:
                    with open(converted_path, 'wb') as f_out:
                        f_out.write(f_in.read())

            # Return the converted file to the user
            return send_file(converted_path, as_attachment=True)

        except Exception as e:
            return f"Error during conversion: {str(e)}"
    
    # Render the conversion page for GET requests
    return render_template('tools.html')

@app.route('/create-text', methods=['POST'])
def create_text():
    content = request.form['text']
    filename = secure_filename(request.form['filename'])
    ext = request.form['extension']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}.{ext}")

    try:
        if ext == 'txt' or ext in ['py', 'js', 'html', 'css', 'cpp', 'java', 'json']:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        else:
            return f"Unsupported extension: .{ext}"

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return f"Error creating file: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

