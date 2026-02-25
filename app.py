import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import qrcode
from qrcode.constants import ERROR_CORRECT_H
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg",
    "pdf",
    "mp3", "wav",
    "mp4"
}

QR_FOLDER = "qr_codes"
os.makedirs(QR_FOLDER, exist_ok=True)

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_qr(data, output_path):
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)


@app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "QR Backend running successfully 🚀"
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/upload", methods=["POST"])
def upload_file():

    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": "File type not allowed",
            "allowed_types": list(ALLOWED_EXTENSIONS)
        }), 400

    try:
        unique_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        filename = f"{unique_id}_{original_filename}"

        upload_result = cloudinary.uploader.upload(file)
        file_url = upload_result.get("secure_url")

        if not file_url:
            return jsonify({"error": "Failed to upload file"}), 500

        qr_filename = f"{unique_id}_qr.png"
        qr_path = os.path.join(QR_FOLDER, qr_filename)

        generate_qr(file_url, qr_path)

        return jsonify({
            "status": "success",
            "message": "File uploaded and QR generated successfully",
            "file_url": file_url,
            "qr_url": f"/qr/{qr_filename}"
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Something went wrong",
            "error": str(e)
        }), 500


@app.route("/qr/<filename>")
def get_qr(filename):
    return send_from_directory(QR_FOLDER, filename)

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({
        "error": "File too large. Maximum size is 10MB."
    }), 413

if __name__ == "__main__":
    app.run(debug=True)