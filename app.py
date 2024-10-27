from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import os
import schedule
import time
import threading
import datetime


scheduler = None  # Global variable to hold the scheduler

app = Flask(__name__)
CORS(app, origins="*")

IMAGE_SIZES = {
    'youtube-thumbnail': (1280, 720),
    'youtube-cover': (2560, 1440),
    'youtube-end-screen': (1920, 1080),
    'youtube-channel-art': (2560, 1440),
    'youtube-banner': (2560, 1440),

    'facebook-story': (1080, 1920),
    'facebook-square': (1200, 1200),
    'facebook-event-cover': (1920, 1080),
    'facebook-cover': (1600, 900),
    'facebook-post': (1200, 630),
    'facebook-ad': (1200, 628),
    'facebook-group-cover': (1640, 856),
    'facebook-cover-photo': (820, 312),

    'instagram-story': (1080, 1920),
    'instagram-portrait': (1080, 1350),
    'instagram-post': (1080, 1080),
    'instagram-landscape': (1080, 566)
}

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def cleanup_folder():
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Removed {filename} at {datetime.datetime.now()}")
        except Exception as e:
            print(f"Error removing {filename} at {datetime.datetime.now()}: {str(e)}")

# Schedule the cleanup_folder function to run every 5 minutes
schedule.every(5).minutes.do(cleanup_folder)

def reset_scheduler():
    global scheduler
    if scheduler:
        # Stop the currently running scheduler
        schedule.clear(scheduler)

    # Create a new scheduler and schedule the cleanup_folder function
    scheduler = schedule.every(5).minutes.do(cleanup_folder)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'Hello World!'})


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
        target_width, target_height = IMAGE_SIZES.get(request.form.get('format', 'youtube-thumbnail'), (1280, 720))
        
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
        reset_scheduler()
    
    return jsonify({'message': 'Image uploaded and resized successfully', 'filename': filename.split('/')[-1]})

@app.route('/download/<filename>', methods=['GET'])
def download_image(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    print(f"Requested file: {filename}")  # Debugging print
    print(f"Full path: {path}")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    else:
        print("File not found")  # Debugging print
        return jsonify({'error': 'File not found'}), 404

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_image(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'message': 'File deleted successfully'})
    else:
        return jsonify({'error': 'File not found'}), 404

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    print("Starting Flask app and cleanup scheduler...")
    reset_scheduler()  # Schedule the cleanup_folder function initially
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    app.run(port=8100, debug=False)
