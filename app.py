from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    filename = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filename)

    # Resize and crop the image
    with Image.open(filename) as img:
        original_width, original_height = img.size
        target_width, target_height = 1080, 1920
        
        # Calculate the new size while maintaining aspect ratio
        aspect_ratio = original_width / original_height
        if aspect_ratio > target_width / target_height:
            new_height = target_height
            new_width = int(aspect_ratio * new_height)
        else:
            new_width = target_width
            new_height = int(new_width / aspect_ratio)
        
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Calculate cropping box
        left = (new_width - target_width) / 2
        top = (new_height - target_height) / 2
        right = (new_width + target_width) / 2
        bottom = (new_height + target_height) / 2

        img = img.crop((left, top, right, bottom))
        img.save(filename)
    
    return jsonify({'message': 'Image uploaded and resized successfully', 'filename': filename})

@app.route('/download/<filename>', methods=['GET'])
def download_image(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_image(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'message': 'File deleted successfully'})
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
