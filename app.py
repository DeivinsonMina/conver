from flask import Flask, request, send_from_directory, url_for, render_template_string
from PIL import Image
from fpdf import FPDF
import os
import subprocess
import tempfile
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = tempfile.gettempdir()
PDF_FOLDER = os.path.join(UPLOAD_FOLDER, "pdfs")
os.makedirs(PDF_FOLDER, exist_ok=True)

def image_to_pdf(image_path, pdf_path):
    image = Image.open(image_path)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(pdf_path, "PDF", resolution=100.0)

def text_to_pdf(text_path, pdf_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    with open(text_path, "r", encoding="utf-8") as f:
        for line in f:
            pdf.cell(200, 10, txt=line.strip(), ln=True)
    pdf.output(pdf_path)

def office_to_pdf(input_path, output_dir):
    subprocess.run([
        'libreoffice',
        '--headless',
        '--convert-to', 'pdf',
        input_path,
        '--outdir', output_dir
    ], check=True)

HTML_FORM = '''
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Convertidor a PDF</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 0; }
    .container { max-width: 400px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px #0001; padding: 30px 20px; }
    h2 { text-align: center; color: #333; }
    .file-input { display: flex; flex-direction: column; align-items: center; margin: 20px 0; }
    input[type="file"] { margin-bottom: 20px; }
    .btn { background: #007bff; color: #fff; border: none; padding: 12px 25px; border-radius: 5px; font-size: 16px; cursor: pointer; transition: background 0.2s; }
    .btn:hover { background: #0056b3; }
    .msg-error { color: #c00; background: #ffeaea; border: 1px solid #c00; padding: 10px; border-radius: 5px; margin-bottom: 15px; text-align: center; }
    .msg-success { color: #080; background: #eaffea; border: 1px solid #080; padding: 10px; border-radius: 5px; margin-bottom: 15px; text-align: center; }
    .download-link { display: block; text-align: center; margin-top: 20px; }
    @media (max-width: 500px) {
      .container { padding: 15px 5px; }
      .btn { width: 100%; }
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>Convertidor a PDF</h2>
    {% if error %}
      <div class="msg-error">{{ error }}</div>
    {% endif %}
    <form method="post" enctype="multipart/form-data" class="file-input">
      <input type="file" name="file" accept=".jpg,.jpeg,.png,.bmp,.txt,.doc,.docx,.xls,.xlsx,.ppt,.pptx" required>
      <button type="submit" class="btn">Convertir a PDF</button>
    </form>
    {% if download_url %}
      <div class="msg-success">¡Conversión exitosa!</div>
      <div class="download-link">
        <a href="{{ download_url }}" class="btn" download>Descargar PDF</a>
      </div>
    {% endif %}
    <p style="text-align:center; color:#888; font-size:13px; margin-top:30px;">
      Soporta imágenes, texto y documentos de Office.<br>
      <b>Tu archivo PDF se descargará automáticamente.</b>
    </p>
  </div>
</body>
</html>
'''

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    download_url = None
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            error = "No se subió ningún archivo."
        else:
            filename = file.filename
            ext = os.path.splitext(filename)[1].lower()
            unique_id = str(uuid.uuid4())
            input_path = os.path.join(UPLOAD_FOLDER, unique_id + "_" + filename)
            file.save(input_path)
            base_name = os.path.splitext(filename)[0]
            pdf_name = unique_id + "_" + base_name + ".pdf"
            pdf_path = os.path.join(PDF_FOLDER, pdf_name)
            try:
                if ext in [".jpg", ".jpeg", ".png", ".bmp"]:
                    image_to_pdf(input_path, pdf_path)
                elif ext == ".txt":
                    text_to_pdf(input_path, pdf_path)
                elif ext in [".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]:
                    office_to_pdf(input_path, PDF_FOLDER)
                    # LibreOffice nombra el PDF igual que el archivo original
                    libre_pdf = os.path.join(PDF_FOLDER, base_name + ".pdf")
                    if os.path.exists(libre_pdf):
                        os.rename(libre_pdf, pdf_path)
                else:
                    error = "Tipo de archivo no soportado."
            except Exception as e:
                error = f"Error: {e}"
            if not error:
                download_url = url_for("download_file", filename=os.path.basename(pdf_path))
    return render_template_string(HTML_FORM, error=error, download_url=download_url)

@app.route("/pdfs/<filename>")
def download_file(filename):
    return send_from_directory(PDF_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)